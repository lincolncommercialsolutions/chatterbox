#!/usr/bin/env python3
import subprocess
import os
import shutil

os.chdir('/home/linkl0n/chatterbox')

# Get remote URL first
try:
    result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                          capture_output=True, text=True, timeout=5)
    remote_url = result.stdout.strip()
    print(f"Remote URL: {remote_url}")
except:
    remote_url = "https://github.com/lincolncommercialsolutions/chatterbox.git"
    print(f"Using default remote URL: {remote_url}")

# Remove .git directory
print("Removing .git directory...")
if os.path.exists('.git'):
    shutil.rmtree('.git')
    print("✓ .git removed")

# Initialize new repo
print("Initializing new repository...")
subprocess.run(['git', 'init'], check=True)
print("✓ Git initialized")

# Add all files
print("Adding files...")
subprocess.run(['git', 'add', '.'], check=True)
print("✓ Files added")

# Commit
print("Creating initial commit...")
subprocess.run(['git', 'commit', '-m', 'Initial commit - clean history'], check=True)
print("✓ Commit created")

# Rename branch
print("Renaming branch to main...")
subprocess.run(['git', 'branch', '-M', 'main'], check=True)
print("✓ Branch renamed")

# Add remote
print("Adding remote...")
subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
print("✓ Remote added")

# Push with force
print("Pushing to GitHub...")
result = subprocess.run(['git', 'push', '-f', 'origin', 'main'], 
                       capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print(result.stderr)

if result.returncode == 0:
    print("\n✅ Successfully pushed to GitHub!")
    print(f"Repository: {remote_url}")
else:
    print(f"\n❌ Push failed with code {result.returncode}")
    print("You may need to authenticate with GitHub")
