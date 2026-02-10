#!/usr/bin/env python3
"""
Test script for Chatterbox TTS API
Validates all endpoints and functionality
"""

import sys
import requests
import json
import base64
import time
from typing import Optional
from pathlib import Path


class TTSAPITester:
    def __init__(self, api_url: str, verbose: bool = False):
        self.api_url = api_url.rstrip('/')
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.session = requests.Session()
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with level."""
        if level == "PASS":
            print(f"✓ {message}")
            self.passed += 1
        elif level == "FAIL":
            print(f"✗ {message}")
            self.failed += 1
        elif level == "INFO":
            if self.verbose:
                print(f"ℹ {message}")
        elif level == "ERROR":
            print(f"✗ ERROR: {message}")
    
    def test_health(self) -> bool:
        """Test health check endpoint."""
        print("\n--- Testing Health Check ---")
        try:
            response = self.session.get(
                f'{self.api_url}/health',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log("Health check successful", "PASS")
                self.log(f"Status: {data['status']}", "INFO")
                self.log(f"Device: {data['device']}", "INFO")
                self.log(f"Model loaded: {data['model_loaded']}", "INFO")
                
                if 'gpu' in data:
                    self.log(f"CUDA available: {data['gpu'].get('cuda_available')}", "INFO")
                
                return True
            else:
                self.log(f"Health check failed: {response.status_code}", "FAIL")
                return False
        
        except Exception as e:
            self.log(f"Health check error: {e}", "FAIL")
            return False
    
    def test_characters(self) -> bool:
        """Test get characters endpoint."""
        print("\n--- Testing Characters Endpoint ---")
        try:
            response = self.session.get(
                f'{self.api_url}/characters',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                characters = data.get('characters', [])
                self.log(f"Got {len(characters)} characters", "PASS")
                
                for char in characters:
                    self.log(f"  - {char['id']}: {char['name']}", "INFO")
                
                if len(characters) > 0:
                    return True
                else:
                    self.log("No characters found", "FAIL")
                    return False
            else:
                self.log(f"Failed to get characters: {response.status_code}", "FAIL")
                return False
        
        except Exception as e:
            self.log(f"Characters endpoint error: {e}", "FAIL")
            return False
    
    def test_languages(self) -> bool:
        """Test languages endpoint."""
        print("\n--- Testing Languages Endpoint ---")
        try:
            response = self.session.get(
                f'{self.api_url}/languages',
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                languages = data.get('languages', [])
                self.log(f"Got {len(languages)} languages", "PASS")
                return True
            else:
                self.log(f"Failed to get languages: {response.status_code}", "FAIL")
                return False
        
        except Exception as e:
            self.log(f"Languages endpoint error: {e}", "FAIL")
            return False
    
    def test_generate_audio(self, text: str = "Hello world") -> bool:
        """Test audio generation endpoint."""
        print("\n--- Testing Audio Generation ---")
        try:
            payload = {
                "text": text,
                "character": "narrator",
                "max_tokens": 400
            }
            
            self.log(f"Sending request: {json.dumps(payload)}", "INFO")
            start_time = time.time()
            
            response = self.session.post(
                f'{self.api_url}/generate-audio',
                json=payload,
                timeout=60
            )
            
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.log(
                        f"Audio generated successfully in {generation_time:.1f}s",
                        "PASS"
                    )
                    self.log(f"Duration: {data['duration']}s", "INFO")
                    self.log(f"Sample rate: {data['sample_rate']}Hz", "INFO")
                    self.log(f"Generation time: {data['generation_time_ms']}ms", "INFO")
                    
                    if 'audio' in data:
                        audio_size = len(data['audio']) / 1024
                        self.log(f"Audio size: {audio_size:.1f}KB (base64)", "INFO")
                    
                    return True
                else:
                    self.log(f"Generation failed: {data.get('error')}", "FAIL")
                    return False
            else:
                self.log(f"Request failed: {response.status_code}", "FAIL")
                self.log(f"Response: {response.text}", "INFO")
                return False
        
        except Exception as e:
            self.log(f"Audio generation error: {e}", "FAIL")
            return False
    
    def test_tts_json(self, text: str = "Test message") -> bool:
        """Test TTS JSON endpoint."""
        print("\n--- Testing TTS JSON Endpoint ---")
        try:
            payload = {
                "text": text,
                "character": "narrator"
            }
            
            response = self.session.post(
                f'{self.api_url}/tts-json',
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    self.log("TTS JSON endpoint working", "PASS")
                    audio_data = data.get('audio', '')
                    self.log(
                        f"Audio size: {len(audio_data) / 1024:.1f}KB (base64)",
                        "INFO"
                    )
                    return True
                else:
                    self.log(f"TTS JSON failed: {data.get('error')}", "FAIL")
                    return False
            else:
                self.log(f"TTS JSON failed: {response.status_code}", "FAIL")
                return False
        
        except Exception as e:
            self.log(f"TTS JSON error: {e}", "FAIL")
            return False
    
    def test_invalid_character(self) -> bool:
        """Test handling of invalid character."""
        print("\n--- Testing Error Handling (Invalid Character) ---")
        try:
            payload = {
                "text": "Test",
                "character": "invalid_character_xyz"
            }
            
            response = self.session.post(
                f'{self.api_url}/generate-audio',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 400:
                data = response.json()
                if not data.get('success'):
                    self.log("Invalid character properly rejected", "PASS")
                    return True
            
            self.log("Invalid character not properly rejected", "FAIL")
            return False
        
        except Exception as e:
            self.log(f"Error handling test failed: {e}", "FAIL")
            return False
    
    def test_empty_text(self) -> bool:
        """Test handling of empty text."""
        print("\n--- Testing Error Handling (Empty Text) ---")
        try:
            payload = {
                "text": "",
                "character": "narrator"
            }
            
            response = self.session.post(
                f'{self.api_url}/generate-audio',
                json=payload,
                timeout=10
            )
            
            if response.status_code == 400:
                self.log("Empty text properly rejected", "PASS")
                return True
            else:
                self.log(f"Empty text not rejected: {response.status_code}", "FAIL")
                return False
        
        except Exception as e:
            self.log(f"Empty text test failed: {e}", "FAIL")
            return False
    
    def test_cors_headers(self) -> bool:
        """Test CORS headers."""
        print("\n--- Testing CORS Headers ---")
        try:
            response = self.session.options(
                f'{self.api_url}/generate-audio',
                headers={'Origin': 'https://example.com'},
                timeout=10
            )
            
            if 'Access-Control-Allow-Origin' in response.headers:
                self.log("CORS headers present", "PASS")
                self.log(
                    f"Allow-Origin: {response.headers['Access-Control-Allow-Origin']}",
                    "INFO"
                )
                return True
            else:
                self.log("CORS headers missing", "FAIL")
                return False
        
        except Exception as e:
            self.log(f"CORS test failed: {e}", "FAIL")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests."""
        print("=" * 60)
        print("Chatterbox TTS API Test Suite")
        print("=" * 60)
        print(f"API URL: {self.api_url}")
        
        tests = [
            ("Health Check", self.test_health),
            ("Characters Endpoint", self.test_characters),
            ("Languages Endpoint", self.test_languages),
            ("Audio Generation", self.test_generate_audio),
            ("TTS JSON Endpoint", self.test_tts_json),
            ("Invalid Character Handling", self.test_invalid_character),
            ("Empty Text Handling", self.test_empty_text),
            ("CORS Headers", self.test_cors_headers),
        ]
        
        results = []
        for name, test_func in tests:
            try:
                result = test_func()
                results.append((name, result))
            except Exception as e:
                self.log(f"Unexpected error in {name}: {e}", "ERROR")
                results.append((name, False))
        
        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        for name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {name}")
        
        total_tests = len(results)
        passed_tests = sum(1 for _, r in results if r)
        failed_tests = total_tests - passed_tests
        
        print("=" * 60)
        print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
        print("=" * 60)
        
        return failed_tests == 0
    
    def close(self):
        """Close session."""
        self.session.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <api_url> [--verbose]")
        print("Example: python test_api.py http://localhost:5000")
        print("Example: python test_api.py https://api.yourdomain.com --verbose")
        sys.exit(1)
    
    api_url = sys.argv[1]
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    tester = TTSAPITester(api_url, verbose=verbose)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    finally:
        tester.close()


if __name__ == "__main__":
    main()
