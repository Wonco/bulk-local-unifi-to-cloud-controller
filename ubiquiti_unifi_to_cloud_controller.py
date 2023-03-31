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
    for dictionary in scanned_output:
        for key, value in dictionary.items():
            #list of MAC OUIs linked to Ubqiti Inc on IEEE website 'https://standards-oui.ieee.org/oui/oui.txt'
            matched_ubiquiti_macs = re.findall(r"""(((24[-:]?5a[-:]?4c|60[-:]?22[-:]?32|e4[-:]?38[-:]?83|
            f0[-:]?9f[-:]?c2|80[-:]?2a[-:]?a8|78[-:]?8a[-:]?20|74[-:]?83[-:]?c2|e0[-:]?63[-:]?da|78[-:]?45[-:]?58|
            ac[-:]?8b[-:]?a9|9c[-:]?05[-:]?d6|28[-:]?70[-:]?4e|04[-:]?18[-:]?d6|24[-:]?a4[-:]?3c|44[-:]?d9[-:]?e7|
            d0[-:]?21[-:]?f9|70[-:]?a7[-:]?41|94[-:]?2a[-:]?6f|f4[-:]?e2[-:]?c6|d8[-:]?b3[-:]?70|b4[-:]?fb[-:]?e4|
            68[-:]?72[-:]?51|fc[-:]?ec[-:]?da|00[-:]?15[-:]?6d|00[-:]?27[-:]?22|dc[-:]?9f[-:]?db|18[-:]?e8[-:]?29|
            74[-:]?ac[-:]?b9|f4[-:]?92[-:]?bf|68[-:]?d7[-:]?9a)([-:]?[0-9a-fA-F]{2}){3})""", key, re.I)
            for line in matched_ubiquiti_macs:
                ubiquiti_devices[key] = value


def system_exit():
    exit_choice = input("\nScript finished. Type exit to quit: ").upper()
    while exit_choice != "exit".upper():
        exit_choice = input("Script finished. Type exit to quit: ").upper()
    else:
        sys.exit()


## ssh_conn - function to ssh into each ip and set inform unifi devices.
def ssh_conn(mac, ip):
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
            print(f'***FAILED*** MAC: {mac}, IP: {ip} not default user/pass. Factory reset unifi device and try again.')
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
        trd = threading.Thread(target=ssh_conn, args=(mac, ip,))
        trd.setDaemon = True
        trd.start()
        thread_instance.put(trd)
        time.sleep(0.08)
    ## Below - for not using queue
    # for thread in thread_instance:
    #     thread.join()


allowed_input = {"Y", "N", "R"}


def handle_input():
    while True:
        choice = input(f'\n{len(ubiquiti_devices)} devices found on subnet {subnet_regex[0]}1/24\nY to set-inform all devices to cloud controller, R to rescan or N to exit: ').upper()
        if choice not in allowed_input:
            print("Please choose a valid option...")
        elif choice == "N":
            print("Exiting script...")
            sys.exit()
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
            time.sleep(3.5)
            ## unhash below x2 lines for sequential instead of threaded
            # for host in ubiquiti_devices:
            #     ssh_conn(host)
            if len(failed_devices) == 1:
                print(f'\nThere was {len(failed_devices)} device that failed:')
            else:
                print(f'\nThere were {len(failed_devices)} devices that failed:')
            for mac, ip in failed_devices.items():
                print(f'***FAILED*** MAC: {mac}, IP: {ip} likely not default user/pass. Factory reset unifi device without internet access and try again.')
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
