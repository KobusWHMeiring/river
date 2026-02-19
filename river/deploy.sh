#!/bin/bash

# --- CONFIGURATION ---
PROJECT_ROOT="/home/carbonplanner/apps/river"
VENV_ACTIVATE="${PROJECT_ROOT}/venv/bin/activate"
WEB_SERVICE="river_web"
# WORKER_SERVICE="river_worker" # Uncomment this if you add a Celery worker later
GIT_BRANCH="main" 

# Stop script on any error
set -e

echo "🚀 Starting deployment for River App..."

# 1. Navigate to Project Root
cd $PROJECT_ROOT

# 2. Pull latest changes (Clears local server-side edits first)
echo "📥 Clearing local server changes and pulling from Git..."
git checkout -- .
git pull origin $GIT_BRANCH

# 3. Activate Virtual Environment
echo "🐍 Activating virtual environment..."
source $VENV_ACTIVATE

# 4. Install Dependencies
echo "📦 Updating requirements..."
pip install -r requirements.txt

# 5. Run Database Migrations
echo "🗄️ Applying database migrations..."
python manage.py migrate

# 6. Collect Static Files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

# 7. Restart Services
echo "🔄 Restarting Gunicorn (Web)..."
sudo systemctl restart $WEB_SERVICE

# echo "🔄 Restarting Celery (Worker)..."
# sudo systemctl restart $WORKER_SERVICE

# 8. Check Status
echo "---------------------------------------"
if systemctl is-active --quiet $WEB_SERVICE; then
    echo "✅ Deployment Successful!"
    echo "🌍 https://river.plot.org.za"
else
    echo "❌ Service failed to restart. Check logs: sudo journalctl -u $WEB_SERVICE -n 50"
    exit 1
fi