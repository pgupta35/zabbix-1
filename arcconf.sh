#!/bin/bash
#
# arcconf.sh - Zabbix script for Adaptec RAID controller monitoring on VMWare ESXi hosts
#
# Matvey Marinin 2013
#

##Stop proceeding on arcconf errors
set -e

if [ $# -ne 2 ]
then
  echo "Usage: `basename $0` <ESXi host> <#CTRL>"
  exit 1
fi

ERR_LOG=/var/cache/zabbix/arcconf.log

##include config file with ESXi credentials ($ESX_HOST, $ESX_PWD)
. $(dirname $0)/arcconf.conf

ESX_HOST=$1
CTRL_NUM=$2

AD_OUTPUT=$( python $(dirname $0)/arcconf.py --host "$ESX_HOST" --user "$ESX_USER" --password "$ESX_PWD" getconfig "$CTRL_NUM" AD 2>>"$ERR_LOG" )
AD_STATUS=$( echo "$AD_OUTPUT" | awk --field-separator ":" '$1 ~ /Controller Status/ && $2 !~ /Optimal/ { print gensub(/^ +/,"","g",$2) }' )
if [ -n "$AD_STATUS" ] ; then
   AD_STATUS="AD: ${AD_STATUS}"
fi

LD_OUTPUT=$( python $(dirname $0)/arcconf.py --host "$ESX_HOST" --user "$ESX_USER" --password "$ESX_PWD" getconfig "$CTRL_NUM" LD 2>>"$ERR_LOG" )

LD_ERRORS=$( echo "$LD_OUTPUT" | awk '
 BEGIN {FS=":"}
 $1 ~ /Logical device number/ { split($1, a, / /); ld=a[4]; }
 $1 ~ /Status of logical device/ && $2 !~ /Optimal/ { print "LD" ld ":" gensub(/^ +/,"","g",$2) }
' )

##collapse multiple lines to one
LD_ERRORS=$(echo "$LD_ERRORS")

LD_FAILEDSTRIPES=$( echo "$LD_OUTPUT" | awk '
 BEGIN {FS=":"}
 $1 ~ /Logical device number/ { split($1, a, / /); ld=a[4]; }
 $1 ~ /Failed stripes/ && $2 !~ /No/ { print "LD" ld ":failed stripes" }
' )

##collapse multiple lines to one
LD_FAILEDSTRIPES=$(echo "$LD_FAILEDSTRIPES") 


PD_OUTPUT=$( python $(dirname $0)/arcconf.py --host "$ESX_HOST" --user "$ESX_USER" --password "$ESX_PWD" getconfig "$CTRL_NUM" PD 2>>"$ERR_LOG" )

PD_ERRORS=$( echo "$PD_OUTPUT" | awk '
 BEGIN {FS=":"}
 $1 ~ /Device #/ { split( gensub(/^ +/,"","g",$1), a, / /); pd=substr(a[2],2); }
 gensub(/^ +/,"","g",$1) ~ /^State/ && $2 !~ /Online/ { print "PD" pd ":" gensub(/^ +/,"","g",$2) }
' )

##collapse multiple lines to one
PD_ERRORS=$(echo "$PD_ERRORS")

RESULT="RAID OK"

#echo AD_STATUS="$AD_STATUS"
#echo LD_ERRORS="$LD_ERRORS"
#echo PD_ERRORS="$PD_ERRORS"
#echo LD_FAILEDSTRIPES="$LD_FAILEDSTRIPES"

## Critical errors
if [ -n "$AD_STATUS" ] || [ -n "$LD_ERRORS" ] || [ -n "$PD_ERRORS" ] ; then
  RESULT="RAID CRITICAL: ${AD_STATUS} ${LD_ERRORS} ${PD_ERRORS}"
fi

## Warnings
if [ -n "$LD_FAILEDSTRIPES" ] ; then
  if [ -n "$RESULT"  ] ;then
    RESULT="${RESULT} "
  fi
  RESULT="RAID WARNING: ${LD_FAILEDSTRIPES} "
fi

echo ${RESULT}