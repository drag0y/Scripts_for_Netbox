import subprocess
import re
import json
import os
from dotenv import load_dotenv


class SwitchSnmpGet:
    ''' Get sysname and model from SNMP '''

    def __init__(self, ipaddress, snmp_com):
        self.ipaddress = ipaddress
        self.snmp_com = snmp_com


    def getsysdescr(self):

        sysdescroid = '1.3.6.1.2.1.1.1'
        parse_snmp = 'STRING: (?P<snmpout>.+)'
        sysdescr = 'unknown'

        process = subprocess.Popen(['snmpwalk', '-c', self.snmp_com, '-v2c', self.ipaddress, sysdescroid], stdout=subprocess.PIPE)

        while True:
            output = process.stdout.readline()

            if output == b'' and process.poll() is not None:
                break
            if output:
                outsnmp = output.decode('utf-8')
                match = re.search(parse_snmp, outsnmp)

                if match:
                    sysdescr = match.group('snmpout')

        return sysdescr


    def getsysname(self):
        ''' Получает hostname через snmp '''
        sysnameoid = '1.3.6.1.2.1.1.5'
        parse_snmp = 'STRING: (?P<snmpout>.+)'
        sysname = 'unknown'

        process = subprocess.Popen(['snmpwalk', '-c', self.snmp_com, '-v2c', self.ipaddress, sysnameoid], stdout=subprocess.PIPE)

        while True:
            output = process.stdout.readline()

            if output == b'' and process.poll() is not None:
                break
            if output:
                outsnmp = output.decode('utf-8')
                match = re.search(parse_snmp, outsnmp)

                if match:
                    sysname = match.group('snmpout')

        return sysname


parseout = (r'for (?P<ipaddress>\d+.\d+.\d+.\d+)'
            r'|MAC Address: (?P<mac>\S+) \((?P<vendor>.+)\)')

load_dotenv()
IPSCAN = os.getenv('IPSCAN')
NETMASK = os.getenv('NETMASK')
SNMP_COM = os.getenv('SNMP_COM')
INTERFACE = os.getenv('INTERFACE')
SITE_SLUG = os.getenv('SITE_SLUG')
SWROLESLUG = os.getenv('SWROLESLUG')

NETWORK = IPSCAN + NETMASK
ipaddress = ''

#print(network)
cmd_for_scan = f'nmap -sP -n {NETWORK}'
cmd = cmd_for_scan.split()

process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

result_list = []

while True:
    output = process.stdout.readline()
    if output == b'' and process.poll() is not None:
        break
    if output:
        outlist = output.strip().decode('utf-8')
        match = re.search(parseout, outlist)

        if match:
            if match.lastgroup == 'ipaddress':
                ipaddress = match.group(match.lastgroup)
                
            else:
                mac_address = match.group('mac').lower()
                vendor = match.group('vendor')
                get_model = SwitchSnmpGet(ipaddress, SNMP_COM)

                result_dict = {
                    'ipaddress': ipaddress+NETMASK,
                    'interface': INTERFACE,
                    'mac_address': mac_address,
                    'vendor': vendor,
                    'model': get_model.getsysdescr(),
                    'hostname': get_model.getsysname(),
                    'siteslug': SITE_SLUG,
                    'swroleslug': SWROLESLUG,
                    }
                
                result_list.append(result_dict)

#network = ipscan.split('/')

with open(f'nmap_{IPSCAN}.json', 'w') as f:
    json.dump(result_list, f, sort_keys=True, indent=2)
