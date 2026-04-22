# employee_api/views.py
# CWE-89: SQL Injection on payroll endpoint

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from auth_service.config import DATABASE_URL, JWT_SECRET, JWT_ALGORITHM
import jwt

app = FastAPI(title="Employee API")
engine = create_engine(DATABASE_URL)


def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/employees/me")
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    user_id = current_user["sub"]
    with engine.connect() as conn:
        # Safe: using parameterised query
        result = conn.execute(
            text("SELECT id, name, email, department FROM employees WHERE id = :uid"),
            {"uid": user_id}
        )
        row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return dict(row._mapping)


@app.get("/employees/{employee_id}/payroll")
async def get_employee_payroll(
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    INTENTIONAL VULNERABILITY: CWE-89
    employee_id from the URL path is interpolated directly into
    the SQL query string. An attacker with a valid JWT can inject:
      employee_id = "1 UNION SELECT username, password, email, salary FROM employees--"
    and extract all records from the database.
    """
    with engine.connect() as conn:
        # line 142 — INTENTIONAL VULNERABILITY: CWE-89 — raw string concatenation
        query = f"SELECT employee_id, period, gross_salary, net_salary, deductions FROM payroll WHERE employee_id = {employee_id}"
        result = conn.execute(text(query))
        rows = result.fetchall()

    return {"payroll": [dict(r._mapping) for r in rows]}


@app.patch("/employees/{employee_id}")
async def update_employee(
    employee_id: int,
    updates: dict,
    current_user: dict = Depends(get_current_user)
):
    # Safe update using ORM
    allowed_fields = {"phone", "address", "emergency_contact"}
    safe_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    if not safe_updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    with engine.connect() as conn:
        conn.execute(
            text("UPDATE employees SET phone = :phone WHERE id = :id"),
            {"phone": safe_updates.get("phone"), "id": employee_id}
        )
        conn.commit()
    return {"message": "Updated"}
