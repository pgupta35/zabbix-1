#!/usr/bin/python
# -*- coding: utf-8 -*- # coding: utf-8
#
# XIV monitoring script for Zabbix
#
# 2014 Matvey Marinin
#
# Usage:
#   xiv_mon.py <host> <xiv_mgmt> <username> <pwd> <discovery|snap_discovery|data>
#
# "discovery" - XIV volume pool discovery data
# "snap_discovery" - XIV snapshot pool discovery data
# "data" - pool disk space usage in Zabbix sender format
#
# Use with "_Special_XIV" Zabbix template
#

import getopt, sys
import time, datetime, calendar
import pywbem

def usage():
  print >> sys.stderr, "Usage: xiv_mon.py <host> <xiv_mgmt> <username> <pwd> <discovery|snap_discovery|data>"

#print sys.argv

if len(sys.argv) != 6:
  print >> sys.stderr, 'ERROR: wrong args'
  usage()
  sys.exit(2)

host = sys.argv[1]
xiv_mgmt = sys.argv[2]
user = sys.argv[3]
password = sys.argv[4]
mode = sys.argv[5]

# Make connection
conn = pywbem.WBEMConnection('https://'+xiv_mgmt, (user, password), 'root/ibm') 
conn.debug = True


if mode in ('discovery', 'snap_discovery'):
  if mode == 'discovery':
    cim_query = "SELECT ElementName,InstanceID FROM CIM_StoragePool WHERE Usage = 2 AND Primordial = FALSE"
  else:
    cim_query = "SELECT ElementName,InstanceID FROM CIM_StoragePool WHERE Usage = 4 AND Primordial = FALSE"

  output = []
  for pool in conn.ExecQuery('WQL', cim_query):
    pool_id = pool.properties['InstanceID'].value
    name = pool.properties['ElementName'].value

    ## Trim snapshot pool name: "Snapshot pool of storage pool other-servers-pool" -> "other-servers-pool"
    if mode == 'snap_discovery':
      name = name.rsplit(None, 1)[-1]
    
    if name and pool_id:
      output.append( '{"{#ID}":"%s", "{#NAME}":"%s"}' % (pool_id, name) )

  print '{ "data":['
  for i, v in enumerate( output ):
    if i < len(output)-1:
      print v+','
    else:
      print v
  print ' ]}'


if mode == 'data':
  #<host> <key> <timestamp> <value>
  #xiv1 xiv.pool.hard_size[xxx] 1373876039 115002271858688
  #xiv1 xiv.pool.hard_size.left[xxx] 1373876039 76903359709184
  #xiv1 xiv.pool.hard_size.pctleft[xxx] 1373876039 56.1000
  #xiv1 xiv.pool.snap.space_left[yyy] 1373876039 1772442615808
  #xiv1 xiv.pool.snap.space_pctleft[yyy] 1373876039 68.0000

  total_hard_size = 0
  total_hard_size_left = 0
  
  ## Volume pool ##
  for pool in conn.ExecQuery('WQL', 'SELECT InstanceID, RemainingPhysicalSpace, VirtualSpaceReserved FROM CIM_StoragePool WHERE Usage = 2 AND Primordial = FALSE'):
    pool_id = pool.properties['InstanceID'].value
    hard_size = pool.properties['VirtualSpaceReserved'].value
    hard_size_left = pool.properties['RemainingPhysicalSpace'].value
    
    if pool_id and hard_size_left is not None and hard_size: #hard_size_left can be 0, hard_size_pct != 0
      timestamp = int(time.time())
      total_hard_size += hard_size
      total_hard_size_left += hard_size_left
      hard_size_pct = 100 - float(hard_size_left)/float(hard_size)*100
      print '%s xiv.pool.hard_size[%s] %d %s' % (host, pool_id, timestamp, hard_size)
      print '%s xiv.pool.hard_size.left[%s] %d %s' % (host, pool_id, timestamp, hard_size_left)
      print '%s xiv.pool.hard_size.pct[%s] %d %s' % (host, pool_id, timestamp, hard_size_pct)
  ##end for
        
  if total_hard_size > 0 and total_hard_size_left > 0:
    total_hard_size_pct = 100 - float(total_hard_size_left)/float(total_hard_size)*100
    print '%s xiv.pool.total_hard_size %d %s' % (host, timestamp, total_hard_size)
    print '%s xiv.pool.total_hard_size_left %d %s' % (host, timestamp, total_hard_size_left)
    print '%s xiv.pool.total_hard_size_pct %d %s' % (host, timestamp, total_hard_size_pct)

  ## Snapshot pool ##
  for pool in conn.ExecQuery('WQL', 'SELECT InstanceID, RemainingManagedSpace, TotalManagedSpace FROM CIM_StoragePool WHERE Usage = 4 AND Primordial = FALSE'):
    pool_id = pool.properties['InstanceID'].value
    snap_remaining_space = pool.properties['RemainingManagedSpace'].value
    snap_total_size = pool.properties['TotalManagedSpace'].value
    if pool_id and snap_remaining_space is not None and snap_total_size: #snap_remaining_space can be 0, snap_total_size != 0
      timestamp = int(time.time())
      snapshot_pctleft = float(snap_remaining_space)/float(snap_total_size)*100
      print '%s xiv.pool.snap.space_left[%s] %d %s' % (host, pool_id, timestamp, snap_remaining_space)
      print '%s xiv.pool.snap.space_pctleft[%s] %d %s' % (host, pool_id, timestamp, snapshot_pctleft)
  ##end for

