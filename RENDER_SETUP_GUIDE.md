# MediaSnap Backend Deployment Guide on Render

This guide provides detailed, step-by-step instructions to deploy your MediaSnap FastAPI backend on Render, ensuring proper configuration for `yt-dlp` and addressing common issues like SSL certificate verification and FFmpeg installation.

## Prerequisites

*   A GitHub account with your `mediasnap-backend` repository pushed.
*   A Render account (free tier is sufficient for testing).

## Step-by-Step Deployment

### 1. Create a New Web Service on Render

1.  Log in to your [Render dashboard](https://dashboard.render.com/).
2.  Click on **"New"** in the top right corner, then select **"Web Service"**.
3.  **Connect to your GitHub account** if you haven't already. Grant Render access to your `mediasnap-backend` repository.
4.  Select your `mediasnap-backend` repository from the list.

### 2. Configure Your Web Service Settings

Fill in the service details as follows:

*   **Name**: Choose a unique name for your service (e.g., `mediasnap-backend-api`). This name will be part of your public URL.
*   **Region**: Select a region geographically close to your users or yourself.
*   **Branch**: `main` (or `master`, depending on your default branch).
*   **Root Directory**: `.` (This is important. Since your `main.py` and `requirements.txt` are at the root of the `mediasnap-backend` repository, you should not specify a subdirectory).
*   **Runtime**: `Python 3`.
*   **Build Command**: 
    ```bash
    pip install -r requirements.txt && apt-get update -y && apt-get install -y ffmpeg ca-certificates
    ```
    *   `pip install -r requirements.txt`: Installs all Python dependencies, including `certifi`.
    *   `apt-get update -y && apt-get install -y ffmpeg ca-certificates`: This command updates the package list and installs `ffmpeg` (essential for `yt-dlp` to process various media formats) and `ca-certificates` (which helps resolve SSL certificate issues by ensuring the system has up-to-date root certificates).

*   **Start Command**: 
    ```bash
    uvicorn main:app --host 0.0.0.0 --port $PORT
    ```
    This command starts your FastAPI application.

*   **Instance Type**: Select the **"Free"** instance type for testing and development.

### 3. Add Environment Variables

It is crucial to configure your environment variables for security and proper functionality.

1.  Scroll down to the **"Environment"** section.
2.  Click **"Add Environment Variable"**.
3.  Add the following variables:
    *   **Key**: `ALLOWED_ORIGINS`
        **Value**: `https://your-github-username.github.io/MediaSnap,http://localhost:8000,http://127.0.0.1:8000`
        *Replace `your-github-username` with your actual GitHub username. This ensures your frontend (hosted on GitHub Pages) and local development environment can communicate with your backend.*
    *   **Key**: `PYTHONHTTPSVERIFY`
        **Value**: `0`
        *This variable is a temporary workaround to explicitly disable Python's HTTPS verification, which can sometimes be overly strict in certain environments. Use with caution in production.*
    *   **Key**: `REQUESTS_CA_BUNDLE`
        **Value**: `/etc/ssl/certs/ca-certificates.crt`
        *This tells Python to use the system's CA certificate bundle, which should be updated by the `ca-certificates` package installed in the build command.*

### 4. Deploy Your Service

1.  After configuring all settings, click the **"Create Web Service"** button at the bottom.
2.  Render will now start building and deploying your backend. This process can take several minutes, especially for the first deployment, as it needs to install dependencies and FFmpeg.
3.  Monitor the deploy logs on your Render dashboard. If there are any issues, the logs will provide details.

### 5. Obtain Your Backend URL

Once the deployment is successful, Render will provide you with a public URL for your backend service (e.g., `https://your-service-name.onrender.com`). Make a note of this URL.

### 6. Update Your Frontend `api.js`

Finally, you need to update your frontend application to point to your newly deployed backend:

1.  Go to your `MediaSnap` frontend repository on GitHub.
2.  Edit the `js/api.js` file.
3.  Change the `API_BASE_URL` constant to your Render backend URL:
    ```javascript
    const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:8000' 
        : 'https://your-service-name.onrender.com'; // Replace with your Render URL
    ```
4.  Commit and push this change to your `MediaSnap` frontend repository. This will trigger a redeployment of your GitHub Pages site, ensuring it uses the correct backend URL.

## Troubleshooting Tips

*   **429 Too Many Requests (Instagram/Facebook)**: Even with optimizations, these platforms can be aggressive. Consider using a proxy service or providing authentication cookies if you need consistent access to private content.
*   **SSL Errors**: Ensure `ca-certificates` is installed and `PYTHONHTTPSVERIFY` and `REQUESTS_CA_BUNDLE` are set as environment variables. If issues persist, `yt-dlp` has its own `--no-check-certificate` option which has been added to `downloader.py` as a fallback.
*   **FFmpeg Issues**: Double-check that `ffmpeg` is correctly installed in your Render build command. Without it, `yt-dlp` might struggle with certain formats or merging video/audio streams.

By following these steps, your MediaSnap application should be fully operational with the backend hosted on Render and the frontend on GitHub Pages.
