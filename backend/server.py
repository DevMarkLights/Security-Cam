from fastapi import FastAPI, File, HTTPException, Request, UploadFile, Body, Form, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from typing import List
from fastapi.middleware.cors import CORSMiddleware
import cv2
import logging
import requests
from requests.auth import HTTPDigestAuth
import time
# from amcrestCamera import move_camera, track, setPreset, goToPreset, goToPostion, scan, stream
from reoLink import move_camera, track, setPreset, goToPreset, stream, startPatrol, stopPatrol, goHome
import asyncio
import base64
import subprocess
import os
from dotenv import load_dotenv
load_dotenv()
DEPLOY_SECRET = os.getenv("DEPLOY_SECRET")


logging.basicConfig(level=logging.ERROR)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

validTrackingParams = ['true','false','True','False']

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174","https://marks-pi.com","http://localhost:3004"],
    allow_credentials=False,   # MUST be FALSE
    allow_methods=["*"],
    allow_headers=["*"],
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
            track(True)
        else: 
            track(False)
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
            move_camera(direction=direction)
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
        setPreset( id = 2, name="Home", enable=1)
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
        goToPreset(id = 2)
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
       asyncio.create_task(asyncio.to_thread(startPatrol))
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
       stopPatrol()
    except Exception as e:
        logging.error(e)
        e_time = time.time()
        request_time = e_time - s_time
        raise HTTPException(status_code=500, detail={"Error":"Could not start scan","Request Time": f'{round(request_time,ndigits=3)}s'})
    
    e_time = time.time()
    request_time = e_time - s_time
    raise HTTPException(status_code=200, detail={"Scan":"Scan started","Request Time": round(request_time,ndigits=3)})  


@app.websocket("/security/ws/stream")
async def getStream(websocket: WebSocket):
    await websocket.accept()
    cap = stream()
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            if frame_count % 3 != 0:
                continue
            
            frame = cv2.resize(frame, (854, 480))
            
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            await websocket.send_text(frame_b64)
            await asyncio.sleep(0.05)  # ~30fps
    except WebSocketDisconnect:
        pass
    finally:
        cap.release()

@app.post("/goHome")
async def home():
    s_time = time.time()
    
    try:
       goHome()
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

app.mount("/security", StaticFiles(directory="dist", html=True), name="static")


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