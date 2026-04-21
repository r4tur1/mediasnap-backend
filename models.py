from pydantic import BaseModel
from typing import List, Optional

class MediaInfoRequest(BaseModel):
    url: str

class FormatInfo(BaseModel):
    format_id: str
    label: str
    ext: str
    filesize: Optional[int] = None
    type: str  # 'video' or 'audio'

class MediaInfoResponse(BaseModel):
    title: str
    uploader: str
    duration: Optional[int] = None
    thumbnail: str
    view_count: Optional[int] = None
    platform: str
    formats: List[FormatInfo]

class ErrorResponse(BaseModel):
    error: str

class ProgressResponse(BaseModel):
    progress: float
    status: str
    task_id: str
