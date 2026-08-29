
from collections import deque
import datetime
from queue import Queue
import subprocess
import sys
import threading
import logging
from fastapi import WebSocket
import requests
from requests.auth import HTTPDigestAuth
import time
import cv2
import numpy as np
import os
from dotenv import load_dotenv
load_dotenv()

print('setting up camera config')
CAMERA_IP = os.getenv("REOLINK_CAMERA_IP")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("CAMERA_PASSWORD")

base_url = f'http://{CAMERA_IP}' 

TOKEN = ''
record_buffer = deque(maxlen=600) # minute of frames
frame_queue = deque(maxlen=30) # queue for frames
stop_event = threading.Event()
RECORDING = False
VIDEO=None
VideoFileName = ''

BUFFER_LIMIT_BYTES = 1_073_741_824  # 1 GB
_cont_buffer: list = []
_cont_buffer_bytes: int = 0
_cont_lock = threading.Lock()

def getToken():
    global TOKEN
    r = requests.post(
        f'{base_url}/api.cgi',
        params={'cmd': 'Login'},
        # headers="Content-Type: application/json"
        json=[{'cmd':'Login', 'action':0, 'param': {'User':{'userName':USERNAME, 'password': PASSWORD}}}]
    )
    
    data = r.json()
    TOKEN = data[0]["value"]["Token"]["name"]
    

def move_camera(direction, speed=2, duration=.05, offset=0):
    if TOKEN == '':
        getToken()
    
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd':'PtzCtrl', 'token':TOKEN},
        json=[{'cmd':'PtzCtrl','action':0, 'param':{'channel':0, 'op': direction, 'speed': speed, 'timeout':duration}}]
    )
    
    time.sleep(duration)
    
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'PtzCtrl', 'token': TOKEN},
        json=[{'cmd': 'PtzCtrl', 'action': 0, 'param': {'channel': 0, 'op': 'Stop', 'speed': speed, 'timeout': 1}}]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd':'PtzCtrl', 'token':TOKEN},
            json=[{'cmd':'PtzCtrl','action':0, 'param':{'channel':0, 'op': direction, 'speed': speed, 'timeout':duration}}]
        )
        
        time.sleep(duration)
    
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'PtzCtrl', 'token': TOKEN},
            json=[{'cmd': 'PtzCtrl', 'action': 0, 'param': {'channel': 0, 'op': 'Stop', 'speed': speed, 'timeout': 1}}]
        )
    
    if r.status_code != 200:
        raise Exception('Bad Request')
         
def track(tracking:bool):
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'SetAiCfg', 'token': TOKEN},
        json=[{
            'cmd': 'SetAiCfg',
            'action': 0,
            'param': {
                'channel': 0,
                'aiTrack': 1 if tracking else 0,
                'bSmartTrack': 1 if tracking else 0,
                'trackType': {},
                'AiDetectType': {
                    'people': 1,
                    'vehicle': 0,
                    'dog_cat': 1,
                    'face': 0
                }
            }
        }]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'SetAiCfg', 'token': TOKEN},
            json=[{
                'cmd': 'SetAiCfg',
                'action': 0,
                'param': {
                    'channel': 0,
                    'aiTrack': 1 if tracking else 0,
                    'bSmartTrack': 1 if tracking else 0,
                    'trackType': {},
                    'AiDetectType': {
                        'people': 1,
                        'vehicle': 0,
                        'dog_cat': 1,
                        'face': 0
                    }
                }
            }]
        )
    
    if r.status_code != 200:
        raise Exception('Bad Request')

def setPreset(preset_id: int, name: str, enable: int = 1):
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'SetPtzPreset', 'token': TOKEN},
        json=[{
            'cmd': 'SetPtzPreset',
            'action': 0,
            'param': {
                'PtzPreset': {
                    'channel': 0,
                    'enable': enable,
                    'id': preset_id,
                    'name': name
                }
            }
        }]
    )
    
    if 'error' in r.json()[0]:
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'SetPtzPreset', 'token': TOKEN},
            json=[{
                'cmd': 'SetPtzPreset',
                'action': 0,
                'param': {
                    'PtzPreset': {
                        'channel': 0,
                        'enable': enable,
                        'id': preset_id,
                        'name': name
                    }
                }
            }]
        )
        
    if r.status_code != 200:
        raise Exception('Bad Request')

def goToPreset(id: int = 1):
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'PtzCtrl', 'token': TOKEN},
        json=[{
            'cmd': 'PtzCtrl',
            'action': 0,
            'param':{
                "channel":0,
                "op":"ToPos",
                "id": id,
                "speed":32
            }
        }]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'PtzCtrl', 'token': TOKEN},
            json=[{
                'cmd': 'PtzCtrl',
                'action': 0,
                'param':{
                    "channel":0,
                    "op":"ToPos",
                    "id": id,
                    "speed":32
                }
            }]
        )
    
    if r.status_code != 200:
        raise Exception('Bad Request')
    
def _flush_buffer(buffer_snapshot: list) -> None:
    """Decode a JPEG frame snapshot and append it to today's daily MP4 via ffmpeg concat."""
    today = datetime.date.today().strftime('%Y-%m-%d')
    daily_file = f'{today}.mp4'
    chunk_file = f'chunk_{int(time.time())}.mp4'

    try:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(chunk_file, fourcc, 10, (854, 480))
        for jpeg_bytes in buffer_snapshot:
            arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is not None:
                writer.write(frame)
        writer.release()

        if os.path.exists(daily_file):
            list_file = f'concat_{int(time.time())}.txt'
            merged_file = f'{today}_merged.mp4'
            with open(list_file, 'w') as f:
                f.write(f"file '{os.path.abspath(daily_file)}'\n")
                f.write(f"file '{os.path.abspath(chunk_file)}'\n")
            result = subprocess.run(
                ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_file, '-c', 'copy', merged_file],
                capture_output=True
            )
            if os.path.exists(list_file):
                os.remove(list_file)
            if result.returncode == 0:
                os.replace(merged_file, daily_file)
                os.remove(chunk_file)
            else:
                logging.error(f'ffmpeg concat failed: {result.stderr.decode()}')
                if os.path.exists(merged_file):
                    os.remove(merged_file)
        else:
            os.rename(chunk_file, daily_file)

        logging.info(f'Buffer flushed → {daily_file}')
    except Exception as e:
        logging.error(f'Buffer flush failed: {e}')
        if os.path.exists(chunk_file):
            try:
                os.remove(chunk_file)
            except Exception:
                pass


def stream(logging, frame_lock):
    stream_url = f'rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/Preview_01_main'
    global RECORDING, VIDEO, VideoFileName, _cont_buffer, _cont_buffer_bytes
    try:
        logging.info("Camera thread started")
        while not stop_event.is_set():
            cap =  cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                logging.error("Failed to open RTSP stream, retrying in 5s")
                time.sleep(5)
                continue
            
            logging.info("RTSP stream opened successfully")
            frame_count = 0
        
            while not stop_event.is_set():
            
                ret, frame = cap.read()
                if not ret:
                    logging.warning("Lost RTSP stream, reconnecting...")
                    break
                
                frame_count += 1
                if frame_count % 3 != 0:
                    continue
                else:
                    frame_count = 0
                
                frame = cv2.resize(frame, (854, 480))
                
                if RECORDING and VIDEO is None:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    VideoFileName = str(datetime.datetime.now()).split('.')[0].replace(' ','_').replace(':', '-')
                    VIDEO = cv2.VideoWriter(filename=f'{VideoFileName}.mp4', fourcc=fourcc, fps=15, frameSize=(854, 480), isColor=True)
                    VIDEO.write(frame)
                elif RECORDING and VIDEO is not None:
                    VIDEO.write(frame)
                elif not RECORDING and VIDEO is not None:
                    VIDEO.release()
                    VIDEO = None
                
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                compressed = buffer.tobytes()
                with frame_lock: # lock queue from being accessed while inserting
                    frame_queue.append(compressed)

                snapshot = None
                with _cont_lock:
                    _cont_buffer.append(compressed)
                    _cont_buffer_bytes += len(compressed)
                    if _cont_buffer_bytes >= BUFFER_LIMIT_BYTES:
                        snapshot = _cont_buffer
                        _cont_buffer = []
                        _cont_buffer_bytes = 0
                if snapshot is not None:
                    threading.Thread(target=_flush_buffer, args=(snapshot,), daemon=True).start()
    except Exception as e:
        logging.error(e)
        raise Exception('Could not start stream')
    finally:
        cap.release()
        VIDEO = None
        RECORDING = False

def buffer_size():
    total = sum(sys.getsizeof(frame) for frame in record_buffer)
    return f"Buffer size: {total / (1024 * 1024):.2f} MB"

def getAbility():
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'GetAbility', 'token': TOKEN},
        json=[{'cmd': 'GetAbility', 'param': {'User': {'userName': USERNAME}}}]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'GetAbility', 'token': TOKEN},
            json=[{'cmd': 'GetAbility', 'param': {'User': {'userName': USERNAME}}}]
        )
    
    if r.status_code != 200:
        raise Exception('Bad Request')

def setPatrolConfig(enable:int=1,id=0):
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'SetPtzPatrol', 'token': TOKEN},
        json=[{'cmd': 'SetPtzPatrol', 
               "action":0,
               'param':{
                    "PtzPatrol":{
                        "channel":0,
                        "enable": enable,
                        "id": id,
                        "speed":4,
                        "running":0,
                        "name":"patrol 0 - 1",
                        'preset':[
                            {
                                'dwellTime': 5,
                                'id':0,
                                'speed':1
                            },
                            {
                                'dwellTime': 5,
                                'id':1,
                                'speed':1
                            }
                        ]
                    }
                }
            }   
        ]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'SetPtzPatrol', 'token': TOKEN},
            json=[{'cmd': 'SetPtzPatrol', 
                "action":0,
                'param':{
                        "PtzPatrol":{
                            "channel":0,
                            "enable": enable,
                            "id": id,
                            "speed":4,
                            "running":0,
                            "name":"patrol 0 - 1",
                            'preset':[
                                {
                                    'dwellTime': 3,
                                    'id':0,
                                    'speed':1
                                },
                                {
                                    'dwellTime': 3,
                                    'id':1,
                                    'speed':1
                                }
                            ]
                        }
                    }
                }   
            ]
        )
    
    if r.status_code != 200:
        raise Exception('Bad Request')

def getPatrolConfig():
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'GetPtzPatrol', 'token': TOKEN},
        json=[{'cmd': 'GetPtzPatrol', 
               "action":0,
               'param':{
                    "channel":0
                }
            }   
        ]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'GetPtzPatrol', 'token': TOKEN},
            json=[{'cmd': 'GetPtzPatrol', 
                "action":0,
                'param':{
                        "channel":0
                    }
                }   
            ]
        )
        
    if r.status_code != 200:
        raise Exception('Bad Request')

def startPatrol():
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd':'PtzCtrl', 'token':TOKEN},
        json=[{'cmd':'PtzCtrl','action':0, 'param':{'channel':0, 'op': 'StartPatrol', 'id': 0, 'speed':1}}]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd':'PtzCtrl', 'token':TOKEN},
            json=[{'cmd':'PtzCtrl','action':0, 'param':{'channel':0, 'op': 'StartPatrol', 'id': 0, 'speed':1}}]
        )

    if r.status_code != 200:
        raise Exception('Bad Request')

def stopPatrol():
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd':'PtzCtrl', 'token':TOKEN},
        json=[{'cmd':'PtzCtrl','action':0, 'param':{'channel':0, 'op': 'StopPatrol', 'id': 0, 'speed':4}}]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd':'PtzCtrl', 'token':TOKEN},
            json=[{'cmd':'PtzCtrl','action':0, 'param':{'channel':0, 'op': 'StopPatrol', 'id': 0, 'speed':4}}]
        )
    
    goHome()

    if r.status_code != 200:
        raise Exception('Bad Request')

def getPresets():
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'GetPtzPreset', 'token': TOKEN},
        json=[{'cmd': 'GetPtzPreset', 'action': 1, 'param': {'channel': 0}}]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'GetPtzPreset', 'token': TOKEN},
            json=[{'cmd': 'GetPtzPreset', 'action': 1, 'param': {'channel': 0}}]
        )
    
    print(r.json())
    if r.status_code != 200:
        raise Exception('Bad Request')

def goHome():
    if TOKEN == '':
        getToken()
        
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'PtzCtrl', 'token': TOKEN},
        json=[{
            'cmd': 'PtzCtrl',
            'action': 0,
            'param':{
                "channel":0,
                "op":"ToPos",
                "id": 2,
                "speed":32
            }
        }]
    )
    
    if 'error' in r.json()[0]:
        getToken()
        r = requests.post(
            url=f'{base_url}/api.cgi',
            params={'cmd': 'PtzCtrl', 'token': TOKEN},
            json=[{
                'cmd': 'PtzCtrl',
                'action': 0,
                'param':{
                    "channel":0,
                    "op":"ToPos",
                    "id": 2,
                    "speed":32
                }
            }]
        )
    
    if r.status_code != 200:
        raise Exception('Bad Request')

def getISPConf():
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'GetIsp', 'token': TOKEN},
        json=[{
            'cmd': 'GetIsp',
            'action': 1,
            'param':{
                "channel":0,
            }
        }]
    )
    
    print(r.json())

def flipImage():
    
    r = requests.post(
        url=f'{base_url}/api.cgi',
        params={'cmd': 'SetIsp', 'token': TOKEN},
        json=[{
            'cmd': 'SetIsp',
            'action': 0,
            'param': {
                'Isp': {
                    'channel': 0,
                    'mirroring': 1,
                    'rotation': 1
                }
            }
        }]
    )
    print(r.json())

if __name__ == "__main__":
    # getToken()
    # flipImage()
    # setPreset(preset_id=1,name="preset1",enable=1)
    # setPatrolConfig()
    print()

