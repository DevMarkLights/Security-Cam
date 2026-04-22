import requests
from requests.auth import HTTPDigestAuth
import cv2
import time
# from motion import move_camera

camera = None

CAMERA_IP = '192.168.2.12'
USERNAME = 'admin'
PASSWORD = 'Mlights82!'

auth = HTTPDigestAuth(USERNAME, PASSWORD)
base_url = f'http://{CAMERA_IP}'   

Configs = ['MotionDetect', 'Ptz']

def connect():

    response = requests.get(
        f'{base_url}/cgi-bin/magicBox.cgi',
        params={'action': 'getSoftwareVersion'},
        auth=auth
        )
    print(response.content.decode('utf-8'))
    
    response = requests.get(
        f'{base_url}/cgi-bin/configManager.cgi',
        params={'action': 'getConfig', 'name':'MotionDetect'},
        auth=auth
        )
    # print(response.content.decode('utf-8'))

    # return camera
        
def stream():
    stream_url = "rtsp://admin:Mlights82!@192.168.2.12:554/cam/realmonitor?channel=1&subtype=0"
    
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print("Error: Could not open stream")
        exit()

    print("Stream opened successfully")

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to grab frame")
            break
        
        # Display the frame
        cv2.imshow('Amcrest Live Feed', frame)
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

def setMotionDetectionOn():
    response = requests.get(
        f'{base_url}/cgi-bin/configManager.cgi',
        params={
            'action': 'setConfig',
            # 'MotionDetect[0].Enable:': 'true',
            'MotionDetect[0].EventHandler.PtzLinkEnable': 'true',
            'MotionDetect[0].EventHandler.PtzLink[0][0]': 'Track',
            'MotionDetect[0].EventHandler.PtzLink[0][1]': '0'
        },
        auth=auth
        )
    print(response.content.decode('utf-8'))
    
def detectMotion():
    response = requests.get(
        f'{base_url}/cgi-bin/eventManager.cgi',
        params={
            'action': 'getEventIndexes',
            'code': 'VideoMotion'
        },
        auth=auth
    )
    content = response.content.decode('utf-8').strip()
    return 'channels[0]=1' in content

def move_camera(direction, speed=4, duration=1):
    # Start
    requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={
            'action': 'start',
            'channel': 0,
            'code': direction,
            'arg1': 0,
            'arg2': speed,
            'arg3': 0
        },
        auth=auth
    )
    time.sleep(duration)
    requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={
            'action': 'stop',
            'channel': 0,
            'code': direction,
            'arg1': 0,
            'arg2': 0,
            'arg3': 0
        },
        auth=auth
    )
        

if __name__ == "__main__":
    # requests.get(
    #     f'{base_url}/cgi-bin/configManager.cgi',
    #     params={'action': 'setConfig', 'LeSmartTrack[0].Enable': 'false'},
    #     auth=auth
    # )
    connect()
    
    r = requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'start', 'channel': 0, 'code': 'PositionABS', 'arg1': 5, 'arg2': 10, 'arg3': 0, 'arg4': 2},
        auth=auth
    )
    
    # if r.status_code != 200:
    #     raise Exception('Bad Request')
    
    # time.sleep(1)
    
    r = requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'start', 'channel': 0, 'code': 'PositionABS', 'arg1': 350, 'arg2': 10, 'arg3': 0, 'arg4': 2},
        auth=auth
    )
    
    r = requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'start', 'channel': 0, 'code': 'GotoPreset', 'arg1': 0, 'arg2': 1, 'arg3': 0},
        auth=auth
    )
    

    
    # if r.status_code != 200:
    #     raise Exception('Bad Request')
   