#!/bin/sh
if [[ ! $1 || ! $2 || ! $3 ]]; then exit 1; fi
declare -i WORKERS=$1
declare -i THREADS=$2
declare -i VERBOSE=$3
WORKDIR=/var/lib/luna/current

for i in $(seq 1 $WORKERS)
do
 $WORKDIR/bin/luna-matcher --log-to-stderr --config-path $WORKDIR/conf/matcher.conf --num-threads $THREADS --log-verbosity $VERBOSE &
done

