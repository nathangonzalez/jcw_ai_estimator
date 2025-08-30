from fastapi import APIRouter, UploadFile, File
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/config")
def config():
    return {"ok": True, "routes": ["/health","/ai/test","/estimate/preview","/upload/blueprint"]}

@router.post("/echo-upload")
def echo_upload(file: UploadFile = File(...)):
    return {"name": file.filename, "content_type": file.content_type or "application/octet-stream"}
