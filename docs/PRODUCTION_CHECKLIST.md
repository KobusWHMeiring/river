# Production Deployment Checklist

## Pre-Deployment Checks

### 1. Environment Configuration
- [ ] Copy `.env.example` to `.env` and fill in production values
- [ ] Set `DEBUG=False`
- [ ] Generate a new `SECRET_KEY` (never use the development key)
- [ ] Configure `ALLOWED_HOSTS` with your domain(s)
- [ ] Set up PostgreSQL database credentials

### 2. Static & Media Files
- [x] `media/` directory added to `.gitignore` ✓
- [x] File upload size limits configured (5MB max) ✓
- [ ] Set up S3 bucket or configure persistent storage for media files
- [ ] Configure CDN (CloudFront/Cloudflare) for media delivery
- [ ] Run `python manage.py collectstatic`

### 3. Database
- [ ] Switch from SQLite to PostgreSQL
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create database backup script
- [ ] Test backup restoration process

### 4. Security Settings (Enable after HTTPS is configured)
- [ ] Uncomment security headers in settings.py:
  - `SECURE_SSL_REDIRECT`
  - `SECURE_HSTS_SECONDS`
  - `SECURE_HSTS_INCLUDE_SUBDOMAINS`
  - `SESSION_COOKIE_SECURE`
  - `CSRF_COOKIE_SECURE`
  - `X_FRAME_OPTIONS`
- [ ] Configure firewall rules
- [ ] Set up fail2ban for brute force protection

### 5. Web Server Configuration
- [ ] Install and configure Nginx
- [ ] Set up SSL certificate (Let's Encrypt)
- [ ] Configure Gunicorn/uWSGI
- [ ] Set up systemd service for Django app
- [ ] Configure Nginx to serve static and media files

### 6. Domain & DNS
- [ ] Point domain A records to server IP
- [ ] Configure www redirect (www → non-www or vice versa)
- [ ] Set up email DNS records (MX, SPF, DKIM, DMARC)

### 7. Monitoring & Logging
- [ ] Set up log rotation (logrotate)
- [ ] Configure error tracking (Sentry recommended)
- [ ] Set up uptime monitoring (UptimeRobot, Pingdom)
- [ ] Configure application performance monitoring

### 8. Backup Strategy
- [ ] Database: Automated daily backups
- [ ] Media files: Sync to S3 or backup storage
- [ ] Test restore procedures
- [ ] Document recovery process

## Quick Production Setup Commands

```bash
# 1. Environment
export DEBUG=False
export SECRET_KEY=$(openssl rand -base64 50)
export ALLOWED_HOSTS=your-domain.com

# 2. Database
python manage.py migrate
python manage.py collectstatic --noinput

# 3. Create superuser (if needed)
python manage.py createsuperuser

# 4. Test production settings
python manage.py check --deploy
```

## Nginx Configuration Template

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    
    # Static files
    location /static/ {
        alias /path/to/project/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /path/to/project/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Post-Deployment Verification

- [ ] Site loads without errors
- [ ] HTTPS working correctly
- [ ] Login/logout functional
- [ ] File uploads working
- [ ] Media files display correctly
- [ ] Admin panel accessible
- [ ] Database queries optimized (check Django Debug Toolbar if enabled)
- [ ] SSL certificate valid and auto-renewing

## Performance Optimization

- [ ] Enable gzip compression in Nginx
- [ ] Configure browser caching headers
- [ ] Set up Redis for caching (optional)
- [ ] Optimize images before upload
- [ ] Enable database connection pooling

## Rollback Plan

Document these steps for quick rollback:
1. Database restore command
2. Previous version deployment
3. DNS rollback procedure
4. Communication plan for users

## Support Contacts

- Hosting provider: ________________
- Domain registrar: ________________
- SSL certificate provider: ________________
- Team members to notify: ________________
