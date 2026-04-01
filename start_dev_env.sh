#!/bin/bash

# FactoryInfoHub Development Environment Setup Script
# This script activates the virtual environment and sets up email configuration

echo "🚀 Starting FactoryInfoHub Development Environment Setup..."

# Check if virtual environment exists
if [ ! -d "/Users/arfatulshaikh/Projects/InfoHub/EnvInfoHub" ]; then
    echo "❌ Virtual environment not found at /Users/arfatulshaikh/Projects/InfoHub/EnvInfoHub"
    echo "Please create the virtual environment first:"
    echo "  python -m venv /Users/arfatulshaikh/Projects/InfoHub/EnvInfoHub"
    echo "  source /Users/arfatulshaikh/Projects/InfoHub/EnvInfoHub/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate the virtual environment
echo "📦 Activating virtual environment..."
source /Users/arfatulshaikh/Projects/InfoHub/EnvInfoHub/bin/activate

# Check if django-redis is installed
if ! python -c "import django_redis" 2>/dev/null; then
    echo "📦 Installing django-redis for cache support..."
    pip install django-redis
fi

# Set environment variables
export EMAIL_HOST_USER="arfatur.shaikh@gmail.com"
export EMAIL_HOST_PASSWORD="lyfq xmir oiul voqe"
export DEBUG=True
export ALLOWED_HOSTS="localhost,127.0.0.1,*"
export SECRET_KEY="django-insecure-development-key-not-for-production-use-this-is-very-weak-and-should-be-changed"

# Verify environment variables are set
echo "📋 Environment variables set:"
echo "  EMAIL_HOST_USER: $EMAIL_HOST_USER"
echo "  EMAIL_HOST_PASSWORD: [HIDDEN]"
echo "  DEBUG: $DEBUG"
echo "  ALLOWED_HOSTS: $ALLOWED_HOSTS"

# Check if Redis is running (optional for development)
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is not running. Starting Redis server..."
        if command -v redis-server >/dev/null 2>&1; then
            redis-server --daemonize yes
            sleep 2
            if redis-cli ping >/dev/null 2>&1; then
                echo "✅ Redis server started successfully"
            else
                echo "❌ Failed to start Redis server"
                echo "⚠️  Continuing without Redis cache (will use database cache fallback)"
            fi
        else
            echo "⚠️  redis-server command not found. Please install Redis if you want to use Redis cache."
            echo "⚠️  Continuing without Redis cache (will use database cache fallback)"
        fi
    fi
else
    echo "⚠️  Redis CLI not found. Please install Redis if you want to use Redis cache."
    echo "⚠️  Continuing without Redis cache (will use database cache fallback)"
fi

# Run database migrations
echo "🗄️  Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: username=admin, password=admin123')
else:
    print('Superuser already exists')
"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "  - Run 'python manage.py runserver 8001' to start the development server"
echo "  - Visit http://localhost:8001 to access the application"
echo "  - Visit http://localhost:8001/admin to access the admin panel"
echo "    (username: admin, password: admin123)"
echo ""
echo "🔧 Environment details:"
echo "  - Server will run on: http://localhost:8001"
echo "  - Database: SQLite (db.sqlite3)"
echo "  - Cache: Redis (if available) or fallback to database cache"
echo "  - Email backend: Console (emails will be printed to terminal)"
echo ""
echo "🚀 Starting development server..."

# Start the development server
python manage.py runserver 0.0.0.0:8001
