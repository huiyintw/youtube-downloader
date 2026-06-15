from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl

from app.downloader import download, get_video_info

app = FastAPI(title="YouTube Downloader", version="1.0.0")

STATIC_DIR = Path(__file__).resolve().parent / "static"
DOWNLOAD_DIR = Path(__file__).resolve().parent.parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


class DownloadRequest(BaseModel):
    url: HttpUrl
    mode: str  # "video" | "audio"
    browser: str = "auto"
    audio_format: str = "m4a"  # "m4a" | "mp3"


class InfoRequest(BaseModel):
    url: HttpUrl
    browser: str = "auto"


@app.post("/api/info")
async def video_info(req: InfoRequest):
    try:
        info = get_video_info(str(req.url), req.browser)
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/download")
async def download_media(req: DownloadRequest):
    if req.mode not in ("video", "audio"):
        raise HTTPException(status_code=400, detail="mode 必須為 video 或 audio")
    if req.audio_format not in ("m4a", "mp3"):
        raise HTTPException(status_code=400, detail="audio_format 必須為 m4a 或 mp3")

    try:
        result = download(str(req.url), req.mode, req.browser, req.audio_format)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/files/{filename}")
async def get_file(filename: str):
    filepath = DOWNLOAD_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(status_code=404, detail="檔案不存在")

    if filename.endswith(".mp4"):
        media_type = "video/mp4"
    elif filename.endswith(".m4a"):
        media_type = "audio/mp4"
    else:
        media_type = "audio/mpeg"
    return FileResponse(filepath, media_type=media_type, filename=filename)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
