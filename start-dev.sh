#!/bin/bash
# Start development environment (Simple Auth - no Kratos)
echo "🚀 Starting development environment with Simple Auth..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access points:"
echo "   Frontend:  http://localhost:5179"
echo "   Backend:   http://localhost:8006"
echo "   API Docs:  http://localhost:8006/docs"
echo "   Adminer:   http://localhost:8085"
echo ""
echo "🔐 Using Simple Auth (JWT) - register at /simple-register"
