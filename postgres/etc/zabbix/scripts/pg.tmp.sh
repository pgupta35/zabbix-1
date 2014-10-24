#!/bin/bash
###   Managed by Spacewalk, don't edit   ###
# pg_stat_tmp error monitoring
# Counts "No space left" errors in the last PostgreSQL log
# Zabbix template: _Special_PostgreSQL
# Matvey Marinin 2014
#
grep -Fcs 'No space left on device' "$(find /var/lib/pgsql/9.1/data/pg_log -maxdepth 1 -name '*.log'|sort -V|tail -n1)" 2>/dev/null
