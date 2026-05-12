import yt_dlp
import os
import tempfile
import asyncio
import random
from typing import Dict, Any, List, Optional

class MediaDownloader:
    def __init__(self):
        # Common User-Agents to mimic real browsers
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
        ]

    def _get_ydl_opts(self, download=False, format_id=None, temp_path=None):
        """Generates yt-dlp options with anti-blocking measures."""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'no_color': True,
            'user_agent': random.choice(self.user_agents),
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            },
            'add_header': [
                'Referer:https://www.google.com/',
            ],
            # Use 'ios' client for YouTube to potentially bypass some bot checks
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'web', 'mweb'],
                    'skip': ['dash', 'hls']
                }
            }
        }

        if download:
            # If it's a digit, it's a specific format. Otherwise it might be 'bestvideo+bestaudio'
            if format_id:
                if format_id.isdigit():
                    opts['format'] = f"{format_id}+bestaudio/best"
                else:
                    opts['format'] = format_id
            else:
                opts['format'] = 'best'
                
            opts.update({
                'outtmpl': temp_path,
                'merge_output_format': 'mp4',
            })
        else:
            opts.update({
                'extract_flat': False,
                'skip_download': True,
            })
            
        return opts

    async def get_info(self, url: str) -> Dict[str, Any]:
        """Fetches media information using yt-dlp with retries and optimized settings."""
        loop = asyncio.get_event_loop()
        
        last_error = None
        for attempt in range(3):
            try:
                ydl_opts = self._get_ydl_opts(download=False)
                # Try different clients on different attempts
                if attempt == 1:
                    ydl_opts['extractor_args']['youtube']['player_client'] = ['android', 'web']
                elif attempt == 2:
                    ydl_opts['extractor_args']['youtube']['player_client'] = ['mweb']

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                    return self._parse_info(info_dict, url)
            except Exception as e:
                last_error = e
                await asyncio.sleep(1)
                
        raise Exception(f"Failed to extract info: {str(last_error)}")

    def _parse_info(self, info: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Parses the raw yt-dlp info into a cleaner format."""
        formats: List[Dict[str, Any]] = []
        raw_formats = info.get('formats', [])
        
        # Audio-only formats
        for f in raw_formats:
            if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                abr = f.get('abr') or f.get('tbr')
                label = f"{int(abr)}kbps" if abr else f.get('format_note', 'Audio')
                formats.append({
                    "format_id": f.get('format_id'),
                    "label": label,
                    "ext": f.get('ext', 'm4a'),
                    "filesize": f.get('filesize') or f.get('filesize_approx'),
                    "type": "audio"
                })
        
        # Video formats
        for f in raw_formats:
            if f.get('vcodec') != 'none':
                height = f.get('height')
                if height and height >= 144:
                    label = f"{height}p"
                    formats.append({
                        "format_id": f.get('format_id'),
                        "label": label,
                        "ext": f.get('ext', 'mp4'),
                        "filesize": f.get('filesize') or f.get('filesize_approx'),
                        "type": "video"
                    })

        # Deduplicate and sort
        unique_formats = []
        seen_keys = set()
        
        def get_sort_val(f):
            label = f['label'].replace('p', '').replace('kbps', '')
            try:
                return int(label)
            except:
                return 0

        sorted_formats = sorted(formats, key=lambda x: (x['type'] == 'audio', -get_sort_val(x)))
        
        for f in sorted_formats:
            key = (f['type'], f['label'])
            if key not in seen_keys:
                unique_formats.append(f)
                seen_keys.add(key)

        return {
            "title": info.get('title', 'Unknown Title'),
            "uploader": info.get('uploader', info.get('uploader_id', 'Unknown Uploader')),
            "duration": info.get('duration'),
            "thumbnail": info.get('thumbnail', ''),
            "view_count": info.get('view_count'),
            "platform": info.get('extractor_key', info.get('extractor', 'unknown')).lower(),
            "formats": unique_formats
        }

    async def download_stream(self, url: str, format_id: str):
        """Downloads the media and yields chunks for streaming."""
        # Use a temporary directory to avoid conflicts
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "download.%(ext)s")
            ydl_opts = self._get_ydl_opts(download=True, format_id=format_id, temp_path=temp_path)
            
            loop = asyncio.get_event_loop()
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
                    actual_path = ydl.prepare_filename(info)
                    
                    # If yt-dlp merged files, the actual path might be different from what we expect
                    # Let's find the file in the temp directory
                    files = os.listdir(temp_dir)
                    if files:
                        actual_path = os.path.join(temp_dir, files[0])
                    
                    if not os.path.exists(actual_path):
                        raise Exception("Download completed but file not found")

                    with open(actual_path, 'rb') as f:
                        while chunk := f.read(1024 * 1024): # 1MB chunks
                            yield chunk
                            
            except Exception as e:
                raise Exception(f"Download failed: {str(e)}")
