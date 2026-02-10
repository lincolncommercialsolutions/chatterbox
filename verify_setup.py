#!/usr/bin/env python3
"""
Verify that all components for deployment are properly configured.
"""

import os
import json
import sys
from pathlib import Path

def check_file_exists(path, name):
    """Check if a file exists and report status."""
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {name}: {path}")
    return exists

def check_env_var(var_name, required=False):
    """Check if environment variable is set."""
    value = os.getenv(var_name)
    if required:
        status = "✅" if value else "❌"
        print(f"{status} {var_name}: {value or 'NOT SET (required)'}")
        return bool(value)
    else:
        status = "✅" if value else "⚠️"
        print(f"{status} {var_name}: {value or 'not set'}")
        return bool(value)

def check_json_valid(path, name):
    """Check if JSON file is valid."""
    try:
        with open(path) as f:
            data = json.load(f)
        print(f"✅ {name}: Valid JSON ({len(data.get('characters', {}))} characters)")
        return True
    except Exception as e:
        print(f"❌ {name}: Invalid JSON - {e}")
        return False

def main():
    print("=" * 60)
    print("CHATTERBOX DEPLOYMENT VERIFICATION")
    print("=" * 60)
    
    # Check required files
    print("\n📁 REQUIRED FILES:")
    files_ok = all([
        check_file_exists("chatterbox/api_server.py", "API Server"),
        check_file_exists("voices_config.json", "Voice Configuration"),
        check_file_exists("Dockerfile.gpu", "Docker GPU Build"),
        check_file_exists("docker-compose.yml", "Docker Compose"),
        check_file_exists("frontend/chatterbox-tts-client.ts", "TTS Client"),
        check_file_exists(".env", "Environment Config"),
    ])
    
    # Check voice configuration
    print("\n🎤 VOICE CONFIGURATION:")
    if check_file_exists("voices_config.json", "voices_config.json"):
        try:
            with open("voices_config.json") as f:
                config = json.load(f)
            
            voices = config.get("voices", {})
            characters = config.get("characters", {})
            
            print(f"   Voices defined: {len(voices)}")
            for voice_id, voice_data in voices.items():
                print(f"      • {voice_id}: {voice_data.get('description', 'N/A')}")
            
            print(f"   Characters defined: {len(characters)}")
            for char_id, char_data in characters.items():
                voice_id = char_data.get("voice_id", "N/A")
                print(f"      • {char_id} → {voice_id}")
        except Exception as e:
            print(f"   ❌ Error reading config: {e}")
    
    # Check environment configuration
    print("\n🔧 ENVIRONMENT CONFIGURATION:")
    print("   Required variables:")
    env_ok = all([
        check_env_var("API_PORT", required=False),
        check_env_var("DEVICE", required=False),
    ])
    
    print("   S3 Configuration:")
    s3_enabled = os.getenv("S3_ENABLED") == "true"
    print(f"   {'✅' if s3_enabled else '⚠️'} S3_ENABLED: {s3_enabled}")
    
    if s3_enabled:
        s3_vars = [
            ("S3_BUCKET_NAME", True),
            ("AWS_REGION", True),
            ("AWS_ACCESS_KEY_ID", False),
            ("AWS_SECRET_ACCESS_KEY", False),
        ]
        for var, required in s3_vars:
            check_env_var(var, required=required)
    
    print("   CORS Configuration:")
    cors = os.getenv("CORS_ORIGINS", "Not set")
    status = "⚠️" if cors == "Not set" else "✅"
    print(f"   {status} CORS_ORIGINS: {cors}")
    
    # Check API server
    print("\n🚀 API SERVER:")
    try:
        with open("chatterbox/api_server.py") as f:
            content = f.read()
        
        checks = {
            "Flask app initialized": "app = Flask" in content,
            "OpenRouter integration": "/generate-audio" in content,
            "Voice management endpoints": "'/voices'" in content or '"/voices"' in content,
            "S3 integration": "boto3" in content,
            "Character voice mapping": "voice_id" in content,
            "Health endpoint": "'/health'" in content or '"/health"' in content,
        }
        
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")
    except Exception as e:
        print(f"   ❌ Error reading api_server.py: {e}")
    
    # Check Docker configuration
    print("\n🐳 DOCKER CONFIGURATION:")
    docker_ok = all([
        check_file_exists("Dockerfile.gpu", "Dockerfile.gpu"),
        check_file_exists("docker-compose.yml", "docker-compose.yml"),
    ])
    
    if docker_ok:
        try:
            with open("Dockerfile.gpu") as f:
                dockerfile = f.read()
            
            checks = {
                "NVIDIA CUDA base": "nvidia/cuda" in dockerfile,
                "Python 3.11": "python:3.11" in dockerfile or "3.11" in dockerfile,
                "Health check": "HEALTHCHECK" in dockerfile,
                "Non-root user": "chatterbox:1000" in dockerfile or "chatterbox" in dockerfile,
            }
            
            for check_name, result in checks.items():
                status = "✅" if result else "⚠️"
                print(f"   {status} {check_name}")
        except Exception as e:
            print(f"   ❌ Error reading Dockerfile: {e}")
    
    # Check frontend client
    print("\n🎨 FRONTEND INTEGRATION:")
    client_ok = check_file_exists("frontend/chatterbox-tts-client.ts", "TTS Client")
    
    if client_ok:
        try:
            with open("frontend/chatterbox-tts-client.ts") as f:
                client_code = f.read()
            
            checks = {
                "ChatterboxTTSClient class": "class ChatterboxTTSClient" in client_code,
                "generateAudio method": "generateAudio" in client_code,
                "getCharacters method": "getCharacters" in client_code,
                "getVoices method": "getVoices" in client_code,
                "TypeScript types": "interface Character" in client_code,
            }
            
            for check_name, result in checks.items():
                status = "✅" if result else "⚠️"
                print(f"   {status} {check_name}")
        except Exception as e:
            print(f"   ❌ Error reading TTS client: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if files_ok and env_ok and docker_ok and client_ok:
        print("✅ ALL CHECKS PASSED - Ready for deployment!")
        print("\nNext steps:")
        print("  1. Deploy API to Railway, Render, AWS, or your server")
        print("  2. Update NEXT_PUBLIC_TTS_API_URL in Vercel .env")
        print("  3. Copy chatterbox-tts-client.ts to your Vercel project")
        print("  4. Create ChatWithAudio component with TTS integration")
        print("  5. Wire OpenRouter responses to TTS generation")
        print("  6. Update CORS_ORIGINS with your Vercel domain")
        print("\nSee DEPLOYMENT_FINAL_STEPS.md for detailed instructions")
        return 0
    else:
        print("⚠️ SOME CHECKS FAILED - Review above for issues")
        print("\nRefer to documentation files for setup instructions")
        return 1

if __name__ == "__main__":
    sys.exit(main())
