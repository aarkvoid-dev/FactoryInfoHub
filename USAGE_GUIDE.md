# Factory InfoHub - Usage Guide

This guide explains how to use all the deployment, configuration, and setup files created for the Factory InfoHub Django application.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Configuration](#environment-configuration)
3. [Redis Setup](#redis-setup)
4. [Production Deployment](#production-deployment)
5. [Security Hardening](#security-hardening)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### For Development (Local)
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env file with your local settings
# - Set DEBUG=True
# - Use SQLite database
# - Configure local Redis (if available)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Start development server
python manage.py runserver
```

### For Production
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env file with production settings (see Environment Configuration below)

# 3. Run setup scripts
sudo ./deployment/setup_redis.sh
sudo ./deployment/setup_production.sh
sudo ./deployment/security_hardening.sh

# 4. Configure environment variables
# 5. Start services
```

## Environment Configuration

### File: `.env.example` → `.env`

**Step 1: Copy the template**
```bash
cp .env.example .env
```

**Step 2: Edit `.env` with your settings**

#### Development Environment
```bash
# Django Configuration
SECRET_KEY=your-development-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Redis Configuration (optional for development)
REDIS_URL=redis://localhost:6379/1
CACHE_REDIS_URL=redis://localhost:6379/1
SESSION_REDIS_HOST=localhost
SESSION_REDIS_PORT=6379
SESSION_REDIS_DB=1
SESSION_REDIS_PASSWORD=

# Email Configuration (Console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=25
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=dev@localhost.com
```

#### Production Environment
```bash
# Django Configuration
SECRET_KEY=your-50-character-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database Configuration (PostgreSQL for production)
DATABASE_URL=postgresql://username:password@localhost:5432/factoryinfohub

# Redis Configuration (required for production)
REDIS_URL=redis://localhost:6379/1
CACHE_REDIS_URL=redis://localhost:6379/1
SESSION_REDIS_HOST=localhost
SESSION_REDIS_PORT=6379
SESSION_REDIS_DB=1
SESSION_REDIS_PASSWORD=your-secure-redis-password

# Email Configuration (SMTP for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
CONTACT_EMAIL_RECIPIENTS=admin@yourdomain.com,support@yourdomain.com

# Security Settings
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/www/factoryinfohub/logs/django.log
```

**Step 3: Set secure permissions**
```bash
chmod 600 .env
```

## Redis Setup

### File: `deployment/setup_redis.sh`

**Purpose**: Automatically installs and configures Redis for production use.

**Usage**:
```bash
# Make executable
chmod +x deployment/setup_redis.sh

# Run setup (requires sudo)
sudo ./deployment/setup_redis.sh
```

**What it does**:
1. Installs Redis server and tools
2. Configures Redis for production (security, performance, persistence)
3. Sets up monitoring and backup scripts
4. Configures firewall rules
5. Creates systemd service configuration

**After running**:
1. **Change Redis password** in `/etc/redis/redis.conf`
2. **Update your `.env` file** with the new password
3. **Restart Redis**: `sudo systemctl restart redis-server`
4. **Test connection**: `redis-cli ping` (should return "PONG")

### Manual Redis Configuration

If you prefer manual setup:

```bash
# Install Redis
sudo apt install redis-server

# Edit configuration
sudo nano /etc/redis/redis.conf

# Add/modify these settings:
bind 127.0.0.1
requirepass your-secure-password-here
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### Testing Redis Connection

```bash
# Test basic connection
redis-cli ping

# Test with password (replace with your password)
redis-cli -a your-secure-password-here ping

# Test Django connection
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 30)
>>> cache.get('test')
'value'
```

## Production Deployment

### File: `deployment/setup_production.sh`

**Purpose**: Complete production environment setup including database, web server, and application server.

**Usage**:
```bash
# Make executable
chmod +x deployment/setup_production.sh

# Run setup (requires sudo)
sudo ./deployment/setup_production.sh
```

**What it does**:
1. Installs system dependencies (Python, PostgreSQL, Redis, Nginx)
2. Sets up PostgreSQL database and user
3. Creates application directory structure
4. Sets up Python virtual environment
5. Configures Gunicorn application server
6. Sets up Nginx reverse proxy
7. Configures SSL with Let's Encrypt
8. Sets up log rotation and monitoring

**Important**: This script will take 15-30 minutes to complete.

### File: `deployment/nginx.conf`

**Purpose**: Nginx configuration for serving the Django application.

**Usage**:
- The setup script automatically copies and configures this file
- Manual setup: Copy to `/etc/nginx/sites-available/factoryinfohub`
- Update domain names and file paths
- Enable site: `sudo ln -s /etc/nginx/sites-available/factoryinfohub /etc/nginx/sites-enabled`

### File: `requirements-production.txt`

**Purpose**: Production-specific Python dependencies.

**Usage**:
```bash
# Install production dependencies
pip install -r requirements-production.txt

# Or install specific packages
pip install gunicorn psycopg2-binary django-redis
```

## Security Hardening

### File: `deployment/security_hardening.sh`

**Purpose**: Applies comprehensive security hardening measures.

**Usage**:
```bash
# Make executable
chmod +x deployment/security_hardening.sh

# Run hardening (requires sudo)
sudo ./deployment/security_hardening.sh
```

**What it does**:
1. **SSH Hardening**: Changes port, disables root login, enables key authentication
2. **Firewall Setup**: Configures UFW with appropriate rules
3. **Kernel Hardening**: Applies security kernel parameters
4. **Intrusion Prevention**: Sets up fail2ban
5. **Automatic Updates**: Configures security updates
6. **File Permissions**: Secures file permissions
7. **Intrusion Detection**: Sets up AIDE
8. **Database Security**: Hardens PostgreSQL and Redis
9. **Monitoring**: Creates security monitoring scripts

**After running**:
- SSH port changes to 2222 (update your SSH client)
- Root login disabled (use sudo)
- Firewall enabled (ensure your ports are open)
- Automatic security updates enabled

## Monitoring and Maintenance

### File: `DEPLOYMENT_GUIDE.md`

**Purpose**: Comprehensive deployment documentation and maintenance procedures.

**Usage**: Read this file for detailed deployment instructions, troubleshooting, and maintenance procedures.

### Monitoring Scripts

#### Application Monitoring
```bash
# View application logs
tail -f /var/www/factoryinfohub/logs/django.log

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# View system logs
journalctl -u factoryinfohub -f
```

#### Redis Monitoring
```bash
# View Redis logs
tail -f /var/log/redis/redis-server.log

# Check Redis status
redis-cli info

# Monitor Redis performance
redis-cli monitor
```

#### System Monitoring
```bash
# Check system resources
htop

# Check disk usage
df -h

# Check memory usage
free -h

# Check network connections
netstat -tlnp
```

### Automated Monitoring

The setup scripts create automated monitoring that:
- Checks application health every 5 minutes
- Monitors Redis every 10 minutes
- Runs database backups daily at 2 AM
- Runs application backups daily at 3 AM
- Sends email alerts for issues

### Log Rotation

Logs are automatically rotated:
- Django logs: Daily, keep 52 weeks
- Nginx logs: Handled by logrotate
- System logs: Handled by journald

## Troubleshooting

### Common Issues

#### Application Won't Start
```bash
# Check Gunicorn status
sudo systemctl status factoryinfohub

# Check logs
sudo journalctl -u factoryinfohub -f

# Check Django settings
python manage.py check --deploy

# Check migrations
python manage.py migrate
```

#### Nginx 502 Bad Gateway
```bash
# Check if Gunicorn socket exists
ls -la /var/www/factoryinfohub/factoryinfohub.sock

# Check Gunicorn service
sudo systemctl status factoryinfohub

# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

#### Database Connection Issues
```bash
# Test PostgreSQL connection
sudo -u postgres psql -d factoryinfohub -c "SELECT version();"

# Check PostgreSQL service
sudo systemctl status postgresql

# Check database permissions
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli ping

# Check Redis service
sudo systemctl status redis-server

# Check Redis configuration
sudo nano /etc/redis/redis.conf
```

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test SSL configuration
sudo nginx -t
```

### Debug Commands

#### Django Debug
```bash
# Check Django settings
python manage.py check --deploy

# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])

# Check cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 30)
>>> cache.get('test')
```

#### System Debug
```bash
# Check open ports
sudo netstat -tlnp

# Check firewall status
sudo ufw status

# Check fail2ban status
sudo fail2ban-client status

# Check disk space
df -h

# Check memory usage
free -h
```

### Getting Help

1. **Check logs**: Always start with application and system logs
2. **Review configuration**: Check environment variables and settings
3. **Test components**: Test database, Redis, and web server separately
4. **Search documentation**: Refer to DEPLOYMENT_GUIDE.md
5. **Community support**: Django and Ubuntu communities

## Quick Reference

### Essential Commands

```bash
# Start/stop services
sudo systemctl start factoryinfohub
sudo systemctl stop factoryinfohub
sudo systemctl restart factoryinfohub
sudo systemctl status factoryinfohub

sudo systemctl start nginx
sudo systemctl restart nginx

sudo systemctl start redis-server
sudo systemctl restart redis-server

sudo systemctl start postgresql
sudo systemctl restart postgresql

# Check logs
sudo journalctl -u factoryinfohub -f
tail -f /var/www/factoryinfohub/logs/django.log

# Django commands
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser

# Redis commands
redis-cli ping
redis-cli info
redis-cli monitor

# Database commands
sudo -u postgres psql factoryinfohub
```

### File Locations

```bash
# Application files
/var/www/factoryinfohub/

# Logs
/var/www/factoryinfohub/logs/
/var/log/nginx/
/var/log/redis/

# Configuration
/etc/nginx/sites-available/factoryinfohub
/etc/redis/redis.conf
/etc/postgresql/

# SSL certificates
/etc/ssl/certs/
/etc/ssl/private/

# Backups
/var/backups/factoryinfohub/
/var/backups/redis/
```

This usage guide provides comprehensive instructions for deploying, configuring, and maintaining your Factory InfoHub application. Always refer to the specific files mentioned for detailed configuration options and advanced usage.
