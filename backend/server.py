from contextlib import asynccontextmanager
import threading

from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Body, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
import cv2
import logging
import requests
from requests.auth import HTTPDigestAuth
import time
# from amcrestCamera import move_camera, track, setPreset, goToPreset, goToPostion, scan, stream
import reoLink
import asyncio
import base64
import subprocess
import os
import re
from dotenv import load_dotenv
load_dotenv()
DEPLOY_SECRET = os.getenv("DEPLOY_SECRET")
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


logging.basicConfig(level=logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

validTrackingParams = ['true','false','True','False']

frame_lock = threading.Lock()
@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=reoLink.stream, args=(logging,frame_lock), daemon=True)
    thread.start()
    yield
    reoLink.stop_event.set()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174","https://marks-pi.com","http://localhost:3004", "http://localhost:8086"],
    allow_credentials=False,   # MUST be FALSE
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

@app.get("/security/track")
async def startTracking(request: Request):
    s_time = time.time()
    tracking: str = request.query_params.get("track")
    tracking = tracking.lower()
    
    if tracking not in validTrackingParams:
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=400, detail={"error":"track value is required", "Request Time": f'{round(request_time,ndigits=3)}s'})
    
    try:
        if tracking == 'true':  
            reoLink.track(True)
        else: 
            reoLink.track(False)
    except Exception as e:
        logging.error(e)
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=500, detail={"Error":"Error starting tracking", "Request Time": f'{round(request_time,ndigits=3)}s'})
    
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Request Time": f'{round(request_time,ndigits=3)}s'})


@app.post("/security/move")
async def move(request: Request):
    s_time = time.time()
    body = await request.json()
    direction = ""
    if "direction" in body:
        direction = body.get("direction")
        try:
            reoLink.move_camera(direction=direction)
        except Exception as e:
            logging.error(e)
            e_time = time.time()
            request_time = e_time - s_time
            raise HTTPException(status_code=500, detail={"Error":"Make sure the first letter in direction is capitalized","Request Time": f'{round(request_time,ndigits=3)}s'})
            
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Request Time": round(request_time,ndigits=3)})

@app.get('/security/health')
async def healthCheck():
    return {"server":"running"}

@app.get('/security/setPreset')
async def preset():
    s_time = time.time()

    try:
        reoLink.setPreset( preset_id=2, name="Home", enable=1)
    except Exception as e:
        logging.error(e)
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=500, detail={"Error":"Could not set preset location","Request Time": f'{round(request_time,ndigits=3)}s'})
    
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Request Time": round(request_time,ndigits=3)})

@app.get('/security/goToPreset')
async def toPreset():
    s_time = time.time()
    
    try:
        reoLink.goToPreset(id = 2)
    except Exception as e:
        logging.error(e)
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=500, detail={"Error":"Could not go to preset location","Request Time": f'{round(request_time,ndigits=3)}s'})
    
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Request Time": round(request_time,ndigits=3)})    

# @app.post('/security/goToPostion')
# async def toPostion(request: Request):
#     s_time = time.time()
#     body = await request.json()
#     x = 0
#     y = 0
#     if 'x' in body and 'y' in body:
#         x = body.get('x')
#         if x < 0 or x > 360:
#             e_time = time.time()
#             request_time = e_time - s_time
#             raise HTTPException(status_code=400, detail={"Error":f"x = {x} invalid 0 - 360","Request Time": f'{round(request_time,ndigits=3)}s'})
#         y = body.get('y')
#         if y < 0 or y > 90:
#             e_time = time.time()
#             request_time = e_time - s_time
#             raise HTTPException(status_code=400, detail={"Error":f"y = {y} invalid 0 - 90","Request Time": f'{round(request_time,ndigits=3)}s'})
#     else:
#         e_time = time.time()
#         request_time = e_time - s_time
#         raise HTTPException(status_code=400, detail={"Error":"x and y are required","Request Time": f'{round(request_time,ndigits=3)}s'})
    
#     try:
#         goToPostion(x=x, y=y)
#     except Exception as e:
#         logging.error(e)
#         e_time = time.time()
#         request_time = e_time - s_time
#         raise HTTPException(status_code=500, detail={"Error":f"Could not go to postion x={x} y={y} location","Request Time": f'{round(request_time,ndigits=3)}s'})
    
#     e_time = time.time()
#     request_time = e_time - s_time
#     raise HTTPException(status_code=200, detail={"Request Time": round(request_time,ndigits=3)})    

@app.get('/security/scan')
async def toScan():
    s_time = time.time()
    
    try:
       asyncio.create_task(asyncio.to_thread(reoLink.startPatrol))
    except Exception as e:
        logging.error(e)
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=500, detail={"Error":"Could not start scan","Request Time": f'{round(request_time,ndigits=3)}s'})
    
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Scan":"Scan started","Request Time": round(request_time,ndigits=3)})  

@app.get('/security/scanStop')
async def toScan():
    s_time = time.time()
    
    try:
       reoLink.stopPatrol()
    except Exception as e:
        logging.error(e)
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=500, detail={"Error":"Could not start scan","Request Time": f'{round(request_time,ndigits=3)}s'})
    
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Scan":"Scan started","Request Time": round(request_time,ndigits=3)})  

@app.get("/security/buffer-size")
def get_buffer_size():
    return {'buffer-size':reoLink.buffer_size()}

@app.get("/security/record")
async def recordVideo(request: Request):
    # global RECORDING, VIDEO, VideoFileName
    r: str = request.query_params.get("record")
    r = r.lower()
    try:
        if r == 'true':
            reoLink.RECORDING = True
            return HTTPException(status_code=200, detail={"Recording": f'Recoring Started'})  
        else:
            reoLink.RECORDING = False
            await asyncio.sleep(3)
            fn = f'{reoLink.VideoFileName}.mp4'
            if reoLink.VideoFileName and os.path.exists(fn):
                return FileResponse(
                    path=fn,
                    media_type='video/mp4',
                    filename=fn,
                    background=BackgroundTask(delete_file, fn)
                )
            logging.error(f"No video found for {reoLink.VideoFileName}")
            raise HTTPException(status_code=404, detail="No recording found") 
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=500, detail={"Error":"Could not start/stop recording video"})
    
@app.websocket("/security/ws/stream")
async def getStream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive(), timeout=0.01)
            except asyncio.TimeoutError:
                pass
            except (WebSocketDisconnect , RuntimeError):
                break
            
            frame = None
            if reoLink.frame_queue:
                with frame_lock:
                    frame = reoLink.frame_queue.popleft()
                    
            if frame:
                await websocket.send_bytes(frame)
            
            await asyncio.sleep(0.033)
    except (WebSocketDisconnect, RuntimeError):
        pass

@app.post("/goHome")
async def home():
    s_time = time.time()
    
    try:
       reoLink.goHome()
    except Exception as e:
        logging.error(e)
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=500, detail={"Error":"Could not go home","Request Time": f'{round(request_time,ndigits=3)}s'})
    
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Success":"Going Home","Request Time": round(request_time,ndigits=3)})  
        

@app.post("/security/deploy")
async def deploy(request: Request):
    body = await request.json()
    if body.get("secret") != DEPLOY_SECRET:
        raise HTTPException(status_code=401)
    
    
    subprocess.Popen(["bash", f"/mnt/nvme/Security-Cam/deploy.bash"])
    return {"status": "deploying", "service": 'Security Service'}

_DATE_FILE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\.mp4$')

@app.get('/security/recordings')
async def list_recordings():
    import datetime
    today = datetime.date.today().strftime('%Y-%m-%d') + '.mp4'
    files = sorted(
        [f for f in os.listdir(BACKEND_DIR) if _DATE_FILE_RE.match(f) and f != today],
        reverse=True
    )
    return {'recordings': files}

@app.get('/security/recordings/{filename}')
async def get_recording(filename: str, request: Request):
    if not _DATE_FILE_RE.match(filename):
        raise HTTPException(status_code=400, detail='Invalid filename')
    path = os.path.join(BACKEND_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Not found')

    file_size = os.path.getsize(path)
    range_header = request.headers.get("range")

    if range_header:
        range_val = range_header.replace("bytes=", "").split("-")
        start = int(range_val[0]) if range_val[0] else 0
        end = int(range_val[1]) if len(range_val) > 1 and range_val[1] else file_size - 1
        end = min(end, file_size - 1)
        chunk_size = end - start + 1

        def iter_range():
            with open(path, "rb") as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    data = f.read(min(262144, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        return StreamingResponse(
            iter_range(),
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(chunk_size),
            },
        )

    def iter_full():
        with open(path, "rb") as f:
            while chunk := f.read(262144):
                yield chunk

    return StreamingResponse(
        iter_full(),
        media_type="video/mp4",
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes",
        },
    )

app.mount("/security", StaticFiles(directory="dist", html=True), name="static")

def delete_file(path: str):
    max_retries = 5
    for _ in range(max_retries):
        try:
            if os.path.exists(path):
                os.remove(path)
            return
        except Exception:
            time.sleep(0.5)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8086,
        log_level="debug",
        reload=False,
        ws_ping_interval=30, 
        ws_ping_timeout=300,
    )
