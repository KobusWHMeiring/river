 Handover: Production-Ready Configuration for "River"
1. The Context
The server is an Ubuntu 24.04 environment hosting multiple Django applications. We use Nginx as a reverse proxy, Gunicorn as the application server, and PostgreSQL as the database.
Current Issue: The application is currently failing on the server because the settings.py is not correctly loading environment variables from the .env file, causing a mismatch where the terminal migrates to SQLite while the web server looks at an empty PostgreSQL database.
2. Required settings.py Standardizations
Please refactor the local settings.py to use django-environ with absolute pathing. This ensures the app works regardless of how the process is started (Gunicorn vs. Terminal).
A. Environment Initialization
Replace the existing environment loading logic with this robust pattern:
code
Python
import os
import environ
from pathlib import Path

# 1. Setup Pathing
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Initialize Environ
env = environ.Env(
    DEBUG=(bool, False)
)

# 3. Force absolute path to .env file (points to project root)
env_file = BASE_DIR / ".env"
if os.path.exists(env_file):
    environ.Env.read_env(env_file)
B. Database Configuration
The server uses a single DATABASE_URL string. Update your DATABASES setting to use the env.db() helper:
code
Python
# Replace the manual dictionary with this:
DATABASES = {
    'default': env.db(),
}
C. Static & Media (Production Pathing)
Ensure these match the server’s Nginx configuration:
code
Python
# Django will collect files here; Nginx serves them from here
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
D. Security Settings (Required for HTTPS)
Because the server uses SSL, the following must be set to allow logins to function:
code
Python
DEBUG = env.bool('DEBUG', default=False)
SECRET_KEY = env('SECRET_KEY')

# Use manual split for Allowed Hosts
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default='').split(',')

# CRITICAL for Django 4.0+ to allow login via HTTPS
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS if '.' in host]
3. Environment File Requirements (.env)
The developer should provide an .env.example in the repo. On the server, the .env file will look like this (ensure no spaces around =):
code
Ini
DEBUG=False
SECRET_KEY=your-random-secret-key
ALLOWED_HOSTS=river.plot.org.za,localhost,127.0.0.1
DATABASE_URL=postgres://river_user:password@localhost:5432/river_db
# If Celery is enabled:
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/2
4. Why these changes matter
Absolute Paths: Gunicorn starts in the river app root, but migrations might be run from different subfolders. Using BASE_DIR / ".env" prevents the "Database Not Found" errors.
env.db() vs os.environ: os.environ only sees system-level variables. django-environ reads the file directly, which is necessary since we aren't using global environment variables to avoid clashing with other apps on the server.
CSRF Origins: Without this, the admin panel will return a 500 or 403 error upon login because the site is behind an Nginx SSL proxy.