#!/bin/bash
set -e

echo "=========================================="
echo "MailHarbor container startup"
echo "=========================================="

echo "Creating directories..."
mkdir -p /data/mail /data/fts /data/logs /config/accounts /etc/dovecot

echo "Setting permissions..."
chown -R vmail:vmail /data/mail /data/fts 2>/dev/null || true

echo "Config file check passed"

export PYTHONPATH=/app:$PYTHONPATH

echo "Initializing configs..."
python3 -m src.init_config
if [ $? -ne 0 ]; then
    echo "Error: Config initialization failed"
    exit 1
fi
echo "Config initialization done"

echo "Starting Supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
