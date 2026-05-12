# MediaSnap - Backend API

The powerful engine behind MediaSnap, built with Python and FastAPI, utilizing `yt-dlp` for robust media extraction.

## Features
- **FastAPI**: High-performance asynchronous API.
- **yt-dlp**: Support for thousands of sites including YouTube, Instagram, and Facebook.
- **Anti-Blocking**: Optimized with random user-agents and headers to improve reliability.
- **Streaming Downloads**: Efficiently streams media directly to the user without storing files permanently on the server.

## API Endpoints

*   **GET /**: Basic health check.
*   **POST /api/info**: Get media information.
    *   Request Body: `{ "url": "<media_url>" }`
    *   Response: MediaInfoResponse schema.
*   **GET /api/download**: Stream media file.
    *   Query Parameters: `url=<media_url>`, `format_id=<format_id>`

## Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`.
3. Install FFmpeg: `sudo apt-get install ffmpeg`.
4. Run the server: `uvicorn main:app --reload`.

## Environment Variables
Create a `.env` file with:
- `ALLOWED_ORIGINS`: Comma-separated list of allowed frontend URLs.
- `PORT`: Port to run the server on (default 8000).

## Cookie-based Authentication for YouTube and Instagram

Due to aggressive bot detection by platforms like YouTube and Instagram, direct `yt-dlp` calls from shared IP addresses (common on free hosting tiers like Render) often fail. To bypass this, the backend now supports loading cookies from a `cookies.txt` file.

**This is the recommended method for reliable downloads, especially for Instagram and YouTube.**

### How to Generate `cookies.txt`

1.  **Create a dedicated (throwaway) account** on YouTube and Instagram using a temporary email service. This is to protect your main accounts and ensure you're not violating any terms of service with your primary accounts.
2.  **Log in** to YouTube and Instagram in your browser using this new account.
3.  **Install a browser extension** to export cookies. Recommended extensions:
    *   **Chrome**: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddkifhfbjgncnpgmgnncfagadefel)
    *   **Firefox**: [Export Cookies](https://addons.mozilla.mozilla.org/en-US/firefox/addon/export-cookies-txt/)
4.  **Export cookies**: Once logged in to both YouTube and Instagram, use the extension to export your cookies as a `cookies.txt` file. Make sure both YouTube and Instagram cookies are included in the same file.

### How to Use `cookies.txt` with MediaSnap Backend

1.  **Rename the exported file** to `cookies.txt` (if it's not already).
2.  **Place the `cookies.txt` file** in the root directory of your `mediasnap-backend` repository. For Render deployment, you will need to add this file to your GitHub repository.
3.  **Commit and Push**: Commit the `cookies.txt` file to your `mediasnap-backend` GitHub repository and push the changes. Render will automatically pick up the new file during deployment.

**Important Security Note**: `cookies.txt` contains sensitive authentication information. Treat it like a password. Do not share it publicly. If you are concerned about committing it directly to your public repository, consider using Render's environment variables for sensitive files or a private repository. However, for a low-traffic, throwaway account, committing to a private GitHub repo is generally acceptable.

## Deployment (Render)
1. Create a new Web Service on Render.
2. Set Root Directory to `.`.
3. Build Command: `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`.
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
