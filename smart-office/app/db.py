

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterable, Sequence

import mysql.connector
from mysql.connector import Error as MySQLError, pooling
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# ------------------------------------------------------------------
# Configuration (override via environment variables)
# ------------------------------------------------------------------
MYSQL_CONFIG = {
    "host":     os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port":     int(os.getenv("MYSQL_PORT", "3306")),
    "user":     os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "12521198"),
    "database": os.getenv("MYSQL_DB", "smart_office"),
    "autocommit": False,
    "charset": "utf8mb4",
    "collation": "utf8mb4_0900_ai_ci",
}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
MONGO_DB  = os.getenv("MONGO_DB", "smart_office")


# ------------------------------------------------------------------
# MySQL connection pool
# ------------------------------------------------------------------
_pool: pooling.MySQLConnectionPool | None = None


def init_pool(pool_size: int = 8) -> None:
    """Initialize the MySQL connection pool (call once at app startup)."""
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="smart_office_pool",
            pool_size=pool_size,
            **MYSQL_CONFIG,
        )


@contextmanager
def get_conn():
    """Yield a pooled MySQL connection; rollback on exception."""
    if _pool is None:
        init_pool()
    conn = _pool.get_connection()
    try:
        yield conn
        conn.commit()
    except MySQLError:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor(dictionary: bool = True):
    """Yield a cursor + its connection, committing on success."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=dictionary)
        try:
            yield cur
        finally:
            cur.close()


# ------------------------------------------------------------------
# Parameterized query helpers (SQL-injection safe)
# ------------------------------------------------------------------
def query_all(sql: str, params: Sequence[Any] = ()) -> list[dict]:
    """Run SELECT, return all rows as dicts."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def query_one(sql: str, params: Sequence[Any] = ()) -> dict | None:
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def execute(sql: str, params: Sequence[Any] = ()) -> int:
    """Run INSERT/UPDATE/DELETE, return lastrowid (or rowcount)."""
    with get_cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid or cur.rowcount


# ------------------------------------------------------------------
# Transaction-safe booking with conflict prevention
# ------------------------------------------------------------------
class BookingConflict(Exception):
    """Raised when the requested interval overlaps an existing booking."""


class BookingError(Exception):
    """Raised for any other booking failure."""


def reserve_desk(
    desk_id: int,
    emp_id: int,
    start_time: datetime,
    end_time: datetime,
    lock_wait_seconds: int = 5,
) -> int:
    """
    Atomically reserve a desk for [start_time, end_time).

    Strategy:
      1. START TRANSACTION
      2. SELECT ... FOR UPDATE on the desk row -> serializes all bookings
         for this desk.
      3. Overlap check using the standard interval-intersection predicate:
             new_start < existing_end AND new_end > existing_start
      4. If conflict -> rollback + BookingConflict
         Else        -> INSERT booking + COMMIT
      5. InnoDB applies next-key (gap) locks on the conflict-check range,
         preventing phantom inserts under REPEATABLE READ.
    """
    if end_time <= start_time:
        raise BookingError("end_time must be after start_time")

    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            # Tighten the wait so deadlocks/long locks surface quickly
            cur.execute(f"SET SESSION innodb_lock_wait_timeout = {int(lock_wait_seconds)}")

            # Lock the desk row to serialize bookings on this desk
            cur.execute(
                "SELECT desk_id FROM desk WHERE desk_id = %s FOR UPDATE",
                (desk_id,),
            )
            if cur.fetchone() is None:
                raise BookingError(f"Desk {desk_id} does not exist")

            # Overlap check (locks matching booking rows / gaps)
            cur.execute(
                """
                SELECT booking_id
                FROM booking
                WHERE desk_id = %s
                  AND status = 'CONFIRMED'
                  AND start_time < %s
                  AND end_time   > %s
                FOR UPDATE
                """,
                (desk_id, end_time, start_time),
            )
            if cur.fetchone() is not None:
                raise BookingConflict(
                    f"Desk {desk_id} is already booked for the requested interval"
                )

            cur.execute(
                """
                INSERT INTO booking (desk_id, emp_id, start_time, end_time, status)
                VALUES (%s, %s, %s, %s, 'CONFIRMED')
                """,
                (desk_id, emp_id, start_time, end_time),
            )
            return cur.lastrowid
        finally:
            cur.close()


# ------------------------------------------------------------------
# High-level read helpers
# ------------------------------------------------------------------
def available_rooms(min_capacity: int, start_time: datetime, end_time: datetime) -> list[dict]:
    """Rooms/desks with capacity >= min_capacity that are free in the interval."""
    return query_all(
        """
        SELECT d.desk_id, d.desk_code, d.capacity
        FROM desk d
        LEFT JOIN booking b
          ON b.desk_id = d.desk_id
         AND b.status = 'CONFIRMED'
         AND b.start_time < %s
         AND b.end_time   > %s
        WHERE d.capacity >= %s
          AND b.booking_id IS NULL
        ORDER BY d.capacity DESC, d.desk_code
        """,
        (end_time, start_time, min_capacity),
    )


def peak_booking_hours(limit: int = 24) -> list[dict]:
    return query_all(
        """
        SELECT HOUR(start_time) AS hour_of_day, COUNT(*) AS bookings
        FROM booking
        WHERE status = 'CONFIRMED'
        GROUP BY HOUR(start_time)
        ORDER BY bookings DESC
        LIMIT %s
        """,
        (limit,),
    )


def zone_utilization() -> list[dict]:
    return query_all(
        """
        SELECT z.zone_name,
               COUNT(b.booking_id) AS bookings,
               RANK() OVER (ORDER BY COUNT(b.booking_id) DESC) AS zone_rank
        FROM zone z
        JOIN desk d ON d.zone_id = z.zone_id
        LEFT JOIN booking b
          ON b.desk_id = d.desk_id AND b.status = 'CONFIRMED'
        GROUP BY z.zone_id, z.zone_name
        ORDER BY zone_rank
        """
    )


def no_shows() -> list[dict]:
    """Employees with confirmed bookings but no check-in."""
    return query_all(
        """
        SELECT e.emp_name, b.booking_id, b.start_time, b.end_time
        FROM booking b
        JOIN employee e ON e.emp_id = b.emp_id
        LEFT JOIN access_log a ON a.booking_id = b.booking_id
        WHERE b.status = 'CONFIRMED'
          AND a.log_id IS NULL
        ORDER BY b.start_time
        """
    )


def below_average_utilization() -> list[dict]:
    return query_all(
        """
        WITH util AS (
            SELECT d.desk_id, d.desk_code, COUNT(b.booking_id) AS uses
            FROM desk d
            LEFT JOIN booking b
              ON b.desk_id = d.desk_id AND b.status = 'CONFIRMED'
            GROUP BY d.desk_id, d.desk_code
        )
        SELECT * FROM util
        WHERE uses < (SELECT AVG(uses) FROM util)
        ORDER BY uses
        """
    )


def current_availability() -> list[dict]:
    return query_all("SELECT * FROM v_current_availability ORDER BY desk_code")


def check_in(booking_id: int) -> None:
    """Record a check-in event. Idempotent on the same booking."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT log_id FROM access_log WHERE booking_id = %s",
            (booking_id,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE access_log SET check_in = COALESCE(check_in, NOW()) WHERE log_id = %s",
                (row["log_id"],),
            )
        else:
            cur.execute(
                "INSERT INTO access_log (booking_id, check_in) VALUES (%s, NOW())",
                (booking_id,),
            )


def check_out(booking_id: int) -> None:
    with get_cursor() as cur:
        cur.execute(
            "UPDATE access_log SET check_out = NOW() WHERE booking_id = %s",
            (booking_id,),
        )


def cancel_booking(booking_id: int, reason: str = "") -> None:
    """Cancel a booking atomically and write the cancellation record."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT booking_id, status FROM booking WHERE booking_id = %s FOR UPDATE",
                (booking_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise BookingError("Booking not found")
            if row["status"] != "CONFIRMED":
                raise BookingError(f"Cannot cancel booking in status {row['status']}")
            cur.execute(
                "UPDATE booking SET status = 'CANCELLED' WHERE booking_id = %s",
                (booking_id,),
            )
            cur.execute(
                "INSERT INTO cancellation (booking_id, reason) VALUES (%s, %s)",
                (booking_id, reason),
            )
        finally:
            cur.close()


# ------------------------------------------------------------------
# MongoDB helpers
# ------------------------------------------------------------------
_mongo_client: MongoClient | None = None


def get_mongo():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
    return _mongo_client[MONGO_DB]


def mongo_resource(resource_id: int) -> dict | None:
    return get_mongo().resource_configs.find_one(
        {"resource_id": resource_id}, {"_id": 0}
    )


def mongo_resources_with_amenity(name: str) -> list[dict]:
    return list(
        get_mongo().resource_configs.find(
            {"amenities.name": name},
            {"_id": 0, "resource_id": 1, "desk_code": 1, "zone": 1},
        )
    )


def mongo_add_amenity(resource_id: int, name: str, count: int = 1) -> None:
    get_mongo().resource_configs.update_one(
        {"resource_id": resource_id},
        {
            "$push": {"amenities": {"name": name, "count": count}},
            "$set": {"updated_at": datetime.utcnow()},
        },
    )


def mongo_amenity_report() -> list[dict]:
    """Aggregation: total amenity units per zone."""
    return list(
        get_mongo().resource_configs.aggregate(
            [
                {"$unwind": "$amenities"},
                {
                    "$group": {
                        "_id": "$zone",
                        "total_units": {"$sum": "$amenities.count"},
                        "distinct": {"$addToSet": "$amenities.name"},
                    }
                },
                {
                    "$project": {
                        "zone": "$_id",
                        "_id": 0,
                        "total_units": 1,
                        "distinct_count": {"$size": "$distinct"},
                    }
                },
                {"$sort": {"total_units": -1}},
            ]
        )
    )


def close() -> None:
    """Clean shutdown: close MySQL pool and Mongo client."""
    global _pool, _mongo_client
    _pool = None
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


# ------------------------------------------------------------------
# Small demo when run directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    from datetime import timedelta

    print("Testing connections ...")
    print("Employees:", len(query_all("SELECT * FROM employee")))
    print("Resources (Mongo):", get_mongo().resource_configs.count_documents({}))
    print("Availability view rows:", len(current_availability()))
    print("Peak hours:", peak_booking_hours(3))
    print("Zone utilization:", zone_utilization()[:3])
    print("Mongo amenity report:", mongo_amenity_report()[:3])
    close()