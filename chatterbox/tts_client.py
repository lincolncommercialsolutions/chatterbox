"""
Chatterbox TTS Client Library
Simple client for integrating with Chatterbox TTS API from Python backends
"""

import requests
import base64
import logging
from typing import Optional, Dict, Any
from io import BytesIO
import wave

logger = logging.getLogger(__name__)


class ChatterboxTTSClient:
    """Client for Chatterbox TTS API."""
    
    def __init__(self, api_url: str, timeout: int = 30, retry_attempts: int = 3):
        """
        Initialize TTS client.
        
        Args:
            api_url: Base URL of the Chatterbox TTS API (e.g., 'https://api.example.com')
            timeout: Request timeout in seconds
            retry_attempts: Number of retry attempts for failed requests
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health and GPU status."""
        try:
            response = self.session.get(
                f'{self.api_url}/health',
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise
    
    def get_characters(self) -> list:
        """Get list of available character voices."""
        try:
            response = self.session.get(
                f'{self.api_url}/characters',
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get('characters', [])
        except Exception as e:
            logger.error(f"Failed to get characters: {e}")
            raise
    
    def generate_audio(
        self,
        text: str,
        character: str = "narrator",
        return_format: str = "base64",
        max_tokens: int = 400
    ) -> Dict[str, Any]:
        """
        Generate audio for OpenRouter AI character response.
        
        Args:
            text: The text to convert to speech
            character: Character voice ID (default: "narrator")
            return_format: Response format - "base64" or "url"
            max_tokens: Maximum tokens for generation
        
        Returns:
            Dict with 'success', 'audio' (base64) or 'audio_url', 'duration', etc.
        """
        payload = {
            "text": text,
            "character": character,
            "return_format": return_format,
            "max_tokens": max_tokens
        }
        
        for attempt in range(self.retry_attempts):
            try:
                response = self.session.post(
                    f'{self.api_url}/generate-audio',
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('success'):
                    return result
                else:
                    raise Exception(result.get('error', 'Generation failed'))
            
            except requests.exceptions.Timeout:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Timeout on attempt {attempt + 1}, retrying...")
                    continue
                raise
            except requests.exceptions.ConnectionError as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
                    continue
                raise
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Error on attempt {attempt + 1}: {e}, retrying...")
                    continue
                logger.error(f"Audio generation failed: {e}")
                raise
        
        raise Exception("Max retry attempts exceeded")
    
    def generate_audio_file(
        self,
        text: str,
        character: str = "narrator",
        output_path: Optional[str] = None
    ) -> BytesIO:
        """
        Generate audio and return as WAV file.
        
        Args:
            text: The text to convert to speech
            character: Character voice ID
            output_path: Optional file path to save audio
        
        Returns:
            BytesIO object with WAV audio data
        """
        result = self.generate_audio(text, character, return_format="base64")
        
        # Decode base64 audio
        audio_data = base64.b64decode(result['audio'])
        audio_buffer = BytesIO(audio_data)
        
        # Save to file if requested
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            logger.info(f"Audio saved to {output_path}")
        
        return audio_buffer
    
    def batch_generate_audio(
        self,
        texts: list,
        character: str = "narrator"
    ) -> list:
        """
        Generate audio for multiple texts.
        
        Args:
            texts: List of texts to convert
            character: Character voice ID
        
        Returns:
            List of audio generation results
        """
        results = []
        for text in texts:
            try:
                result = self.generate_audio(text, character)
                results.append({
                    "text": text,
                    "success": True,
                    **result
                })
            except Exception as e:
                results.append({
                    "text": text,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def close(self):
        """Close the session."""
        self.session.close()


class OpenRouterTTSIntegration:
    """
    Specialized integration for OpenRouter character responses.
    Automatically generates audio for AI responses.
    """
    
    def __init__(self, api_url: str, default_character: str = "narrator"):
        """
        Initialize OpenRouter integration.
        
        Args:
            api_url: Chatterbox API URL
            default_character: Default character voice for responses
        """
        self.client = ChatterboxTTSClient(api_url)
        self.default_character = default_character
        self.character_map = {}  # Map character names to voice IDs
    
    def map_character(self, ai_character_name: str, voice_id: str):
        """Map an AI character name to a TTS voice ID."""
        self.character_map[ai_character_name.lower()] = voice_id
    
    def get_voice_for_character(self, ai_character_name: str) -> str:
        """Get the TTS voice ID for an AI character."""
        return self.character_map.get(
            ai_character_name.lower(),
            self.default_character
        )
    
    def process_response(
        self,
        ai_response: str,
        ai_character_name: str
    ) -> Dict[str, Any]:
        """
        Process an OpenRouter AI response and generate audio.
        
        Args:
            ai_response: The AI character's response text
            ai_character_name: Name of the AI character
        
        Returns:
            Dict with response text, audio (base64), duration, etc.
        """
        voice_id = self.get_voice_for_character(ai_character_name)
        
        try:
            audio_result = self.client.generate_audio(
                ai_response,
                character=voice_id,
                return_format="base64"
            )
            
            return {
                "text": ai_response,
                "character": ai_character_name,
                "audio": audio_result.get('audio'),
                "duration": audio_result.get('duration'),
                "sample_rate": audio_result.get('sample_rate'),
                "success": True
            }
        except Exception as e:
            logger.error(f"Failed to generate audio for {ai_character_name}: {e}")
            return {
                "text": ai_response,
                "character": ai_character_name,
                "success": False,
                "error": str(e)
            }
    
    def close(self):
        """Close the client."""
        self.client.close()


# Convenience functions
def create_client(api_url: str, **kwargs) -> ChatterboxTTSClient:
    """Create a Chatterbox TTS client."""
    return ChatterboxTTSClient(api_url, **kwargs)


def create_openrouter_integration(api_url: str, **kwargs) -> OpenRouterTTSIntegration:
    """Create an OpenRouter integration client."""
    return OpenRouterTTSIntegration(api_url, **kwargs)


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Check if API URL is provided
    if len(sys.argv) < 2:
        print("Usage: python tts_client.py <api_url> [text]")
        print("Example: python tts_client.py http://localhost:5000 'Hello world'")
        sys.exit(1)
    
    api_url = sys.argv[1]
    text = sys.argv[2] if len(sys.argv) > 2 else "Hello, I am a character voice."
    
    # Create client and test
    client = ChatterboxTTSClient(api_url)
    
    try:
        # Health check
        print("Checking API health...")
        health = client.health_check()
        print(f"✓ API healthy: {health['status']}")
        print(f"  Device: {health['device']}")
        print(f"  Model loaded: {health['model_loaded']}")
        
        # Get characters
        print("\nAvailable characters:")
        characters = client.get_characters()
        for char in characters:
            print(f"  - {char['id']}: {char['name']} ({char['language']})")
        
        # Generate audio
        print(f"\nGenerating audio for: '{text}'")
        result = client.generate_audio(text, character="narrator")
        
        if result['success']:
            print(f"✓ Audio generated successfully")
            print(f"  Duration: {result['duration']}s")
            print(f"  Sample rate: {result['sample_rate']}Hz")
            print(f"  Generation time: {result['generation_time_ms']}ms")
            print(f"  Audio size: {len(result['audio']) / 1024:.1f}KB (base64)")
        else:
            print(f"✗ Generation failed: {result.get('error')}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
    finally:
        client.close()
