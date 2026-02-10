"""
Chatterbox TTS API Server with character voice profiles
Production-ready AWS deployment with GPU support and OpenRouter integration
Provides REST API endpoints for text-to-speech generation with pre-configured character voices
"""

import torch
import numpy as np
import json
import uuid
import os
import base64
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import logging
import traceback
from functools import lru_cache

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import soundfile as sf

from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES

# AWS S3 Support
try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Enhanced CORS for Vercel frontend
CORS(app, resources={
    r"/*": {
        "origins": os.getenv('CORS_ORIGINS', '*').split(','),
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

# Global model instance
MODEL = None
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Configuration from environment
API_PORT = int(os.getenv('API_PORT', 5000))
MAX_TEXT_LENGTH = int(os.getenv('MAX_TEXT_LENGTH', 500))
DEFAULT_MAX_TOKENS = int(os.getenv('DEFAULT_MAX_TOKENS', 400))
CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
BATCH_SIZE = int(os.getenv('BATCH_SIZE', 1))

# S3 Configuration
S3_ENABLED = os.getenv('S3_ENABLED', 'false').lower() == 'true' and BOTO3_AVAILABLE
S3_BUCKET = os.getenv('S3_BUCKET_NAME', '')
S3_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_AUDIO_PREFIX = os.getenv('S3_AUDIO_PREFIX', 'chatterbox/audio/')
S3_VOICES_PREFIX = os.getenv('S3_VOICES_PREFIX', 'chatterbox/voices/')

# S3 Client (only if enabled)
S3_CLIENT = None
if S3_ENABLED and S3_BUCKET:
    try:
        S3_CLIENT = boto3.client('s3', region_name=S3_REGION)
        logger.info(f"S3 enabled: {S3_BUCKET} in {S3_REGION}")
    except Exception as e:
        logger.warning(f"Failed to initialize S3: {e}")
        S3_ENABLED = False

# Audio cache for repeated requests (helps with OpenRouter retries)
AUDIO_CACHE = {} if CACHE_ENABLED else None
MAX_CACHE_SIZE = 100

if DEVICE == "cuda":
    try:
        logger.info(f"CUDA Available: {torch.cuda.is_available()}")
        logger.info(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        torch.cuda.empty_cache()
    except Exception as e:
        logger.warning(f"Could not initialize CUDA: {e}")

# Voice Library - Define all available voices
# Each voice is an audio sample that defines the speaking style
VOICE_LIBRARY = {
    "narrator": {
        "name": "Professional Narrator",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "description": "Clear, professional voice for narration",
        "quality": "high",
        "tags": ["professional", "formal", "narrative"]
    },
    "friendly": {
        "name": "Friendly Voice",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "description": "Warm and approachable voice",
        "quality": "high",
        "tags": ["friendly", "warm", "casual"]
    },
    "expert": {
        "name": "Expert Voice",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "description": "Authoritative voice for knowledge sharing",
        "quality": "high",
        "tags": ["expert", "authoritative", "formal"]
    },
    "child": {
        "name": "Child Voice",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "description": "Youthful, energetic voice",
        "quality": "high",
        "tags": ["child", "energetic", "playful"]
    },
    "mysterious": {
        "name": "Mysterious Voice",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "description": "Enigmatic and intriguing voice",
        "quality": "high",
        "tags": ["mysterious", "dramatic", "theatrical"]
    },
    "calm": {
        "name": "Calm Voice",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "description": "Soothing and meditative voice",
        "quality": "high",
        "tags": ["calm", "soothing", "meditative"]
    }
}

# Character Configurations - Map characters to voices and generation parameters
# This defines AI characters and which voice they use
CHARACTER_VOICES = {
    "narrator": {
        "name": "Narrator",
        "voice_id": "narrator",  # Reference to VOICE_LIBRARY
        "language": "en",
        "exaggeration": 0.5,
        "temperature": 0.7,
        "cfg_weight": 0.6,
        "description": "Professional narrator voice"
    },
    "assistant": {
        "name": "AI Assistant",
        "voice_id": "friendly",
        "language": "en",
        "exaggeration": 0.6,
        "temperature": 0.8,
        "cfg_weight": 0.5,
        "description": "Friendly AI assistant"
    },
    "expert": {
        "name": "Expert",
        "voice_id": "expert",
        "language": "en",
        "exaggeration": 0.4,
        "temperature": 0.6,
        "cfg_weight": 0.7,
        "description": "Knowledgeable expert"
    },
    "luna": {
        "name": "Luna",
        "voice_id": "mysterious",
        "language": "en",
        "exaggeration": 0.5,
        "temperature": 0.8,
        "cfg_weight": 0.6,
        "description": "Mysterious character voice"
    },
    "sage": {
        "name": "Sage",
        "voice_id": "calm",
        "language": "en",
        "exaggeration": 0.3,
        "temperature": 0.6,
        "cfg_weight": 0.8,
        "description": "Wise and calm character"
    },
    "elara": {
        "name": "Elara",
        "voice_id": "friendly",
        "language": "en",
        "exaggeration": 0.7,
        "temperature": 0.9,
        "cfg_weight": 0.5,
        "description": "Cheerful and warm character"
    }
}


def get_or_load_model():
    """Load the Chatterbox model if not already loaded."""
    global MODEL
    if MODEL is None:
        logger.info(f"Loading Chatterbox model on device: {DEVICE}")
        try:
            MODEL = ChatterboxMultilingualTTS.from_pretrained(DEVICE)
            logger.info(f"Model loaded successfully. Device: {MODEL.device}")
            logger.info(f"Sample rate: {MODEL.sr}Hz")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            traceback.print_exc()
            raise
    return MODEL


def get_cache_key(text: str, character_id: str) -> str:
    """Generate cache key for audio."""
    cache_str = f"{text}_{character_id}"
    return hashlib.md5(cache_str.encode()).hexdigest()


def get_cached_audio(text: str, character_id: str) -> Optional[Tuple[bytes, int, float]]:
    """Retrieve cached audio if available."""
    if AUDIO_CACHE is None:
        return None
    
    cache_key = get_cache_key(text, character_id)
    if cache_key in AUDIO_CACHE:
        logger.info(f"Cache hit for text: {text[:50]}...")
        return AUDIO_CACHE[cache_key]
    
    return None


def cache_audio(text: str, character_id: str, audio_bytes: bytes, sample_rate: int, duration: float):
    """Cache generated audio."""
    if AUDIO_CACHE is None:
        return
    
    # Simple LRU: remove oldest if cache is full
    if len(AUDIO_CACHE) >= MAX_CACHE_SIZE:
        oldest_key = next(iter(AUDIO_CACHE))
        del AUDIO_CACHE[oldest_key]
        logger.debug("Cache evicted oldest entry")
    
    cache_key = get_cache_key(text, character_id)
    AUDIO_CACHE[cache_key] = (audio_bytes, sample_rate, duration)
    logger.debug(f"Cached audio: {cache_key}")


def generate_audio_bytes(text: str, character_id: str = "narrator", voice_id: Optional[str] = None, max_tokens: int = 400, use_cache: bool = True) -> Tuple[bytes, int, float]:
    """
    Generate audio from text using a character voice profile.
    
    Args:
        text: Text to convert to speech
        character_id: Character to use (defines generation parameters)
        voice_id: Override voice for this character (optional)
        max_tokens: Maximum tokens for generation
        use_cache: Enable caching
    
    Returns: (audio_bytes, sample_rate, duration_seconds)
    """
    try:
        # Check cache first
        cache_key_override = f"{text}_{character_id}_{voice_id}" if voice_id else f"{text}_{character_id}"
        if use_cache:
            cached = get_cached_audio(cache_key_override, "")
            if cached:
                return cached
        
        model = get_or_load_model()
        
        # Get character profile
        if character_id not in CHARACTER_VOICES:
            raise ValueError(f"Unknown character: {character_id}. Available: {list(CHARACTER_VOICES.keys())}")
        
        character = CHARACTER_VOICES[character_id]
        
        # Determine which voice to use
        actual_voice_id = voice_id if voice_id else character.get("voice_id", "narrator")
        
        if actual_voice_id not in VOICE_LIBRARY:
            raise ValueError(f"Unknown voice: {actual_voice_id}. Available: {list(VOICE_LIBRARY.keys())}")
        
        voice = VOICE_LIBRARY[actual_voice_id]
        language = character["language"]
        
        logger.info(f"Generating audio for character '{character_id}' with voice '{actual_voice_id}': {text[:100]}...")
        
        # Generate speech with GPU acceleration
        wav = model.generate(
            text=text[:300],
            language_id=language,
            audio_prompt_path=voice["audio_url"],
            exaggeration=character["exaggeration"],
            temperature=character["temperature"],
            cfg_weight=character["cfg_weight"],
            max_new_tokens=max_tokens,
        )
        
        # Ensure numpy array
        if isinstance(wav, np.ndarray):
            wav_np = wav
        elif hasattr(wav, 'cpu'):
            wav_np = wav.cpu().squeeze(0).numpy() if wav.dim() > 1 else wav.cpu().numpy()
        else:
            wav_np = np.asarray(wav)
        
        # Convert to float32 if needed
        if wav_np.dtype != np.float32:
            wav_np = wav_np.astype(np.float32)
        
        # Normalize audio to prevent clipping
        max_val = np.abs(wav_np).max()
        if max_val > 1.0:
            wav_np = wav_np / max_val * 0.95
        
        # Encode to WAV bytes
        audio_buffer = io.BytesIO()
        sf.write(audio_buffer, wav_np, model.sr, format='WAV')
        audio_buffer.seek(0)
        audio_bytes = audio_buffer.getvalue()
        
        duration = len(wav_np) / model.sr
        
        # Clear GPU cache to prevent memory buildup
        if DEVICE == "cuda":
            torch.cuda.empty_cache()
        
        logger.info(f"Audio generated: {len(audio_bytes)} bytes, {duration:.1f}s duration")
        
        # Cache the result
        if use_cache:
            cache_audio(cache_key_override, "", audio_bytes, model.sr, duration)
        
        return audio_bytes, model.sr, duration
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        traceback.print_exc()
        raise


# ============ API Routes ============

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    gpu_info = {}
    if DEVICE == "cuda":
        try:
            gpu_info = {
                "cuda_available": True,
                "device": torch.cuda.get_device_name(0),
                "memory_allocated": f"{torch.cuda.memory_allocated(0) / 1e9:.1f}GB",
                "memory_reserved": f"{torch.cuda.memory_reserved(0) / 1e9:.1f}GB",
            }
        except:
            gpu_info = {"cuda_available": False}
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "device": DEVICE,
        "model_loaded": MODEL is not None,
        "gpu": gpu_info,
        "cache_enabled": CACHE_ENABLED,
        "cache_size": len(AUDIO_CACHE) if AUDIO_CACHE else 0
    })


@app.route('/generate-audio', methods=['POST'])
def generate_audio():
    """
    OpenRouter integration endpoint - Generate audio for AI character responses.
    
    Request JSON:
    {
        "text": "The AI character's response text",
        "character": "narrator",          // optional, defaults to "narrator"
        "voice_id": "friendly",           // optional, override character's default voice
        "language": "en",                 // optional, uses character's language if not specified
        "max_tokens": 400,               // optional, defaults to 400
        "return_format": "base64"        // optional: "base64" or "url", defaults to "base64"
    }
    
    Response JSON:
    {
        "success": true,
        "audio": "base64_encoded_wav_data",  // if return_format is "base64"
        "audio_url": "...",                  // if return_format is "url"
        "sample_rate": 24000,
        "duration": 2.5,
        "character": "narrator",
        "voice_id": "friendly",
        "text_length": 45,
        "generation_time_ms": 1234
    }
    """
    try:
        import base64
        import time
        
        start_time = time.time()
        data = request.get_json()
        
        # Validate input
        if not data or "text" not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'text' field"
            }), 400
        
        text = str(data["text"]).strip()
        if not text:
            return jsonify({
                "success": False,
                "error": "Text cannot be empty"
            }), 400
        
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({
                "success": False,
                "error": f"Text too long (max {MAX_TEXT_LENGTH} characters)"
            }), 400
        
        # Get character
        character_id = data.get("character", "narrator")
        if character_id not in CHARACTER_VOICES:
            return jsonify({
                "success": False,
                "error": f"Unknown character: {character_id}",
                "available_characters": list(CHARACTER_VOICES.keys())
            }), 400
        
        # Get optional voice override
        voice_id = data.get("voice_id")
        if voice_id and voice_id not in VOICE_LIBRARY:
            return jsonify({
                "success": False,
                "error": f"Unknown voice: {voice_id}",
                "available_voices": list(VOICE_LIBRARY.keys())
            }), 400
        
        max_tokens = int(data.get("max_tokens", DEFAULT_MAX_TOKENS))
        max_tokens = max(100, min(max_tokens, 1000))  # Clamp
        return_format = data.get("return_format", "base64").lower()
        
        if return_format not in ["base64", "url"]:
            return_format = "base64"
        
        actual_voice = voice_id or CHARACTER_VOICES[character_id].get("voice_id", "narrator")
        logger.info(f"OpenRouter: Generating audio for '{character_id}' (voice: '{actual_voice}'): {text[:60]}...")
        
        # Generate audio
        audio_bytes, sample_rate, duration = generate_audio_bytes(
            text=text,
            character_id=character_id,
            voice_id=voice_id,
            max_tokens=max_tokens,
            use_cache=True
        )
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        response_data = {
            "success": True,
            "sample_rate": int(sample_rate),
            "duration": round(duration, 2),
            "character": character_id,
            "voice_id": actual_voice,
            "text_length": len(text),
            "generation_time_ms": generation_time_ms,
            "cached": False  # Could track this if needed
        }
        
        # Return based on format
        if return_format == "base64":
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            response_data["audio"] = audio_base64
        else:
            # For URL format, would need to implement file storage (S3, etc)
            response_data["audio_url"] = f"/audio/{uuid.uuid4().hex}"
        
        logger.info(f"OpenRouter: Audio ready in {generation_time_ms}ms, duration: {duration:.1f}s")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"OpenRouter audio generation error: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@app.route('/characters', methods=['GET'])
def list_characters():
    """List all available character voice profiles."""
    characters = []
    for char_id, config in CHARACTER_VOICES.items():
        characters.append({
            "id": char_id,
            "name": config["name"],
            "language": config["language"],
            "description": config["description"]
        })
    
    return jsonify({
        "characters": characters,
        "total": len(characters)
    })


@app.route('/characters/<character_id>', methods=['GET'])
def get_character(character_id: str):
    """Get details about a specific character."""
    if character_id not in CHARACTER_VOICES:
        return jsonify({"error": f"Character '{character_id}' not found"}), 404
    
    config = CHARACTER_VOICES[character_id]
    return jsonify({
        "id": character_id,
        "name": config["name"],
        "language": config["language"],
        "description": config["description"],
        "parameters": {
            "exaggeration": config["exaggeration"],
            "temperature": config["temperature"],
            "cfg_weight": config["cfg_weight"]
        }
    })


@app.route('/voices', methods=['GET'])
def list_voices():
    """List all available voices."""
    voices = []
    for voice_id, config in VOICE_LIBRARY.items():
        voices.append({
            "id": voice_id,
            "name": config["name"],
            "language": config["language"],
            "description": config["description"],
            "quality": config.get("quality", "high"),
            "tags": config.get("tags", [])
        })
    
    return jsonify({
        "voices": voices,
        "total": len(voices)
    })


@app.route('/voices/<voice_id>', methods=['GET'])
def get_voice(voice_id: str):
    """Get details about a specific voice."""
    if voice_id not in VOICE_LIBRARY:
        return jsonify({"error": f"Voice '{voice_id}' not found"}), 404
    
    config = VOICE_LIBRARY[voice_id]
    
    # Find which characters use this voice
    characters_using_voice = [
        char_id for char_id, char_config in CHARACTER_VOICES.items()
        if char_config.get("voice_id") == voice_id
    ]
    
    return jsonify({
        "id": voice_id,
        "name": config["name"],
        "language": config["language"],
        "description": config["description"],
        "quality": config.get("quality", "high"),
        "tags": config.get("tags", []),
        "used_by_characters": characters_using_voice
    })


@app.route('/characters/<character_id>/voice', methods=['POST'])
def set_character_voice(character_id: str):
    """
    Change the voice for a character.
    
    Request JSON:
    {
        "voice_id": "friendly"
    }
    """
    try:
        if character_id not in CHARACTER_VOICES:
            return jsonify({
                "error": f"Character '{character_id}' not found"
            }), 404
        
        data = request.get_json()
        if not data or "voice_id" not in data:
            return jsonify({"error": "Missing 'voice_id' field"}), 400
        
        voice_id = data["voice_id"]
        
        if voice_id not in VOICE_LIBRARY:
            return jsonify({
                "error": f"Voice '{voice_id}' not found",
                "available_voices": list(VOICE_LIBRARY.keys())
            }), 400
        
        # Update the character's voice
        CHARACTER_VOICES[character_id]["voice_id"] = voice_id
        
        logger.info(f"Updated character '{character_id}' to use voice '{voice_id}'")
        
        return jsonify({
            "success": True,
            "character": character_id,
            "voice_id": voice_id,
            "voice_name": VOICE_LIBRARY[voice_id]["name"]
        }), 200
    
    except Exception as e:
        logger.error(f"Error updating character voice: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/languages', methods=['GET'])
def list_languages():
    """List all supported languages."""
    return jsonify({
        "languages": SUPPORTED_LANGUAGES,
        "total": len(SUPPORTED_LANGUAGES)
    })


@app.route('/tts', methods=['POST'])
def generate_tts():
    """
    Generate TTS audio from text.
    
    Request JSON:
    {
        "text": "Hello world",
        "character_id": "narrator",  // optional, defaults to "narrator"
        "language": "en",  // optional, defaults to character's language
        "max_tokens": 400  // optional, defaults to 400
    }
    
    Response: Audio file (WAV format)
    """
    try:
        data = request.get_json()
        
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text = str(data["text"]).strip()
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        if len(text) > 500:
            return jsonify({"error": "Text too long (max 500 characters)"}), 400
        
        character_id = data.get("character_id", "narrator")
        max_tokens = int(data.get("max_tokens", 400))
        max_tokens = max(100, min(max_tokens, 1000))  # Clamp to 100-1000
        
        # Generate audio
        audio_bytes, sample_rate, duration = generate_audio_bytes(
            text=text,
            character_id=character_id,
            max_tokens=max_tokens
        )
        
        # Return as audio file
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype='audio/wav',
            as_attachment=True,
            download_name=f"tts_{uuid.uuid4().hex[:8]}.wav"
        )
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/tts-json', methods=['POST'])
def generate_tts_json():
    """
    Generate TTS audio and return as JSON with base64 encoded audio.
    
    Request JSON:
    {
        "text": "Hello world",
        "character_id": "narrator",  // optional
        "max_tokens": 400  // optional
    }
    
    Response JSON:
    {
        "success": true,
        "audio": "base64_encoded_wav_data",
        "sample_rate": 24000,
        "duration": 2.5,
        "character_id": "narrator"
    }
    """
    try:
        import base64
        
        data = request.get_json()
        
        if not data or "text" not in data:
            return jsonify({
                "success": False,
                "error": "Missing 'text' field"
            }), 400
        
        text = str(data["text"]).strip()
        if not text:
            return jsonify({
                "success": False,
                "error": "Text cannot be empty"
            }), 400
        
        character_id = data.get("character_id", "narrator")
        max_tokens = int(data.get("max_tokens", 400))
        max_tokens = max(100, min(max_tokens, 1000))
        
        # Generate audio
        audio_bytes, sample_rate, duration = generate_audio_bytes(
            text=text,
            character_id=character_id,
            max_tokens=max_tokens
        )
        
        # Encode as base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return jsonify({
            "success": True,
            "audio": audio_base64,
            "sample_rate": int(sample_rate),
            "duration": round(duration, 2),
            "character_id": character_id,
            "text_length": len(text)
        })
        
    except Exception as e:
        logger.error(f"TTS JSON generation error: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@app.route('/tts-stream', methods=['POST'])
def stream_tts():
    """
    Stream TTS generation (useful for OpenRouter integration).
    Accepts streaming text input and returns audio.
    
    Request JSON:
    {
        "text": "Hello world",
        "character_id": "narrator",
        "max_tokens": 400
    }
    """
    return generate_tts()


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


def create_app():
    """Application factory."""
    logger.info("Initializing Chatterbox TTS API Server")
    logger.info(f"Device: {DEVICE}")
    logger.info(f"Available characters: {list(CHARACTER_VOICES.keys())}")
    logger.info(f"Supported languages: {len(SUPPORTED_LANGUAGES)}")
    return app


if __name__ == '__main__':
    app = create_app()
    
    logger.info("=" * 60)
    logger.info("Chatterbox TTS API Server - AWS Production Deployment")
    logger.info("=" * 60)
    logger.info(f"Device: {DEVICE}")
    logger.info(f"API Port: {API_PORT}")
    logger.info(f"Max Text Length: {MAX_TEXT_LENGTH}")
    logger.info(f"Cache Enabled: {CACHE_ENABLED}")
    logger.info(f"Batch Size: {BATCH_SIZE}")
    logger.info("=" * 60)
    
    # Load model on startup
    try:
        logger.info("Loading TTS model...")
        get_or_load_model()
        logger.info("✓ Model loaded successfully")
    except Exception as e:
        logger.error(f"✗ Failed to load model on startup: {e}")
        logger.info("Server will attempt to load model on first request")
    
    logger.info(f"Loaded {len(VOICE_LIBRARY)} voices and {len(CHARACTER_VOICES)} characters")
    
    logger.info("=" * 60)
    logger.info("Available endpoints:")
    logger.info("  GET  /health                      - Health check with GPU info")
    logger.info("  POST /generate-audio              - OpenRouter integration (primary)")
    logger.info("  POST /tts                         - Generate TTS audio file")
    logger.info("  POST /tts-json                    - Generate TTS with base64 response")
    logger.info("  GET  /characters                  - List available characters")
    logger.info("  GET  /characters/<id>             - Get character details")
    logger.info("  POST /characters/<id>/voice       - Change character's voice")
    logger.info("  GET  /voices                      - List available voices")
    logger.info("  GET  /voices/<voice_id>           - Get voice details")
    logger.info("  GET  /languages                   - List supported languages")
    logger.info("=" * 60)
    
    # Run server - production-ready configuration
    app.run(
        host='0.0.0.0',
        port=API_PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )
