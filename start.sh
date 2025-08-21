#!/bin/bash

# Start Alex Orator Bot Docker services
# Linux/Mac script

echo "🚀 Starting Alex Orator Bot Docker services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: docker-compose is not available."
    exit 1
fi

echo ""
echo "🔧 Starting services..."
echo ""

# Start PostgreSQL
echo "🐘 Starting PostgreSQL..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check PostgreSQL status
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "❌ Error: PostgreSQL failed to start."
    echo "📋 Checking logs..."
    docker-compose logs postgres
    exit 1
fi

echo "✅ PostgreSQL is running."

# Start Redis (optional)
echo "🔴 Starting Redis..."
docker-compose up -d redis

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
sleep 5

# Check Redis status
if ! docker-compose ps redis | grep -q "Up"; then
    echo "⚠️  Warning: Redis failed to start. Continuing without Redis..."
else
    echo "✅ Redis is running."
fi

echo ""
echo "🎉 All services started successfully!"
echo ""

# Show services status
echo "📊 Services status:"
docker-compose ps

echo ""
echo "🌐 Service URLs:"
echo "   PostgreSQL: localhost:5434"
echo "   Redis: localhost:6379"
echo ""

echo "💡 You can now start the admin panel with:"
echo "   streamlit run admin_panel/admin_app.py"
echo ""

echo "✨ Setup complete! Happy coding!" 