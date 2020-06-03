#!/usr/bin/bash

#Preliminary implementation of script which performs ssh-key generation for matcher-daemon and config tuning.
#Feel free to modify

yes | sudo ssh-keygen -b 2048 -t  rsa -f /etc/matcher-daemon/id_rsa  -q -N "" > /dev/null
chown matcher-daemon /etc/matcher-daemon/id_rsa*
su -c 'mkdir -p  ~/.ssh' matcher-daemon
su -c 'ssh-keyscan -H  localhost  >> ~/.ssh/known_hosts' matcher-daemon
su -c 'cat /etc/matcher-daemon/id_rsa.pub >> ~/.ssh/authorized_keys' matcher-daemon

MatcherConfig=/etc/matcher-daemon/matcher-daemon-config.json

sed -i -e 's|"indexer_host.*|"indexer_host": "localhost"\,|g' $MatcherConfig
sed -i -e 's|"index_holding_dir.*|"index_holding_dir": "/var/lib/luna/index"\,|g' $MatcherConfig
sed -i -e 's|"ssh_key.*|"ssh_key": "/etc/matcher-daemon/id_rsa"\,|g' $MatcherConfig
