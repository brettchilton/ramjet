#!/bin/bash
# Start production environment (with Kratos)
echo "🚀 Starting production environment with Kratos..."
docker-compose --profile production up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:5179"
echo "   Backend:   http://localhost:8006"
echo "   API Docs:  http://localhost:8006/docs"
echo "   Adminer:   http://localhost:8085"
echo "   Kratos:    http://localhost:4433"
echo ""
echo "🔐 Using Kratos Auth - register at /auth/registration"
