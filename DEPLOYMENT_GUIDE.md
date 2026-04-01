# Factory InfoHub - Production Deployment Guide

This guide provides comprehensive instructions for deploying the Factory InfoHub Django application to a production environment with security hardening, performance optimization, and monitoring.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Manual Deployment](#manual-deployment)
4. [Security Hardening](#security-hardening)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Performance Optimization](#performance-optimization)
9. [Backup and Recovery](#backup-and-recovery)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04 LTS or later (recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB SSD minimum
- **CPU**: 2 cores minimum
- **Network**: Internet access for package installation

### Required Software
- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Nginx
- Git

### Domain and SSL
- Domain name pointing to your server
- SSL certificate (Let's Encrypt recommended)

## Quick Start

For automated deployment, use the provided scripts:

```bash
# 1. Clone the repository
git clone <your-repository-url>
cd FactoryInfoHub

# 2. Make scripts executable
chmod +x deployment/setup_production.sh
chmod +x deployment/security_hardening.sh

# 3. Run production setup (takes 15-30 minutes)
sudo ./deployment/setup_production.sh

# 4. Apply security hardening
sudo ./deployment/security_hardening.sh

# 5. Configure environment variables
cp .env.example .env
# Edit .env with your production values

# 6. Restart services
sudo systemctl restart factoryinfohub
sudo systemctl restart nginx
```

## Manual Deployment

### 1. System Setup

#### Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git
```

#### Install Python and Dependencies
```bash
sudo apt install -y python3.10 python3.10-venv python3.10-dev
sudo apt install -y build-essential libpq-dev libssl-dev libffi-dev
```

### 2. Database Setup (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres createuser --interactive factoryuser
sudo -u postgres createdb factoryinfohub -O factoryuser

# Set password
sudo -u postgres psql -c "ALTER USER factoryuser PASSWORD 'your-secure-password';"
```

### 3. Redis Setup

```bash
# Install Redis
sudo apt install -y redis-server

# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test connection
redis-cli ping
```

### 4. Application Setup

#### Create Application Directory
```bash
sudo mkdir -p /var/www/factoryinfohub
sudo chown -R $USER:$USER /var/www/factoryinfohub
cd /var/www/factoryinfohub
```

#### Setup Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r /path/to/your/project/requirements.txt
pip install gunicorn psycopg2-binary django-redis

deactivate
```

#### Copy Application Files
```bash
# Copy your Django project
cp -r /path/to/your/project/* /var/www/factoryinfohub/

# Set permissions
sudo chown -R www-data:www-data /var/www/factoryinfohub
sudo chmod -R 755 /var/www/factoryinfohub
```

### 5. Environment Configuration

#### Create Environment File
```bash
cp .env.example .env
```

#### Configure Environment Variables
Edit `.env` file with your production values:

```bash
# Generate secure secret key
SECRET_KEY=$(python3.10 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))")

# Update .env file
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
sed -i "s/DEBUG=.*/DEBUG=False/" .env
sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com/" .env
sed -i "s/DATABASE_URL=.*/DATABASE_URL=postgresql:\/\/factoryuser:your-password@localhost:5432\/factoryinfohub/" .env
sed -i "s/REDIS_URL=.*/REDIS_URL=redis:\/\/localhost:6379\/1/" .env

# Set secure permissions
chmod 600 .env
```

### 6. Django Setup

```bash
cd /var/www/factoryinfohub
source venv/bin/activate

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (optional)
python manage.py createsuperuser

deactivate
```

### 7. Gunicorn Configuration

#### Create Gunicorn Service
```bash
sudo tee /etc/systemd/system/factoryinfohub.service > /dev/null <<EOF
[Unit]
Description=Factory InfoHub Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/factoryinfohub
Environment="PATH=/var/www/factoryinfohub/venv/bin"
ExecStart=/var/www/factoryinfohub/venv/bin/gunicorn --workers 3 --bind unix:factoryinfohub.sock --timeout 30 --max-requests 1000 --max-requests-jitter 50 FactoryInfoHub.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

#### Start Gunicorn Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable factoryinfohub
sudo systemctl start factoryinfohub
```

### 8. Nginx Configuration

#### Copy Nginx Configuration
```bash
sudo cp deployment/nginx.conf /etc/nginx/sites-available/factoryinfohub
```

#### Update Configuration
```bash
sudo sed -i "s|yourdomain.com|yourdomain.com|g" /etc/nginx/sites-available/factoryinfohub
sudo sed -i "s|/path/to/your/static/files/|/var/www/factoryinfohub/static/|g" /etc/nginx/sites-available/factoryinfohub
sudo sed -i "s|/path/to/your/media/files/|/var/www/factoryinfohub/media/|g" /etc/nginx/sites-available/factoryinfohub
```

#### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/factoryinfohub /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 9. SSL Configuration

#### Install Certbot
```bash
sudo apt install -y certbot python3-certbot-nginx
```

#### Obtain SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### Setup Auto-Renewal
```bash
sudo crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
```

## Security Hardening

### SSH Hardening
```bash
sudo ./deployment/security_hardening.sh
```

### Firewall Configuration
```bash
# Enable UFW
sudo ufw --force enable

# Allow necessary ports
sudo ufw allow 2222/tcp  # SSH (changed port)
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
```

### File Permissions
```bash
# Set secure permissions
sudo find /var/www/factoryinfohub -type d -exec chmod 755 {} \;
sudo find /var/www/factoryinfohub -type f -exec chmod 644 {} \;
sudo chmod 600 /var/www/factoryinfohub/.env
sudo chown -R www-data:www-data /var/www/factoryinfohub
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# Django Configuration
SECRET_KEY=your-50-character-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Redis Configuration
REDIS_URL=redis://localhost:6379/1
CACHE_REDIS_URL=redis://localhost:6379/1

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/www/factoryinfohub/logs/django.log
```

### Production-Specific Settings

#### Database Optimization
```python
# In settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'factoryinfohub',
        'USER': 'factoryuser',
        'PASSWORD': 'your-password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'connect_timeout': 20,
        },
        'CONN_MAX_AGE': 600,
    }
}
```

#### Caching Configuration
```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('CACHE_REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'factoryinfohub',
        'TIMEOUT': 300,
    }
}
```

## Monitoring and Maintenance

### Application Monitoring

#### Health Check Endpoint
Add to your `urls.py`:
```python
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("healthy", content_type="text/plain")

urlpatterns = [
    # ... other patterns
    path('health/', health_check, name='health_check'),
]
```

#### Log Monitoring
```bash
# View application logs
tail -f /var/www/factoryinfohub/logs/django.log

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# View system logs
journalctl -u factoryinfohub -f
```

### Performance Monitoring

#### System Resources
```bash
# Monitor CPU and memory
htop

# Monitor disk usage
df -h

# Monitor network
iftop
```

#### Application Performance
```bash
# Check Gunicorn status
sudo systemctl status factoryinfohub

# Check Nginx status
sudo systemctl status nginx

# Check database connections
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

### Automated Monitoring Script

The deployment includes a monitoring script at `/usr/local/bin/factoryinfohub-monitor.sh` that:
- Checks application health every 5 minutes
- Monitors disk and memory usage
- Sends alerts via email
- Automatically restarts services if needed

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Gunicorn logs
sudo journalctl -u factoryinfohub -f

# Check Django migrations
source venv/bin/activate
python manage.py migrate
deactivate
```

#### Nginx 502 Bad Gateway
```bash
# Check if Gunicorn socket exists
ls -la /var/www/factoryinfohub/factoryinfohub.sock

# Check Gunicorn service status
sudo systemctl status factoryinfohub

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
sudo -u postgres psql -d factoryinfohub -c "SELECT version();"

# Check PostgreSQL service
sudo systemctl status postgresql
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --dry-run
```

### Debug Commands

#### Django Debug
```bash
cd /var/www/factoryinfohub
source venv/bin/activate

# Check Django settings
python manage.py check --deploy

# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])

deactivate
```

#### System Debug
```bash
# Check open ports
sudo netstat -tlnp

# Check firewall status
sudo ufw status

# Check fail2ban status
sudo fail2ban-client status
```

## Performance Optimization

### Database Optimization

#### PostgreSQL Tuning
```sql
-- Enable query logging
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Optimize connection pooling
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';

-- Restart PostgreSQL
sudo systemctl restart postgresql
```

#### Django Database Optimization
```python
# In settings.py
DATABASES = {
    'default': {
        # ... other settings
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
        'OPTIONS': {
            'connect_timeout': 20,
        }
    }
}

# Enable query optimization
DATABASES['default']['OPTIONS']['application_name'] = 'factoryinfohub'
```

### Caching Strategy

#### Redis Caching
```python
# In settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'factoryinfohub',
        'TIMEOUT': 300,  # 5 minutes
    }
}

# Cache views
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
def my_view(request):
    # View logic
    pass
```

#### Static File Optimization
```python
# In settings.py
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Enable gzip compression in Nginx
gzip on;
gzip_vary on;
gzip_min_length 1000;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss application/atom+xml image/svg+xml;
```

### Gunicorn Optimization
```bash
# In Gunicorn service file
ExecStart=/var/www/factoryinfohub/venv/bin/gunicorn \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 30 \
    --bind unix:factoryinfohub.sock \
    FactoryInfoHub.wsgi:application
```

## Backup and Recovery

### Database Backup

#### Automated Database Backup
```bash
# Create backup script
sudo tee /usr/local/bin/backup-database.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/factoryinfohub"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/factoryinfohub_$DATE.sql"

mkdir -p $BACKUP_DIR
sudo -u postgres pg_dump factoryinfohub > $BACKUP_FILE
gzip $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-database.sh

# Add to crontab
sudo crontab -l | { cat; echo "0 2 * * * /usr/local/bin/backup-database.sh"; } | sudo crontab -
```

#### Manual Database Backup
```bash
# Backup
sudo -u postgres pg_dump factoryinfohub > backup.sql

# Restore
sudo -u postgres psql factoryinfohub < backup.sql
```

### Application Backup

#### File Backup Script
```bash
# Create backup script
sudo tee /usr/local/bin/backup-application.sh > /dev/null << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/factoryinfohub"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/var/www/factoryinfohub"

mkdir -p $BACKUP_DIR
tar -czf "$BACKUP_DIR/factoryinfohub_app_$DATE.tar.gz" -C $APP_DIR .

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-application.sh

# Add to crontab
sudo crontab -l | { cat; echo "0 3 * * * /usr/local/bin/backup-application.sh"; } | sudo crontab -
```

### Recovery Procedures

#### Database Recovery
```bash
# Stop application
sudo systemctl stop factoryinfohub

# Restore database
sudo -u postgres dropdb factoryinfohub
sudo -u postgres createdb factoryinfohub
sudo -u postgres psql factoryinfohub < backup.sql

# Start application
sudo systemctl start factoryinfohub
```

#### Application Recovery
```bash
# Stop application
sudo systemctl stop factoryinfohub

# Restore files
tar -xzf backup.tar.gz -C /var/www/

# Set permissions
sudo chown -R www-data:www-data /var/www/factoryinfohub

# Start application
sudo systemctl start factoryinfohub
```

## Security Best Practices

### Regular Security Tasks

1. **Update System**: Run `sudo apt update && sudo apt upgrade` weekly
2. **Monitor Logs**: Check `/var/log/auth.log` for failed login attempts
3. **Review Backups**: Test backup restoration monthly
4. **SSL Renewal**: Monitor certificate expiration
5. **Security Scans**: Run vulnerability scans quarterly

### Security Monitoring

#### Log Analysis
```bash
# Monitor failed login attempts
grep "Failed password" /var/log/auth.log | tail -20

# Monitor application errors
tail -f /var/www/factoryinfohub/logs/django.log | grep ERROR

# Monitor Nginx errors
tail -f /var/log/nginx/error.log
```

#### Security Tools
```bash
# Install security scanning tools
sudo apt install -y lynis rkhunter

# Run security audit
sudo lynis audit system

# Check for rootkits
sudo rkhunter --check
```

## Support and Maintenance

### Regular Maintenance Tasks

#### Weekly
- Check application logs for errors
- Monitor disk space usage
- Review security logs
- Test backup restoration

#### Monthly
- Update system packages
- Review and rotate logs
- Check SSL certificate expiration
- Performance review

#### Quarterly
- Security audit
- Performance optimization review
- Update dependencies
- Disaster recovery testing

### Getting Help

If you encounter issues:

1. **Check Logs**: Application, system, and service logs
2. **Review Configuration**: Environment variables and settings
3. **Test Components**: Database, Redis, and web server separately
4. **Search Documentation**: This guide and Django documentation
5. **Community Support**: Django and Ubuntu communities

### Emergency Procedures

#### Application Down
1. Check service status: `sudo systemctl status factoryinfohub`
2. Check logs: `sudo journalctl -u factoryinfohub -f`
3. Restart service: `sudo systemctl restart factoryinfohub`
4. Check dependencies: Database, Redis, Nginx

#### Security Incident
1. Isolate the server if necessary
2. Change all passwords and keys
3. Review access logs
4. Update security measures
5. Notify relevant parties

---

For more information, refer to:
- [Django Documentation](https://docs.djangoproject.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Ubuntu Server Guide](https://ubuntu.com/server/docs)