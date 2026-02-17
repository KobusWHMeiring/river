#!/bin/bash

# River Application Deployment Script
# Run this on your production server after DNS is configured

set -e  # Exit on any error

echo "=== River Production Deployment Script ==="
echo ""

# Configuration
APP_USER="carbonplanner"
APP_DIR="/home/carbonplanner/apps/river"
DOMAIN="market.plot.org.za"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting deployment..."

# 1. Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# 2. Install dependencies
print_status "Installing dependencies..."
apt install -y python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib certbot python3-certbot-nginx

# 3. Create log directories
print_status "Creating log directories..."
mkdir -p /var/log/gunicorn
chown -R $APP_USER:$APP_USER /var/log/gunicorn

# 4. Setup PostgreSQL (if not already done)
print_status "Setting up PostgreSQL..."
sudo -u postgres psql -f psql_setup.sql || print_warning "Database may already exist"

# 5. Setup application directory
print_status "Setting up application directory..."
mkdir -p $APP_DIR
chown -R $APP_USER:$APP_USER $APP_DIR
mkdir -p $APP_DIR/media
mkdir -p $APP_DIR/staticfiles

# 6. Setup Python virtual environment
print_status "Setting up Python virtual environment..."
cd $APP_DIR
if [ ! -d "venv" ]; then
    sudo -u $APP_USER python3 -m venv venv
fi

# 7. Install Python dependencies
print_status "Installing Python dependencies..."
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt || print_warning "requirements.txt not found, skipping"

# 8. Setup environment file
if [ ! -f "$APP_DIR/.env" ]; then
    print_warning ".env file not found! Copying from .env.example..."
    cp $APP_DIR/.env.example $APP_DIR/.env
    print_error "Please edit $APP_DIR/.env with your production values before continuing!"
    exit 1
fi

# 9. Run Django management commands
print_status "Running Django migrations..."
cd $APP_DIR
export $(grep -v '^#' .env | xargs)
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py migrate

print_status "Collecting static files..."
sudo -u $APP_USER $APP_DIR/venv/bin/python manage.py collectstatic --noinput

# 10. Setup systemd service
print_status "Setting up systemd service..."
cp $APP_DIR/river/river_web.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable river_web

# 11. Setup Nginx
print_status "Setting up Nginx..."
cp $APP_DIR/river/nginx_config /etc/nginx/sites-available/river
ln -sf /etc/nginx/sites-available/river /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t || exit 1

# 12. Start/restart services
print_status "Starting services..."
systemctl restart river_web
systemctl restart nginx

# 13. Setup SSL with Certbot
print_status "Setting up SSL certificate..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || print_warning "SSL setup may require manual intervention"

# 14. Final status check
print_status "Checking service status..."
systemctl status river_web --no-pager || true
systemctl status nginx --no-pager || true

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Your application should be accessible at:"
echo "  - http://$DOMAIN (redirects to HTTPS)"
echo "  - https://$DOMAIN"
echo ""
echo "Useful commands:"
echo "  - View logs: sudo journalctl -u river_web -f"
echo "  - Restart app: sudo systemctl restart river_web"
echo "  - Check status: sudo systemctl status river_web"
echo ""
