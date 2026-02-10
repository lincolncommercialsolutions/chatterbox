#!/usr/bin/env python3
import subprocess
import os
import shutil

os.chdir('/home/linkl0n/chatterbox')

# Get remote URL
try:
    result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                          capture_output=True, text=True, check=True)
    remote_url = result.stdout.strip()
    print(f"Saved remote URL: {remote_url}")
except:
    remote_url = "https://github.com/lincolncommercialsolutions/chatterbox.git"
    print(f"Using default remote URL: {remote_url}")

# Remove .git directory
if os.path.exists('.git'):
    shutil.rmtree('.git')
    print("Removed old .git directory")

# Initialize new repo
subprocess.run(['git', 'init'], check=True)
print("Initialized new git repository")

subprocess.run(['git', 'add', '.'], check=True)
print("Added all files")

subprocess.run(['git', 'commit', '-m', 'Initial commit - clean history without credentials'], check=True)
print("Created initial commit")

subprocess.run(['git', 'branch', '-M', 'main'], check=True)
print("Renamed branch to main")

# Add remote
subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
print(f"Added remote: {remote_url}")

print("\n✅ Git repository reset successfully!")
print("Next step: git push -f origin main")
