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

#### Calculate actual UTC offset to workaround 'MSK' timezone DST change in 2014 ####
#### pysphere uses time.timezone to convert datetime from UTC to local timezone  ####
t = time.time()
td = (datetime.datetime.utcfromtimestamp(t) - datetime.datetime.fromtimestamp(t))
utc_offset = (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6
time.timezone = utc_offset
print >> sys.stderr, 'DST offset: ', str(utc_offset)
####

def usage():
  print >> sys.stderr, "Usage: vmw_host_mon.py <vcenter_zabbix_host> <vcenter_dns_name> <vc_user> <vc_password> <discovery|time|status>"

#print sys.argv

if len(sys.argv) != 6:
  print >> sys.stderr, 'ERROR: wrong args'
  usage()
  sys.exit(2)

vcenter_host = sys.argv[1]
vcenter_dns = sys.argv[2]
user = sys.argv[3]
password = sys.argv[4]
mode = sys.argv[5]

server = VIServer()
server.connect(vcenter_dns, user, password)
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

  if mode == 'time':
    #output time difference in zabbix_sender format:
    #<hostname> <key> <timestamp> <value>
    #vcenter vmware.host.timediff[host-1249] 1373876039 -1
        
    for x in server._get_object_properties_bulk( hosts.keys(), {'HostSystem':['configManager.dateTimeSystem']} ) :
      try:
        host_id = x.Obj
        host_name = hosts[x.Obj]
        hostDateTimeSystem = x.PropSet[0].Val #can throw AttributeError

        ''' call vSphere SDK HostDateTimeSystem.QueryDateTime() method '''
        dtReqClass = VI.QueryDateTimeRequestMsg()
        dtReq = dtReqClass.new__this(hostDateTimeSystem)
        dtReq.set_attribute_type(hostDateTimeSystem.get_attribute_type())
        dtReqClass.set_element__this(dtReq)

        timestamp = int(time.time()) #save local time at SDK call to compare with remote host
        res2 = server._proxy.QueryDateTime(dtReqClass)
        res = res2._returnval #get remote ESXi host time as time.struct_time tuple in a local timezone

        host_time = int(time.mktime(res))
        time_diff = host_time - timestamp #time difference in seconds between ESXi host and system running this script

        #<hostname> <key> <timestamp> <value>
        print '%s vmware.host.timediff[%s] %d %s' % (vcenter_host, host_id, timestamp, time_diff)
        
      except ZSI_FaultException as e: #this exception is raised for unavailable hosts, hide it to prevent log trashing
        pass
      except AttributeError as e:
        print >> sys.stderr, "Host %s: AttributeError %s" % (host_name, e) #if host has no time data, skip it
	pass
      except Exception as e:
        print >> sys.stderr, "Exception %s.%s: %s" % ( type(e).__module__, type(e).__name__, e )
        pass

  if mode == 'status':
    #output host status in zabbix_sender format: <hostname> <key> <timestamp> <value>
    #
    # Host status items from VMWare vSphere API:
    # host.summary.overallStatus = { gray | green | red | yellow } (ManagedEntityStatus)
    # host.runtimeinfo.connectionState = { connected | disconnected | notResponding } (HostSystemConnectionState)
    # host.runtimeinfo.dasHostState.state = { connectedToMaster | election | fdmUnreachable | hostDown | initializationError | master | networkIsolated | networkPartitionedFromMaster | uninitializationError | uninitialized } (ClusterDasFdmAvailabilityState)
    # host.runtimeinfo.inMaintenanceMode = { true | false }

    hostItems = {
      'summary.overallStatus':'status',
      'runtime.inMaintenanceMode':'maintenance_mode',
      'runtime.connectionState': 'connection_state',
      'runtime.dasHostState.state': 'ha_state'
      }
        
    for x in server._get_object_properties_bulk( hosts.keys(), {'HostSystem' : hostItems.keys()} ) :
      host_id = x.Obj
      host_name = hosts[x.Obj]
      timestamp = int(time.time())

      for i in x.PropSet:
        item_label = hostItems[i.Name]
        item_value = i.Val
        #<hostname> <key> <timestamp> <value>
        print '%s vmware.host.%s[%s] %d %s' % (vcenter_host, item_label, host_id, timestamp, item_value)

      '''
      #DEBUG
      print host_name,
      for i in x.PropSet:
        item_label = hostItems[i.Name]
        item_value = i.Val
        print '%s=%s' % (item_label, item_value),
      print
      '''      
finally:
  server.disconnect()
