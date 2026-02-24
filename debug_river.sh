#!/bin/bash
# Debug script for River Django app

echo "=== RIVER APP DEBUG INFO ==="
echo ""

echo "1. Checking if gunicorn is running..."
ps aux | grep "river" | grep gunicorn | grep -v grep
echo ""

echo "2. Recent error logs (last 50 lines):"
tail -50 /var/log/gunicorn/river_error.log 2>/dev/null || echo "No error log found"
echo ""

echo "3. Recent access logs (last 20 lines):"
tail -20 /var/log/gunicorn/river_access.log 2>/dev/null || echo "No access log found"
echo ""

echo "4. Checking Django settings..."
cd /home/carbonplanner/apps/river
source venv/bin/activate
python -c "from river import settings; print(f'DEBUG mode: {settings.DEBUG}'); print(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')" 2>/dev/null || echo "Could not load settings"
echo ""

echo "5. Checking database..."
python -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('Database: OK')" 2>/dev/null || echo "Database: ERROR"
echo ""

echo "6. Checking media uploads directory..."
ls -la /home/carbonplanner/apps/river/media/ 2>/dev/null | head -5 || echo "No media directory"
echo ""

echo "=== END DEBUG INFO ==="
