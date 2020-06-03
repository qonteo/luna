#!/bin/sh
if [[ ! $1 || ! $2 ]]; then exit 1; fi
declare -i WORKERS=$1
declare -i VERBOSE=$2
WORKDIR=/var/lib/luna/current

for i in $(seq 1 $WORKERS)
do
 $WORKDIR/bin/luna-extractor --log-to-stderr --config-path $WORKDIR/conf/extractor.conf --log-verbosity $VERBOSE &
done

