#!/usr/bin/env bash
################################################################################

PYMODULE=bcrypt

PACKAGE_EL6=py-bcrypt-0.3-1.el6.x86_64.rpm
PACKAGE_EL7=py-bcrypt-0.4-4.el7.x86_64.rpm

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

if [ -f /etc/os-release ]; then
	. /etc/os-release
fi

distro_id=${ID,,}
distro_version=${VERSION_ID}

case "$distro_id" in 
	*'centos'* | *'redhat'* | *'rhel'* )
		distro_id='el'
	;;
esac

case "$distro_id:$distro_version" in
	"el:7"* )
		# CentOS/RHEL 7
		echo Installing ${PACKAGE_EL7}
		rpm -ivh ${DIR}/${PACKAGE_EL7}
		;;
	* )
		# Other
		echo Installing ${PACKAGE_EL6}
		rpm -ivh ${DIR}/${PACKAGE_EL6}
		;;
esac
