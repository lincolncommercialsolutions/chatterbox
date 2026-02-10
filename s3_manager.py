#!/usr/bin/env python3
"""
S3 Manager for Chatterbox TTS
Handles S3 bucket creation, file uploads, and audio file management
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import boto3
from botocore.exceptions import ClientError

load_dotenv()

class S3Manager:
    """Manage S3 operations for Chatterbox"""
    
    def __init__(self):
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.audio_prefix = os.getenv('S3_AUDIO_PREFIX', 'chatterbox/audio/')
        self.voices_prefix = os.getenv('S3_VOICES_PREFIX', 'chatterbox/voices/')
        
        self.s3_client = boto3.client(
            's3',
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
    
    def create_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✓ Bucket '{self.bucket_name}' already exists")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"Creating bucket '{self.bucket_name}' in {self.region}...")
                try:
                    if self.region == 'us-east-1':
                        self.s3_client.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3_client.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    print(f"✓ Bucket '{self.bucket_name}' created successfully")
                    
                    # Enable versioning
                    self.s3_client.put_bucket_versioning(
                        Bucket=self.bucket_name,
                        VersioningConfiguration={'Status': 'Enabled'}
                    )
                    print(f"✓ Versioning enabled for bucket")
                    
                    return True
                except Exception as e:
                    print(f"✗ Failed to create bucket: {e}")
                    return False
            else:
                print(f"✗ Error checking bucket: {e}")
                return False
    
    def upload_audio(self, file_path: str, s3_key: str = None):
        """Upload audio file to S3"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"✗ File not found: {file_path}")
            return False
        
        if s3_key is None:
            s3_key = f"{self.audio_prefix}{file_path.name}"
        
        try:
            file_size = file_path.stat().st_size
            print(f"Uploading {file_path.name} ({file_size / 1024:.1f} KB) to S3...")
            
            self.s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'audio/mpeg' if file_path.suffix == '.mp3' else 'audio/wav',
                    'Metadata': {'source': 'chatterbox-tts'}
                }
            )
            
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            print(f"✓ Uploaded to: {url}")
            return url
            
        except Exception as e:
            print(f"✗ Upload failed: {e}")
            return False
    
    def list_audio_files(self, prefix: str = None):
        """List audio files in S3"""
        prefix = prefix or self.audio_prefix
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                print(f"No files found with prefix: {prefix}")
                return []
            
            files = []
            for obj in response['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'modified': obj['LastModified']
                })
            
            print(f"Found {len(files)} file(s) in {prefix}:")
            for file in files:
                print(f"  - {file['key']} ({file['size']} bytes)")
            
            return files
            
        except Exception as e:
            print(f"✗ Error listing files: {e}")
            return []
    
    def delete_audio(self, s3_key: str):
        """Delete audio file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f"✓ Deleted: {s3_key}")
            return True
        except Exception as e:
            print(f"✗ Delete failed: {e}")
            return False
    
    def generate_presigned_url(self, s3_key: str, expiration: int = 3600):
        """Generate presigned URL for temporary access"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            print(f"✗ Failed to generate presigned URL: {e}")
            return None

def main():
    """Command-line interface for S3 management"""
    manager = S3Manager()
    
    if len(sys.argv) < 2:
        print("S3 Manager for Chatterbox TTS")
        print("\nUsage:")
        print("  python s3_manager.py create-bucket   - Create S3 bucket")
        print("  python s3_manager.py list             - List audio files")
        print("  python s3_manager.py upload <file>    - Upload audio file")
        return
    
    command = sys.argv[1]
    
    if command == 'create-bucket':
        manager.create_bucket()
    
    elif command == 'list':
        manager.list_audio_files()
    
    elif command == 'upload' and len(sys.argv) > 2:
        manager.upload_audio(sys.argv[2])
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
