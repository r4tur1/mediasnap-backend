import yt_dlp
import os
import tempfile
import asyncio
from typing import Dict, Any, List, Optional
from models import MediaInfoResponse, FormatInfo

class MediaDownloader:
    def __init__(self):
        self.ydl_opts_info = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }

    async def get_info(self, url: str) -> Dict[str, Any]:
        """Fetches media information using yt-dlp."""
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_info) as ydl:
                info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                return self._parse_info(info_dict, url)
        except Exception as e:
            raise Exception(f"Failed to extract info: {str(e)}")

    def _parse_info(self, info: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Parses the raw yt-dlp info into a cleaner format."""
        formats: List[Dict[str, Any]] = []
        
        # Extract formats
        raw_formats = info.get('formats', [])
        
        # Video formats (filter for those with video and audio, or video only)
        # Note: YouTube often splits video and audio for high quality
        # yt-dlp can merge them during download, so we show combined labels
        
        # Audio-only formats
        for f in raw_formats:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                formats.append({
                    "format_id": f.get('format_id'),
                    "label": f"{f.get('abr', 'Unknown')}kbps" if f.get('abr') else f.get('format_note', 'Audio'),
                    "ext": f.get('ext'),
                    "filesize": f.get('filesize') or f.get('filesize_approx'),
                    "type": "audio"
                })
        
        # Video formats
        for f in raw_formats:
            if f.get('vcodec') != 'none':
                # Skip low quality story formats or similar
                if f.get('height') and f.get('height') >= 144:
                    formats.append({
                        "format_id": f.get('format_id'),
                        "label": f"{f.get('height')}p" if f.get('height') else f.get('format_note', 'Video'),
                        "ext": f.get('ext'),
                        "filesize": f.get('filesize') or f.get('filesize_approx'),
                        "type": "video"
                    })

        # Sort and deduplicate formats (simplified)
        unique_formats = []
        seen_labels = set()
        
        # Sort by resolution descending
        video_formats = sorted([f for f in formats if f['type'] == 'video'], 
                              key=lambda x: int(x['label'].replace('p', '')) if 'p' in x['label'] else 0, 
                              reverse=True)
        
        for f in video_formats:
            if f['label'] not in seen_labels:
                unique_formats.append(f)
                seen_labels.add(f['label'])
                
        # Add audio formats
        audio_formats = sorted([f for f in formats if f['type'] == 'audio'], 
                              key=lambda x: float(x['label'].replace('kbps', '')) if 'kbps' in x['label'] else 0, 
                              reverse=True)
        
        for f in audio_formats:
            if f['label'] not in seen_labels:
                unique_formats.append(f)
                seen_labels.add(f['label'])

        return {
            "title": info.get('title', 'Unknown Title'),
            "uploader": info.get('uploader', 'Unknown Uploader'),
            "duration": info.get('duration'),
            "thumbnail": info.get('thumbnail', ''),
            "view_count": info.get('view_count'),
            "platform": info.get('extractor', 'unknown'),
            "formats": unique_formats
        }

    async def download_stream(self, url: str, format_id: str):
        """Downloads the media and yields chunks for streaming."""
        # Create a temp file
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)
        
        # yt-dlp options for downloading
        ydl_opts = {
            'format': f"{format_id}+bestaudio/best" if format_id.isdigit() else format_id,
            'outtmpl': temp_path,
            'quiet': True,
            'no_warnings': True,
            'merge_output_format': 'mp4',
        }
        
        loop = asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get info first to get the correct extension
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                actual_path = ydl.prepare_filename(info)
                
                # Check if file exists (it might have a different extension than temp_path)
                if not os.path.exists(actual_path) and os.path.exists(temp_path):
                    actual_path = temp_path
                
                # Yield file chunks
                with open(actual_path, 'rb') as f:
                    while chunk := f.read(8192):
                        yield chunk
                        
                # Clean up
                if os.path.exists(actual_path):
                    os.remove(actual_path)
                if os.path.exists(temp_path) and actual_path != temp_path:
                    os.remove(temp_path)
                    
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise Exception(f"Download failed: {str(e)}")
