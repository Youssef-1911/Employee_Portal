-- infra/init.sql
-- Demo database seed for Employee Portal

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    national_id VARCHAR(20),
    bank_account VARCHAR(30),
    department VARCHAR(50),
    role VARCHAR(20) DEFAULT 'employee',
    phone VARCHAR(20),
    address TEXT,
    emergency_contact VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payroll (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    period VARCHAR(20) NOT NULL,
    gross_salary NUMERIC(10,2) NOT NULL,
    net_salary NUMERIC(10,2) NOT NULL,
    deductions NUMERIC(10,2) DEFAULT 0,
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(id),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id INTEGER REFERENCES employees(id),
    filename VARCHAR(255) NOT NULL,
    s3_key VARCHAR(500) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    actor_id INTEGER,
    action VARCHAR(100),
    target_table VARCHAR(50),
    target_id VARCHAR(100),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Seed demo employees
INSERT INTO employees (name, email, national_id, bank_account, department, role) VALUES
('Alice Johnson', 'alice@company.com', 'NID-001-2001', 'GB29NWBK60161331926819', 'Engineering', 'employee'),
('Bob Smith', 'bob@company.com', 'NID-002-1998', 'GB29NWBK60161331926820', 'HR', 'admin'),
('Carol White', 'carol@company.com', 'NID-003-1995', 'GB29NWBK60161331926821', 'Finance', 'employee'),
('David Brown', 'david@company.com', 'NID-004-2000', 'GB29NWBK60161331926822', 'Engineering', 'employee');

-- Seed demo payroll
INSERT INTO payroll (employee_id, period, gross_salary, net_salary, deductions) VALUES
(1, '2024-03', 85000.00, 62000.00, 23000.00),
(2, '2024-03', 72000.00, 54000.00, 18000.00),
(3, '2024-03', 91000.00, 66000.00, 25000.00),
(4, '2024-03', 78000.00, 57000.00, 21000.00);
