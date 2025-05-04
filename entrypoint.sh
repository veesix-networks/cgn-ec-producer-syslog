#!/bin/sh
set -e

/opt/venv/bin/python3 /app/render_config.py

echo "🚀 Starting cgn-ec-syslog-producer"
/usr/sbin/syslog-ng -f /etc/cgn_ec/rendered.conf -F