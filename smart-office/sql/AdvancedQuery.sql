SELECT d.desk_id, d.desk_code, d.capacity
FROM desk d
LEFT JOIN booking b
  ON b.desk_id = d.desk_id
 AND b.status = 'CONFIRMED'
 AND b.start_time < '2026-11-22 14:00:00'
 AND b.end_time   > '2026-11-22 12:00:00'
WHERE d.capacity >= 20
  AND b.booking_id IS NULL;


SELECT HOUR(start_time) AS hour_of_day, COUNT(*) AS bookings
FROM booking
WHERE status = 'CONFIRMED'
GROUP BY HOUR(start_time)
ORDER BY bookings DESC;

SELECT z.zone_name,
       COUNT(b.booking_id) AS bookings,
       RANK() OVER (ORDER BY COUNT(b.booking_id) DESC) AS zone_rank
FROM zone z
JOIN desk d ON d.zone_id = z.zone_id
LEFT JOIN booking b ON b.desk_id = d.desk_id AND b.status='CONFIRMED'
GROUP BY z.zone_id, z.zone_name;

SELECT e.emp_name, b.booking_id, b.start_time
FROM booking b
JOIN employee e ON e.emp_id = b.emp_id
LEFT JOIN access_log a ON a.booking_id = b.booking_id
WHERE b.status = 'CONFIRMED'
  AND a.log_id IS NULL;

WITH util AS (
    SELECT d.desk_id, d.desk_code, COUNT(b.booking_id) AS uses
    FROM desk d
    LEFT JOIN booking b ON b.desk_id = d.desk_id AND b.status='CONFIRMED'
    GROUP BY d.desk_id, d.desk_code
)
SELECT * FROM util
WHERE uses < (SELECT AVG(uses) FROM util);

WITH RECURSIVE days AS (
    SELECT DATE('2026-11-01') AS d
    UNION ALL
    SELECT d + INTERVAL 1 DAY FROM days WHERE d < '2026-11-30'
)

SELECT days.d, COUNT(b.booking_id) AS bookings
FROM days
LEFT JOIN booking b
  ON DATE(b.start_time) = days.d AND b.status='CONFIRMED'
GROUP BY days.d
ORDER BY days.d;


CREATE VIEW v_current_availability AS
SELECT d.desk_id, d.desk_code, d.capacity
FROM desk d
LEFT JOIN booking b
  ON b.desk_id = d.desk_id
 AND b.status='CONFIRMED'
 AND NOW() BETWEEN b.start_time AND b.end_time
WHERE b.booking_id IS NULL;


