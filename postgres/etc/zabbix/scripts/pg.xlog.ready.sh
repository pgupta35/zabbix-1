#!/bin/bash
###   Managed by Spacewalk, don't edit   ###
# Postgres xlog monitoring: counts ready-for-archiving xlog files
# Zabbix template: _Special_PostgreSQL
#
# Matvey Marinin 2014
#

# Чтобы предотвратить ложно-положительные результаты при проблемах с правами (с неправильным sudoers find не может вывести список файлов, т.к. права на них только у postgres),
# проверяется статус команды find, в случае ошибки данные в Zabbix не возвращаются.
set -o pipefail
if RESULT=$(find /var/lib/pgsql/9.1/data/pg_xlog/archive_status -maxdepth 1 -iname "*.ready" 2>/dev/null | wc -l); then echo "$RESULT"; fi
