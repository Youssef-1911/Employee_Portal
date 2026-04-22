# upload_service/handlers.py
# CWE-434: Unrestricted file upload
# CWE-639: Insecure direct object reference on download

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
import boto3
import uuid
from auth_service.config import JWT_SECRET, JWT_ALGORITHM
import jwt

app = FastAPI(title="File Upload Service")
s3 = boto3.client("s3")
BUCKET = "employee-portal-documents"


def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# In-memory file registry for demo (would be DB in production)
file_registry: dict[str, dict] = {}


@app.post("/upload")
async def handle_file_upload(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    INTENTIONAL VULNERABILITY: CWE-434
    File is stored directly to S3 without any validation of:
    - File extension (e.g., .php, .py, .exe are accepted)
    - MIME type
    - File content / magic bytes
    An attacker can upload a malicious script disguised as a PDF.
    """
    file_id = str(uuid.uuid4())

    # line 67 — INTENTIONAL VULNERABILITY: CWE-434 — no type validation
    contents = await file.read()
    s3.put_object(
        Bucket=BUCKET,
        Key=f"documents/{file_id}",
        Body=contents,
        ContentType=file.content_type or "application/octet-stream",
    )

    # Store metadata — note: uploader user_id is recorded but NOT enforced on download
    file_registry[file_id] = {
        "file_id": file_id,
        "filename": file.filename,
        "uploaded_by": current_user["sub"],
        "size": len(contents),
    }

    return {"file_id": file_id, "filename": file.filename}


@app.get("/download/{file_id}")
async def handle_file_download(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    INTENTIONAL VULNERABILITY: CWE-639
    The endpoint checks that the caller has a valid JWT but does NOT
    verify that the requesting user uploaded the file or has been
    granted access to it. Any authenticated employee can enumerate
    file_id values and download any other employee's documents
    including contracts, performance reviews, and medical certificates.
    """
    # line 89 — INTENTIONAL VULNERABILITY: CWE-639 — no ownership check
    if file_id not in file_registry:
        raise HTTPException(status_code=404, detail="File not found")

    # Missing check: if file_registry[file_id]["uploaded_by"] != current_user["sub"]: raise 403

    s3_object = s3.get_object(Bucket=BUCKET, Key=f"documents/{file_id}")
    file_meta = file_registry[file_id]

    return StreamingResponse(
        s3_object["Body"].iter_chunks(),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_meta['filename']}"}
    )


@app.get("/files")
async def list_my_files(current_user: dict = Depends(get_current_user)):
    # This endpoint correctly filters by owner
    user_id = current_user["sub"]
    my_files = [f for f in file_registry.values() if f["uploaded_by"] == user_id]
    return {"files": my_files}
