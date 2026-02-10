#!/usr/bin/env python3
"""
Configuration validation script for Chatterbox TTS
Verifies all settings are properly configured for S3 deployment
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    """Print formatted header."""
    print(f"\n{BLUE}{BOLD}{text}{RESET}")
    print("-" * 70)

def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    """Print error message."""
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text):
    """Print info message."""
    print(f"{BLUE}ℹ{RESET} {text}")

def validate_config():
    """Validate all configuration settings."""
    load_dotenv()
    
    errors = []
    warnings = []
    successes = []
    
    print_header("Chatterbox TTS - Configuration Validation")
    
    # 1. Check environment file
    print_header("1. Environment Configuration")
    
    if Path(".env").exists():
        print_success(".env file found")
    else:
        print_error(".env file not found")
        errors.append(".env file missing")
    
    # 2. Check Python environment
    print_header("2. Python Environment")
    
    try:
        import torch
        print_success(f"PyTorch installed (version {torch.__version__})")
    except ImportError:
        errors.append("PyTorch not installed")
        print_error("PyTorch not installed")
    
    try:
        import flask
        print_success(f"Flask installed (version {flask.__version__})")
    except ImportError:
        errors.append("Flask not installed")
        print_error("Flask not installed")
    
    try:
        import boto3
        print_success(f"boto3 installed (version {boto3.__version__})")
    except ImportError:
        errors.append("boto3 not installed")
        print_error("boto3 not installed")
    
    # 3. Check AWS credentials
    print_header("3. AWS Credentials")
    
    aws_key = os.getenv('AWS_ACCESS_KEY_ID', '').strip()
    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY', '').strip()
    
    if aws_key and aws_key != 'your_access_key_id':
        print_success("AWS_ACCESS_KEY_ID configured")
        successes.append("AWS credentials configured")
    else:
        print_error("AWS_ACCESS_KEY_ID not configured or empty")
        errors.append("AWS credentials missing")
    
    if aws_secret and aws_secret != 'your_secret_access_key':
        print_success("AWS_SECRET_ACCESS_KEY configured")
    else:
        print_error("AWS_SECRET_ACCESS_KEY not configured or empty")
        errors.append("AWS secret key missing")
    
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    print_success(f"AWS_REGION set to {aws_region}")
    
    # 4. Check S3 configuration
    print_header("4. S3 Configuration")
    
    s3_enabled = os.getenv('S3_ENABLED', 'false').lower() == 'true'
    print_success(f"S3_ENABLED: {s3_enabled}")
    
    s3_bucket = os.getenv('S3_BUCKET_NAME', '').strip()
    if s3_bucket and s3_bucket != 'your-bucket-name':
        print_success(f"S3_BUCKET_NAME: {s3_bucket}")
    else:
        print_warning("S3_BUCKET_NAME not configured")
        warnings.append("S3 bucket name not configured")
    
    s3_audio_prefix = os.getenv('S3_AUDIO_PREFIX', 'chatterbox/audio/')
    print_info(f"S3_AUDIO_PREFIX: {s3_audio_prefix}")
    
    s3_presigned_expiry = os.getenv('S3_PRESIGNED_URL_EXPIRY', '3600')
    print_info(f"S3_PRESIGNED_URL_EXPIRY: {s3_presigned_expiry}s")
    
    # 5. Test S3 connection
    if s3_enabled and aws_key and aws_secret:
        print_header("5. S3 Connection Test")
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            s3_client = boto3.client(
                's3',
                region_name=aws_region,
                aws_access_key_id=aws_key,
                aws_secret_access_key=aws_secret
            )
            
            # List buckets
            response = s3_client.list_buckets()
            bucket_count = len(response.get('Buckets', []))
            print_success(f"S3 connection successful - Found {bucket_count} bucket(s)")
            
            # Check if target bucket exists
            if s3_bucket:
                try:
                    s3_client.head_bucket(Bucket=s3_bucket)
                    print_success(f"Target bucket '{s3_bucket}' exists and is accessible")
                    successes.append("S3 bucket accessible")
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == '404':
                        print_warning(f"Target bucket '{s3_bucket}' does not exist")
                        warnings.append(f"Bucket '{s3_bucket}' doesn't exist")
                        print_info("Run: python s3_manager.py create-bucket")
                    elif error_code == '403':
                        print_error(f"Access denied to bucket '{s3_bucket}'")
                        errors.append("S3 bucket access denied")
                    else:
                        print_error(f"Error checking bucket: {e}")
                        errors.append(f"S3 error: {error_code}")
        except NoCredentialsError:
            print_error("AWS credentials not found")
            errors.append("AWS credentials invalid")
        except Exception as e:
            print_error(f"S3 connection test failed: {e}")
            errors.append(f"S3 test error: {str(e)}")
    else:
        print_warning("S3 connection test skipped (S3 not enabled or credentials missing)")
    
    # 6. Check API configuration
    print_header("6. API Configuration")
    
    api_port = os.getenv('API_PORT', '5000')
    print_info(f"API_PORT: {api_port}")
    
    api_host = os.getenv('API_HOST', '0.0.0.0')
    print_info(f"API_HOST: {api_host}")
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    print_info(f"LOG_LEVEL: {log_level}")
    
    max_text_length = os.getenv('MAX_TEXT_LENGTH', '500')
    print_info(f"MAX_TEXT_LENGTH: {max_text_length}")
    
    cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    print_success(f"Cache: {'Enabled' if cache_enabled else 'Disabled'}")
    
    # 7. Check character configuration
    print_header("7. Character Configuration")
    
    config_file = os.getenv('CHARACTER_CONFIG_FILE', 'character_voices.json')
    
    if Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            voices = config.get('voices', {})
            characters = config.get('characters', {})
            
            print_success(f"Character config loaded")
            print_info(f"  - Voices: {len(voices)}")
            for voice_id in list(voices.keys())[:3]:
                print_info(f"    • {voice_id}")
            if len(voices) > 3:
                print_info(f"    ... and {len(voices) - 3} more")
            
            print_info(f"  - Characters: {len(characters)}")
            for char_id in list(characters.keys())[:3]:
                print_info(f"    • {char_id}")
            if len(characters) > 3:
                print_info(f"    ... and {len(characters) - 3} more")
            
            successes.append("Character configuration valid")
            
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON in {config_file}: {e}")
            errors.append("Character config invalid JSON")
        except Exception as e:
            print_error(f"Error reading {config_file}: {e}")
            errors.append("Character config read error")
    else:
        print_error(f"{config_file} not found")
        errors.append("Character configuration file missing")
    
    # 8. Check CORS configuration
    print_header("8. CORS Configuration")
    
    cors_origins = os.getenv('CORS_ORIGINS', '*')
    origins_list = [o.strip() for o in cors_origins.split(',')]
    print_info(f"Allowed origins ({len(origins_list)}):")
    for origin in origins_list[:5]:
        print_info(f"  • {origin}")
    if len(origins_list) > 5:
        print_info(f"  ... and {len(origins_list) - 5} more")
    
    # 9. Check character defaults
    print_header("9. Default Character")
    
    default_char = os.getenv('DEFAULT_CHARACTER', 'assistant')
    print_info(f"DEFAULT_CHARACTER: {default_char}")
    
    if Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                characters = config.get('characters', {})
                if default_char in characters:
                    print_success(f"Default character '{default_char}' exists in config")
                else:
                    print_warning(f"Default character '{default_char}' not found in config")
                    warnings.append(f"Default character not found in config")
        except:
            pass
    
    # Summary
    print_header("Configuration Summary")
    
    print(f"\n{BOLD}Checks:{RESET}")
    print(f"  {GREEN}✓ Passed: {len(successes)}{RESET}")
    print(f"  {YELLOW}⚠ Warnings: {len(warnings)}{RESET}")
    print(f"  {RED}✗ Errors: {len(errors)}{RESET}")
    
    if errors:
        print(f"\n{BOLD}{RED}Errors to fix:{RESET}")
        for error in errors:
            print(f"  {RED}✗{RESET} {error}")
    
    if warnings:
        print(f"\n{BOLD}{YELLOW}Warnings:{RESET}")
        for warning in warnings:
            print(f"  {YELLOW}⚠{RESET} {warning}")
    
    print()
    
    if not errors:
        print(f"{GREEN}{BOLD}✓ Configuration is valid!{RESET}")
        print(f"\nReady to start the API server:")
        print(f"  python chatterbox/api_server.py")
        return True
    else:
        print(f"{RED}{BOLD}✗ Please fix the errors above{RESET}")
        return False

if __name__ == "__main__":
    success = validate_config()
    sys.exit(0 if success else 1)
