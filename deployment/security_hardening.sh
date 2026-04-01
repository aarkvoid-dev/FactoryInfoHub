#!/bin/bash

# Factory InfoHub Security Hardening Script
# This script applies security hardening measures to the production environment

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

# Harden SSH configuration
harden_ssh() {
    log "Hardening SSH configuration..."
    
    # Backup original SSH config
    sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Apply security settings
    sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
    sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
    sudo sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
    sudo sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/' /etc/ssh/sshd_config
    sudo sed -i 's/#ClientAliveInterval 0/ClientAliveInterval 300/' /etc/ssh/sshd_config
    sudo sed -i 's/#ClientAliveCountMax 3/ClientAliveCountMax 2/' /etc/ssh/sshd_config
    
    # Add additional security settings
    echo "Protocol 2" | sudo tee -a /etc/ssh/sshd_config
    echo "LoginGraceTime 60" | sudo tee -a /etc/ssh/sshd_config
    echo "X11Forwarding no" | sudo tee -a /etc/ssh/sshd_config
    echo "AllowUsers $(whoami)" | sudo tee -a /etc/ssh/sshd_config
    
    # Restart SSH service
    sudo systemctl restart sshd
    
    log "SSH configuration hardened."
    info "Note: SSH port changed to 2222. Update your firewall rules accordingly."
}

# Setup firewall (UFW)
setup_firewall() {
    log "Setting up firewall (UFW)..."
    
    # Enable UFW
    sudo ufw --force enable
    
    # Set default policies
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    
    # Allow SSH (with new port)
    sudo ufw allow 2222/tcp
    
    # Allow HTTP and HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Allow PostgreSQL (only from localhost)
    sudo ufw allow from 127.0.0.1 to any port 5432
    
    # Allow Redis (only from localhost)
    sudo ufw allow from 127.0.0.1 to any port 6379
    
    log "Firewall configured."
}

# Harden system kernel parameters
harden_kernel() {
    log "Hardening kernel parameters..."
    
    # Backup sysctl.conf
    sudo cp /etc/sysctl.conf /etc/sysctl.conf.backup
    
    # Add security parameters
    cat << 'EOF' | sudo tee -a /etc/sysctl.conf
    
# Security hardening parameters
# Disable IP forwarding
net.ipv4.ip_forward = 0

# Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Disable source route
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Enable TCP SYN Cookie Protection
net.ipv4.tcp_syncookies = 1

# Disable ICMP echo requests (ping)
net.ipv4.icmp_echo_ignore_all = 1

# Enable IP spoofing protection
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log Martian Packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Disable kernel core dumps
fs.suid_dumpable = 0
EOF
    
    # Apply changes
    sudo sysctl -p
    
    log "Kernel parameters hardened."
}

# Setup fail2ban for intrusion prevention
setup_fail2ban() {
    log "Setting up fail2ban..."
    
    # Install fail2ban
    sudo apt install -y fail2ban
    
    # Create jail.local configuration
    sudo tee /etc/fail2ban/jail.local > /dev/null << 'EOF'
[DEFAULT]
# Ban hosts for 1 hour
bantime = 3600

# A host is banned if it has generated "maxretry" during the last "findtime"
findtime = 600

# Max number of failures before a host gets banned
maxretry = 3

# Ban time for recidive (repeat offenders)
bantime.increment = true
bantime.rndtime = 300
bantime.maxtime = 86400

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
port = http,https
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
EOF
    
    # Create nginx filters
    sudo tee /etc/fail2ban/filter.d/nginx-noscript.conf > /dev/null << 'EOF'
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*(\.php|\.asp|\.exe|\.pl|\.cgi|\.scgi)
ignoreregex =
EOF

    sudo tee /etc/fail2ban/filter.d/nginx-badbots.conf > /dev/null << 'EOF'
[Definition]
failregex = ^<HOST> -.*"(GET|POST).*(bot|crawler|spider|scraper)
ignoreregex =
EOF
    
    # Restart fail2ban
    sudo systemctl restart fail2ban
    sudo systemctl enable fail2ban
    
    log "Fail2ban configured and started."
}

# Setup automatic security updates
setup_security_updates() {
    log "Setting up automatic security updates..."
    
    # Install unattended-upgrades
    sudo apt install -y unattended-upgrades
    
    # Configure automatic updates
    sudo tee /etc/apt/apt.conf.d/50unattended-upgrades > /dev/null << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "root";
EOF
    
    # Enable automatic updates
    sudo dpkg-reconfigure -f noninteractive unattended-upgrades
    
    log "Automatic security updates configured."
}

# Harden file permissions
harden_permissions() {
    log "Hardening file permissions..."
    
    # Set secure permissions for critical directories
    sudo find /var/www/factoryinfohub -type d -exec chmod 755 {} \;
    sudo find /var/www/factoryinfohub -type f -exec chmod 644 {} \;
    
    # Set specific permissions for sensitive files
    sudo chmod 600 /var/www/factoryinfohub/.env
    sudo chmod 600 /var/www/factoryinfohub/db.sqlite3
    
    # Set ownership
    sudo chown -R www-data:www-data /var/www/factoryinfohub
    
    # Secure log files
    sudo chmod 640 /var/www/factoryinfohub/logs/*.log
    sudo chown www-data:adm /var/www/factoryinfohub/logs/*.log
    
    log "File permissions hardened."
}

# Setup intrusion detection with AIDE
setup_aide() {
    log "Setting up AIDE (Advanced Intrusion Detection Environment)..."
    
    # Install AIDE
    sudo apt install -y aide
    
    # Initialize AIDE database
    sudo aide --init
    
    # Move the new database to the correct location
    sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db
    
    # Create cron job for regular checks
    echo "0 2 * * * /usr/bin/aide --check" | sudo crontab -
    
    log "AIDE configured for intrusion detection."
}

# Harden PostgreSQL
harden_postgresql() {
    log "Hardening PostgreSQL configuration..."
    
    # Edit PostgreSQL configuration
    sudo -u postgres psql -c "ALTER SYSTEM SET listen_addresses = 'localhost';"
    sudo -u postgres psql -c "ALTER SYSTEM SET log_statement = 'all';"
    sudo -u postgres psql -c "ALTER SYSTEM SET log_min_duration_statement = 1000;"
    sudo -u postgres psql -c "ALTER SYSTEM SET log_connections = on;"
    sudo -u postgres psql -c "ALTER SYSTEM SET log_disconnections = on;"
    
    # Restart PostgreSQL
    sudo systemctl restart postgresql
    
    log "PostgreSQL hardened."
}

# Harden Redis
harden_redis() {
    log "Hardening Redis configuration..."
    
    # Backup Redis config
    sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
    
    # Apply security settings
    sudo sed -i 's/# requirepass foobared/requirepass your-redis-password-here/' /etc/redis/redis.conf
    sudo sed -i 's/bind 127.0.0.1 ::1/bind 127.0.0.1/' /etc/redis/redis.conf
    sudo sed -i 's/# maxmemory <bytes>/maxmemory 256mb/' /etc/redis/redis.conf
    sudo sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    
    # Restart Redis
    sudo systemctl restart redis-server
    
    log "Redis hardened."
}

# Create security monitoring script
create_security_monitor() {
    log "Creating security monitoring script..."
    
    sudo tee /usr/local/bin/security-monitor.sh > /dev/null << 'EOF'
#!/bin/bash

# Security Monitoring Script
LOG_FILE="/var/log/security-monitor.log"
EMAIL="admin@yourdomain.com"

# Function to log messages
log_message() {
    echo "$(date): $1" >> $LOG_FILE
}

# Check for failed login attempts
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log | wc -l)
if [ $FAILED_LOGINS -gt 10 ]; then
    log_message "WARNING: High number of failed login attempts: $FAILED_LOGINS"
    echo "Failed login attempts: $FAILED_LOGINS" | mail -s "Security Alert" $EMAIL
fi

# Check for new users
NEW_USERS=$(grep "useradd" /var/log/auth.log | tail -5)
if [ ! -z "$NEW_USERS" ]; then
    log_message "New users created recently:"
    echo "$NEW_USERS" >> $LOG_FILE
fi

# Check disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    log_message "WARNING: Disk usage is above 90%"
    echo "Disk usage: $DISK_USAGE%" | mail -s "Disk Space Alert" $EMAIL
fi

# Check for suspicious processes
SUSPICIOUS_PROCESSES=$(ps aux | grep -E "(nc|netcat|ncat)" | grep -v grep)
if [ ! -z "$SUSPICIOUS_PROCESSES" ]; then
    log_message "WARNING: Suspicious processes detected:"
    echo "$SUSPICIOUS_PROCESSES" >> $LOG_FILE
    echo "Suspicious processes detected" | mail -s "Security Alert" $EMAIL
fi

# Check fail2ban status
BANNED_IPS=$(fail2ban-client status sshd | grep "Number of jail" | awk '{print $5}')
if [ $BANNED_IPS -gt 0 ]; then
    log_message "fail2ban has banned $BANNED_IPS IP addresses"
fi
EOF
    
    sudo chmod +x /usr/local/bin/security-monitor.sh
    
    # Add to crontab
    sudo crontab -l | { cat; echo "*/15 * * * * /usr/local/bin/security-monitor.sh"; } | sudo crontab -
    
    log "Security monitoring script created."
}

# Main execution
main() {
    log "Starting Factory InfoHub security hardening..."
    
    harden_ssh
    setup_firewall
    harden_kernel
    setup_fail2ban
    setup_security_updates
    harden_permissions
    setup_aide
    harden_postgresql
    harden_redis
    create_security_monitor
    
    log "Factory InfoHub security hardening completed!"
    info "Security measures applied:"
    info "1. SSH hardened (port changed to 2222)"
    info "2. Firewall configured"
    info "3. Kernel parameters hardened"
    info "4. fail2ban installed for intrusion prevention"
    info "5. Automatic security updates enabled"
    info "6. File permissions secured"
    info "7. AIDE configured for file integrity monitoring"
    info "8. PostgreSQL and Redis hardened"
    info "9. Security monitoring script installed"
    warn "IMPORTANT: Remember to:"
    warn "1. Update firewall rules for new SSH port (2222)"
    warn "2. Set up SSH key authentication"
    warn "3. Change default passwords"
    warn "4. Configure email alerts properly"
    warn "5. Test all security measures"
}

# Run main function
main "$@"