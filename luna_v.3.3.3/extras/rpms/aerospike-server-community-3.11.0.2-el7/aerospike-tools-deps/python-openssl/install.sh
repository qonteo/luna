#!/usr/bin/env bash
################################################################################

PYMODULE=OpenSSL
PIPMODULE=pyOpenSSL
PACKAGE=pyOpenSSL
# centos6 pyOpenSSL.x86_64 0:0.13.1-2.el6
# centos7 pyOpenSSL.x86_64 0:0.13.1-3.el7
# debian7 python-openssl_0.13-2+deb7u1_amd64.deb

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
    * )
        echo Installing ${PACKAGE}
        yum install -y ${PACKAGE}
        ;;
esac
