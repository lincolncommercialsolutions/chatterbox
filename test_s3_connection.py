#!/usr/bin/env python3
"""
Test S3 connection with configured AWS credentials
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_s3_connection():
    """Test AWS S3 connection and list buckets"""
    
    # Get AWS credentials from environment
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    print("=" * 60)
    print("S3 Connection Test")
    print("=" * 60)
    print(f"Region: {region}")
    print(f"Bucket: {bucket_name}")
    print(f"Access Key ID: {access_key[:10]}..." if access_key else "Not set")
    print()
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            's3',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        
        print("✓ S3 Client created successfully")
        print()
        
        # Test 1: List all buckets
        print("Test 1: Listing S3 Buckets...")
        response = s3_client.list_buckets()
        buckets = response.get('Buckets', [])
        
        if buckets:
            print(f"Found {len(buckets)} bucket(s):")
            for bucket in buckets:
                print(f"  - {bucket['Name']} (created: {bucket['CreationDate']})")
        else:
            print("No buckets found")
        
        print()
        
        # Test 2: Check if target bucket exists
        if bucket_name:
            print(f"Test 2: Checking if bucket '{bucket_name}' exists...")
            try:
                s3_client.head_bucket(Bucket=bucket_name)
                print(f"✓ Bucket '{bucket_name}' exists and is accessible")
                
                # List objects in bucket
                print(f"\n  Listing objects in '{bucket_name}':")
                response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
                
                if 'Contents' in response:
                    print(f"  Found {len(response['Contents'])} object(s):")
                    for obj in response['Contents'][:10]:
                        print(f"    - {obj['Key']} ({obj['Size']} bytes)")
                    if response.get('IsTruncated'):
                        print(f"    ... and more")
                else:
                    print(f"  Bucket is empty")
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    print(f"✗ Bucket '{bucket_name}' does not exist")
                elif error_code == '403':
                    print(f"✗ Access denied to bucket '{bucket_name}'")
                else:
                    print(f"✗ Error: {e}")
        
        print()
        print("=" * 60)
        print("✓ S3 Connection Test Passed!")
        print("=" * 60)
        
        return True
        
    except NoCredentialsError:
        print("✗ AWS credentials not found!")
        print("Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set")
        return False
        
    except ClientError as e:
        print(f"✗ AWS Client Error: {e}")
        return False
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_s3_connection()
    sys.exit(0 if success else 1)
