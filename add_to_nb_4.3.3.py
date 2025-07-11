import os
import json
import requests
import logging
import logging.handlers

from dotenv import load_dotenv


class NbPostDevice:
    ''' NetBox POST device '''

    def __init__(self, ipaddress, hostname, model, mac_address, interface, siteslug, swroleslug):
        self.ipaddress = ipaddress
        self.hostname = hostname
        self.model = model
        self.mac_address = mac_address
        self.interface = interface
        self.siteslug = siteslug
        self.swroleslug = swroleslug


    def postdevice(self):
        POSTSW = f"{URLNB}/api/dcim/devices/"

        sw_add = {
            "name": self.hostname,
            "device_type": {
            "model": self.model
            },
            "role": {
            "slug": self.swroleslug
            },
            "site": {
            "slug": self.siteslug
            },
            "description": "Added by script"
        }

        response = requests.post(POSTSW, headers=HEADERS, verify=False, json=sw_add)

        if response.status_code == 201:
            out_dev = response.json()
            dev_id = out_dev['id']

            return response.status_code, dev_id

        else:
            return response.status_code, 0

    def postint(self):
        POSTINT = f"{URLNB}/api/dcim/interfaces/"

        int_add = {
            "device": {
            "name": self.hostname
            },
            "name": self.interface,
            "type": "virtual",
            "enabled": True,
        }

        response = requests.post(POSTINT, headers=HEADERS, verify=False, json=int_add)

        if response.status_code == 201:
            out_int = response.json()
            int_id = out_int['id']

            return response.status_code, int_id

        else:
            return response.status_code, 0


    def postip(self, int_id):
        POSTIP = f"{URLNB}/api/ipam/ip-addresses/"

        ip_add = {
            "address": self.ipaddress,
            "status": "active",
            "assigned_object_type": "dcim.interface",
            "assigned_object_id": int(int_id)
        }

        response = requests.post(POSTIP, headers=HEADERS, verify=False, json=ip_add)

        return response.status_code


    def postmac(self, int_id):
        POSTIP = f"{URLNB}/api/dcim/mac-addresses/"

        mac_add = {
            "mac_address": self.mac_address,
            "assigned_object_type": "dcim.interface",
            "assigned_object_id": int(int_id)
        }

        response = requests.post(POSTIP, headers=HEADERS, verify=False, json=mac_add)

        return response.status_code


    def postmainip(self, dev_id):
        POSTMAINIP = f"{URLNB}/api/dcim/devices/{dev_id}/"

        main_ip = {
            "primary_ip4": {
            "address": self.ipaddress
            }
        }

        response = requests.patch(POSTMAINIP, headers=HEADERS, verify=False, json=main_ip)

        return response.status_code

    def postmainmac(self, int_id):
        POSTMAINIP = f"{URLNB}/api/dcim/interfaces/{int_id}/"

        main_mac = {
            "primary_mac_address": {
            "mac_address": self.mac_address
            }
        }

        response = requests.patch(POSTMAINIP, headers=HEADERS, verify=False, json=main_mac)

        return response.status_code


load_dotenv()
TOKEN_API = os.getenv('API_KEY')
HEADERS = {"Authorization": TOKEN_API}
URLNB = os.getenv('URLNB')
SITE_NAME = os.getenv('SITE_NAME')
IPSCAN = os.getenv('IPSCAN')
SWITCHES_FILE = os.getenv('SWITCHES_FILE')

LOGDIR = "./"
LOGNAME = f"log_switch_add_{IPSCAN}.log"

logger = logging.getLogger('SWITCH_ADD')
logger.setLevel(logging.DEBUG)
logfile = logging.handlers.RotatingFileHandler(f'{LOGDIR}{LOGNAME}', mode='w')

logfile.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logfile.setFormatter(formatter)
logger.addHandler(logfile)


with open(SWITCHES_FILE, 'r') as f:
    dt = f.read()
    switches_from_file = json.loads(dt)

    for sw in switches_from_file:
        swadd = NbPostDevice(**sw)

        add_code, dev_id = swadd.postdevice()
        if add_code == 201:
            logger.info(f'Устройство ({sw["hostname"]} - {sw["ipaddress"]}) - было добавлено')
        else:
            logger.error(f'Ошибка добавления ({sw["hostname"]} - {sw["ipaddress"]})')
            break

        add_int, int_id = swadd.postint()
        if add_int == 201:
            logger.info(f'Интерфейс для ({sw["hostname"]} - {sw["ipaddress"]}) - добавлен')
        else:
            logger.error(f'Ошибка добавления интерфейся для ({sw["hostname"]} - {sw["ipaddress"]})')
            break

        add_ip = swadd.postip(int_id)
        if add_ip == 201:
            logger.info(f'IP адресс для ({sw["hostname"]} - {sw["ipaddress"]}) - добавлен')
        else:
            logger.error(f'Ошибка добавления IP ({sw["hostname"]} - {sw["ipaddress"]})')
            break

        add_mac = swadd.postmac(int_id)
        if add_mac == 201:
            logger.info(f'MAC адресс для ({sw["hostname"]} - {sw["mac_address"]}) - добавлен')
        else:
            logger.error(f'Ошибка добавления MAC ({sw["hostname"]} - {sw["mac_address"]})')
            break

        mainip = swadd.postmainip(dev_id)
        if mainip == 200:
            logger.info(f'Основной IP адресс для ({sw["hostname"]} - {sw["ipaddress"]}) - добавлен')
        else:
            logger.error(f'Ошибка добавления основного IP ({sw["hostname"]} - {sw["ipaddress"]})')
            break

        mainmac = swadd.postmainmac(int_id)
        if mainmac == 200:
            logger.info(f'Основной MAC адресс для ({sw["hostname"]} - {sw["mac_address"]}) - добавлен')
        else:
            logger.error(f'Ошибка добавления основного MAC ({sw["hostname"]} - {sw["mac_address"]})')
            break
