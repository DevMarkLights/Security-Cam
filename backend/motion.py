import cv2
import requests
from requests.auth import HTTPDigestAuth
import time
import numpy as np
import asyncio
import threading

CAMERA_IP = '192.168.2.12'
USERNAME = 'admin'
PASSWORD = 'Mlights82!'

auth = HTTPDigestAuth(USERNAME, PASSWORD)
base_url = f'http://{CAMERA_IP}'

stream_url = f'rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/cam/realmonitor?channel=1&subtype=0'

cap = cv2.VideoCapture(stream_url)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1) # stops buffering from increasing

bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    history=500,      # frames to build background model
    varThreshold=50,  # sensitivity, higher = less sensitive
    detectShadows=False
)

prev_frame = None

DEADZONE_X = 400
DEADZONE_Y = 200
is_moving = False
frame_count = 0


def move_camera(direction, speed=4, duration=0.2, offset=0):
    global is_moving
    is_moving = True
    requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'start', 'channel': 0, 'code': direction, 'arg1': 0, 'arg2': speed, 'arg3': 0},
        auth=auth
    )
    time.sleep(duration)
    requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'stop', 'channel': 0, 'code': direction, 'arg1': 0, 'arg2': 0, 'arg3': 0},
        auth=auth
    )
    is_moving = False


def move_camera_async(direction,offset):
    if not is_moving:
        thread = threading.Thread(target=move_camera, args=(direction,))
        thread.start()

skip_frames = 0

print("Warming up background model...")
for _ in range(500):
    ret, frame = cap.read()
    if not ret:
        break
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    bg_subtractor.apply(gray)

print("Starting motion tracker...")
while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # frame_count += 1
    # if frame_count % 10 != 0:  # only process every 10th frame
    #     continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    
    frame_cx = frame.shape[1] // 2
    frame_cy = frame.shape[0] // 2
    moved = False

    if prev_frame is None:
        prev_frame = gray
        continue
    
    if skip_frames > 0:
        skip_frames -= 1
        prev_frame = gray
        continue
    
    # if is_moving:
    #     prev_frame = gray  # reset so camera movement doesn't trigger detection
    #     continue

    # Detect motion
    # diff = cv2.absdiff(prev_frame, gray)
    # thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
    # thresh = cv2.dilate(thresh, None, iterations=2)
    
    mask = bg_subtractor.apply(gray)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    largest = max(contours, key=cv2.contourArea) if contours else None

    if largest is not None and cv2.contourArea(largest) > 8000:
        print(f"Largest contour area: {cv2.contourArea(largest)}")
        x, y, w, h = cv2.boundingRect(largest)
        motion_cx = x + w // 2
        motion_cy = y + h // 2
        frame_cx = frame.shape[1] // 2
        frame_cy = frame.shape[0] // 2

        offset_x = motion_cx - frame_cx
        offset_y = motion_cy - frame_cy

        # print(f"Motion at offset X: {offset_x}, Y: {offset_y}")
        
        # if abs(offset_x) > DEADZONE_X and abs(offset_y) > DEADZONE_Y:
        #     if offset_x < 0 and offset_y < 0:
        #         move_camera_async('LeftUp', max(abs(offset_x), abs(offset_y)))
        #         moved = True
        #     elif offset_x > 0 and offset_y < 0:
        #         move_camera_async('RightUp', max(abs(offset_x), abs(offset_y)))
        #         moved = True
        #     elif offset_x < 0 and offset_y > 0:
        #         move_camera_async('LeftDown', max(abs(offset_x), abs(offset_y)))
        #         moved = True
        #     elif offset_x > 0 and offset_y > 0:
        #         move_camera_async('RightDown', max(abs(offset_x), abs(offset_y)))
        #         moved = True
        # elif abs(offset_x) > DEADZONE_X:
        #     move_camera_async('Left' if offset_x < 0 else 'Right', abs(offset_x))
        #     moved = True
        # elif abs(offset_y) > DEADZONE_Y:
        #     move_camera_async('Up' if offset_y < 0 else 'Down', abs(offset_y))
        #     moved = True
            
        ## Camera mounted upside down
        if abs(offset_x) > DEADZONE_X and abs(offset_y) > DEADZONE_Y:
            if offset_x < 0 and offset_y < 0:
                move_camera(direction='RightUp', offset=max(abs(offset_x), abs(offset_y)))
                # moved = True
            elif offset_x > 0 and offset_y < 0:
                move_camera(direction='LeftUp', offset=max(abs(offset_x), abs(offset_y)))
                # moved = True
            elif offset_x < 0 and offset_y > 0:
                move_camera(direction='RightDown', offset=max(abs(offset_x), abs(offset_y)))
                # moved = True
            elif offset_x > 0 and offset_y > 0:
                move_camera(direction='LeftDown', offset=max(abs(offset_x), abs(offset_y)))
                # moved = True
        elif abs(offset_x) > DEADZONE_X:
            move_camera(direction='Left' if offset_x < 0 else 'Right', offset=abs(offset_x))
            # moved = True
        elif abs(offset_y) > DEADZONE_Y:
            move_camera(direction='Up' if offset_y < 0 else 'Down', offset=abs(offset_y))
            # moved = True
        
        prev_frame = gray
        skip_frames = 5
    else:
                
        prev_frame = gray
            
            
    # cv2.imshow('Camera Feed', frame)
    # wait(.05)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()