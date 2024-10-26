### Variable file to continually be referenced with other Network Validation Scripts ###

''' The host Endpoint_MX references an endpoint router which will generate traffic to document reachability and failover traffic loss.
Modify as needed to fit your environment. '''

import getpass

# You will be prompted to name your LogDirectory and LogFile variables when importing this file in the different Network Validation Scripts
# These variables will be passed to session_log in order to log the commands during failover testing
# A separate logfile is made for each router

LogDirectory = input('Enter the name of the directory where you would like to log the data for this test: ')
R01_LogFile = input('Enter the name of the log file for Router 1: ')
R02_LogFile = input('Enter the name of the log file for Router 2: ')



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
    'session_log': LogDirectory + '/' + R01_LogFile
    }

Host02 = {
    'device_type': 'juniper',
    'host': Router_02,
    'username': '<username>',
    'password': passwd,
    'port': 22,
    'session_log': LogDirectory + '/' + R02_LogFile
}

# ...insert more hosts as needed

Endpoint_MX = {
    'device_type': 'juniper',
    'host': Endpoint_MX,
    'username': '<username>',
    'password': passwd,
    'port': 22,
}
