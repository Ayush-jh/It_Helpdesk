DELIMITER $$

CREATE PROCEDURE reserve_desk(
    IN p_desk_id INT,
    IN p_emp_id  INT,
    IN p_start   DATETIME,
    IN p_end     DATETIME
)
BEGIN
    DECLARE v_conflict INT DEFAULT 0;

    START TRANSACTION;

    -- Lock the desk row to serialize all bookings on this desk
    SELECT desk_id INTO @d FROM desk WHERE desk_id = p_desk_id FOR UPDATE;

    -- Check overlap
    SELECT COUNT(*) INTO v_conflict
    FROM booking
    WHERE desk_id = p_desk_id
      AND status = 'CONFIRMED'
      AND start_time < p_end
      AND end_time   > p_start
    FOR UPDATE;

    IF v_conflict > 0 THEN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
          SET MESSAGE_TEXT = 'Booking conflict: overlapping reservation exists.';
    ELSE
        INSERT INTO booking (desk_id, emp_id, start_time, end_time)
        VALUES (p_desk_id, p_emp_id, p_start, p_end);
        COMMIT;
    END IF;
END$$

DELIMITER ;