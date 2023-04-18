#!/usr/bin/env python3
import datetime
import queue
import re
import socket
import sys
import threading
import time


import paramiko
import scapy.all as scapy


## Source = https://stackoverflow.com/questions/166506/finding-local-ip-addresses-using-pythons-stdlib
## get_ip - finds the ip of the device running the script and adds /24.
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP + '/24'


## Source = https://levelup.gitconnected.com/writing-a-network-scanner-using-python-a41273baf1e2
## scan - uses the /24 subnet to arp the network and create a kv dictionary
def scan(ip):
    arp_req_frame = scapy.ARP(pdst=ip)
    broadcast_ether_frame = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    broadcast_ether_arp_req_frame = broadcast_ether_frame / arp_req_frame
    answered_list = scapy.srp(broadcast_ether_arp_req_frame, timeout=10, verbose=False)[0]
    result = []
    for i in range(0, len(answered_list)):
        client_dict = {answered_list[i][1].hwsrc: answered_list[i][1].psrc}
        result.append(client_dict)
    return result


ubiquiti_devices = {}


def match_macs(scanned_output):
    ubiquiti_ouis = ('00156d', '002722', '0418d6', '18e829', '245a4c', '24a43c', 
                    '28704e', '44d9e7', '602232', '687251', '70a741', '7483c2', 
                    '784558', '788a20', '802aa8', '9c05d6', 'ac8ba9', 'b4fbe4', 
                    'd021f9', 'd8b370', 'dc9fdb', 'e063da', 'e43883', 'f09fc2', 
                    'f492bf', 'f4e2c6', 'fcecda', '74acb9', '942a6f', '68d79a')

    stripper = lambda x: x.replace(":", "").replace("-", "")
    for arp_response in scanned_output:
        for mac, ip in arp_response.items():
            if stripper(mac).startswith(ubiquiti_ouis):
                ubiquiti_devices[mac] = ip


def system_exit():
    exit_choice = input("\nScript finished. Type exit to quit: ").upper()
    while exit_choice != "exit".upper():
        exit_choice = input("Script finished. Type exit to quit: ").upper()
    else:
        sys.exit()


## ssh_connect - function to ssh into each ip and set inform unifi devices.
def ssh_connect(mac, ip):
    port = 22
    username = "ubnt"
    password = "ubnt"
    command = "set-inform "  # controller server location
    date_time = datetime.datetime.now().strftime("%H:%M:%S %p")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip, port, username, password)
        connection = ssh.invoke_shell()

        time.sleep(0.1)
        connection.send("\n")
        connection.send(command + "\n")
        time.sleep(0.1)

        if connection:
            print(f"MAC: {mac}, IP: {ip} is completed, it was started at {date_time}")
        else:
            print(f'***FAILED*** MAC: {mac}, IP: {ip} not default user/pass. Factory reset Unifi device and try again.')
            time.sleep(2)
    except paramiko.ssh_exception.BadHostKeyException as e:
        print(f"Device, {mac}, {ip}, host key could not be verified: {e}")
        failed_devices[mac] = ip
    except paramiko.ssh_exception.AuthenticationException as e:
        print(f"Error connecting to device, {mac}, {ip}, likely due to incorrect user/pass: {e}")
        failed_devices[mac] = ip
    except paramiko.ssh_exception.SSHException as e:
        print(f"Failures in SSH2 protocol negotiation or logic errors on device, {mac}, {ip}, : {e}")
        failed_devices[mac] = ip
    except paramiko.ssh_exception.NoValidConnectionsError as e:
        print(f"Multiple connection attempts were made to device, {mac}, {ip}, and were not succeed: {e}")
        failed_devices[mac] = ip
    except socket.error as e:
        print(f"Socket error: {e}")
        failed_devices[mac] = ip
    finally:
        ssh.close()


failed_devices = {}


## ssh_thread - to multi thread the ssh connections instead of sequentially.
def ssh_thread(ubiquiti_devices):
    thread_instance = queue.Queue()
    for mac, ip in ubiquiti_devices.items():
        trd = threading.Thread(target=ssh_connect, args=(mac, ip,))
        trd.setDaemon = True
        trd.start()
        thread_instance.put(trd)
        time.sleep(0.08)


allowed_input = {"Y", "N", "R", "P"}


def handle_input():
    while True:
        choice = input(f'\n{len(ubiquiti_devices)} devices found on subnet {subnet_regex[0]}1/24\nY to set-inform all devices to cloud controller, R to rescan, P to print MAC : IP or N to exit: ').upper()
        if choice not in allowed_input:
            print("Please choose a valid option...")
        elif choice == "N":
            print("Exiting script...")
            sys.exit()
        elif choice == "P":
            for mac, ip in ubiquiti_devices.items():
                print(f'Found MAC: {mac}, IP: {ip} ')
            handle_input()
        elif choice == "R":
            print("\nRescanning network...")
            scanned_output = scan(get_ip())
            time.sleep(1)
            match_macs(scanned_output)
            for mac, ip in ubiquiti_devices.items():
                print("Found MAC: {}, IP: {} ".format(mac, ip))
            time.sleep(0.2)
            handle_input()
        elif choice == "Y":
            ssh_thread(ubiquiti_devices)
            time.sleep(20)

            if len(failed_devices) == 1:
                print(f'\nThere was {len(failed_devices)} device that failed:')
            else:
                print(f'\nThere were {len(failed_devices)} devices that failed:')
            for mac, ip in failed_devices.items():
                print(f'***FAILED*** MAC: {mac}, IP: {ip} likely not default user/pass. Factory reset unifi device without internet access (WAN) and try again.')
            system_exit()

            
# Gets ip of host machine.
IP = get_ip()


# Pulls first 3 decimals of subnet.
subnet_regex = re.search(r'(([0-9]{1,3}[.]{1}){3})', IP)


print(f"\nScanning devices on your subnet {subnet_regex[0]}0/24 ... Please wait.")
      
      
# List of nodes on subnet from IP.
scanned_output = scan(IP)

# Calls the regex string to list of MAC/IPs.
match_macs(scanned_output)


if len(ubiquiti_devices) == 0:
    print(f"\nNo Unifi devices found on subnet: {subnet_regex[0]}0/24 \nExiting script.")
    time.sleep(5)
elif len(ubiquiti_devices) >= 1:
    handle_input()
