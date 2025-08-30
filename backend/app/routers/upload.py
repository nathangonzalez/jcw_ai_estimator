import os, uuid
from pathlib import Path
from typing import Tuple
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.background import BackgroundTask
from app.core.settings import settings
from app.schemas import UploadResp

router = APIRouter(prefix="/upload", tags=["upload"])

ALLOWED_MIME = {
    "application/pdf", "image/png", "image/jpeg",
    "image/vnd.dwg", "image/vnd.dxf", "application/acad",
    "application/octet-stream",
}

def _validate(file: UploadFile) -> Tuple[str, str]:
    name = file.filename or "upload"
    ext = os.path.splitext(name)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"unsupported extension: {ext}")
    ctype = (file.content_type or "").lower()
    if ctype and ctype not in ALLOWED_MIME:
        if not ctype.startswith("image/") and ctype != "application/pdf" and "dw" not in ctype and "dxf" not in ctype:
            raise HTTPException(status_code=415, detail=f"unsupported content-type: {ctype}")
    return name, ext

def _save_local(file: UploadFile, target: str, limit: int) -> tuple[str, int]:
    out_dir = Path(settings.LOCAL_FILES_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / target
    size = 0
    with out_path.open("wb") as f:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                try: out_path.unlink(missing_ok=True)
                finally: ...
                raise HTTPException(status_code=413, detail="file too large")
            f.write(chunk)
    return f"/files/{target}", size

def _save_gcs(file: UploadFile, target: str) -> tuple[str, int]:
    from google.cloud import storage  # lazy import
    client = storage.Client()
    bucket = client.bucket(settings.GCS_BUCKET)
    blob = bucket.blob(f"uploads/{target}")
    pos = file.file.tell()
    file.file.seek(0, 2); size = file.file.tell(); file.file.seek(pos)
    blob.upload_from_file(file.file, content_type=file.content_type, rewind=True)
    url = blob.generate_signed_url(expiration=60)
    return url, size

@router.post("/blueprint", response_model=UploadResp)
def upload_blueprint(file: UploadFile = File(...)):
    name, ext = _validate(file)
    target = f"{uuid.uuid4().hex}{ext}"

    if settings.STORAGE_BACKEND.lower() == "gcs":
        if not settings.GCS_BUCKET:
            raise HTTPException(status_code=500, detail="GCS bucket not configured")
        url, size = _save_gcs(file, target)
        storage = "gcs"
    else:
        url, size = _save_local(file, target, settings.MAX_FILE_SIZE)
        storage = "local"

    task = BackgroundTask(lambda: file.file.close())
    return UploadResp(
        filename=name, size=size, content_type=file.content_type or "application/octet-stream",
        url=url, storage=storage
    )
