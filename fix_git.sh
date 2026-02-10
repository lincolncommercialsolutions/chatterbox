#!/bin/bash
cd /home/linkl0n/chatterbox

# Save current remote
REMOTE_URL=$(git remote get-url origin 2>/dev/null)

# Remove git directory and start fresh
rm -rf .git

# Initialize new repo
git init
git add .
git commit -m "Initial commit - clean history without credentials"
git branch -M main

# Re-add remote
if [ -n "$REMOTE_URL" ]; then
    git remote add origin "$REMOTE_URL"
fi

echo "Git repository has been reset with clean history"
echo "Remote: $REMOTE_URL"
