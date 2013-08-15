#!/usr/bin/python
# -*- coding: utf-8 -*- # coding: utf-8
#
# INSTALL:
#  easy_install pysphere (pip pysphere)
#
#

import getopt, sys
import time, datetime, calendar
from pysphere import VIServer
from pysphere.resources import VimService_services as VI
from pysphere.ZSI import FaultException as ZSI_FaultException

def usage():
  print >> sys.stderr, "Usage: vmw_host_mon.py <vcenter> <vc_user> <vc_password> <discovery|data>"

#print sys.argv

if len(sys.argv) != 5:
  print >> sys.stderr, 'ERROR: wrong args'
  usage()
  sys.exit(2)

vcenter = sys.argv[1]
user = sys.argv[2]
password = sys.argv[3]
mode = sys.argv[4]

server = VIServer()
server.connect(vcenter, user, password)
try:

  hosts = server.get_hosts()

  if mode == 'discovery':
    output = []
    for mof, name in hosts.items():
      output.append( '{"{#ID}":"%s", "{#NAME}":"%s"}' % (mof, name) )
      
    print '{ "data":['
    for i, v in enumerate( output ):
      if i < len(output)-1:
        print v+','
      else:
        print v
    print ' ]}'

  if mode == 'data':
    #<hostname> <key> <timestamp> <value>
    #vc-cloud.corp.tensor.ru vmware.host.timediff[host-1249] 1373876039 -1
        
    for x in server._get_object_properties_bulk( hosts.keys(), {'HostSystem':['configManager.dateTimeSystem']} ) :
      host_id = x.Obj
      host_name = hosts[x.Obj]
      hostDateTimeSystem = x.PropSet[0].Val
      
      try:
        ''' call vSphere SDK HostDateTimeSystem.QueryDateTime() method '''
        dtReqClass = VI.QueryDateTimeRequestMsg()
        dtReq = dtReqClass.new__this(hostDateTimeSystem)
        dtReq.set_attribute_type(hostDateTimeSystem.get_attribute_type())
        dtReqClass.set_element__this(dtReq)
      
        timestamp = int(time.time()) #save local time at SDK call to compare with remote host
        res = server._proxy.QueryDateTime(dtReqClass)._returnval #get remote ESXi host time as time.struct_time tuple
        host_time = int(time.mktime(res))
        time_diff = host_time - timestamp #time difference in seconds between ESXi host and system running this script
        #print host_id, host_name, time_diff
        print '%s vmware.host.timediff[%s] %d %s' % (vcenter, host_id, timestamp, time_diff)
      except ZSI_FaultException as e: ##Exception raised for unavailable hosts, skip to prevent log trashing
        pass
      except Exception as e:
        print >> sys.stderr, "Exception %s.%s: %s" % ( type(e).__module__, type(e).__name__, e )
        pass

finally:
  server.disconnect()
