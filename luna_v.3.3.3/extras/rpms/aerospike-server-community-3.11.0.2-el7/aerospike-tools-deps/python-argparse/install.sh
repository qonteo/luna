#!/usr/bin/env bash
################################################################################

PYMODULE=argparse

PACKAGE=python-argparse-1.2.1-2.el6.noarch.rpm

################################################################################

if [ $EUID -ne 0 ]; then
	echo "This script requires root or sudo privileges."
	exit 1
fi

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

python <<EOF
try:
	import ${PYMODULE}
	import sys
	sys.exit(0)
except Exception as e:
	import sys
	sys.exit(1)
EOF
has_pymodule=$?

if [ $has_pymodule -eq 0 ]; then
	exit 0
fi

echo Installing ${PACKAGE}
rpm -ivh ${DIR}/${PACKAGE}
