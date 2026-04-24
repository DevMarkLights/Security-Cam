
import requests
from requests.auth import HTTPDigestAuth
import time
import cv2
import os
from dotenv import load_dotenv
load_dotenv()

print('setting up camera config')
CAMERA_IP = os.getenv("REOLINK_CAMERA_IP")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("CAMERA_PASSWORD")

base_url = f'http://{CAMERA_IP}' 

TOKEN = ''

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
    
def stream():
    stream_url = f'rtsp://{USERNAME}:{PASSWORD}@{CAMERA_IP}:554/Preview_01_main'
    cap =  cv2.VideoCapture(stream_url)
    return cap

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