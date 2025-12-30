#!/bin/bash
# MailHarbor health check script

# Check Dovecot IMAP port
if ! nc -z localhost 143 2>/dev/null; then
    echo "Error: Dovecot IMAP port 143 is not responding"
    exit 1
fi

# Check Dovecot process
if ! pgrep -x "dovecot" > /dev/null; then
    echo "Error: Dovecot process is not running"
    exit 1
fi

# Check Fetchmail process
if ! pgrep -x "fetchmail" > /dev/null; then
    echo "Error: Fetchmail process is not running"
    exit 1
fi

# All checks passed
exit 0
