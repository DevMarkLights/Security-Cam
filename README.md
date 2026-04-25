# Security Camera API

A self-hosted FastAPI backend for controlling a Reolink E1 Pro PTZ WiFi camera over a local network. Built on a Raspberry Pi 5 and exposed via Cloudflare Tunnel.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Camera:** Reolink E1 Pro 1080p WiFi PTZ Camera
- **Protocol:** Reolink HTTP CGI API via `requests`
- **Infrastructure:** Raspberry Pi 5, Cloudflare Tunnel, Nginx

## Features

- Toggle AI-powered auto tracking on/off (`bSmartTrack`)
- Manual PTZ directional movement with stop command
- Set and return to preset positions
- Patrol mode (sweeps between saved presets)
- Image flip/mirror correction for upside-down mounting
- Token-based authentication with auto re-authentication
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

### `GET /security/setPreset?id=1&name=preset1`
Save the camera's current position as a named preset.

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `id` | int | Preset ID (0–63) |
| `name` | string | Preset name |

**Response:**
```json
{ "Request Time": 0.123 }
```

---

### `GET /security/goToPreset?id=1`
Move the camera to a saved preset position.

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `id` | int | Preset ID to move to |

**Response:**
```json
{ "Request Time": 0.123 }
```

---

### `GET /security/scan`
Start patrol mode — camera sweeps between saved presets automatically.

**Response:**
```json
{ "Scan": "Scan started", "Request Time": 0.123 }
```

---

### `GET /security/stopScan`
Stop patrol mode.

**Response:**
```json
{ "Request Time": 0.123 }
```

---

## Camera Module (`camera.py`)

All camera communication is handled through the Reolink HTTP CGI API using token-based authentication.

| Function | Description |
|----------|-------------|
| `get_token()` | Authenticates and stores session token (expires after 1 hour) |
| `move_camera(direction, speed, duration)` | Sends PTZ directional command then stops after duration |
| `set_tracking(enabled)` | Toggles `bSmartTrack` and `aiTrack` for AI auto tracking |
| `set_preset(id, name)` | Saves current position as a named preset |
| `go_to_preset(id)` | Moves camera to saved preset position |
| `set_patrol_config(id, enable)` | Configures patrol route between presets |
| `start_patrol()` | Starts automated patrol between presets |
| `stop_patrol()` | Stops patrol mode |
| `flip_image()` | Enables mirroring and rotation for upside-down mounting |
| `get_ability()` | Returns full camera capability map |

## Running the Server

```bash
pip install fastapi uvicorn requests
python server.py
```

Server runs on port `8086` by default.

## Notes

- Mounted upside down — `mirroring` and `rotation` are enabled via `SetIsp`
- Auto tracking uses the camera's built-in AI (`bSmartTrack`) — no OpenCV required
- Token expires after 3600 seconds (1 hour) — re-authentication is handled automatically
- Preset must be saved via `/security/setPreset` before `/security/goToPreset` can be used
- Disable auto tracking before calling `goToPreset` — active tracking overrides PTZ commands
- Do not physically move the camera by hand after saving presets — this breaks positional reference
- ONVIF enabled for future absolute positioning support
- Camera is on 5GHz WiFi for stable high-bandwidth streaming
- RTSP stream: `rtsp://admin:password@<ip>:554/Preview_01_main`