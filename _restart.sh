#!/bin/bash
# kill old dev server proc
PID=$(ps aux | grep "annahl-ops-web/app.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$PID" ]; then kill "$PID" 2>/dev/null; sleep 2; fi
systemctl --user daemon-reload
systemctl --user restart annahl-ops-web
sleep 4
echo "status: $(systemctl --user is-active annahl-ops-web)"
echo "gunicorn procs: $(ps aux | grep gunicorn | grep -v grep | wc -l)"
echo "listening 8080: $( (ss -ltn 2>/dev/null || netstat -ltn 2>/dev/null) | grep 8080 | wc -l)"
