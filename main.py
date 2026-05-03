import os
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import yt_dlp
import tempfile
import shutil
from dotenv import load_dotenv
from downloader import MediaDownloader
from models import MediaInfoRequest, MediaInfoResponse, FormatInfo, ErrorResponse

# Load environment variables
load_dotenv()

app = FastAPI(title="MediaSnap API")

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

downloader = MediaDownloader()

# Global progress tracker (in-memory for simplicity)
progress_tracker: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    return {"message": "MediaSnap API is running!"}

@app.post("/api/info", response_model=MediaInfoResponse)
async def get_media_info(request: MediaInfoRequest):
    """
    Fetches media information and available formats.
    """
    try:
        info = await downloader.get_info(request.url)
        return info
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/download")
async def download_media(url: str, format_id: str):
    """
    Streams the media file back to the browser.
    """
    try:
        # Get filename first for content-disposition header
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'media')
            ext = info.get('ext', 'mp4')
            # Sanitize filename to avoid header issues
            safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '.', '_', '-')]).strip()
            filename = f"{safe_title}.{ext}"

        return StreamingResponse(
            downloader.download_stream(url, format_id),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Returns the current download progress for a task.
    """
    if task_id in progress_tracker:
        return progress_tracker[task_id]
    return {"progress": 0, "status": "unknown"}

# Custom error handler for JSON responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
