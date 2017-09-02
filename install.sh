#!/bin/bash

set -xe
set -o pipefail

bindir=~/bin
unitdir=~/.config/systemd/user
configdir=~/.rsync-backup

# install the binary
pip install --user -U -r requirements.txt
install -d "${bindir}"
install -T -m 755 rsync-backup.py "${bindir}/rsync-backup"

# install the config dir
install -d "${rsync-backup}"

# install the service file
install -d "${unitdir}"
install -m 644 rsync-backup-check.service "${unitdir}"
install -m 644 rsync-backup-check.timer "${unitdir}"

# enable the timer and reload
systemctl --user daemon-reload
systemctl --user enable rsync-backup-check.timer
