#!/bin/bash
echo "🧹 Cleaning git cache for ignored files..."

# Remove all __pycache__ from git tracking
echo "Removing Python cache files..."
git rm -r --cached backend/**/__pycache__/ 2>/dev/null || true
find backend -type d -name __pycache__ -exec git rm -r --cached {} + 2>/dev/null || true

# Remove node_modules if it was tracked (it was deleted so just update index)
echo "Updating git index for deleted node_modules..."
git add -u frontend/node_modules/ 2>/dev/null || true

# Remove any .pyc files
echo "Removing .pyc files..."
find backend -name "*.pyc" -exec git rm --cached {} + 2>/dev/null || true

echo "✅ Git cache cleaned!"
echo "Run 'git status' to verify"
