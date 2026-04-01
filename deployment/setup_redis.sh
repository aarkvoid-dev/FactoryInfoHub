#!/bin/bash

# Redis Setup Script for Factory InfoHub
# This script configures Redis for production use with proper security and optimization

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

# Install Redis
install_redis() {
    log "Installing Redis..."
    
    # Update package list
    sudo apt update
    
    # Install Redis
    sudo apt install -y redis-server redis-tools
    
    log "Redis installed successfully."
}

# Configure Redis for production
configure_redis() {
    log "Configuring Redis for production..."
    
    # Backup original configuration
    sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
    
    # Apply production configuration
    sudo tee /etc/redis/redis.conf > /dev/null << 'EOF'
# Redis configuration file example.
# Note that in order to read the configuration file, Redis must be
# started with the file path as first argument:
# ./redis-server /path/to/redis.conf

# Network
bind 127.0.0.1 ::1
port 0
tcp-backlog 511
timeout 300
tcp-keepalive 300

# General
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
always-show-logo yes

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# Replication
replica-serve-stale-data yes
replica-read-only yes
repl-diskless-sync no
repl-diskless-sync-delay 5
repl-disable-tcp-nodelay no
repl-backlog-size 1mb
repl-backlog-ttl 3600

# Security
# Set a password for Redis (replace 'your-redis-password-here' with a strong password)
requirepass your-redis-password-here

# Limits
maxclients 10000

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Append only file
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
aof-use-rdb-preamble yes

# Lua scripting
lua-time-limit 5000

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency monitoring
latency-monitor-threshold 0

# Event notification
notify-keyspace-events Ex

# Hashes
hash-max-ziplist-entries 512
hash-max-ziplist-value 64

# Lists
list-max-ziplist-size -2
list-compress-depth 0

# Sets
set-max-intset-entries 512

# Sorted sets
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# HyperLogLog
hll-sparse-max-bytes 3000

# Streams
stream-node-max-bytes 4096
stream-node-max-entries 100

# Active rehashing
activerehashing yes

# Client output buffer limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Client query buffer limit
client-query-buffer-limit 1gb

# Protocol
proto-max-bulk-len 512mb

# Frequency of background tasks
hz 10

# Enable active expiration of keys
active-expire-effort 1

# Enable active rehashing
active-rehashing yes

# Enable active defragmentation (Redis 4.0+)
activedefrag yes
active-defrag-ignore-bytes 100mb
active-defrag-threshold-lower 10
active-defrag-threshold-upper 100
active-defrag-cycle-min 1
active-defrag-cycle-max 25

# Enable memory usage tracking
memory-tracking no
EOF
    
    log "Redis configuration updated."
}

# Create Redis directories and set permissions
setup_directories() {
    log "Setting up Redis directories and permissions..."
    
    # Create directories
    sudo mkdir -p /var/run/redis
    sudo mkdir -p /var/log/redis
    sudo mkdir -p /var/lib/redis
    
    # Set ownership and permissions
    sudo chown redis:redis /var/run/redis
    sudo chown redis:redis /var/log/redis
    sudo chown redis:redis /var/lib/redis
    sudo chmod 755 /var/run/redis
    sudo chmod 755 /var/log/redis
    sudo chmod 755 /var/lib/redis
    
    log "Redis directories configured."
}

# Configure Redis systemd service
configure_service() {
    log "Configuring Redis systemd service..."
    
    # Create systemd service override
    sudo mkdir -p /etc/systemd/system/redis-server.service.d
    
    sudo tee /etc/systemd/system/redis-server.service.d/override.conf > /dev/null << 'EOF'
[Service]
ExecStartPost=/bin/run-parts --verbose /etc/redis/redis-server.post-up.d
ExecStop=/bin/run-parts --verbose /etc/redis/redis-server.pre-down.d
ExecStopPost=/bin/run-parts --verbose /etc/redis/redis-server.post-down.d
Restart=always
RestartSec=3
EOF
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    log "Redis service configured."
}

# Start and enable Redis
start_redis() {
    log "Starting Redis service..."
    
    # Start Redis
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    # Check status
    if sudo systemctl is-active --quiet redis-server; then
        log "Redis service started successfully."
    else
        error "Failed to start Redis service."
        sudo systemctl status redis-server
        exit 1
    fi
}

# Test Redis connection
test_redis() {
    log "Testing Redis connection..."
    
    # Test connection
    if redis-cli ping | grep -q PONG; then
        log "Redis connection test successful."
    else
        error "Redis connection test failed."
        exit 1
    fi
    
    # Test authentication (if password is set)
    if [ -n "$REDIS_PASSWORD" ]; then
        if redis-cli -a "$REDIS_PASSWORD" ping | grep -q PONG; then
            log "Redis authentication test successful."
        else
            error "Redis authentication test failed."
            exit 1
        fi
    fi
}

# Configure firewall for Redis
configure_firewall() {
    log "Configuring firewall for Redis..."
    
    # Allow Redis port only from localhost
    sudo ufw allow from 127.0.0.1 to any port 6379
    sudo ufw allow from ::1 to any port 6379
    
    log "Firewall configured for Redis."
}

# Create Redis monitoring script
create_monitoring_script() {
    log "Creating Redis monitoring script..."
    
    sudo tee /usr/local/bin/redis-monitor.sh > /dev/null << 'EOF'
#!/bin/bash

# Redis Monitoring Script
LOG_FILE="/var/log/redis-monitor.log"
EMAIL="admin@yourdomain.com"

# Function to log messages
log_message() {
    echo "$(date): $1" >> $LOG_FILE
}

# Check Redis status
if ! systemctl is-active --quiet redis-server; then
    log_message "ERROR: Redis service is not running"
    systemctl restart redis-server
    sleep 5
    if systemctl is-active --quiet redis-server; then
        log_message "Redis service restarted successfully"
    else
        log_message "ERROR: Failed to restart Redis service"
        echo "Redis service failed to restart" | mail -s "Redis Alert" $EMAIL
    fi
fi

# Check Redis connection
if ! redis-cli ping | grep -q PONG; then
    log_message "ERROR: Redis connection failed"
    echo "Redis connection failed" | mail -s "Redis Alert" $EMAIL
fi

# Check memory usage
MEMORY_USAGE=$(redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
log_message "Redis memory usage: $MEMORY_USAGE"

# Check key count
KEY_COUNT=$(redis-cli dbsize)
log_message "Redis key count: $KEY_COUNT"

# Check Redis performance
SLOW_LOG_COUNT=$(redis-cli slowlog len)
if [ $SLOW_LOG_COUNT -gt 10 ]; then
    log_message "WARNING: High number of slow queries: $SLOW_LOG_COUNT"
fi
EOF
    
    sudo chmod +x /usr/local/bin/redis-monitor.sh
    
    # Add to crontab
    sudo crontab -l | { cat; echo "*/10 * * * * /usr/local/bin/redis-monitor.sh"; } | sudo crontab -
    
    log "Redis monitoring script created."
}

# Create Redis backup script
create_backup_script() {
    log "Creating Redis backup script..."
    
    sudo tee /usr/local/bin/redis-backup.sh > /dev/null << 'EOF'
#!/bin/bash

# Redis Backup Script
BACKUP_DIR="/var/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/redis_backup_$DATE.rdb"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create backup
redis-cli BGSAVE
sleep 5

# Copy RDB file
if [ -f /var/lib/redis/dump.rdb ]; then
    cp /var/lib/redis/dump.rdb "$BACKUP_FILE"
    gzip "$BACKUP_FILE"
    
    # Keep only last 7 days
    find $BACKUP_DIR -name "*.rdb.gz" -mtime +7 -delete
    
    echo "$(date): Redis backup created: ${BACKUP_FILE}.gz" >> /var/log/redis-backup.log
else
    echo "$(date): ERROR - Redis RDB file not found" >> /var/log/redis-backup.log
fi
EOF
    
    sudo chmod +x /usr/local/bin/redis-backup.sh
    
    # Add to crontab
    sudo crontab -l | { cat; echo "0 2 * * * /usr/local/bin/redis-backup.sh"; } | sudo crontab -
    
    log "Redis backup script created."
}

# Display configuration summary
display_summary() {
    log "Redis setup completed successfully!"
    info "Configuration Summary:"
    info "1. Redis listening on localhost:6379"
    info "2. Password authentication enabled"
    info "3. Memory limit: 256MB with LRU eviction"
    info "4. AOF persistence enabled"
    info "5. Monitoring and backup scripts installed"
    info "6. Firewall configured for localhost access only"
    warn "IMPORTANT: Remember to:"
    warn "1. Change the Redis password in /etc/redis/redis.conf"
    warn "2. Update the password in your Django .env file"
    warn "3. Test the Redis connection with your application"
    warn "4. Monitor Redis performance and memory usage"
}

# Main execution
main() {
    log "Starting Redis setup for Factory InfoHub..."
    
    check_root
    install_redis
    configure_redis
    setup_directories
    configure_service
    start_redis
    test_redis
    configure_firewall
    create_monitoring_script
    create_backup_script
    display_summary
}

# Run main function
main "$@"