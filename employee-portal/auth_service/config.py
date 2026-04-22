# auth_service/config.py
# CWE-798: Hardcoded credential in source code

JWT_SECRET = "hr-portal-secret-2024"   # line 9 — INTENTIONAL VULNERABILITY: CWE-798
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 14

DATABASE_URL = "postgresql://db_user:db_pass@localhost:5432/employee_portal"
REDIS_URL = "redis://localhost:6379"

ADMIN_ROLE = "admin"
EMPLOYEE_ROLE = "employee"
