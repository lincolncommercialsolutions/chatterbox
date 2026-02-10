#!/usr/bin/env python3
"""
Integration test for Chatterbox TTS API
Tests the complete end-to-end flow with OpenRouter integration and S3 storage
"""

import os
import sys
import json
import requests
import time
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
TEST_TEXT = "Hello world! This is a test of the Chatterbox TTS system with character voice synthesis."
TEST_CHARACTERS = ["narrator", "assistant", "luna", "sage", "echo", "zephyr"]

def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_section(text):
    """Print section divider."""
    print(f"\n→ {text}")
    print("-" * 70)

def test_health_check():
    """Test health check endpoint."""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ API Status: {data.get('status')}")
        print(f"✓ Device: {data.get('device')}")
        print(f"✓ Model Loaded: {data.get('model_loaded')}")
        print(f"✓ Cache Enabled: {data.get('cache_enabled')}")
        print(f"✓ Cache Size: {data.get('cache_size')}")
        
        if data.get('gpu'):
            print(f"✓ GPU Memory: {data['gpu'].get('memory_allocated', 'N/A')}")
        
        if data.get('s3'):
            s3_info = data['s3']
            print(f"✓ S3 Enabled: {s3_info.get('enabled')}")
            if s3_info.get('enabled'):
                print(f"  - Bucket: {s3_info.get('bucket')}")
                print(f"  - Region: {s3_info.get('region')}")
        
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_get_characters():
    """Test getting available characters."""
    print_section("Testing Character Endpoints")
    
    try:
        # Get all characters
        response = requests.get(f"{API_BASE_URL}/characters", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        characters = data.get('characters', [])
        print(f"✓ Found {len(characters)} character(s):")
        
        for char in characters:
            print(f"  - {char['id']}: {char['name']} ({char['language']})")
        
        return characters
    except Exception as e:
        print(f"✗ Failed to get characters: {e}")
        return []

def test_get_voices():
    """Test getting available voices."""
    print_section("Testing Voice Endpoints")
    
    try:
        # Get all voices
        response = requests.get(f"{API_BASE_URL}/voices", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        voices = data.get('voices', [])
        print(f"✓ Found {len(voices)} voice(s):")
        
        for voice in voices:
            print(f"  - {voice['id']}: {voice['name']}")
        
        return voices
    except Exception as e:
        print(f"✗ Failed to get voices: {e}")
        return []

def test_audio_generation_base64(character_id="narrator"):
    """Test audio generation with base64 response."""
    print_section(f"Testing Audio Generation (base64) - Character: {character_id}")
    
    try:
        payload = {
            "text": TEST_TEXT,
            "character": character_id,
            "return_format": "base64",
            "max_tokens": 400
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/generate-audio",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            print(f"✓ Audio generated successfully")
            print(f"  - Character: {data.get('character')}")
            print(f"  - Voice: {data.get('voice_id')}")
            print(f"  - Duration: {data.get('duration')}s")
            print(f"  - Sample Rate: {data.get('sample_rate')}Hz")
            print(f"  - Generation Time: {data.get('generation_time_ms')}ms")
            print(f"  - Storage: {data.get('storage')}")
            print(f"  - Total Time: {elapsed:.1f}s")
            
            has_audio = bool(data.get('audio'))
            print(f"  - Has Audio Data: {has_audio}")
            if has_audio:
                print(f"  - Audio Size: {len(data.get('audio', ''))} bytes (base64)")
            
            return True
        else:
            print(f"✗ Generation failed: {data.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Audio generation failed: {e}")
        return False

def test_audio_generation_s3_url(character_id="narrator", use_presigned=False):
    """Test audio generation with S3 URL response."""
    url_type = "presigned" if use_presigned else "public"
    print_section(f"Testing Audio Generation (S3 {url_type} URL) - Character: {character_id}")
    
    try:
        payload = {
            "text": TEST_TEXT,
            "character": character_id,
            "return_format": "url",
            "presigned": use_presigned,
            "max_tokens": 400
        }
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/generate-audio",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            print(f"✓ Audio generated and uploaded to S3")
            print(f"  - Character: {data.get('character')}")
            print(f"  - Voice: {data.get('voice_id')}")
            print(f"  - Duration: {data.get('duration')}s")
            print(f"  - Storage: {data.get('storage')}")
            print(f"  - URL Type: {data.get('url_type', 'public')}")
            
            if data.get('audio_url'):
                # Truncate URL for display
                url = data.get('audio_url')
                display_url = url[:70] + "..." if len(url) > 70 else url
                print(f"  - S3 URL: {display_url}")
                print(f"  - Full URL Length: {len(url)} chars")
                
                # Verify URL is accessible
                try:
                    head_response = requests.head(url, timeout=5)
                    if head_response.status_code == 200:
                        print(f"  ✓ URL is accessible")
                    else:
                        print(f"  ⚠ URL returned status {head_response.status_code}")
                except Exception as e:
                    print(f"  ⚠ Could not verify URL accessibility: {e}")
            else:
                print(f"  ⚠ No S3 URL in response")
            
            print(f"  - Total Time: {elapsed:.1f}s")
            return True
        else:
            print(f"✗ Generation failed: {data.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Audio generation failed: {e}")
        return False

def test_character_voice_change(character_id="assistant", new_voice="expert"):
    """Test changing a character's voice."""
    print_section(f"Testing Character Voice Change - {character_id} to {new_voice}")
    
    try:
        payload = {"voice_id": new_voice}
        
        response = requests.post(
            f"{API_BASE_URL}/characters/{character_id}/voice",
            json=payload,
            timeout=5
        )
        
        response.raise_for_status()
        data = response.json()
        
        if data.get('success'):
            print(f"✓ Character voice changed")
            print(f"  - Character: {data.get('character')}")
            print(f"  - New Voice: {data.get('voice_id')}")
            print(f"  - Voice Name: {data.get('voice_name')}")
            return True
        else:
            print(f"✗ Voice change failed: {data.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Voice change failed: {e}")
        return False

def run_all_tests():
    """Run all integration tests."""
    print_header("CHATTERBOX TTS API - INTEGRATION TEST SUITE")
    print(f"API URL: {API_BASE_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # Test 1: Health Check
    results['health_check'] = test_health_check()
    
    if not results['health_check']:
        print_header("ERROR: API is not responding. Cannot continue with other tests.")
        return results
    
    # Test 2: Get Characters
    characters = test_get_characters()
    results['get_characters'] = len(characters) > 0
    
    # Test 3: Get Voices
    voices = test_get_voices()
    results['get_voices'] = len(voices) > 0
    
    # Test 4: Audio generation with different characters (base64)
    results['audio_generation_base64'] = {}
    for char in ["narrator", "assistant", "luna"]:
        results['audio_generation_base64'][char] = test_audio_generation_base64(char)
        time.sleep(1)  # Rate limiting
    
    # Test 5: Audio generation with S3 URL (public)
    results['audio_generation_s3_public'] = {}
    for char in ["narrator", "assistant"]:
        results['audio_generation_s3_public'][char] = test_audio_generation_s3_url(char, use_presigned=False)
        time.sleep(1)
    
    # Test 6: Audio generation with S3 presigned URL
    results['audio_generation_s3_presigned'] = {}
    for char in ["narrator"]:
        results['audio_generation_s3_presigned'][char] = test_audio_generation_s3_url(char, use_presigned=True)
        time.sleep(1)
    
    # Test 7: Character voice change
    results['character_voice_change'] = test_character_voice_change("assistant", "expert")
    
    # Print summary
    print_header("TEST SUMMARY")
    
    for test_name, test_result in results.items():
        if isinstance(test_result, dict):
            for sub_test, result in test_result.items():
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{status}: {test_name}[{sub_test}]")
        else:
            status = "✓ PASS" if test_result else "✗ FAIL"
            print(f"{status}: {test_name}")
    
    # Count results
    total_tests = sum(1 for r in results.values() if isinstance(r, bool)) + sum(
        len(v) for v in results.values() if isinstance(v, dict)
    )
    passed_tests = sum(1 for r in results.values() if isinstance(r, bool) and r) + sum(
        sum(1 for v in vals.values() if v) for vals in (results.values() if isinstance(results.get(k), dict) else [{}])
        for k in results
    )
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    return results

if __name__ == "__main__":
    print("Starting Chatterbox TTS API integration tests...")
    print("Make sure the API server is running on:", API_BASE_URL)
    print()
    
    try:
        results = run_all_tests()
        
        # Exit with error code if any tests failed
        all_passed = all(
            v for v in results.values() 
            if isinstance(v, bool) or (isinstance(v, dict) and all(v.values()))
        )
        
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
