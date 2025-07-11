import os
import json
import requests
import logging
import logging.handlers
from dotenv import load_dotenv


class NbCheckDevice:
    ''' NetBox check device '''

    def __init__(self, ipaddress, hostname, model, mac_address, interface, siteslug, swroleslug):
        self.ipaddress = ipaddress
        self.hostname = hostname
        self.model = model
        self.mac_address = mac_address
        self.interface = interface
        self.swroleslug = swroleslug
        self.siteslug = siteslug


    def getdevice(self):
        URLSW = f"{URLNB}/api/dcim/devices/?name="
        print(URLSW+self.hostname)
        response = requests.get(URLSW+self.hostname, headers=HEADERS, verify=False)
        device_list = json.loads(json.dumps(response.json()))

        if device_list['count'] > 0:
            swmodel = False

            return device_list['count'], swmodel

        else:
            URLMODEL = f'{URLNB}/api/dcim/device-types/?model='
            swmodel = False

            response = requests.get(URLMODEL+self.model, headers=HEADERS, verify=False)
            model_list = json.loads(json.dumps(response.json()))

            if model_list['count'] > 0:
                for ml in model_list['results']:
                    swmodel = ml['model']

                return 0, swmodel

            else:
                return 0, swmodel

load_dotenv()

TOKEN_API = os.getenv('API_KEY')
HEADERS = {"Authorization": TOKEN_API}
URLNB = os.getenv('URLNB')
SWPOST = f'{URLNB}/api/dcim/devices/'
CHECK_FILE = os.getenv('CHECK_FILE')
IPSCAN = os.getenv('IPSCAN')

LOGDIR = "./"
LOGNAME = f"log_switch_check_{IPSCAN}.log"

logger = logging.getLogger('SWITCH_CHECK')
logger.setLevel(logging.DEBUG)
logfile = logging.handlers.RotatingFileHandler(f'{LOGDIR}{LOGNAME}', mode='w')

logfile.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logfile.setFormatter(formatter)
logger.addHandler(logfile)


with open(CHECK_FILE, 'r') as f:
    dt = f.read()
    switches_from_file = json.loads(dt)

    unknown_devices = []
    exist_devices = []
    none_model = []
    add_devices = []

    for l in switches_from_file:
        _ = l.pop('vendor')
        if l['hostname'] == 'unknown' or l['model'] == 'unknown' == 'unknown':
            logger.info(f'Коммутатор ({l["ipaddress"]}) нужно будет добавить руками')
            unknown_devices.append(l)
        else:
            device = NbCheckDevice(**l)
            device_count, swmodel = device.getdevice()
            if device_count > 0:
                logger.info(f'Коммутатор ({l["ipaddress"]}) уже есть в НетБоксе')
                exist_devices.append(l)
            elif swmodel == False:
                logger.info(f'Для коммутатора ({l["ipaddress"]}) нужно создать модель')
                none_model.append(l)
            else:
                logger.info(f'Коммутатор ({l["ipaddress"]}, {swmodel}) можно добавить скриптом')
                switch_model = {'model': swmodel}
                add_devices.append({**l, **switch_model})

with open(f'unknown_{CHECK_FILE}', 'w') as f:
    json.dump(unknown_devices, f, sort_keys=True, indent=2)

with open(f'exist_{CHECK_FILE}', 'w') as f:
    json.dump(exist_devices, f, sort_keys=True, indent=2)

with open(f'none_model_{CHECK_FILE}', 'w') as f:
    json.dump(none_model, f, sort_keys=True, indent=2)

with open(f'add_{CHECK_FILE}', 'w') as f:
    json.dump(add_devices, f, sort_keys=True, indent=2)
