#!/bin/bash
set -e

cd /home/linkl0n/chatterbox

# Kill any ongoing git operations
rm -f .git/index.lock
rm -f .git/REBASE_HEAD
rm -rf .git/rebase-merge
rm -rf .git/rebase-apply

# Get the remote URL before cleanup
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "")

# Remove .git directory completely
rm -rf .git

# Start fresh
git init
git add .
git commit -m "Initial commit - clean history without credentials"
git branch -M main

# Re-add remote if it existed
if [ -n "$REMOTE_URL" ]; then
    git remote add origin "$REMOTE_URL"
    echo "Remote added: $REMOTE_URL"
fi

# Push with force to overwrite history
echo "Pushing to GitHub with force..."
git push -f origin main

echo ""
echo "✅ Successfully pushed to GitHub with clean history!"
echo "Repository: $REMOTE_URL"
