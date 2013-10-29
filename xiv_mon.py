#!/usr/bin/python
# -*- coding: utf-8 -*- # coding: utf-8
#
# XIV monitoring script for Zabbix
#
# 2013 Matvey Marinin
#
# Usage:
#   xiv_mon.py <host> <xiv_mgmt> <username> <pwd> <discovery|data>
#
# - In "discovery" mode returns XIV storage pool discovery data
# - In "data" mode returns disk space usage in Zabbix sender format
#
# Use with "_Special_XIV" Zabbix template
#

import getopt, sys
import time, datetime, calendar
import pywbem

def usage():
  print >> sys.stderr, "Usage: xiv_mon.py <host> <xiv_mgmt> <username> <pwd> <discovery|data>"

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


if mode == 'discovery':
  output = []
  for pool in conn.ExecQuery('WQL', 'SELECT ElementName,InstanceID FROM IBMTSDS_VirtualPool'):
    pool_id = pool.properties['InstanceID'].value
    name = pool.properties['ElementName'].value
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

  total_hard_size = 0
  total_hard_size_left = 0
  
      
  for pool in conn.ExecQuery('WQL', 'SELECT InstanceID,RemainingPhysicalSpace,VirtualSpaceReserved FROM IBMTSDS_VirtualPool'):
    pool_id = pool.properties['InstanceID'].value
    hard_size = pool.properties['VirtualSpaceReserved'].value
    hard_size_left = pool.properties['RemainingPhysicalSpace'].value
    
    if pool_id and hard_size_left and hard_size:
      timestamp = int(time.time())
      total_hard_size += hard_size
      total_hard_size_left += hard_size_left
      
      print '%s xiv.pool.hard_size[%s] %d %s' % (host, pool_id, timestamp, hard_size)
      print '%s xiv.pool.hard_size.left[%s] %d %s' % (host, pool_id, timestamp, hard_size_left)
      
      if hard_size > 0:
        hard_size_pct = 100 - float(hard_size_left)/float(hard_size)*100
        print '%s xiv.pool.hard_size.pct[%s] %d %s' % (host, pool_id, timestamp, hard_size_pct)
  ##end for

  if total_hard_size > 0 and total_hard_size_left > 0:
    total_hard_size_pct = 100 - float(total_hard_size_left)/float(total_hard_size)*100
    print '%s xiv.pool.total_hard_size %d %s' % (host, timestamp, total_hard_size)
    print '%s xiv.pool.total_hard_size_left %d %s' % (host, timestamp, total_hard_size_left)
    print '%s xiv.pool.total_hard_size_pct %d %s' % (host, timestamp, total_hard_size_pct)

