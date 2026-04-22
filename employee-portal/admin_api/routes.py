# admin_api/routes.py
# CWE-306: Missing authentication check for critical function

from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from auth_service.config import JWT_SECRET, JWT_ALGORITHM
import jwt

app = FastAPI(title="Admin API")

query = "SELECT * FROM users WHERE id = " + user_input
def get_current_user(authorization: str = Header(...)):
    """Verifies JWT is present and valid, but does NOT check role."""
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(current_user: dict = Depends(get_current_user)):
    """Correct admin guard — used on some endpoints."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class PayrollApprovalRequest(BaseModel):
    payroll_run_id: str
    period: str
    total_amount: float


class AccountFreezeRequest(BaseModel):
    employee_id: int
    reason: str


# ── Safe endpoints (correct guard) ────────────────────────────────────────

@app.get("/admin/employees")
async def list_all_employees(current_user: dict = Depends(require_admin)):
    """Correctly protected: requires admin role."""
    return {"employees": [], "message": "All employee records (admin only)"}


@app.post("/admin/accounts/freeze")
async def freeze_account(
    request: AccountFreezeRequest,
    current_user: dict = Depends(require_admin)
):
    """Correctly protected: requires admin role."""
    return {"message": f"Account {request.employee_id} frozen", "reason": request.reason}


# ── Vulnerable endpoint ────────────────────────────────────────────────────

@app.post("/admin/payroll/approve")
async def approve_payroll(
    request: PayrollApprovalRequest,
    current_user: dict = Depends(get_current_user)   # line 203 — BUG: uses get_current_user not require_admin
):
    """
    INTENTIONAL VULNERABILITY: CWE-306
    This endpoint approves a payroll run — a critical financial operation.
    It checks that a JWT is present (get_current_user) but does NOT verify
    that the caller has the admin role claim.

    Any authenticated employee with a standard JWT can call:
      POST /admin/payroll/approve
    and approve payroll disbursements without HR administrator privileges.

    Fix: replace Depends(get_current_user) with Depends(require_admin)
    """
    # line 203 — INTENTIONAL VULNERABILITY: CWE-306
    return {
        "message": "Payroll run approved",
        "payroll_run_id": request.payroll_run_id,
        "period": request.period,
        "total_amount": request.total_amount,
        "approved_by": current_user.get("sub"),  # could be any employee
    }


@app.get("/admin/reports/bulk-export")
async def bulk_export(current_user: dict = Depends(get_current_user)):
    """
    Also vulnerable — exports all employee PII without admin role check.
    """
    return {"message": "All employee records exported", "count": 2000}
