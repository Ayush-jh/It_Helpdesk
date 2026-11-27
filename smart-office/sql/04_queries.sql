USE smart_office;
START TRANSACTION;
SELECT desk_id FROM desk WHERE desk_id = 2 FOR UPDATE;
SELECT COUNT(*) FROM booking
WHERE desk_id=2 AND status='CONFIRMED'
  AND start_time < '2026-11-22 12:00:00'
  AND end_time   > '2026-11-22 10:00:00'
FOR UPDATE;
-- returns 0 → no conflict
-- (hold transaction open for now)