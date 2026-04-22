
import requests
from requests.auth import HTTPDigestAuth
import time
import os
from dotenv import load_dotenv
load_dotenv()

print('setting up camera config')
CAMERA_IP = os.getenv("FRONT_DOOR_CAMERA_IP")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("CAMERA_PASSWORD")

auth = HTTPDigestAuth(USERNAME, PASSWORD)
base_url = f'http://{CAMERA_IP}' 

def move_camera(direction, speed=4, duration=0.2, offset=0):
    r = requests.get(
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
    
    if r.status_code != 200:
        raise Exception('Bad Request')
         
def track(tracking:str):
    r = requests.get(
        f'{base_url}/cgi-bin/configManager.cgi',
        params={'action': 'setConfig', 'LeSmartTrack[0].Enable': tracking},
        auth=auth
    )
    
    if r.status_code != 200:
        raise Exception('Bad Request')


def setPreset():
    r = requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'start', 'channel': 0, 'code': 'SetPreset', 'arg1': 0, 'arg2': 1, 'arg3': 0},
        auth=auth
    )
    
    if r.status_code != 200:
        raise Exception('Bad Request')

def goToPreset():
    r = requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'start', 'channel': 0, 'code': 'GotoPreset', 'arg1': 0, 'arg2': 1, 'arg3': 0},
        auth=auth
    )
    
    if r.status_code != 200:
        raise Exception('Bad Request')
    

def goToPostion(x:int, y: int, z: int = 0, speed:int = 2):
    r = requests.get(
        f'{base_url}/cgi-bin/ptz.cgi',
        params={'action': 'start', 'channel': 0, 'code': 'PositionABS', 'arg1': x, 'arg2': y, 'arg3': z, 'arg4': speed},
        auth=auth
    )
    
    if r.status_code != 200:
        raise Exception('Bad Request')

def scan():
    goToPostion(x=5, y=10)
    # time.sleep(1)
    goToPostion(x=350,y=10)
    goToPreset()
    