#!/usr/bin/env bash
################################################################################

if [ $EUID -ne 0 ]; then
	echo "This script requires root or sudo privileges."
	exit 1
fi

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

for dep in $(cd ${DIR} && ls | grep -v install.sh); do
	if [ -x ${DIR}/${dep}/install.sh ]; then
		${DIR}/${dep}/install.sh
	fi
done
