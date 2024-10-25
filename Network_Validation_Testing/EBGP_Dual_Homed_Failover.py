#! /usr/bin/env python3

from netmiko.exceptions import NetMikoTimeoutException
from paramiko.ssh_exception import SSHException
from netmiko.exceptions import AuthenticationException
from netmiko import ConnectHandler
from netmiko import juniper
from paramiko import *
import jinja2
import os, shutil, os.path
import getpass
import json
import logging

'''This script is used to validate network failover and document outage time.  Two CPE Routers are each homed to separate PE routers upstream, through EBGP, while sharing all routes with each other
through IBGP.  The MX routers also share a Layer 2 cross-connect connection between them and run VRRP for the LAN side networks.  The failover will occur in this test by deactivating the EBGP 
connection from the CPE side via the "deactivate" command one router at a time.  Test ICMP traffic is run from the endpoint MX at the same time as the failover with outage times logged.  '''




# Import your host variables from reference Variable file in same directory

from Variables_Hosts import *


def BGP_Failover_Testing():
    try:
        # Initialize connections to both hosts defined in the Variables_Host file
        net_connectR01 = ConnectHandler(**Host01)
        net_connectR02 = ConnectHandler(**Host02)

        # BGP command run to display all BGP neighbors in json format for easier parsing 
      
        BGP_command = "show bgp neighbor | display json"
        
        
        # Confirm BGP is established  to External BGP peers first before proceeding to the failover testing
        # Checking that all of Router 1's neighbors are in the 'Established' state by parsing json output
       
        R01_BGP_output = net_connectR01.send_command(BGP_command)
        R01_data_json = json.loads(R01_BGP_output)
        
        print(Router_01_Hostname + " current BGP status")
      
        # Print each neighbor's status from Router 1's perspective.  If any configured neighbors are not in the Established state, then the script will exit and further troubleshooting is needed
      
        for neighbor in R01_data_json["bgp-information"][0]["bgp-peer"]:
            print ("session with " + neighbor["peer-address"][0]['data'] + " is " + neighbor["peer-state"][0]['data'])
            Neighbor_State = neighbor["peer-state"][0]['data']
            if Neighbor_State !=  'Established':
                net_connectR02.disconnect()
                net_connectR01.disconnect()
                print('Disconnecting from Routers.  Cannot perform failover test, one of neighbors is not Established on ' + Router_01_Hostname)
                exit()
              
            else:
                pass

        # Print each neighbor's status from Router 2's perspective.  If any configured neighbors are not in the Established state, then the script will exit and further troubleshooting is needed

        R02_BGP_output = net_connectR02.send_command(BGP_command)
        R02_data_json = json.loads(R02_BGP_output)

        print(Router_02_Hostname + " current BGP status")
        for neighbor in R02_data_json["bgp-information"][0]["bgp-peer"]:
            print ("session with " + neighbor["peer-address"][0]['data'] + " is " + neighbor["peer-state"][0]['data'])
            Neighbor_State = neighbor["peer-state"][0]['data']
            if Neighbor_State !=  'Established':
                net_connectR02.disconnect()
                net_connectR01.disconnect()
                exit()
                print('Disconnecting from Routers.  Cannot perform failover test, one of neighbors is not Established on ' + Router_02_Hostname)
            else:
                pass
              
        # Continue assuming all tests pass, gather eBGP neighbors from each router.  Convert output from string to list.
        # Neighbor will be the seventh term in list.  Store as variable for each router.
        # Parsing through config to get neighbor IP address and storing 
        EBGP_Neighbor_1 = net_connectR01.send_command('show configuration protocols bgp group <group-name> | match neighbor | display set')
        EBGP_Neighbor_2 = net_connectR02.send_command('show configuration protocols bgp group <group-name> | match neighbor | display set')
        EBGP_Neighbor_1_list = EBGP_Neighbor_1.split()
        EBGP_Neighbor_2_list = EBGP_Neighbor_2.split()
        R01_EBGP_neighbor = EBGP_Neighbor_1_list[6]
        R02_EBGP_neighbor = EBGP_Neighbor_2_list[6] 

        # Connect to Endpoint MX in order to run pings and establish prompt as a variable in 
        # order to accurately log 

        net_connect_endpoint = ConnectHandler(**Endpoint_MX)

        # Store prompt as variable by using find_prompt() method.  This method sends a \n\ down the channel and returns the current prompt i.e. 'user@mx960>'
        endpoint_prompt = net_connect_endpoint.find_prompt()

        # Set variable to log the ICMP traffic / traffic loss for Router 1 Failover

        # Using write_channel so that pings can run concurrently.   The \x03 ascii will be sent down the channel after to interrupt the command.
        

        net_connect_endpoint.write_channel("ping " + Target_IP + " interface " + Endpoint_IRB + "\n")
        
        ###### START OF ROUTER 1 FAILOVER TESTING ######
        # Shut down EBGP neighbor on Router #1.  Run a show | compare, commit check, and then and_quit=True 
        net_connectR01.send_config_set('deactivate protocols bgp group <group-name> neighbor ' + R01_EBGP_neighbor)
        net_connectR01.send_command_expect('show | compare | no-more' + '\n')
        net_connectR01.commit(check=True)
        net_connectR01.commit(and_quit=True, comment="Deactivating BGP to Router 1's PE peer for Failover ICMP Testing")
        # Confirm BGP session is now down on Router #1
        net_connectR01.send_command("show bgp summary | match " + R01_EBGP_neighbor)
        # Terminate the pings after R01 disables and confirms BGP neighborship to PE Router #1 is down
        net_connect_endpoint.write_channel('\x03')
        R01_BGP_Failover_Logging = net_connect_endpoint.read_channel()
        # Write this output to a dedicated LogFile for storing and documenting ICMP packet loss.  
        
        with open(Router_01_Hostname + '_BGP_Failover_ICMP_Logging.txt', 'w') as w:
            w.write(endpoint_prompt + R01_BGP_Failover_Logging)
            w.close()
        # Rollback the configuration on R1 in order to bring BGP back up
        net_connectR01.send_config_set('rollback 1')
        net_connectR01.send_command_expect('show | compare | no-more' + '\n')
        net_connectR01.commit(check=True)
        net_connectR01.commit(and_quit=True, comment="Rolling back change and bringing BGP Peer back up to PE connected to Router 1")
        # Confirm BGP Session back up on Router 1
        net_connectR01.send_command("show bgp summary | match " + R01_EBGP_neighbor)
        ###### End of Router 1 Failover Test ######

        # Start pings again to target IP downstream of R01 and R02

        net_connect_endpoint.write_channel("ping " + Target_IP + " interface " + Endpoint_IRB + "\n")
        
        ###### START OF ROUTER 2 FAILOVER TESTING ######
        # Shut down EBGP neighbor on Router #2.  Run a show | compare, commit check, and then and_quit=True 
        net_connectR02.send_config_set('deactivate protocols bgp group <group-name> neighbor ' + R02_EBGP_neighbor)
        net_connectR02.send_command_expect('show | compare | no-more' + '\n')
        net_connectR02.commit(check=True)
        net_connectR02.commit(and_quit=True, comment="Deactivating BGP to Router 2's PE peer for Failover ICMP Testing")
        # Confirm BGP session is now down on Router #2
        net_connectR02.send_command("show bgp summary | match " + R02_EBGP_neighbor)
        # Terminate the pings after R02 disables and confirms BGP neighborship to PE Router #2 is down
        net_connect_endpoint.write_channel('\x03')
        R02_BGP_Failover_Logging = net_connect_endpoint.read_channel()
        # Write this output to a dedicated LogFile for storing and documenting ICMP packet loss.  
        
        with open(Router_02_Hostname + '_BGP_Failover_ICMP_Logging.txt', 'w') as w:
            w.write(endpoint_prompt + R02_BGP_Failover_Logging)
            w.close()
        # Rollback the configuration on R2 in order to bring BGP back up
        net_connectR02.send_config_set('rollback 1')
        net_connectR02.send_command_expect('show | compare | no-more' + '\n')
        net_connectR02.commit(check=True)
        net_connectR02.commit(and_quit=True, comment="Rolling back change and bringing BGP Peer back up to PE connected to Router 2")
        # Confirm BGP Session back up on Router 2
        net_connectR02.send_command("show bgp summary | match " + R02_EBGP_neighbor)

        ###### End of Router 2 Failover Test ######


        # Disconnect from all devices

        net_connectR01.disconnect()
        net_connectR02.disconnect()
        net_connect_endpoint.disconnect()



    except(AuthenticationException):
        print('Authentication Failure for ' + Router_01_Hostname + ' and ' + Router_02_Hostname)
    except(NetMikoTimeoutException):
        print('Timeout to device: ' + Router_01_Hostname + ' or ' + Router_02_Hostname)
    except(SSHException):
        print('SSH may not be enabled on ' + Router_01_Hostname + ' or ' + Router_02_Hostname + '.  Check the configuration again')

BGP_Failover_Testing()
