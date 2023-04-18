# bulk-local-unifi-to-cloud-controller

Readme File for Unifi Device Discovery and Configuration Script

This script is designed to discover Unifi devices on a network and configure their inform settings for management by a Unifi controller.

The script utilizes Python 3 with the following dependencies:

- Paramiko
- Scapy

To run the script, clone the repository and execute the Python script. The script will begin by discovering devices on the local network, matching the manufacturer's MAC address prefix to Unifi devices, and then configuring their inform settings using SSH.


The script includes the following notable functions:

- get_ip() - finds the IP address of the device running the script and adds /24.
- scan(ip) - uses the /24 subnet to ARP the network and create a key-value dictionary of MAC addresses and their corresponding IP addresses.
- match_macs(scanned_output) - matches Unifi devices by their MAC address prefixes and adds them to a dictionary.
- ssh_conn(mac, ip) - connects to a device via SSH and sets the inform setting for the Unifi device.
- ssh_thread(ubiquiti_devices) - multi-threads the SSH connections.


After discovering and configuring devices, the script prompts the user to enter "exit" to quit. The script also records any devices that failed to connect or authenticate.

Note that the script currently uses default username and password credentials for Unifi devices (ubnt:ubnt). The "set-inform" is currently blank and needs to be change to your desired location. To customize these settings, edit the ssh_connect() function accordingly, specifically the value of 'command' for the "set-inform".

Contributions and feedback are welcome.

                                              .                                 
                                     *//////(((((((((((*                        
                                 /////(((((((((((((#######(                     
                              *///(((((((((((#############%%#                   
                           *//(((((((((##############%%%%%%%%%#                 
                         //((((((#############%%%%%%%%%%%%%&&&&&                
                       //((((###########%%%%%%%%%%%%%%&&&&&&&&&&&               
                      /(((#########%%#%%%%%%%%%%%&%&&&&&&&&&&&@&@&              
                    /((########%%%%%%%%%%%%%%&%&&&&&&&&&&&&&&@@@@@@             
                   ((######*   /*    %%%%&&&&&&&&&&&&&&&&@@@@@@@@@@             
                  (####%% %%%%%%%%%%&  %&&&&&&&&&&&&&&&@@@@@@@@@@@@             
                 ###%%%.%%%%%%&&&&&&&&, &&&&&&&&&&&&&@@@@@@@@@@@@@@@            
                ##%%%%*%%%%&&&&&&&&&&&&  &&&&&&&&&&@@@@@@@@@@@@@@@@@            
               #%%%%&%&&&&&&&&&&&&&&&&&/ &&&&&&&&&@@@@@@@@@@@@@@@@@@            
               %%%%&.&&&&&&*&*&&&&&&&&&* &&&&&&&&@@@@@@@@@@@@@@@@@@@            
              %%%&&/&&&&&&*U&*&&&&&&&&& %&&&&&&&@@@@@@@@@@@@@@@@@@@             
              %&&&&*&&&&&&&@&&&&&&&&&&% &&&&&&@@@@@@@@@@@@@@@@@@@@@             
             %&&&&&*&&&&&&&&&&&&&&&&&& &&&&@@@@@@@@@@@@@@@@@@@@@@@@             
             &&&&&&(#&&&&&&&&&&&&&&&( &&@&&@@@@@@@@@@@@@@@@@@@@@@@              
             &&&&&&&,&&&&&&&&@&&&&@ .&@@@@@@@@@@@@@@@@@@@@@@@@@@@               
             &&&&&&&&*.&&&@&&&&@.. @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@               
             &&&&&&&&&&*......./@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                
             (%&&&&&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                 
              %&&&&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                  
              %%&&&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                    
               %&&&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                     
                %&&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@                       
                 %&&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%                        
                  &&&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@@@@.                          
                    &&&&&&&@@@@@@@@@@@@@@@@@@@@@@@@                             
                      ,&&&&&&@@@@@@@@@@@@@@@@@@@                                
                          &&&&&@@@@@@@@@@@@&                                    

