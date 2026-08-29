#!/bin/sh
set -eu

if [ "$(id -u)" = "0" ]; then
    install -d -o 10001 -g 10001 -m 0750 /var/lib/afritech
    exec gosu 10001:10001 "$@"
fi

exec "$@"
