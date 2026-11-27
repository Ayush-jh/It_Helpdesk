# """
# server.py — Flask API for the Smart Office UI.

# Reuses app/db.py. Run from project root:
#     python -m api.server
# Then open http://127.0.0.1:5000/ in a browser (it serves ui/ as static).
# """

# import sys, os
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# from datetime import datetime
# from flask import Flask, jsonify, request, send_from_directory
# from flask_cors import CORS

# import db
# from db import (
#     BookingConflict, BookingError,
#     reserve_desk, available_rooms, peak_booking_hours,
#     zone_utilization, no_shows, below_average_utilization,
#     current_availability, check_in, check_out, cancel_booking,
#     query_all, query_one, execute,
#     mongo_resource, mongo_resources_with_amenity,
#     mongo_add_amenity, mongo_amenity_report,
# )

# UI_DIR = os.path.join(os.path.dirname(__file__), "..", "ui")
# app = Flask(__name__, static_folder=UI_DIR, static_url_path="")
# CORS(app)


# def parse_dt(s):
#     s = s.replace("T", " ")
#     for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
#         try: return datetime.strptime(s, fmt)
#         except ValueError: pass
#     raise ValueError(f"Bad datetime: {s!r}")


# # ---------------------------------------------------------------
# # Serve UI
# # ---------------------------------------------------------------
# @app.route("/")
# def index():
#     return send_from_directory(UI_DIR, "index.html")


# # ---------------------------------------------------------------
# # Reference data
# # ---------------------------------------------------------------
# @app.get("/api/employees")
# def api_employees():
#     return jsonify(query_all(
#         "SELECT emp_id, emp_name, email, role FROM employee ORDER BY emp_name"))


# @app.get("/api/desks")
# def api_desks():
#     return jsonify(query_all("""
#         SELECT d.desk_id, d.desk_code, d.desk_type, d.capacity,
#                z.zone_name, f.floor_name
#         FROM desk d
#         JOIN zone z ON z.zone_id = d.zone_id
#         JOIN floor f ON f.floor_id = z.floor_id
#         ORDER BY f.floor_name, z.zone_name, d.desk_code"""))


# @app.get("/api/bookings")
# def api_bookings():
#     return jsonify(query_all("""
#         SELECT b.booking_id, b.desk_id, d.desk_code,
#                b.emp_id, e.emp_name,
#                b.start_time, b.end_time, b.status
#         FROM booking b
#         JOIN desk d ON d.desk_id = b.desk_id
#         JOIN employee e ON e.emp_id = b.emp_id
#         ORDER BY b.start_time DESC
#         LIMIT 200"""))


# # ---------------------------------------------------------------
# # Book / cancel / check-in / check-out
# # ---------------------------------------------------------------
# @app.post("/api/bookings")
# def api_create_booking():
#     data = request.get_json(force=True)
#     try:
#         bid = reserve_desk(
#             int(data["desk_id"]),
#             int(data["emp_id"]),
#             parse_dt(data["start_time"]),
#             parse_dt(data["end_time"]),
#         )
#         return jsonify({"ok": True, "booking_id": bid}), 201
#     except BookingConflict as e:
#         return jsonify({"ok": False, "error": str(e), "type": "conflict"}), 409
#     except (BookingError, ValueError) as e:
#         return jsonify({"ok": False, "error": str(e), "type": "bad_request"}), 400


# @app.post("/api/bookings/<int:bid>/cancel")
# def api_cancel(bid):
#     reason = (request.get_json(silent=True) or {}).get("reason", "")
#     try:
#         cancel_booking(bid, reason)
#         return jsonify({"ok": True})
#     except BookingError as e:
#         return jsonify({"ok": False, "error": str(e)}), 400


# @app.post("/api/bookings/<int:bid>/checkin")
# def api_checkin(bid):
#     try:
#         check_in(bid); return jsonify({"ok": True})
#     except Exception as e:
#         return jsonify({"ok": False, "error": str(e)}), 400


# @app.post("/api/bookings/<int:bid>/checkout")
# def api_checkout(bid):
#     try:
#         check_out(bid); return jsonify({"ok": True})
#     except Exception as e:
#         return jsonify({"ok": False, "error": str(e)}), 400


# # ---------------------------------------------------------------
# # Reports
# # ---------------------------------------------------------------
# @app.get("/api/availability")
# def api_availability():
#     cap = int(request.args.get("capacity", 1))
#     start = parse_dt(request.args["start"])
#     end = parse_dt(request.args["end"])
#     return jsonify(available_rooms(cap, start, end))


# @app.get("/api/reports/peak-hours")
# def api_peak():       return jsonify(peak_booking_hours(10))

# @app.get("/api/reports/zone-utilization")
# def api_zone():       return jsonify(zone_utilization())

# @app.get("/api/reports/no-shows")
# def api_noshows():    return jsonify(no_shows())

# @app.get("/api/reports/below-average")
# def api_below():      return jsonify(below_average_utilization())

# @app.get("/api/reports/current-availability")
# def api_current():    return jsonify(current_availability())


# # ---------------------------------------------------------------
# # MongoDB
# # ---------------------------------------------------------------
# @app.get("/api/mongo/resources")
# def api_mongo_resources():
#     q = request.args.get("amenity")
#     return jsonify(mongo_resources_with_amenity(q)) if q else jsonify([])

# @app.get("/api/mongo/resource/<int:rid>")
# def api_mongo_resource(rid):
#     r = mongo_resource(rid)
#     return jsonify(r) if r else (jsonify({"error": "not found"}), 404)

# @app.post("/api/mongo/resource/<int:rid>/amenity")
# def api_mongo_add_amenity(rid):
#     d = request.get_json(force=True)
#     mongo_add_amenity(rid, d["name"], int(d.get("count", 1)))
#     return jsonify({"ok": True})

# @app.get("/api/mongo/amenity-report")
# def api_mongo_report(): return jsonify(mongo_amenity_report())


# # ---------------------------------------------------------------
# if __name__ == "__main__":
#     print("→ Open http://127.0.0.1:5000/ in your browser")
#     app.run(host="127.0.0.1", port=5000, debug=True)

"""
server.py — Flask API for the Smart Office UI.

Requires (see app/requirements.txt):
    flask, flask-cors, mysql-connector-python, pymongo, python-dotenv

Run from project root:
    python3.13 -m api.server
Then open http://127.0.0.1:5000/
"""

import sys
import os

# ---------- sys.path setup ----------
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "app"))

# ---------- imports ----------
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import db
from db import (
    BookingConflict, BookingError,
    reserve_desk, available_rooms, peak_booking_hours,
    zone_utilization, no_shows, below_average_utilization,
    current_availability, check_in, check_out, cancel_booking,
    query_all, query_one, execute,
    mongo_resource, mongo_resources_with_amenity,
    mongo_add_amenity, mongo_amenity_report,
)

UI_DIR = os.path.join(_ROOT, "ui")
app = Flask(__name__, static_folder=UI_DIR, static_url_path="")
CORS(app)


def parse_dt(s):
    s = s.replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Bad datetime: {s!r}")


# ---------- Serve UI ----------
@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")


# ---------- Reference data ----------
@app.get("/api/employees")
def api_employees():
    return jsonify(query_all(
        "SELECT emp_id, emp_name, email, role FROM employee ORDER BY emp_name"))


@app.get("/api/desks")
def api_desks():
    return jsonify(query_all("""
        SELECT d.desk_id, d.desk_code, d.desk_type, d.capacity,
               z.zone_name, f.floor_name
        FROM desk d
        JOIN zone z ON z.zone_id = d.zone_id
        JOIN floor f ON f.floor_id = z.floor_id
        ORDER BY f.floor_name, z.zone_name, d.desk_code"""))


@app.get("/api/bookings")
def api_bookings():
    return jsonify(query_all("""
        SELECT b.booking_id, b.desk_id, d.desk_code,
               b.emp_id, e.emp_name,
               b.start_time, b.end_time, b.status
        FROM booking b
        JOIN desk d ON d.desk_id = b.desk_id
        JOIN employee e ON e.emp_id = b.emp_id
        ORDER BY b.start_time DESC
        LIMIT 200"""))


# ---------- Book / cancel / check-in / check-out ----------
@app.post("/api/bookings")
def api_create_booking():
    data = request.get_json(force=True)
    try:
        bid = reserve_desk(
            int(data["desk_id"]),
            int(data["emp_id"]),
            parse_dt(data["start_time"]),
            parse_dt(data["end_time"]),
        )
        return jsonify({"ok": True, "booking_id": bid}), 201
    except BookingConflict as e:
        return jsonify({"ok": False, "error": str(e), "type": "conflict"}), 409
    except (BookingError, ValueError) as e:
        return jsonify({"ok": False, "error": str(e), "type": "bad_request"}), 400


@app.post("/api/bookings/<int:bid>/cancel")
def api_cancel(bid):
    reason = (request.get_json(silent=True) or {}).get("reason", "")
    try:
        cancel_booking(bid, reason)
        return jsonify({"ok": True})
    except BookingError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/bookings/<int:bid>/checkin")
def api_checkin(bid):
    try:
        check_in(bid)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.post("/api/bookings/<int:bid>/checkout")
def api_checkout(bid):
    try:
        check_out(bid)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ---------- Reports ----------
@app.get("/api/availability")
def api_availability():
    cap = int(request.args.get("capacity", 1))
    start = parse_dt(request.args["start"])
    end = parse_dt(request.args["end"])
    return jsonify(available_rooms(cap, start, end))


@app.get("/api/reports/peak-hours")
def api_peak():
    return jsonify(peak_booking_hours(10))


@app.get("/api/reports/zone-utilization")
def api_zone():
    return jsonify(zone_utilization())


@app.get("/api/reports/no-shows")
def api_noshows():
    return jsonify(no_shows())


@app.get("/api/reports/below-average")
def api_below():
    return jsonify(below_average_utilization())


@app.get("/api/reports/current-availability")
def api_current():
    return jsonify(current_availability())


# ---------- MongoDB ----------
@app.get("/api/mongo/resources")
def api_mongo_resources():
    q = request.args.get("amenity")
    return jsonify(mongo_resources_with_amenity(q)) if q else jsonify([])


@app.get("/api/mongo/resource/<int:rid>")
def api_mongo_resource(rid):
    r = mongo_resource(rid)
    return jsonify(r) if r else (jsonify({"error": "not found"}), 404)


@app.post("/api/mongo/resource/<int:rid>/amenity")
def api_mongo_add_amenity(rid):
    d = request.get_json(force=True)
    mongo_add_amenity(rid, d["name"], int(d.get("count", 1)))
    return jsonify({"ok": True})


@app.get("/api/mongo/amenity-report")
def api_mongo_report():
    return jsonify(mongo_amenity_report())


# ---------- Main ----------
if __name__ == "__main__":
    print("→ Open http://127.0.0.1:5000/ in your browser")
    app.run(host="127.0.0.1", port=5000, debug=True)