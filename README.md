# Security Camera API

A self-hosted FastAPI backend for controlling an Amcrest IP2M-841 PTZ WiFi camera over a local network. Built on a Raspberry Pi 5 and exposed via Cloudflare Tunnel.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Camera:** Amcrest IP2M-841 1080p WiFi PTZ Camera
- **Protocol:** Amcrest HTTP CGI API via `requests` with HTTP Digest Auth
- **Infrastructure:** Raspberry Pi 5, Cloudflare Tunnel, Nginx

## Features

- Toggle AI-powered auto tracking on/off (`LeSmartTrack`)
- Manual PTZ directional movement
- Absolute position control (pan/tilt coordinates)
- Set and return to preset positions
- Auto scan mode (sweeps between two positions and returns to home)
- Health check endpoint
- Request timing on all responses
- Input validation with descriptive error messages

## Endpoints

### `GET /security/health`
Health check to confirm the server is running.

**Response:**
```json
{ "server": "running" }
```

---

### `GET /security/track?track=true`
Enable or disable the camera's built-in AI auto tracking.

**Query Params:**
| Param | Type | Values |
|-------|------|--------|
| `track` | string | `true`, `false` |

**Response:**
```json
{ "Request Time": "0.123s" }
```

---

### `POST /security/move`
Move the camera in a specified direction.

**Request Body:**
```json
{ "direction": "Left" }
```

**Valid Directions:**
`Left`, `Right`, `Up`, `Down`, `LeftUp`, `LeftDown`, `RightUp`, `RightDown`

**Response:**
```json
{ "Request Time": 0.123 }
```

---

### `POST /security/goToPostion`
Move the camera to an absolute pan/tilt position.

**Request Body:**
```json
{ "x": 180, "y": 45 }
```

**Validation:**
- `x` — horizontal pan angle, range `0–360`
- `y` — vertical tilt angle, range `0–90`

**Response:**
```json
{ "Request Time": 0.123 }
```

---

### `GET /security/setPreset`
Save the camera's current position as preset 1.

**Response:**
```json
{ "Request Time": 0.123 }
```

---

### `GET /security/goToPreset`
Return the camera to the saved preset 1 position.

**Response:**
```json
{ "Request Time": 0.123 }
```

---

### `GET /security/scan`
Start an auto scan — moves the camera through two positions and returns to the preset home. Runs asynchronously in the background so the response is immediate.

**Response:**
```json
{ "Scan": "Scan started", "Request Time": 0.123 }
```

---

## Camera Module (`camera.py`)

All camera communication is handled through the Amcrest HTTP CGI API using HTTP Digest Auth.

| Function | Description |
|----------|-------------|
| `move_camera(direction, speed, duration)` | Sends start/stop PTZ directional commands |
| `track(tracking)` | Toggles `LeSmartTrack[0].Enable` via configManager |
| `setPreset()` | Saves current position as preset 1 |
| `goToPreset()` | Moves camera to preset 1 |
| `goToPostion(x, y)` | Moves camera to absolute coordinates via `PositionABS` |
| `scan()` | Sweeps through two positions then returns home |

## Running the Server

```bash
pip install fastapi uvicorn requests
python server.py
```

Server runs on port `8086` by default.

## Notes

- Auto tracking uses the camera's built-in AI (`LeSmartTrack`) — no OpenCV required
- All PTZ commands use the Amcrest CGI API (`/cgi-bin/ptz.cgi`)
- Config commands use `/cgi-bin/configManager.cgi`
- The camera must be on the same local network as the Pi
- Preset position must be set once via `/security/setPreset` before `/security/goToPreset` can be used
