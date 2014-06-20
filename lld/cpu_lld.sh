#!/bin/bash
# 
# Zabbix CPU discovery script
# Returns JSON discovery data for use with low-level discovery item (https://www.zabbix.com/documentation/2.0/manual/discovery/low_level_discovery)
#
# Matvey Marinin 2013
#
# USAGE:
#   cpu_lld.sh {local|<remote server name>}
#
# Local usage: ./cpu_lld.sh local
# Usage with remote zabbix agent: ./cpu_lld.sh lms2-db
#

if [[ $1 == 'local' ]]; then
  CPU_NUM=$(nproc);
else
  CPU_NUM=$(zabbix_get -s "$1" -p 10050 -k system.cpu.num)
fi

OUTPUT='{"data":[ '

if [[ -n "$CPU_NUM"  ]]; then
  for (( i=0; i<$CPU_NUM; i++ ))
  do
    OUTPUT=${OUTPUT}'{"{#CPU}":"'$i'"}'
    if (( i<$CPU_NUM-1 )); then
      OUTPUT="${OUTPUT}, "
    fi
  done
fi

OUTPUT="${OUTPUT} ]}"
echo "$OUTPUT"

