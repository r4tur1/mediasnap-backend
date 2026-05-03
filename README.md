# MediaSnap - Backend API

The powerful engine behind MediaSnap, built with Python and FastAPI, utilizing `yt-dlp` for robust media extraction.

## Features
- **FastAPI**: High-performance asynchronous API.
- **yt-dlp**: Support for thousands of sites including YouTube, Instagram, and Facebook.
- **Anti-Blocking**: Optimized with random user-agents and headers to improve reliability.
- **Streaming Downloads**: Efficiently streams media directly to the user without storing files permanently on the server.

## Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Install FFmpeg: `sudo apt-get install ffmpeg`.
4. Run the server: `uvicorn main:app --reload`.

## Environment Variables
Create a `.env` file with:
- `ALLOWED_ORIGINS`: Comma-separated list of allowed frontend URLs.
- `PORT`: Port to run the server on (default 8000).

## Deployment (Render)
1. Create a new Web Service on Render.
2. Set Root Directory to `.`.
3. Build Command: `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`.
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
