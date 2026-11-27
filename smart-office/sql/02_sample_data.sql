INSERT INTO floor (floor_name, building) VALUES
('Ground','HQ'),('First','HQ'),('Second','HQ');

INSERT INTO zone (floor_id, zone_name) VALUES
(1,'Open Hot Desks'),(1,'Quiet Zone'),(2,'Meeting Wing'),(2,'Cabins'),(3,'Collab'),(3,'Focus');

INSERT INTO desk (zone_id, desk_code, desk_type, capacity) VALUES
(1,'D-101','HOT_DESK',1),(1,'D-102','HOT_DESK',1),(1,'D-103','HOT_DESK',1),
(2,'D-201','HOT_DESK',1),(2,'D-202','HOT_DESK',1),
(3,'MR-301','MEETING_ROOM',20),(3,'MR-302','MEETING_ROOM',12),
(4,'C-401','CABIN',4),(4,'C-402','CABIN',6),
(5,'D-501','HOT_DESK',1),(5,'D-502','HOT_DESK',1),
(6,'D-601','HOT_DESK',1),(6,'D-602','HOT_DESK',1);

INSERT INTO employee (emp_name,email,role) VALUES
('Alice','alice@corp.com','EMPLOYEE'),
('Bob','bob@corp.com','EMPLOYEE'),
('Carol','carol@corp.com','FACILITY_MANAGER'),
('Dave','dave@corp.com','ADMIN'),
('Eve','eve@corp.com','SECURITY');