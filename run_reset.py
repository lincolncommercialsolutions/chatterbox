#!/usr/bin/env python3
import subprocess
import sys

script_path = '/home/linkl0n/chatterbox/reset_and_push.sh'

# Make script executable
subprocess.run(['chmod', '+x', script_path], check=True)

# Run the script
result = subprocess.run(['bash', script_path], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

sys.exit(result.returncode)
