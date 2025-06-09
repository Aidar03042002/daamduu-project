# Daamduu Deployment Guide

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Nginx
- Gunicorn
- Virtual Environment

## Environment Setup

1. Create a `.env` file in the project root with the following variables:
```env
# Django settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=daamduu.settings_prod

# Database settings
DB_NAME=daamduu
DB_USER=daamduu_user
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Stripe settings
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret

# Redis settings
REDIS_URL=redis://localhost:6379/1

# AWS settings (if using S3 for static/media files)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=your-region
```

## Installation Steps

1. Clone the repository:
```bash
git clone https://github.com/your-username/daamduu.git
cd daamduu
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
python manage.py collectstatic
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

## Nginx Configuration

Create a new Nginx configuration file at `/etc/nginx/sites-available/daamduu`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /path/to/daamduu;
    }

    location /media/ {
        root /path/to/daamduu;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn.sock;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/daamduu /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## Gunicorn Service

Create a systemd service file at `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
User=your-user
Group=www-data
WorkingDirectory=/path/to/daamduu
ExecStart=/path/to/daamduu/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/gunicorn.sock \
    daamduu.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start and enable the service:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## SSL Configuration

Install Certbot:
```bash
sudo apt install certbot python3-certbot-nginx
```

Obtain SSL certificate:
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Monitoring

1. Set up logging:
```bash
mkdir logs
touch logs/django.log
chmod 666 logs/django.log
```

2. Monitor the application:
```bash
sudo journalctl -u gunicorn
tail -f logs/django.log
```

## Backup

Set up regular database backups:
```bash
pg_dump -U daamduu_user daamduu > backup.sql
```

## Security Checklist

- [ ] Change default database password
- [ ] Set up firewall (UFW)
- [ ] Configure fail2ban
- [ ] Set up regular security updates
- [ ] Enable HTTPS
- [ ] Set secure cookie settings
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable HSTS
- [ ] Configure secure headers

## Troubleshooting

1. Check Gunicorn logs:
```bash
sudo journalctl -u gunicorn
```

2. Check Nginx logs:
```bash
sudo tail -f /var/log/nginx/error.log
```

3. Check Django logs:
```bash
tail -f logs/django.log
```

4. Check Redis:
```bash
redis-cli ping
```

5. Check PostgreSQL:
```bash
sudo -u postgres psql -d daamduu
```

## Maintenance

1. Regular updates:
```bash
pip install --upgrade -r requirements.txt
python manage.py migrate
python manage.py collectstatic
sudo systemctl restart gunicorn
```

2. Database maintenance:
```bash
python manage.py dbshell
VACUUM ANALYZE;
```

3. Clear cache:
```bash
python manage.py shell
from django.core.cache import cache
cache.clear()
``` 