#!/bin/bash
#
# FactoryInfoHub Deployment Update Script
# This script updates the code on the production server from GitHub.
#
# Usage:
#   ./deploy_update.sh
#
# Or with a specific branch:
#   ./deploy_update.sh develop
#

set -e  # Exit on any error

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/var/www/FactoryInfoHub}"
BRANCH="${1:-main}"
VENV_DIR="${PROJECT_DIR}/venv"
LOG_FILE="${PROJECT_DIR}/logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "FactoryInfoHub Deployment Update"
echo "========================================"
echo "Project Directory: ${PROJECT_DIR}"
echo "Branch: ${BRANCH}"
echo "Log File: ${LOG_FILE}"
echo "========================================"

# Function to log and print
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    log "${RED}Error: Project directory ${PROJECT_DIR} does not exist${NC}"
    exit 1
fi

# Navigate to project directory
cd "$PROJECT_DIR"

# Create logs directory if it doesn't exist
mkdir -p "${PROJECT_DIR}/logs"

log "\n${YELLOW}[1/6] Pulling latest changes from GitHub...${NC}"
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"
log "${GREEN}✓ Code updated successfully${NC}"

log "\n${YELLOW}[2/6] Checking for new dependencies...${NC}"
if [ -f "requirements-production.txt" ]; then
    source "${VENV_DIR}/bin/activate"
    pip install -r requirements-production.txt --upgrade
    deactivate
    log "${GREEN}✓ Dependencies checked${NC}"
else
    log "${YELLOW}⚠ requirements-production.txt not found, skipping pip install${NC}"
fi

log "\n${YELLOW}[3/6] Running database migrations...${NC}"
"${VENV_DIR}/bin/python" manage.py migrate --no-input
log "${GREEN}✓ Migrations completed${NC}"

log "\n${YELLOW}[4/6] Collecting static files...${NC}"
"${VENV_DIR}/bin/python" manage.py collectstatic --no-input
log "${GREEN}✓ Static files collected${NC}"

log "\n${YELLOW}[5/6] Restarting Gunicorn service...${NC}"
if systemctl is-active --quiet gunicorn; then
    systemctl restart gunicorn
    log "${GREEN}✓ Gunicorn restarted${NC}"
else
    log "${YELLOW}⚠ Gunicorn service not found or not running${NC}"
fi

log "\n${YELLOW}[6/6] Clearing cache (if Redis is running)...${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        redis-cli flushdb || true
        log "${GREEN}✓ Redis cache cleared${NC}"
    else
        log "${YELLOW}⚠ Redis not running, skipping cache clear${NC}"
    fi
else
    log "${YELLOW}⚠ redis-cli not found, skipping cache clear${NC}"
fi

log "\n========================================"
log "${GREEN}Deployment completed successfully!${NC}"
log "========================================"
log "\nNext steps:"
log "1. Check the application: https://your-domain.com"
log "2. Review logs: tail -f ${LOG_FILE}"
log "3. If you need to create dummy data:"
log "   ${VENV_DIR}/bin/python scripts/create_dummy_data.py"
log "\n========================================"