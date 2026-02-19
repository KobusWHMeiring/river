# river Deployment Guide

This guide walks you through setting up **river** on your production server.

**Generated for:** river@plot.org  
**App Location:** /home/carbonplanner/apps/river  
**Django Project:** river

---

## Step 1: DNS Configuration (The Domain)

Before doing anything on the server, go to your domain provider.

1. **Add a new A Record**
2. **Host/Name:** `river@plot` (or your subdomain)
3. **Value/Target:** Your server's IP address (e.g., 169.239.182.221)
4. **TTL:** 300 (5 minutes)
5. Save and wait (usually takes 5-10 minutes to propagate)

**Verify DNS:**
```bash
# From your local machine, test if DNS is resolving
ping river@plot.org
# or
dig river@plot.org
```

---

## Step 2: Database Setup (PostgreSQL)

You need a dedicated database for this application.

**Option A: Automatic (using generated script)**
```bash
# Copy the generated SQL file to your server
scp psql_setup.sql carbonplanner@your-server:~/river/

# On the server, run it
sudo -u postgres psql -f ~/river/psql_setup.sql
```

**Option B: Manual Setup**
```bash
sudo -u postgres psql
```

Then run these SQL commands:
```sql
-- 1. Create DB and User
CREATE DATABASE river_db;
CREATE USER river_user WITH PASSWORD '63Fkxo4JorzkIhS2';
GRANT ALL PRIVILEGES ON DATABASE river_db TO river_user;

-- 2. Move INTO the new database (CRITICAL STEP)
\c river_db

-- 3. Grant the internal permissions
GRANT ALL ON SCHEMA public TO river_user;
ALTER DATABASE river_db OWNER TO river_user;

-- 4. Exit
\q
```

---

## Step 3: Application Setup

### 3.1 Create Directory & Clone Code
```bash
mkdir -p /home/carbonplanner/apps/river
cd /home/carbonplanner/apps/river

# Clone your repository
git clone https://github.com/yourusername/river.git .

# Or if you already have the code elsewhere, copy it
cp -r /path/to/your/code/* /home/carbonplanner/apps/river/
```

### 3.2 Setup Python Virtual Environment
```bash
cd /home/carbonplanner/apps/river
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production server dependencies
pip install gunicorn psycopg2-binary
```

### 3.3 Create Environment File
```bash
cd /home/carbonplanner/apps/river
cp .env.example .env
nano .env
```

**Paste this (already customized for your app):**
```
DEBUG=False
SECRET_KEY=MIMW7WW2nctBku96ivK24jCwMDZXohfj4HhmywlCMeMJFTwYyR
ALLOWED_HOSTS=river@plot.org,localhost,127.0.0.1

# Database
DB_NAME=river_db
DB_USER=river_user
DB_PASSWORD=63Fkxo4JorzkIhS2
DB_HOST=localhost
DB_PORT=5432

# Static/Media
STATIC_ROOT=/home/carbonplanner/apps/river/staticfiles
MEDIA_ROOT=/home/carbonplanner/apps/river/media

# Timezone
TIME_ZONE=Africa/Johannesburg
LANGUAGE_CODE=en-us
```



### 3.4 Run Django Migrations & Collect Static
```bash
cd /home/carbonplanner/apps/river
source venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (optional)
python manage.py createsuperuser
```

---

## Step 4: Web Service (Gunicorn)

The web service runs your Django application.

```bash
sudo nano /etc/systemd/system/river_web.service
```

**Paste the content from:** `river/river_web.service`

**Enable and start the service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable river_web
sudo systemctl start river_web
```

**Check status:**
```bash
sudo systemctl status river_web
```

---



## Step 5: Nginx Setup (HTTP First)

**Important:** Start with HTTP only, then add HTTPS after!

### Initial HTTP Configuration
```bash
sudo nano /etc/nginx/sites-available/river
```

**Use this temporary HTTP config:**
```nginx
server {
    listen 80;
    server_name river@plot.org;

    # Certbot challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Static files
    location /static/ {
        alias /home/carbonplanner/apps/river/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/carbonplanner/apps/river/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Django app
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/carbonplanner/apps/river/river.sock;
    }

    client_max_body_size 10M;
}
```

**Enable the site:**
```bash
# Create symlink
sudo ln -s /etc/nginx/sites-available/river /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 6: SSL Certificate (HTTPS)

Now that HTTP is working, add HTTPS with Let's Encrypt.

### Install Certbot (if not already)
```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Get Certificate
```bash
sudo certbot --nginx -d river@plot.org
```

**Follow the prompts:**
1. Enter your email (for renewal notices)
2. Agree to terms
3. Choose whether to redirect HTTP to HTTPS (Yes, recommended!)

**Certbot will automatically:**
- Create SSL certificates
- Update your Nginx config with HTTPS
- Set up automatic renewal

### Verify HTTPS
```bash
# Test the site
https://river@plot.org

# Check SSL certificate (from your local machine)
openssl s_client -connect river@plot.org:443 -servername river@plot.org
```

---

## Step 7: Verify & Test

### Check All Services
```bash
# Web service
sudo systemctl status river_web

# Nginx
sudo systemctl status nginx

# Check logs
sudo journalctl -u river_web -n 50 --no-pager
```

### Test Application
```bash
# Test locally on server
curl http://localhost:80

# Test from outside (should redirect to HTTPS)
curl -I http://river@plot.org
```

### Create Test Data
```bash
cd /home/carbonplanner/apps/river
source venv/bin/activate

# Create a test user
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='test').exists():
    User.objects.create_superuser('test', 'test@example.com', 'testpass123')
    print('Test user created')
else:
    print('Test user already exists')
"
```

---

## Common Issues & Solutions

### 1. Permission Denied Errors
```bash
# Fix permissions
sudo chown -R carbonplanner:www-data /home/carbonplanner/apps/river
sudo chmod -R 755 /home/carbonplanner/apps/river

# For media uploads
sudo chown -R carbonplanner:www-data /home/carbonplanner/apps/river/media
sudo chmod -R 775 /home/carbonplanner/apps/river/media
```

### 2. Static Files Not Loading
```bash
# Re-collect static files
cd /home/carbonplanner/apps/river
source venv/bin/activate
python manage.py collectstatic --noinput --clear

# Restart services
sudo systemctl restart river_web
sudo systemctl restart nginx
```

### 3. Database Connection Errors
```bash
# Test database connection
sudo -u postgres psql -d river_db -c "SELECT 1;"

# Check if user has permissions
sudo -u postgres psql -c "\du"
```

### 4. 502 Bad Gateway
```bash
# Check if Gunicorn is running
sudo systemctl status river_web

# Check logs
sudo journalctl -u river_web -f

# Check socket file exists
ls -la /home/carbonplanner/apps/river/river.sock
```

### 5. SSL Certificate Issues
```bash
# Test renewal
certbot renew --dry-run

# Force renewal if needed
certbot renew --force-renewal

# Check certificate status
openssl x509 -in /etc/letsencrypt/live/river@plot.org/fullchain.pem -noout -text
```

---

## Maintenance Commands

### View Logs
```bash
# Web server logs
sudo journalctl -u river_web -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services
```bash
# Restart web service
sudo systemctl restart river_web


# Restart Nginx
sudo systemctl restart nginx

# Restart all
sudo systemctl restart river_web nginx
```

### Update Application
```bash
cd /home/carbonplanner/apps/river

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart river_web
```

---

## Deployment & Environment Checklist

Before declaring the deployment a success, verify these items:

### 1. Environment Verification (.env loading)
- [ ] **Verify `django-environ` installation**: Ensure `django-environ` is in `requirements.txt`.
- [ ] **Verify `.env` placement**: The `.env` file must be in the same directory as `manage.py` (your `BASE_DIR`).
- [ ] **Check `DATABASE_URL`**: Ensure the `.env` file contains a valid `DATABASE_URL` (e.g., `postgres://user:pass@localhost:5432/db_name`).
- [ ] **Verify Settings consistency**: Ensure `settings.py` uses `env.db()` for the `DATABASES` setting.

### 2. Service Verification
- [ ] **Check Gunicorn Logs**: `sudo journalctl -u river_web -f` - ensure no "Database connection" errors on startup.
- [ ] **Check Nginx Syntax**: `sudo nginx -t` - ensure no server name conflicts.
- [ ] **Verify Static Files**: Visit `https://river@plot.org/static/admin/css/base.css` to ensure static files are served.

---

## Security Checklist

- [ ] Change default admin password
- [ ] Set strong SECRET_KEY in .env
- [ ] Disable DEBUG mode (DEBUG=False)
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Set up firewall (ufw/iptables)
- [ ] Enable automatic security updates
- [ ] Set up fail2ban
- [ ] Configure log rotation
- [ ] Set up database backups
- [ ] Enable SSL (HTTPS)
- [ ] Set up monitoring/alerting

---

## Quick Reference

| Task | Command |
|------|---------|
| Check web service | `sudo systemctl status river_web` |
| View web logs | `sudo journalctl -u river_web -f` |
| Restart web | `sudo systemctl restart river_web` |
| Test Nginx config | `sudo nginx -t` |
| Restart Nginx | `sudo systemctl restart nginx` |
| Database shell | `sudo -u postgres psql river_db` |
| Django shell | `cd /home/carbonplanner/apps/river && source venv/bin/activate && python manage.py shell` |
| Backup database | `pg_dump river_db > backup.sql` |
| Restore database | `sudo -u postgres psql river_db < backup.sql` |

---

**Generated:** 80cf23c70ed958d7  
**App:** river  
**Domain:** river@plot.org  
**Database:** river_db / river_user

For support, check the documentation in `docs/` folder.
