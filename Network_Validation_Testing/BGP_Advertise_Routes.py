#! /usr/bin/env python3

from netmiko.exceptions import NetMikoTimeoutException
from paramiko.ssh_exception import SSHException
from netmiko.exceptions import AuthenticationException
from netmiko import ConnectHandler
import jinja2
import os, shutil, os.path
from paramiko import *
import getpass


# Import your host variables from Variables file

from Variables_Hosts import *

''' Confirming that BGP is advertising local routes to upstream peer from local router.  This script uses one router only but can be used for multiple.
The route policy advertisement for this test was a simple one as an example in which only directly connected IRBs are being advertised.  Modification
would be necessary for different route policy requirements based on environment.'''




def BGP_Route_Advertisement()
    try:
        net_connectR01 = ConnectHandler(**Host01)
        promptR01 = net_connectR01.find_prompt()
        print("Confirming BGP Route Advertisement for " + Router_01_Hostname + " at " + Site_Name)
        # Parsing config output in set format to filter on BGP neighbor.  Converting from string to list as the neighbor IP will be the seventh item in the list.
        Gather_BGP_Neighbor = net_connectR01.send_command('show configuration protocols bgp group <group-name> | match neighbor | display set')
        BGP_Neighbor_list = Gather_BGP_Neighbor.split()
        # Pass the BGP neighbor in the seventh term as a variable
        BGP_Neighbor = BGP_Neighbor_list[6]
        # Loop through Local IRBs to gather networks that are being advertised.  
        ''' The procedure below is as follows:
        i) The routers are running VRRP for their local LAN addresses, so a "show configuration" command is ran to filter on the virtual-address
        ii) The output (Gather_Local_IRBs) is converted to a list for easier parsing.  The Local IRB address/mask is ninth in the list (eighth index)
        Example output "set interfaces irb unit <#> family inet address <Router_Local_IP>/<Mask> vrrp-group <#> virtual-address <Virtual IP>"
        We are capturing the <Router_Local_IP>/<Mask> in this output 
        iii) Since the Local IP is +2 from the network address, a procedure is done to isolate the local address and subtract 2 in order to get the network subnet
        iv) Join the network address with the subnet mask as a variable and check that this is being advertised to BGP neighbor
        v) Loop back through all the Local IRBs in the host file list with a for loop.  '''
        for i in Local_IRBs:
            Gather_Local_IRBs = net_connectR01.send_command('show configuration interfaces ' + i + ' | match virtual-address | display set')
            Gather_Local_IRBs_List = Gather_Local_IRBs.split()
            Local_IRB_Subnet = Gather_Local_IRBs_List[8]
            # Splitting into a list of two items...IP address and Subnet Mask separated by '/' character
            Local_IRB_Subnet = Local_IRB_Subnet.split('/')
            # Split the IP address into a sub list of different octetcs
            octets_list = Local_IRB_Subnet[0].split('.')
            netmask = Local_IRB_Subnet[1]
            last_oct = octets_list[3]
            last_oct = int(last_oct)
            # Convert the last octect to network address by subtracting two 
            netwk_addr_oct = last_oct - 2
            netwk_addr_oct = str(netwk_addr_oct)
            # Replace last term of octet list with the correct term to create the network address
            octets[3] = netwk_addr_oct
            # Convert octet list back to string of network address
            octets = '.'.join(octets)
            Local_IRB_Subnet[0] = octets
            # At this point the list 'Local_IRB_Subnet' has two items.  i) the network address and ii) the network mask.  
            # The variable below joins it into one network address and mask variable by joining via the '/' separator.  i.e. 192.168.1.0/24
            network_address_and_mask = '/'.join(Local_IRB_Subnet)
            # Below we check to see if the route shows up in the route advertisement output.  It's important to strip the command so a false output from the 
            # command line is not returned
          
            BGP_route_advertisement_output_only = net_connectR01.send_command('show route advertising-protocol bgp ' + BGP_Neighbor + ' | match ' + network_address_and_mask + ' | no-more\n',
                                                                      strip_prompt=True, strip_command=True)
            # Print to screen to see the output
          
            print(promptR01 + BGP_route_advertisement_output_only)
            # Check output to determine pass or fail.  If any of the network addresses and masks are not visible, then the test fails
            if network_address_and_mask in BGP_route_advertisement_output_only:
                print("Test has passed!  " + network_address_and_mask + " is being advertised to BGP neighbor on Router01")
            else:
                print("Test failed!  " + network_address_and_mask + " is not being advertised to BGP neighbor on Router 01, check your config.")
            
            
        
    except(AuthenticationException):
        print('Authentication Failure for ' + Router_01_Hostname)
    except(NetMikoTimeoutException):
        print('Timeout to device: ' + Router_01_Hostname)
    except(SSHException):
        print('SSH may not be enabled on ' + Router_01_Hostname + '.  Check the configuration again')

BGP_Route_Advertisement()
        


