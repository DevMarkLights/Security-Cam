# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A self-hosted security camera control system for a Reolink E1 Pro PTZ camera. Runs on a Raspberry Pi 5, exposed via Cloudflare Tunnel at `marks-pi.com`. The stack is a FastAPI backend that proxies camera commands over the Reolink HTTP CGI API, paired with a React frontend served as static files from the backend.

## Architecture

```
frontend/          React + Vite SPA
  src/
    SecurityDashboard.jsx   Single-component UI (PTZ, tracking, scan, record)
    SecurityDashboard.css

backend/
  server.py        FastAPI app — routes, WebSocket stream endpoint, deploy hook
  reoLink.py       All camera I/O: token auth, PTZ, AI tracking, patrol, RTSP capture
  amcrestCamera.py (unused/legacy — kept for reference)
```

**Data flow:**
1. On startup, `server.py` spawns a background thread running `reoLink.stream()`, which opens the RTSP feed via OpenCV and pushes JPEG frames into a `deque`.
2. The `/security/ws/stream` WebSocket endpoint drains that deque every 33ms and sends raw JPEG bytes to the browser.
3. The React UI receives binary WebSocket frames, creates Blob URLs, and renders them as `<img>` tags (~30 fps).
4. PTZ/tracking/scan actions go through REST endpoints on `server.py`, which call functions in `reoLink.py`.
5. The built frontend (`frontend/dist/`) is copied into `backend/dist/` and served as static files at `/security` by FastAPI.

**Token management:** `reoLink.py` holds a module-level `TOKEN` string. Every camera function checks if it's empty and calls `getToken()` if so. On error response from the camera the token is refreshed and the request retried once. Tokens expire after 3600s.

**Recording:** `RECORDING`, `VIDEO`, and `VideoFileName` are module-level globals in `reoLink.py`. Setting `reoLink.RECORDING = True` causes the stream loop to open a `VideoWriter`. When set back to `False`, the writer is released and the file is returned as a `FileResponse` then deleted.

**Preset IDs:** Preset 2 is hardcoded as "Home". The `goHome()` function always goes to preset 2. The "Absolute Position" panel in the UI is disabled (opacity 0.5, pointer-events none) — the backend endpoint for it is commented out.

## Environment Variables

Backend reads from a `.env` file (via `python-dotenv`):

| Variable | Purpose |
|---|---|
| `REOLINK_CAMERA_IP` | IP of the camera on the local network |
| `USERNAME` | Camera login username |
| `CAMERA_PASSWORD` | Camera login password |
| `DEPLOY_SECRET` | Secret for the `POST /security/deploy` webhook |

## Commands

### Backend

```bash
cd backend
# Install deps (use venv)
pip install -r requirements.txt

# Run dev server
python server.py
# Runs on http://0.0.0.0:8086
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # Dev server on http://localhost:3004
npm run build      # Outputs to frontend/dist/
npm run lint       # ESLint check
```

### Deploy (on Raspberry Pi)

```bash
bash deploy.bash
# Pulls latest, builds frontend, copies dist to backend/, restarts systemd service
```

The `POST /security/deploy` endpoint triggers this script remotely when called with the correct `DEPLOY_SECRET` body.

## Key Constraints

- **CORS origins** are hardcoded in `server.py`: `http://localhost:5174`, `https://marks-pi.com`, `http://localhost:3004`. Add here when testing from a new origin.
- **`local` flag** in `SecurityDashboard.jsx` (line 7) switches API and WebSocket base URLs between localhost and production. Set `const local = true` for local development.
- **Frontend base path** is `/security/` (vite.config.js). All asset paths and the static mount in `server.py` must stay in sync.
- Camera is mounted upside-down — `mirroring` and `rotation` are enabled via `flipImage()`. Do not toggle these without physically re-mounting.
- Disable AI tracking before calling `goToPreset` — active tracking overrides PTZ commands.
- The RTSP stream drops every 3rd frame (`frame_count % 3 != 0: continue`) to reduce CPU load before resizing to 854×480.
