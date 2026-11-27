CREATE DATABASE smart_office;
USE smart_office;

-- Employees
CREATE TABLE employee (
    emp_id      INT PRIMARY KEY AUTO_INCREMENT,
    emp_name    VARCHAR(100) NOT NULL,
    email       VARCHAR(150) UNIQUE NOT NULL,
    role        ENUM('EMPLOYEE','FACILITY_MANAGER','ADMIN','SECURITY') DEFAULT 'EMPLOYEE'
) ENGINE=InnoDB;

-- Floors
CREATE TABLE floor (
    floor_id    INT PRIMARY KEY AUTO_INCREMENT,
    floor_name  VARCHAR(50) NOT NULL,
    building    VARCHAR(100) NOT NULL
) ENGINE=InnoDB;

-- Zones
CREATE TABLE zone (
    zone_id     INT PRIMARY KEY AUTO_INCREMENT,
    floor_id    INT NOT NULL,
    zone_name   VARCHAR(50) NOT NULL,
    FOREIGN KEY (floor_id) REFERENCES floor(floor_id)
) ENGINE=InnoDB;

-- Desks / Rooms
CREATE TABLE desk (
    desk_id     INT PRIMARY KEY AUTO_INCREMENT,
    zone_id     INT NOT NULL,
    desk_code   VARCHAR(20) UNIQUE NOT NULL,
    desk_type   ENUM('HOT_DESK','CABIN','MEETING_ROOM') DEFAULT 'HOT_DESK',
    capacity    INT DEFAULT 1,
    FOREIGN KEY (zone_id) REFERENCES zone(zone_id)
) ENGINE=InnoDB;

-- Bookings (core)
CREATE TABLE booking (
    booking_id  INT PRIMARY KEY AUTO_INCREMENT,
    desk_id     INT NOT NULL,
    emp_id      INT NOT NULL,
    start_time  DATETIME NOT NULL,
    end_time    DATETIME NOT NULL,
    status      ENUM('CONFIRMED','CANCELLED','COMPLETED') DEFAULT 'CONFIRMED',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (desk_id) REFERENCES desk(desk_id),
    FOREIGN KEY (emp_id) REFERENCES employee(emp_id),
    CONSTRAINT chk_time CHECK (end_time > start_time)
) ENGINE=InnoDB;

-- Cancellations
CREATE TABLE cancellation (
    cancel_id    INT PRIMARY KEY AUTO_INCREMENT,
    booking_id   INT NOT NULL,
    cancelled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason       VARCHAR(255),
    FOREIGN KEY (booking_id) REFERENCES booking(booking_id)
) ENGINE=InnoDB;

-- Access / check-in log
CREATE TABLE access_log (
    log_id      INT PRIMARY KEY AUTO_INCREMENT,
    booking_id  INT NOT NULL,
    check_in    DATETIME,
    check_out   DATETIME,
    FOREIGN KEY (booking_id) REFERENCES booking(booking_id)
) ENGINE=InnoDB;

-- Conflict-check index
CREATE INDEX idx_booking_conflict ON booking (desk_id, start_time, end_time);