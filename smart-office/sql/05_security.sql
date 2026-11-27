CREATE ROLE 'employee_role';
CREATE ROLE 'manager_role';
CREATE ROLE 'admin_role';

GRANT SELECT, INSERT ON smart_office.booking TO 'employee_role';
GRANT SELECT ON smart_office.v_current_availability TO 'employee_role';

GRANT SELECT, UPDATE, DELETE ON smart_office.booking TO 'manager_role';
GRANT SELECT ON smart_office.* TO 'manager_role';

GRANT ALL PRIVILEGES ON smart_office.* TO 'admin_role';

CREATE USER 'alice'@'localhost' IDENTIFIED BY 'StrongP@ss1';
CREATE USER 'carol'@'localhost' IDENTIFIED BY 'StrongP@ss2';
GRANT 'employee_role' TO 'alice'@'localhost';
GRANT 'manager_role'  TO 'carol'@'localhost';
SET DEFAULT ROLE 'employee_role' TO 'alice'@'localhost';
SET DEFAULT ROLE 'manager_role'  TO 'carol'@'localhost';




EXPLAIN
SELECT i.incident_id, i.title, u.name, d.name
FROM Incident i
JOIN User u ON i.reported_by = u.user_id
JOIN Department d ON u.department_id = d.department_id
WHERE i.status = 'Open'
ORDER BY i.incident_id DESC
LIMIT 10;