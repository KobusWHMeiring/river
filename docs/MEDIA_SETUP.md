# Media Files Handling - Development vs Production

## Current Issue
Photos are uploading successfully but returning 404 when trying to view them.

## Development Setup (Current)

The media serving is configured in `river/urls.py`:
```python
+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Important:** This only works when `DEBUG=True`.

### To Fix in Development:

1. **Ensure DEBUG is enabled:**
   Set environment variable or update settings:
   ```bash
   export DEBUG=True
   ```

2. **Verify media directory exists:**
   ```bash
   mkdir -p media/photos
   ```

3. **Check file permissions:**
   Ensure the web server process has write access to the `media/` directory.

## Production Setup (IMPORTANT)

**DO NOT serve media files through Django in production!**

### Option 1: Nginx (Recommended)

```nginx
# In your Nginx server block
location /media/ {
    alias /path/to/your/project/media/;
}

location /static/ {
    alias /path/to/your/project/static/;
}
```

### Option 2: Whitenoise (for static files only)

For media files in production, use a proper file server or cloud storage.

### Option 3: Cloud Storage (Best for Production)

Use AWS S3, Google Cloud Storage, or Azure Blob Storage:

1. Install django-storages:
   ```bash
   pip install django-storages[boto3]
   ```

2. Update settings:
   ```python
   DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
   AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
   AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
   AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
   AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
   MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
   ```

3. Remove the static() from urls.py in production

## Current Configuration

**Settings:**
- `MEDIA_URL = '/media/'`
- `MEDIA_ROOT = BASE_DIR / 'media'`

**URL Configuration:**
```python
# river/urls.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your urls
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Immediate Fix for Development

Run these commands:
```bash
# 1. Set DEBUG mode
export DEBUG=True

# 2. Create media directory
mkdir -p media/photos

# 3. Restart Django server
python manage.py runserver
```

## Production Checklist

Before deploying to production:

- [ ] Set `DEBUG=False`
- [ ] Remove `+ static()` from urls.py OR configure proper media serving
- [ ] Set up Nginx/Apache to serve media files
- [ ] OR configure cloud storage (S3, GCS, Azure)
- [ ] Ensure `MEDIA_ROOT` is outside version control (add to .gitignore)
- [ ] Set up backup strategy for uploaded files
- [ ] Configure proper file size limits
- [ ] Set up virus scanning for uploads (optional but recommended)

## Environment Variables for Production

```bash
# Required
DEBUG=False
SECRET_KEY=your-secret-key-here

# For cloud storage (if using)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...

# Or for local media storage with Nginx
# Ensure MEDIA_ROOT points to a persistent volume
```

## Testing Media Uploads

After setup, test with:
1. Upload a photo through the visit log form
2. Check it appears in `media/photos/YYYY/MM/DD/`
3. Access via browser: `http://localhost:8000/media/photos/YYYY/MM/DD/filename.jpg`

## File Naming

Django automatically handles filename collisions by appending random characters (e.g., `filename_XYaWaPG.jpg`).

## Security Considerations

1. **Never expose MEDIA_ROOT directly** - always serve through URL
2. **Validate file types** - currently accepting any image/*
3. **Limit file sizes** - add MAX_UPLOAD_SIZE setting
4. **Scan for malware** - consider django-clamav or similar
5. **Use HTTPS** for media URLs in production
6. **Set proper CORS headers** if media served from different domain

## Recommended Production Architecture

```
Internet
    |
    v
CDN (CloudFront/Cloudflare)  <- Cache media files
    |
    v
Nginx/Apache                 <- Serve static/media
    |
    v
Django Application           <- Handle uploads, generate URLs
    |
    v
S3/Cloud Storage             <- Store actual files
```
