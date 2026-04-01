#!/bin/bash

# Factory InfoHub Production Setup Script
# This script sets up a production environment for the Factory InfoHub Django application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons."
        exit 1
    fi
}

# Install system dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install Python, PostgreSQL, Redis, Nginx
    sudo apt install -y \
        python3.10 \
        python3.10-venv \
        python3.10-dev \
        postgresql \
        postgresql-contrib \
        redis-server \
        nginx \
        curl \
        wget \
        git \
        build-essential \
        libpq-dev \
        libssl-dev \
        libffi-dev \
        libjpeg-dev \
        zlib1g-dev \
        libwebp-dev \
        libmagic1
    
    log "System dependencies installed successfully."
}

# Setup PostgreSQL database
setup_database() {
    log "Setting up PostgreSQL database..."
    
    # Start PostgreSQL service
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
    
    # Create database user and database
    sudo -u postgres createuser --interactive factoryuser <<EOF
y
y
y
EOF
    
    sudo -u postgres createdb factoryinfohub -O factoryuser
    
    # Set password for the user
    sudo -u postgres psql -c "ALTER USER factoryuser PASSWORD 'your-secure-password-here';"
    
    log "PostgreSQL database setup completed."
}

# Setup Redis
setup_redis() {
    log "Setting up Redis..."
    
    # Start Redis service
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Test Redis connection
    redis-cli ping
    
    log "Redis setup completed."
}

# Create application directory structure
create_directories() {
    log "Creating application directory structure..."
    
    # Create main application directory
    sudo mkdir -p /var/www/factoryinfohub
    sudo chown -R $USER:$USER /var/www/factoryinfohub
    
    # Create logs directory
    mkdir -p /var/www/factoryinfohub/logs
    
    # Create virtual environment directory
    mkdir -p /var/www/factoryinfohub/venv
    
    log "Directory structure created."
}

# Setup Python virtual environment
setup_virtualenv() {
    log "Setting up Python virtual environment..."
    
    cd /var/www/factoryinfohub
    
    # Create virtual environment
    python3.10 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required packages
    pip install -r /path/to/your/project/requirements.txt
    
    # Install additional production packages
    pip install gunicorn psycopg2-binary django-redis
    
    deactivate
    
    log "Virtual environment setup completed."
}

# Copy application files
copy_application() {
    log "Copying application files..."
    
    cd /var/www/factoryinfohub
    
    # Copy your Django project files
    # Replace /path/to/your/project with your actual project path
    cp -r /path/to/your/project/* .
    
    # Set proper permissions
    sudo chown -R www-data:www-data /var/www/factoryinfohub
    sudo chmod -R 755 /var/www/factoryinfohub
    
    log "Application files copied."
}

# Setup environment variables
setup_environment() {
    log "Setting up environment variables..."
    
    cd /var/www/factoryinfohub
    
    # Create .env file from template
    cp .env.example .env
    
    # Generate a secure secret key
    SECRET_KEY=$(python3.10 -c "import secrets; print(''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)))")
    
    # Update .env file with production values
    sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/DEBUG=.*/DEBUG=False/" .env
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com/" .env
    sed -i "s/DATABASE_URL=.*/DATABASE_URL=postgresql:\/\/factoryuser:your-secure-password-here@localhost:5432\/factoryinfohub/" .env
    sed -i "s/REDIS_URL=.*/REDIS_URL=redis:\/\/localhost:6379\/1/" .env
    sed -i "s/LOG_FILE=.*/LOG_FILE=\/var\/www\/factoryinfohub\/logs\/django.log/" .env
    
    # Set proper permissions for .env file
    chmod 600 .env
    
    log "Environment variables configured."
}

# Setup Gunicorn service
setup_gunicorn() {
    log "Setting up Gunicorn service..."
    
    cd /var/www/factoryinfohub
    
    # Create Gunicorn service file
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
    
    # Reload systemd and start service
    sudo systemctl daemon-reload
    sudo systemctl enable factoryinfohub
    sudo systemctl start factoryinfohub
    
    log "Gunicorn service configured and started."
}

# Setup Nginx
setup_nginx() {
    log "Setting up Nginx..."
    
    # Copy Nginx configuration
    sudo cp deployment/nginx.conf /etc/nginx/sites-available/factoryinfohub
    
    # Update paths in Nginx config
    sudo sed -i "s|yourdomain.com|yourdomain.com|g" /etc/nginx/sites-available/factoryinfohub
    sudo sed -i "s|/path/to/your/static/files/|/var/www/factoryinfohub/static/|g" /etc/nginx/sites-available/factoryinfohub
    sudo sed -i "s|/path/to/your/media/files/|/var/www/factoryinfohub/media/|g" /etc/nginx/sites-available/factoryinfohub
    sudo sed -i "s|/path/to/your/ssl/certificate.crt|/etc/ssl/certs/yourdomain.crt|g" /etc/nginx/sites-available/factoryinfohub
    sudo sed -i "s|/path/to/your/ssl/private.key|/etc/ssl/private/yourdomain.key|g" /etc/nginx/sites-available/factoryinfohub
    
    # Enable site
    sudo ln -s /etc/nginx/sites-available/factoryinfohub /etc/nginx/sites-enabled
    
    # Test Nginx configuration
    sudo nginx -t
    
    # Restart Nginx
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    
    log "Nginx configured and started."
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    log "Setting up SSL with Let's Encrypt..."
    
    # Install Certbot
    sudo apt install -y certbot python3-certbot-nginx
    
    # Obtain SSL certificate (replace with your domain)
    sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
    
    # Setup automatic renewal
    sudo crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -
    
    log "SSL setup completed."
}

# Setup log rotation
setup_logrotate() {
    log "Setting up log rotation..."
    
    sudo tee /etc/logrotate.d/factoryinfohub > /dev/null <<EOF
/var/www/factoryinfohub/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload factoryinfohub
    endscript
}
EOF
    
    log "Log rotation configured."
}

# Setup monitoring
setup_monitoring() {
    log "Setting up basic monitoring..."
    
    # Create monitoring script
    sudo tee /usr/local/bin/factoryinfohub-monitor.sh > /dev/null <<'EOF'
#!/bin/bash

# Factory InfoHub Monitoring Script
LOG_FILE="/var/log/factoryinfohub-monitor.log"
APP_URL="https://yourdomain.com/health/"

# Function to log messages
log_message() {
    echo "$(date): $1" >> $LOG_FILE
}

# Check if application is responding
if curl -f -s $APP_URL > /dev/null; then
    log_message "Application is healthy"
else
    log_message "WARNING: Application is not responding"
    # Try to restart the service
    systemctl restart factoryinfohub
    sleep 10
    if curl -f -s $APP_URL > /dev/null; then
        log_message "Application restarted successfully"
    else
        log_message "ERROR: Application restart failed"
        # Send alert email (if configured)
        echo "Factory InfoHub application is down" | mail -s "Application Alert" admin@yourdomain.com
    fi
fi

# Check disk space
DISK_USAGE=$(df /var/www/factoryinfohub | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log_message "WARNING: Disk usage is above 80%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 80 ]; then
    log_message "WARNING: Memory usage is above 80%"
fi
EOF
    
    sudo chmod +x /usr/local/bin/factoryinfohub-monitor.sh
    
    # Add to crontab
    sudo crontab -l | { cat; echo "*/5 * * * * /usr/local/bin/factoryinfohub-monitor.sh"; } | sudo crontab -
    
    log "Monitoring setup completed."
}

# Run Django migrations and collect static files
setup_django() {
    log "Running Django setup..."
    
    cd /var/www/factoryinfohub
    source venv/bin/activate
    
    # Run migrations
    python manage.py migrate
    
    # Collect static files
    python manage.py collectstatic --noinput
    
    # Create superuser (optional)
    # python manage.py createsuperuser
    
    deactivate
    
    log "Django setup completed."
}

# Main execution
main() {
    log "Starting Factory InfoHub production setup..."
    
    check_root
    
    install_dependencies
    setup_database
    setup_redis
    create_directories
    setup_virtualenv
    copy_application
    setup_environment
    setup_gunicorn
    setup_nginx
    setup_ssl
    setup_logrotate
    setup_monitoring
    setup_django
    
    log "Factory InfoHub production setup completed successfully!"
    info "Application should now be accessible at https://yourdomain.com"
    info "Don't forget to:"
    info "1. Update the domain names in the configuration files"
    info "2. Set up proper SSL certificates"
    info "3. Configure email settings in .env file"
    info "4. Set up database backups"
    info "5. Monitor the application logs"
}

# Run main function
main "$@"