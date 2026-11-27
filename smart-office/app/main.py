

from __future__ import annotations

import sys
from datetime import datetime, timedelta

import db
from db import (
    BookingConflict,
    BookingError,
    available_rooms,
    below_average_utilization,
    cancel_booking,
    check_in,
    check_out,
    current_availability,
    mongo_add_amenity,
    mongo_amenity_report,
    mongo_resource,
    mongo_resources_with_amenity,
    no_shows,
    peak_booking_hours,
    query_all,
    query_one,
    reserve_desk,
    zone_utilization,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def parse_dt(s: str) -> datetime:
    """Accept 'YYYY-MM-DD HH:MM' or ISO with T."""
    s = s.strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Bad datetime: {s!r} (use 'YYYY-MM-DD HH:MM')")


def hr(title: str = "") -> None:
    print("\n" + "=" * 68)
    if title:
        print(title)
        print("=" * 68)


def print_rows(rows: list[dict]) -> None:
    if not rows:
        print("  (no rows)")
        return
    headers = list(rows[0].keys())
    widths = [max(len(str(h)), *(len(str(r.get(h, ""))) for r in rows)) for h in headers]
    print("  " + " | ".join(str(h).ljust(w) for h, w in zip(headers, widths)))
    print("  " + "-+-".join("-" * w for w in widths))
    for r in rows:
        print("  " + " | ".join(str(r.get(h, "")).ljust(w) for h, w in zip(headers, widths)))


# ------------------------------------------------------------------
# Seed demo data
# ------------------------------------------------------------------
def seed_demo_data() -> None:
    """Insert sample employees, desks, and bookings if the DB is empty."""
    hr("Seeding demo data")

    if query_one("SELECT COUNT(*) AS c FROM employee")["c"] > 0:
        print("  Employee table already populated; skipping seed.")
        return

    emps = [
        ("Alice",  "alice@corp.com",  "EMPLOYEE"),
        ("Bob",    "bob@corp.com",    "EMPLOYEE"),
        ("Carol",  "carol@corp.com",  "FACILITY_MANAGER"),
        ("Dave",   "dave@corp.com",   "ADMIN"),
        ("Eve",    "eve@corp.com",    "SECURITY"),
        ("Frank",  "frank@corp.com",  "EMPLOYEE"),
        ("Grace",  "grace@corp.com",  "EMPLOYEE"),
        ("Heidi",  "heidi@corp.com",  "EMPLOYEE"),
    ]
    for name, email, role in emps:
        db.execute(
            "INSERT INTO employee (emp_name, email, role) VALUES (%s, %s, %s)",
            (name, email, role),
        )
    print(f"  + {len(emps)} employees")

    floors = [("Ground", "HQ"), ("First", "HQ"), ("Second", "HQ")]
    for fn, b in floors:
        db.execute("INSERT INTO floor (floor_name, building) VALUES (%s, %s)", (fn, b))

    zones = [
        (1, "Open Hot Desks"), (1, "Quiet Zone"),
        (2, "Meeting Wing"),   (2, "Cabins"),
        (3, "Collab"),         (3, "Focus"),
    ]
    for fid, zn in zones:
        db.execute("INSERT INTO zone (floor_id, zone_name) VALUES (%s, %s)", (fid, zn))

    desks = [
        (1, "D-101", "HOT_DESK", 1),
        (1, "D-102", "HOT_DESK", 1),
        (1, "D-103", "HOT_DESK", 1),
        (2, "D-201", "HOT_DESK", 1),
        (2, "D-202", "HOT_DESK", 1),
        (3, "MR-301", "MEETING_ROOM", 20),
        (3, "MR-302", "MEETING_ROOM", 12),
        (4, "C-401", "CABIN", 4),
        (4, "C-402", "CABIN", 6),
        (5, "D-501", "HOT_DESK", 1),
        (5, "D-502", "HOT_DESK", 1),
        (6, "D-601", "HOT_DESK", 1),
        (6, "D-602", "HOT_DESK", 1),
    ]
    for zid, code, typ, cap in desks:
        db.execute(
            "INSERT INTO desk (zone_id, desk_code, desk_type, capacity) VALUES (%s, %s, %s, %s)",
            (zid, code, typ, cap),
        )
    print(f"  + {len(desks)} desks/rooms")

    # Historical bookings to make reports meaningful
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    sample = [
        (1, 1, today + timedelta(hours=9),  today + timedelta(hours=11)),
        (1, 2, today + timedelta(hours=11), today + timedelta(hours=13)),
        (2, 3, today + timedelta(hours=9),  today + timedelta(hours=10)),
        (2, 6, today + timedelta(hours=14), today + timedelta(hours=16)),
        (6, 1, today + timedelta(hours=13), today + timedelta(hours=15)),
        (6, 7, today + timedelta(hours=16), today + timedelta(hours=18)),
        (3, 4, today + timedelta(days=1, hours=9), today + timedelta(days=1, hours=12)),
    ]
    for desk_id, emp_id, s, e in sample:
        db.execute(
            "INSERT INTO booking (desk_id, emp_id, start_time, end_time, status) "
            "VALUES (%s, %s, %s, %s, 'CONFIRMED')",
            (desk_id, emp_id, s, e),
        )
    print(f"  + {len(sample)} bookings")

    # One check-in so "no-show" report is non-empty
    first_booking = query_one("SELECT booking_id FROM booking ORDER BY booking_id LIMIT 1")
    if first_booking:
        check_in(first_booking["booking_id"])
    print("  + 1 access_log (check-in)")

    print("  Seeding complete.")


# ------------------------------------------------------------------
# Scenarios
# ------------------------------------------------------------------
def demo_availability() -> None:
    hr("Availability: rooms with capacity >= 20 for tomorrow 12:00-14:00")
    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
    rows = available_rooms(20, tomorrow, tomorrow + timedelta(hours=2))
    print_rows(rows)


def demo_reports() -> None:
    hr("Reports")

    print("\n[Peak booking hours]")
    print_rows(peak_booking_hours(5))

    print("\n[Zone utilization ranking]")
    print_rows(zone_utilization())

    print("\n[No-shows: confirmed bookings without check-in]")
    print_rows(no_shows())

    print("\n[Desks below average utilization]")
    print_rows(below_average_utilization())

    print("\n[Current availability view]")
    print_rows(current_availability())


def demo_mongo() -> None:
    hr("MongoDB extension")
    print("[Resource config for D-102 (resource_id=2)]")
    print(" ", mongo_resource(2))

    print("\n[Resources with 'Dual Monitor']")
    print_rows(mongo_resources_with_amenity("Dual Monitor"))

    print("\n[Add 'Wireless Charger' to resource 4]")
    mongo_add_amenity(4, "Wireless Charger", 1)
    print("  done")

    print("\n[Amenity inventory per zone (aggregation)]")
    print_rows(mongo_amenity_report())


def demo_booking_conflict() -> None:
    hr("Booking conflict demo — Desk 2 (D-102)")

    tomorrow = (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_a = tomorrow + timedelta(hours=10)
    end_a   = tomorrow + timedelta(hours=12)
    start_b = tomorrow + timedelta(hours=11)
    end_b   = tomorrow + timedelta(hours=13)

    print(f"  Booking A: desk 2, emp 1, {start_a} -> {end_a}")
    try:
        bid = reserve_desk(2, 1, start_a, end_a)
        print(f"  ✓ Booked A: booking_id={bid}")
    except BookingError as e:
        print(f"  ✗ Booked A failed: {e}")
        return

    print(f"  Booking B: desk 2, emp 2, {start_b} -> {end_b}  (SHOULD FAIL)")
    try:
        reserve_desk(2, 2, start_b, end_b)
        print("  ✗ UNEXPECTED — B was booked!")
    except BookingConflict as e:
        print(f"  ✓ Blocked as expected: {e}")

    print("  Non-overlapping booking C: 13:00 -> 14:00")
    try:
        bid_c = reserve_desk(2, 2, end_b, end_b + timedelta(hours=1))
        print(f"  ✓ Booked C: booking_id={bid_c}")
    except (BookingConflict, BookingError) as e:
        print(f"  ✗ Booked C failed: {e}")


def demo_checkin_out() -> None:
    hr("Check-in / check-out")
    row = query_one(
        "SELECT booking_id FROM booking WHERE status='CONFIRMED' "
        "ORDER BY booking_id DESC LIMIT 1"
    )
    if not row:
        print("  No bookings to test.")
        return
    bid = row["booking_id"]
    check_in(bid);   print(f"  ✓ check_in  booking {bid}")
    check_out(bid);  print(f"  ✓ check_out booking {bid}")
    print_rows(query_all("SELECT * FROM access_log WHERE booking_id=%s", (bid,)))


def demo_cancel() -> None:
    hr("Cancellation")
    row = query_one(
        "SELECT booking_id FROM booking WHERE status='CONFIRMED' "
        "ORDER BY booking_id DESC LIMIT 1"
    )
    if not row:
        print("  No bookings to cancel.")
        return
    bid = row["booking_id"]
    cancel_booking(bid, reason="demo cancellation")
    print(f"  ✓ Cancelled booking {bid}")
    print_rows(query_all("SELECT * FROM cancellation WHERE booking_id=%s", (bid,)))


def concurrency_guide() -> None:
    hr("Two-session concurrency test — follow along in MySQL CLI")
    print("""\
Open TWO terminals connected to MySQL as different users (alice / bob):

---- TERMINAL 1 (Alice) ----
  USE smart_office;
  START TRANSACTION;
  SELECT desk_id FROM desk WHERE desk_id = 2 FOR UPDATE;
  SELECT booking_id FROM booking
   WHERE desk_id=2 AND status='CONFIRMED'
     AND start_time < '2026-11-22 12:00:00'
     AND end_time   > '2026-11-22 10:00:00'
   FOR UPDATE;
  -- (leave this transaction open)

---- TERMINAL 2 (Bob) ----
  USE smart_office;
  START TRANSACTION;
  SELECT desk_id FROM desk WHERE desk_id = 2 FOR UPDATE;
  -- ⏳ BLOCKS — Alice holds the row lock

---- BACK TO TERMINAL 1 ----
  INSERT INTO booking (desk_id, emp_id, start_time, end_time)
  VALUES (2, 1, '2026-11-22 10:00:00', '2026-11-22 12:00:00');
  COMMIT;

---- TERMINAL 2 unblocks ----
  -- the SELECT ... FOR UPDATE now returns the new row -> conflict
  ROLLBACK;

Take screenshots at each step for the report.
""")


# ------------------------------------------------------------------
# Interactive menu
# ------------------------------------------------------------------
def menu() -> None:
    while True:
        hr("Smart Office CLI")
        print(
            " 1) Seed demo data\n"
            " 2) Availability query\n"
            " 3) Reports (peak, zones, no-shows, below-avg, view)\n"
            " 4) MongoDB demo\n"
            " 5) Booking conflict demo (programmatic)\n"
            " 6) Check-in / check-out demo\n"
            " 7) Cancel booking demo\n"
            " 8) Two-session concurrency guide\n"
            " 0) Exit"
        )
        choice = input(" > ").strip()
        try:
            if choice == "1": seed_demo_data()
            elif choice == "2": demo_availability()
            elif choice == "3": demo_reports()
            elif choice == "4": demo_mongo()
            elif choice == "5": demo_booking_conflict()
            elif choice == "6": demo_checkin_out()
            elif choice == "7": demo_cancel()
            elif choice == "8": concurrency_guide()
            elif choice == "0":
                print("Bye.")
                return
            else:
                print("  Unknown choice.")
        except Exception as e:
            print(f"  ERROR: {e}")


# ------------------------------------------------------------------
# Argv dispatch
# ------------------------------------------------------------------
def main(argv: list[str]) -> int:
    if not argv or argv[0] == "menu":
        menu()
        return 0

    cmd = argv[0]
    try:
        if cmd == "seed":
            seed_demo_data()
        elif cmd == "demo":
            seed_demo_data()
            demo_availability()
            demo_reports()
            demo_mongo()
            demo_booking_conflict()
            demo_checkin_out()
        elif cmd == "book":
            desk, emp, s, e = argv[1], argv[2], argv[3], argv[4]
            bid = reserve_desk(int(desk), int(emp), parse_dt(s), parse_dt(e))
            print(f"Booked: booking_id={bid}")
        elif cmd == "availability":
            cap, s, e = int(argv[1]), argv[2], argv[3]
            print_rows(available_rooms(cap, parse_dt(s), parse_dt(e)))
        elif cmd == "reports":
            demo_reports()
        elif cmd == "concurrency":
            concurrency_guide()
        else:
            print(__doc__)
            return 1
        return 0
    except (BookingConflict, BookingError) as e:
        print(f"Booking error: {e}", file=sys.stderr)
        return 2
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))