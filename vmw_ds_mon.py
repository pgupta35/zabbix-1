#!/usr/bin/python
# -*- coding: utf-8 -*- # coding: utf-8
#
# INSTALL:
#  easy_install pysphere (pip pysphere)
#
#

import getopt, sys
import time
from pysphere import VIServer

def usage():
  print >> sys.stderr, "Usage: vmw_mon.py <vcenter> <vc_user> <vc_password> <discovery|data>"

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

  datastores = server.get_datastores()

  if mode == 'discovery':
    output = []
    for mof, name in datastores.items():
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
    #vc-cloud vmware.ds.capacity[datastore-397] 1366194015 1610344300544
    #vc-cloud vmware.ds.free[datastore-397] 1366194015 246725738496
    timestamp = int(time.time())

    def printDS(ds, key, value):
        print '%s vmware.ds.%s[%s] %d %s' % ( vcenter, key, ds, timestamp, value )
    
    for ds in server._get_object_properties_bulk(datastores.keys(), {'Datastore':['summary.capacity', 'summary.freeSpace']} ):
      printDS(ds.Obj, 'capacity', ds.PropSet[0].Val)
      printDS(ds.Obj, 'free', ds.PropSet[1].Val)
finally:
  server.disconnect()
