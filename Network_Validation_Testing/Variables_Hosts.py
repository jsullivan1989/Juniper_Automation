### Variable file to continually be referenced with other Network Validation Scripts ###

''' The host Endpoint_MX references an endpoint router which will generate traffic to document reachability and failover traffic loss.
Modify as needed to fit your environment. '''

import getpass

passwd = getpass.getpass('Please enter your SSH password for your account: ')
Router_01 = '<Router #1 IP Address>'
Router_02 = '<Router #2 IP Address>'
# ...Add more routers or networking devices as needed 
# Endpoint MX router to source ICMP traffic from
Endpoint_MX = '<Endpoint_MX_Router_IP_Address>'
# Endpoint L3 IRB to generate traffic.  IRB.10 used as an example
Endpoint_IRB = 'irb.10'
Router_01_Hostname = '<Router_01_Hostname>'
Router_02_Hostname = '<Router_02_Hostname>'
# List of local IRBs on either Router 01 or 02 to run test network configuration, route advertisements, etc.
Local_IRBs = ['irb.1', 'irb.2', 'irb.3']
Site_Name = "<site_name>"
# Target IP Address to run ICMP traffic towards
Target_IP_Address = "<target_IP_address>"


# The session logfile would also need to be changed as well

Host01 = {
    'device_type': 'juniper',
    'host': Router_01,
    'username': '<username>',
    'password': passwd,
    'port': 22,
    'session_log': '/path/<logging_file_name>'
    }

Host02 = {
    'device_type': 'juniper',
    'host': Router_02,
    'username': '<username>',
    'password': passwd,
    'port': 22,
    'session_log': '/path/<logging_file_name>
}

# ...insert more hosts as needed

Endpoint_MX = {
    'device_type': 'juniper',
    'host': Endpoint_MX,
    'username': '<username>',
    'password': passwd,
    'port': 22,
}
