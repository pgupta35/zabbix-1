#!/usr/bin/python
# -*- coding: utf-8 -*- # coding: utf-8
#
# arcconf.py - remote arcconf utility written in Python
#
# Matvey Marinin 2013
#
# Script to monitor Adaptec RAID controller status on VMWare ESXi hosts using Adaptec CIM Provider (arcconf)
#
# Usage: python arcconf.py --host esx1 --user root --password <pwd> GETCONFIG 1 AL
#
# The two components should be installed on ESXi host:
#  - recent aacraid driver from Adaptec site (http://www.adaptec.com/en-us/speed/raid/aac/linux/aacraid_vmware_drivers_1_2_1-29900_tgz.htm)
#  - Adaptec remote arcconf CIM Provider - vmware-esx-provider-arcconf.vib (http://www.adaptec.com/en-us/speed/raid/storage_manager/cim_vmware_v7_31_18856_zip.htm)
#
# Only subset of arcconf commands will work. The following commands has been successfully tested:
# GETCONFIG
# GETLOGS
# GETSMARTSTATS
# GETSTATUS
# GETVERSION
# RESCAN
# SETALARM
# 

import pywbem
import getopt, sys

def usage():
  print >> sys.stderr, "Usage: arcconf.py --host <ESXi host name/IP> --user <username> --password <pwd> <arcconf command>"

try:
  opts, args = getopt.getopt(sys.argv[1:], "-h", ["help", "host=", "user=", "password="])
except getopt.GetoptError, err:
  print >> sys.stderr, str(err)
  usage()
  sys.exit(2)

host = None
user = None
password = None
for o, a in opts:
  if o == "--host":
    host = a
  elif o == "--user":
    user = a
  elif o == "--password":
    password = a
  elif o in ("-h", "--help"):
    usage()
    sys.exit()

if not host:
  print >> sys.stderr, 'ERROR: --host must be set'
  usage()
  sys.exit(2)

if not user or not password:
  print >> sys.stderr, 'ERROR: --user and --password options must be set'
  usage()
  sys.exit(2)

if not args:
  print >> sys.stderr, 'ERROR: Specify arcconf command to execute'
  usage()
  sys.exit(2)

# Make connection
conn = pywbem.WBEMConnection('https://'+host+':5989', (user, password), 'root/pmc/arc/cli')
conn.debug = True

'''
[Version ("1.0.0")]
class ARC_CLIExecutor {
        [Description ("Id of the instance")]
        string InstanceID;
        [Description ("The method to invoke the CLI command")]
        sint32 executeCommand(boolean warningFlag, string commands, string localFileName, string result, uint32 warningType);
};

InstanceID = ARC_CLI_Engine
'''

arccli = conn.EnumerateInstanceNames('ARC_CLIExecutor')[0]
commands = args
result = conn.InvokeMethod( 'executeCommand', arccli, warningFlag=True, commands=commands, localFileName='')

if not result[0]:
  print 'SUCCESS:'
  print result[1]['result']
  exit(0)
else:
  print 'ERROR:'
  print result[1]['result']
  exit(result[0])
