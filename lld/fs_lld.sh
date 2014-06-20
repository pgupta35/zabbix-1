#!/bin/bash
###   Managed by Spacewalk, don't edit   ###
#
# Filesystem low-level discovery script for Zabbix.
# Lists filesystems visible by df command
# Zabbix user needs permission to 'sudo /bin/df'
# Matvey Marinin 2013
#
# Zabbix template: _Basic_Linux_Filesystems_LLD

FILESYSTEMS=$(sudo df -P 2> /dev/null | tail -n +2 | awk '{if ($6 !~ /^\/dev/) print $6}' | uniq)

OUTPUT='{"data":[ '
FIRST=1

for f in $FILESYSTEMS; do
    if ((FIRST)); then FIRST=0; else OUTPUT="${OUTPUT}, "; fi
    OUTPUT=${OUTPUT}'{"{#FSNAME}":"'$f'"}'
done

OUTPUT="${OUTPUT} ]}"
echo "$OUTPUT"
