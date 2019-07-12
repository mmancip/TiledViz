# $Id: postgres.profile 343914 2009-02-22 17:23:50Z nanardon $
# Olivier Thauvin <nanardon@mandriva.org>

# Default database location
PGDATA=/var/lib/pgsql/data

# Setting up minimal envirronement
[ -f /etc/sysconfig/i18n ] && . /etc/sysconfig/i18n
[ -f /etc/sysconfig/postgresql ] && . /etc/sysconfig/postgresql

export LANG LC_ALL LC_CTYPE LC_COLLATE LC_NUMERIC LC_CTYPE LC_TIME
export PGDATA

PS1="[\u@\h \W]\$ "
