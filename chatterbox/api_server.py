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
import tempfile
import shutil

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import io
import soundfile as sf

# Import chatterbox modules with fallback for different environments
try:
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
except ImportError as e:
    print(f"⚠️ Standard import failed: {e}")
    print("🔧 Attempting fallback import with adjusted Python path...")
    import sys
    import os
    
    # Add src directory to Python path as fallback
    current_dir = Path(__file__).parent
    src_path = current_dir / 'src'
    if src_path.exists():
        sys.path.insert(0, str(src_path))
        print(f"📁 Added to Python path: {src_path}")
    
    # Try import again
    try:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
        print("✅ Fallback import successful!")
    except ImportError as e2:
        print(f"❌ Fallback import also failed: {e2}")
        print("❌ Critical dependency missing - cannot start server")
        sys.exit(1)

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

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


# ============ Admin Functions ============

def load_config_file():
    """Load configuration from character_voices.json or voices_config.json"""
    config_files = ['character_voices.json', 'voices_config.json']
    
    for config_file in config_files:
        config_path = Path(__file__).parent.parent / config_file
        if config_path.exists():
            logger.info(f"Loading config from {config_path}")
            with open(config_path, 'r') as f:
                return json.load(f), config_path
    
    # Return default config if no file found
    logger.warning("No config file found, using default configuration")
    return {
        "voices": dict(VOICE_LIBRARY),
        "characters": dict(CHARACTER_VOICES)
    }, None

def save_config_file(config, config_path=None):
    """Save configuration to file"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / 'character_voices.json'
    
    logger.info(f"Saving config to {config_path}")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def reload_voices_and_characters():
    """Reload voices and characters from config file"""
    global VOICE_LIBRARY, CHARACTER_VOICES
    
    config, _ = load_config_file()
    if 'voices' in config:
        VOICE_LIBRARY.update(config['voices'])
    if 'characters' in config:
        CHARACTER_VOICES.update(config['characters'])
    
    logger.info(f"Reloaded {len(VOICE_LIBRARY)} voices and {len(CHARACTER_VOICES)} characters")

def upload_audio_to_s3(file_data, filename, voice_id):
    """Upload audio file to S3"""
    if not S3_ENABLED or not S3_CLIENT:
        raise Exception("S3 not configured")
    
    # Ensure safe filename
    safe_filename = secure_filename(filename)
    file_ext = Path(safe_filename).suffix
    s3_key = f"{S3_VOICES_PREFIX}{voice_id}{file_ext}"
    
    try:
        # Upload to S3
        S3_CLIENT.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_data,
            ContentType=f"audio/{file_ext[1:]}" if file_ext else "audio/wav"
        )
        
        # Generate public URL
        audio_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"Uploaded audio to S3: {audio_url}")
        return audio_url
        
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        raise

# ============ Admin API Routes ============

@app.route('/admin')
def admin_interface():
    """Serve admin interface"""
    return render_template_string(ADMIN_HTML_TEMPLATE)

@app.route('/admin/voices', methods=['GET'])
def admin_get_voices():
    """Get all voices with admin details"""
    try:
        voices_with_details = {}
        for voice_id, voice_data in VOICE_LIBRARY.items():
            # Find which characters use this voice
            using_characters = [
                char_id for char_id, char_data in CHARACTER_VOICES.items()
                if char_data.get('voice_id') == voice_id
            ]
            
            voices_with_details[voice_id] = {
                **voice_data,
                "used_by_characters": using_characters
            }
        
        return jsonify({
            "success": True,
            "voices": voices_with_details,
            "total": len(voices_with_details)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/characters', methods=['GET'])
def admin_get_characters():
    """Get all characters with admin details"""
    try:
        return jsonify({
            "success": True,
            "characters": CHARACTER_VOICES,
            "total": len(CHARACTER_VOICES)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/upload-voice', methods=['POST'])
def admin_upload_voice():
    """Upload new voice audio file"""
    try:
        # Check if file is in request
        if 'audio_file' not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"}), 400
        
        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Get form data
        voice_id = request.form.get('voice_id', '').strip()
        voice_name = request.form.get('voice_name', '').strip()
        description = request.form.get('description', '').strip()
        language = request.form.get('language', 'en').strip()
        tags = request.form.get('tags', '').strip()
        
        if not voice_id or not voice_name:
            return jsonify({"success": False, "error": "Voice ID and name are required"}), 400
        
        # Check if voice ID already exists
        if voice_id in VOICE_LIBRARY:
            return jsonify({"success": False, "error": f"Voice ID '{voice_id}' already exists"}), 400
        
        # Read file data
        file_data = file.read()
        
        # Upload to S3 (if enabled) or save locally
        if S3_ENABLED:
            audio_url = upload_audio_to_s3(file_data, file.filename, voice_id)
        else:
            # Save locally as fallback
            local_dir = Path(__file__).parent.parent / 'audio_samples'
            local_dir.mkdir(exist_ok=True)
            local_path = local_dir / f"{voice_id}_{file.filename}"
            with open(local_path, 'wb') as f:
                f.write(file_data)
            audio_url = str(local_path)
        
        # Create voice configuration
        voice_config = {
            "name": voice_name,
            "language": language,
            "audio_url": audio_url,
            "description": description or f"Custom voice: {voice_name}",
            "quality": "high",
            "tags": [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else ["custom"]
        }
        
        # Add to in-memory config
        VOICE_LIBRARY[voice_id] = voice_config
        
        # Save to configuration file
        config, config_path = load_config_file()
        if 'voices' not in config:
            config['voices'] = {}
        config['voices'][voice_id] = voice_config
        save_config_file(config, config_path)
        
        logger.info(f"Added new voice: {voice_id} -> {audio_url}")
        
        return jsonify({
            "success": True,
            "voice_id": voice_id,
            "voice_config": voice_config,
            "message": f"Voice '{voice_name}' uploaded successfully"
        })
        
    except Exception as e:
        logger.error(f"Voice upload failed: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/create-character', methods=['POST'])
def admin_create_character():
    """Create new character"""
    try:
        data = request.get_json()
        
        character_id = data.get('character_id', '').strip()
        character_name = data.get('character_name', '').strip()
        voice_id = data.get('voice_id', '').strip()
        language = data.get('language', 'en').strip()
        description = data.get('description', '').strip()
        system_prompt = data.get('system_prompt', '').strip()
        
        # Generation parameters
        exaggeration = float(data.get('exaggeration', 0.5))
        temperature = float(data.get('temperature', 0.7))
        cfg_weight = float(data.get('cfg_weight', 0.6))
        
        # UI metadata
        emoji = data.get('emoji', '🤖').strip()
        color = data.get('color', '#4A90E2').strip()
        
        if not character_id or not character_name or not voice_id:
            return jsonify({"success": False, "error": "Character ID, name, and voice ID are required"}), 400
        
        if character_id in CHARACTER_VOICES:
            return jsonify({"success": False, "error": f"Character ID '{character_id}' already exists"}), 400
        
        if voice_id not in VOICE_LIBRARY:
            return jsonify({"success": False, "error": f"Voice ID '{voice_id}' does not exist"}), 400
        
        # Create character configuration
        character_config = {
            "name": character_name,
            "voice_id": voice_id,
            "language": language,
            "description": description or f"Character: {character_name}",
            "exaggeration": exaggeration,
            "temperature": temperature,
            "cfg_weight": cfg_weight
        }
        
        # Add optional fields
        if system_prompt:
            character_config["system_prompt"] = system_prompt
        if emoji or color:
            character_config["metadata"] = {}
            if emoji:
                character_config["metadata"]["emoji"] = emoji
            if color:
                character_config["metadata"]["color"] = color
        
        # Add to in-memory config
        CHARACTER_VOICES[character_id] = character_config
        
        # Save to configuration file
        config, config_path = load_config_file()
        if 'characters' not in config:
            config['characters'] = {}
        config['characters'][character_id] = character_config
        save_config_file(config, config_path)
        
        logger.info(f"Created new character: {character_id}")
        
        return jsonify({
            "success": True,
            "character_id": character_id,
            "character_config": character_config,
            "message": f"Character '{character_name}' created successfully"
        })
        
    except Exception as e:
        logger.error(f"Character creation failed: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/delete-voice/<voice_id>', methods=['DELETE'])
def admin_delete_voice(voice_id):
    """Delete voice (if not used by any character)"""
    try:
        if voice_id not in VOICE_LIBRARY:
            return jsonify({"success": False, "error": f"Voice '{voice_id}' does not exist"}), 404
        
        # Check if voice is used by any character
        using_characters = [
            char_id for char_id, char_data in CHARACTER_VOICES.items()
            if char_data.get('voice_id') == voice_id
        ]
        
        if using_characters:
            return jsonify({
                "success": False,
                "error": f"Voice '{voice_id}' is used by characters: {', '.join(using_characters)}"
            }), 400
        
        # Remove from memory
        del VOICE_LIBRARY[voice_id]
        
        # Remove from config file
        config, config_path = load_config_file()
        if 'voices' in config and voice_id in config['voices']:
            del config['voices'][voice_id]
            save_config_file(config, config_path)
        
        logger.info(f"Deleted voice: {voice_id}")
        
        return jsonify({
            "success": True,
            "message": f"Voice '{voice_id}' deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Voice deletion failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/delete-character/<character_id>', methods=['DELETE'])
def admin_delete_character(character_id):
    """Delete character"""
    try:
        if character_id not in CHARACTER_VOICES:
            return jsonify({"success": False, "error": f"Character '{character_id}' does not exist"}), 404
        
        # Remove from memory
        del CHARACTER_VOICES[character_id]
        
        # Remove from config file
        config, config_path = load_config_file()
        if 'characters' in config and character_id in config['characters']:
            del config['characters'][character_id]
            save_config_file(config, config_path)
        
        logger.info(f"Deleted character: {character_id}")
        
        return jsonify({
            "success": True,
            "message": f"Character '{character_id}' deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Character deletion failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/test-voice/<voice_id>', methods=['POST'])
def admin_test_voice(voice_id):
    """Test a voice by generating sample audio"""
    try:
        data = request.get_json() or {}
        test_text = data.get('text', "Hello, this is a test of the voice.")
        
        if voice_id not in VOICE_LIBRARY:
            return jsonify({"success": False, "error": f"Voice '{voice_id}' not found"}), 404
        
        # Generate audio using a temporary character
        temp_character = {
            "voice_id": voice_id,
            "language": "en",
            "exaggeration": 0.5,
            "temperature": 0.7,
            "cfg_weight": 0.6
        }
        
        # Temporarily add test character
        test_char_id = f"__test__{voice_id}"
        CHARACTER_VOICES[test_char_id] = temp_character
        
        try:
            audio_bytes, sample_rate, duration = generate_audio_bytes(
                test_text, test_char_id, use_cache=False
            )
            
            # Convert to base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            return jsonify({
                "success": True,
                "audio": audio_b64,
                "duration": duration,
                "sample_rate": sample_rate,
                "text": test_text
            })
            
        finally:
            # Clean up temp character
            if test_char_id in CHARACTER_VOICES:
                del CHARACTER_VOICES[test_char_id]
        
    except Exception as e:
        logger.error(f"Voice test failed: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/reload-config', methods=['POST'])
def admin_reload_config():
    """Reload configuration from file"""
    try:
        reload_voices_and_characters()
        return jsonify({
            "success": True,
            "message": f"Reloaded {len(VOICE_LIBRARY)} voices and {len(CHARACTER_VOICES)} characters"
        })
    except Exception as e:
        logger.error(f"Config reload failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/admin/test-s3', methods=['GET'])
def admin_test_s3():
    """Test S3 connection and configuration"""
    try:
        if not S3_ENABLED:
            return jsonify({
                "success": False, 
                "error": "S3 is not enabled",
                "s3_enabled": False,
                "boto3_available": BOTO3_AVAILABLE,
                "bucket": S3_BUCKET
            })
        
        if not S3_CLIENT:
            return jsonify({
                "success": False, 
                "error": "S3 client not initialized",
                "s3_enabled": S3_ENABLED,
                "boto3_available": BOTO3_AVAILABLE,
                "bucket": S3_BUCKET
            })
        
        # Test bucket access by listing objects
        response = S3_CLIENT.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=S3_VOICES_PREFIX,
            MaxKeys=1
        )
        
        # Test credentials by uploading a small test file
        test_key = f"{S3_VOICES_PREFIX}test_connection.txt"
        S3_CLIENT.put_object(
            Bucket=S3_BUCKET,
            Key=test_key,
            Body=b"S3 connection test",
            ContentType="text/plain"
        )
        
        # Clean up test file
        S3_CLIENT.delete_object(Bucket=S3_BUCKET, Key=test_key)
        
        return jsonify({
            "success": True,
            "message": "S3 connection successful",
            "s3_enabled": True,
            "boto3_available": True,
            "bucket": S3_BUCKET,
            "region": S3_REGION,
            "voices_prefix": S3_VOICES_PREFIX,
            "audio_prefix": S3_AUDIO_PREFIX
        })
        
    except Exception as e:
        logger.error(f"S3 connection test failed: {e}")
        return jsonify({
            "success": False,
            "error": f"S3 test failed: {str(e)}",
            "s3_enabled": S3_ENABLED,
            "boto3_available": BOTO3_AVAILABLE,
            "bucket": S3_BUCKET
        }), 500


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


# ============ Admin Interface HTML Template ============

ADMIN_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatterbox TTS Admin</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }
        
        .tab {
            flex: 1;
            padding: 15px 20px;
            cursor: pointer;
            border: none;
            background: transparent;
            font-size: 1em;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .tab.active {
            background: white;
            border-bottom-color: #4a90e2;
            color: #4a90e2;
            font-weight: 600;
        }
        
        .tab-content {
            padding: 30px;
        }
        
        .tab-pane {
            display: none;
        }
        
        .tab-pane.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
            color: #495057;
        }
        
        .form-control {
            width: 100%;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.3s ease;
        }
        
        .form-control:focus {
            outline: none;
            border-color: #4a90e2;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #4a90e2 0%, #357abd 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(74, 144, 226, 0.3);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
        }
        
        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(231, 76, 60, 0.3);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
            color: white;
        }
        
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(46, 204, 113, 0.3);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
            color: white;
        }
        
        .btn-secondary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(108, 117, 125, 0.3);
        }
        
        .status-indicator {
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.9em;
            font-weight: 600;
            min-width: 80px;
            text-align: center;
        }
        
        .status-indicator.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-indicator.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status-indicator.loading {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: none;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border-left: 4px solid #28a745;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border-left: 4px solid #dc3545;
        }
        
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .card {
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }
        
        .card:hover {
            border-color: #4a90e2;
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        }
        
        .card-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        
        .card-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #495057;
            margin: 0;
        }
        
        .card-actions {
            display: flex;
            gap: 10px;
        }
        
        .btn-small {
            padding: 6px 12px;
            font-size: 0.9em;
        }
        
        .voice-info, .character-info {
            margin-bottom: 10px;
        }
        
        .voice-info strong, .character-info strong {
            color: #4a90e2;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #6c757d;
        }
        
        .loading.show {
            display: block;
        }
        
        .file-upload {
            position: relative;
            display: inline-block;
            cursor: pointer;
            width: 100%;
        }
        
        .file-upload input[type="file"] {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        .file-upload-label {
            display: block;
            padding: 20px;
            border: 2px dashed #4a90e2;
            border-radius: 8px;
            text-align: center;
            color: #4a90e2;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .file-upload:hover .file-upload-label {
            background: rgba(74, 144, 226, 0.1);
            border-color: #357abd;
        }
        
        .range-group {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
        }
        
        .range-item {
            text-align: center;
        }
        
        .range-item label {
            display: block;
            margin-bottom: 5px;
            font-size: 0.9em;
            color: #495057;
        }
        
        .range-item input[type="range"] {
            width: 100%;
            margin: 10px 0;
        }
        
        .range-item .value {
            font-weight: 600;
            color: #4a90e2;
            font-size: 1.1em;
        }
        
        audio {
            width: 100%;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ Chatterbox TTS Admin</h1>
            <p>Manage voices, characters, and audio generation settings</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('voices')">🎵 Voices</button>
            <button class="tab" onclick="showTab('characters')">🤖 Characters</button>
            <button class="tab" onclick="showTab('upload')">⬆️ Upload Voice</button>
            <button class="tab" onclick="showTab('create')">✨ Create Character</button>
        </div>
        
        <div class="tab-content">
            <!-- Voices Tab -->
            <div id="voices-tab" class="tab-pane active">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2>Voice Library</h2>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <button class="btn btn-secondary" onclick="testS3Connection()">🔗 Test S3</button>
                        <button class="btn btn-primary" onclick="loadVoices()">🔄 Refresh</button>
                        <span id="s3-status" class="status-indicator"></span>
                    </div>
                </div>
                <div id="voices-container">
                    <div class="loading show">Loading voices...</div>
                </div>
            </div>
            
            <!-- Characters Tab -->
            <div id="characters-tab" class="tab-pane">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2>Character Profiles</h2>
                    <button class="btn btn-primary" onclick="loadCharacters()">🔄 Refresh</button>
                </div>
                <div id="characters-container">
                    <div class="loading show">Loading characters...</div>
                </div>
            </div>
            
            <!-- Upload Voice Tab -->
            <div id="upload-tab" class="tab-pane">
                <h2>Upload New Voice</h2>
                <div id="upload-messages"></div>
                
                <form id="upload-form" onsubmit="uploadVoice(event)">
                    <div class="form-group">
                        <label>Audio File (WAV, MP3, or FLAC)</label>
                        <div class="file-upload">
                            <input type="file" name="audio_file" accept=".wav,.mp3,.flac" required>
                            <div class="file-upload-label">
                                🎵 Click to select audio file or drag & drop
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div class="form-group">
                            <label for="voice_id">Voice ID *</label>
                            <input type="text" class="form-control" name="voice_id" placeholder="e.g., my_voice" required>
                            <small>Unique identifier (letters, numbers, underscores only)</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="voice_name">Voice Name *</label>
                            <input type="text" class="form-control" name="voice_name" placeholder="e.g., My Custom Voice" required>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Description</label>
                        <textarea class="form-control" name="description" rows="3" placeholder="Describe this voice..."></textarea>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div class="form-group">
                            <label for="language">Language</label>
                            <select class="form-control" name="language">
                                <option value="en">English</option>
                                <option value="es">Spanish</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="it">Italian</option>
                                <option value="pt">Portuguese</option>
                                <option value="pl">Polish</option>
                                <option value="tr">Turkish</option>
                                <option value="ru">Russian</option>
                                <option value="nl">Dutch</option>
                                <option value="cs">Czech</option>
                                <option value="ar">Arabic</option>
                                <option value="zh-cn">Chinese (Simplified)</option>
                                <option value="ja">Japanese</option>
                                <option value="hu">Hungarian</option>
                                <option value="ko">Korean</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="tags">Tags (comma separated)</label>
                            <input type="text" class="form-control" name="tags" placeholder="e.g., calm, professional, male">
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">⬆️ Upload Voice</button>
                </form>
            </div>
            
            <!-- Create Character Tab -->
            <div id="create-tab" class="tab-pane">
                <h2>Create New Character</h2>
                <div id="create-messages"></div>
                
                <form id="create-form" onsubmit="createCharacter(event)">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div class="form-group">
                            <label for="character_id">Character ID *</label>
                            <input type="text" class="form-control" name="character_id" placeholder="e.g., my_character" required>
                            <small>Unique identifier (letters, numbers, underscores only)</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="character_name">Character Name *</label>
                            <input type="text" class="form-control" name="character_name" placeholder="e.g., My Character" required>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="voice_id_select">Voice *</label>
                        <select class="form-control" name="voice_id" id="voice_id_select" required>
                            <option value="">Select a voice...</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Description</label>
                        <textarea class="form-control" name="description" rows="2" placeholder="Describe this character..."></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="system_prompt">System Prompt (Optional)</label>
                        <textarea class="form-control" name="system_prompt" rows="3" placeholder="Instructions for this character's behavior..."></textarea>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div class="form-group">
                            <label for="language">Language</label>
                            <select class="form-control" name="language">
                                <option value="en">English</option>
                                <option value="es">Spanish</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="it">Italian</option>
                                <option value="pt">Portuguese</option>
                                <option value="pl">Polish</option>
                                <option value="tr">Turkish</option>
                                <option value="ru">Russian</option>
                                <option value="nl">Dutch</option>
                                <option value="cs">Czech</option>
                                <option value="ar">Arabic</option>
                                <option value="zh-cn">Chinese (Simplified)</option>
                                <option value="ja">Japanese</option>
                                <option value="hu">Hungarian</option>
                                <option value="ko">Korean</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="emoji">Emoji</label>
                            <input type="text" class="form-control" name="emoji" placeholder="🤖" maxlength="2">
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="color">Color</label>
                        <input type="color" class="form-control" name="color" value="#4A90E2">
                    </div>
                    
                    <h3>Generation Parameters</h3>
                    <div class="range-group">
                        <div class="range-item">
                            <label>Exaggeration</label>
                            <input type="range" name="exaggeration" min="0" max="1" step="0.1" value="0.5" oninput="updateRangeValue(this)">
                            <div class="value">0.5</div>
                            <small>Speech expressiveness</small>
                        </div>
                        
                        <div class="range-item">
                            <label>Temperature</label>
                            <input type="range" name="temperature" min="0" max="1" step="0.1" value="0.7" oninput="updateRangeValue(this)">
                            <div class="value">0.7</div>
                            <small>Voice variation</small>
                        </div>
                        
                        <div class="range-item">
                            <label>CFG Weight</label>
                            <input type="range" name="cfg_weight" min="0" max="1" step="0.1" value="0.6" oninput="updateRangeValue(this)">
                            <div class="value">0.6</div>
                            <small>Voice adherence</small>
                        </div>
                    </div>
                    
                    <button type="submit" class="btn btn-primary">✨ Create Character</button>
                </form>
            </div>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            // Load data if needed
            if (tabName === 'voices') loadVoices();
            if (tabName === 'characters') loadCharacters();
            if (tabName === 'create') loadVoicesForSelect();
        }
        
        function updateRangeValue(input) {
            const valueDisplay = input.parentNode.querySelector('.value');
            valueDisplay.textContent = input.value;
        }
        
        function showMessage(containerId, message, type = 'success') {
            const container = document.getElementById(containerId);
            container.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
            setTimeout(() => {
                container.innerHTML = '';
            }, 5000);
        }
        
        async function loadVoices() {
            const container = document.getElementById('voices-container');
            container.innerHTML = '<div class="loading show">Loading voices...</div>';
            
            try {
                const response = await fetch('/admin/voices');
                const data = await response.json();
                
                if (data.success) {
                    displayVoices(data.voices);
                } else {
                    container.innerHTML = `<div class="alert alert-error">Error: ${data.error}</div>`;
                }
            } catch (error) {
                container.innerHTML = `<div class="alert alert-error">Failed to load voices: ${error.message}</div>`;
            }
        }
        
        function displayVoices(voices) {
            const container = document.getElementById('voices-container');
            
            if (Object.keys(voices).length === 0) {
                container.innerHTML = '<p>No voices found.</p>';
                return;
            }
            
            let html = '<div class="cards-grid">';
            
            for (const [voiceId, voice] of Object.entries(voices)) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title">${voice.name} (${voiceId})</h3>
                            <div class="card-actions">
                                <button class="btn btn-success btn-small" onclick="testVoice('${voiceId}')">🎵 Test</button>
                                <button class="btn btn-danger btn-small" onclick="deleteVoice('${voiceId}')">🗑️ Delete</button>
                            </div>
                        </div>
                        
                        <div class="voice-info">
                            <p><strong>Language:</strong> ${voice.language}</p>
                            <p><strong>Description:</strong> ${voice.description}</p>
                            <p><strong>Quality:</strong> ${voice.quality}</p>
                            ${voice.tags ? `<p><strong>Tags:</strong> ${voice.tags.join(', ')}</p>` : ''}
                            ${voice.used_by_characters && voice.used_by_characters.length > 0 ? 
                                `<p><strong>Used by:</strong> ${voice.used_by_characters.join(', ')}</p>` : 
                                '<p><strong>Used by:</strong> No characters</p>'
                            }
                        </div>
                        
                        <div id="test-${voiceId}"></div>
                    </div>
                `;
            }
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        async function loadCharacters() {
            const container = document.getElementById('characters-container');
            container.innerHTML = '<div class="loading show">Loading characters...</div>';
            
            try {
                const response = await fetch('/admin/characters');
                const data = await response.json();
                
                if (data.success) {
                    displayCharacters(data.characters);
                } else {
                    container.innerHTML = `<div class="alert alert-error">Error: ${data.error}</div>`;
                }
            } catch (error) {
                container.innerHTML = `<div class="alert alert-error">Failed to load characters: ${error.message}</div>`;
            }
        }
        
        function displayCharacters(characters) {
            const container = document.getElementById('characters-container');
            
            if (Object.keys(characters).length === 0) {
                container.innerHTML = '<p>No characters found.</p>';
                return;
            }
            
            let html = '<div class="cards-grid">';
            
            for (const [characterId, character] of Object.entries(characters)) {
                const emoji = character.metadata?.emoji || '🤖';
                const color = character.metadata?.color || '#4A90E2';
                
                html += `
                    <div class="card">
                        <div class="card-header">
                            <h3 class="card-title" style="color: ${color}">
                                ${emoji} ${character.name} (${characterId})
                            </h3>
                            <div class="card-actions">
                                <button class="btn btn-success btn-small" onclick="testCharacter('${characterId}')">🎵 Test</button>
                                <button class="btn btn-danger btn-small" onclick="deleteCharacter('${characterId}')">🗑️ Delete</button>
                            </div>
                        </div>
                        
                        <div class="character-info">
                            <p><strong>Voice:</strong> ${character.voice_id}</p>
                            <p><strong>Language:</strong> ${character.language}</p>
                            <p><strong>Description:</strong> ${character.description}</p>
                            ${character.system_prompt ? `<p><strong>System Prompt:</strong> ${character.system_prompt}</p>` : ''}
                            <p><strong>Parameters:</strong> 
                                Exaggeration: ${character.exaggeration}, 
                                Temperature: ${character.temperature}, 
                                CFG Weight: ${character.cfg_weight}
                            </p>
                        </div>
                        
                        <div id="test-char-${characterId}"></div>
                    </div>
                `;
            }
            
            html += '</div>';
            container.innerHTML = html;
        }
        
        // [Rest of JavaScript functions continue...]
        async function loadVoicesForSelect() {
            try {
                const response = await fetch('/admin/voices');
                const data = await response.json();
                
                if (data.success) {
                    const select = document.getElementById('voice_id_select');
                    select.innerHTML = '<option value="">Select a voice...</option>';
                    
                    for (const [voiceId, voice] of Object.entries(data.voices)) {
                        select.innerHTML += `<option value="${voiceId}">${voice.name} (${voiceId})</option>`;
                    }
                }
            } catch (error) {
                console.error('Failed to load voices for select:', error);
            }
        }
        
        async function uploadVoice(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const submitButton = event.target.querySelector('button[type="submit"]');
            
            submitButton.disabled = true;
            submitButton.textContent = '⏳ Uploading...';
            
            try {
                const response = await fetch('/admin/upload-voice', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('upload-messages', `✅ ${data.message}`, 'success');
                    event.target.reset();
                    document.querySelector('.file-upload-label').textContent = '🎵 Click to select audio file or drag & drop';
                } else {
                    showMessage('upload-messages', `❌ ${data.error}`, 'error');
                }
            } catch (error) {
                showMessage('upload-messages', `❌ Upload failed: ${error.message}`, 'error');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = '⬆️ Upload Voice';
            }
        }
        
        async function createCharacter(event) {
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());
            
            const submitButton = event.target.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            submitButton.textContent = '⏳ Creating...';
            
            try {
                const response = await fetch('/admin/create-character', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage('create-messages', `✅ ${result.message}`, 'success');
                    event.target.reset();
                    // Reset range values
                    document.querySelectorAll('input[type="range"]').forEach(input => {
                        input.value = input.defaultValue;
                        updateRangeValue(input);
                    });
                } else {
                    showMessage('create-messages', `❌ ${result.error}`, 'error');
                }
            } catch (error) {
                showMessage('create-messages', `❌ Creation failed: ${error.message}`, 'error');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = '✨ Create Character';
            }
        }
        
        async function testVoice(voiceId) {
            const testContainer = document.getElementById(`test-${voiceId}`);
            testContainer.innerHTML = '<div class="loading show">Generating test audio...</div>';
            
            try {
                const response = await fetch(`/admin/test-voice/${voiceId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: "Hello, this is a test of the voice." })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const audioUrl = `data:audio/wav;base64,${data.audio}`;
                    testContainer.innerHTML = `
                        <audio controls>
                            <source src="${audioUrl}" type="audio/wav">
                            Your browser does not support audio playback.
                        </audio>
                        <p><small>Duration: ${data.duration.toFixed(1)}s</small></p>
                    `;
                } else {
                    testContainer.innerHTML = `<div class="alert alert-error">Test failed: ${data.error}</div>`;
                }
            } catch (error) {
                testContainer.innerHTML = `<div class="alert alert-error">Test failed: ${error.message}</div>`;
            }
        }
        
        async function testCharacter(characterId) {
            const testContainer = document.getElementById(`test-char-${characterId}`);
            testContainer.innerHTML = '<div class="loading show">Generating test audio...</div>';
            
            try {
                const response = await fetch('/generate-audio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        text: "Hello, this is a test of the character voice.",
                        character: characterId
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const audioUrl = data.audio_url || `data:audio/wav;base64,${data.audio}`;
                    testContainer.innerHTML = `
                        <audio controls>
                            <source src="${audioUrl}" type="audio/wav">
                            Your browser does not support audio playback.
                        </audio>
                        <p><small>Duration: ${data.duration.toFixed(1)}s</small></p>
                    `;
                } else {
                    testContainer.innerHTML = `<div class="alert alert-error">Test failed: ${data.error}</div>`;
                }
            } catch (error) {
                testContainer.innerHTML = `<div class="alert alert-error">Test failed: ${error.message}</div>`;
            }
        }
        
        async function deleteVoice(voiceId) {
            if (!confirm(`Are you sure you want to delete voice "${voiceId}"?`)) return;
            
            try {
                const response = await fetch(`/admin/delete-voice/${voiceId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('voices-container', `✅ ${data.message}`, 'success');
                    loadVoices(); // Reload voices list
                } else {
                    showMessage('voices-container', `❌ ${data.error}`, 'error');
                }
            } catch (error) {
                showMessage('voices-container', `❌ Delete failed: ${error.message}`, 'error');
            }
        }
        
        async function deleteCharacter(characterId) {
            if (!confirm(`Are you sure you want to delete character "${characterId}"?`)) return;
            
            try {
                const response = await fetch(`/admin/delete-character/${characterId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showMessage('characters-container', `✅ ${data.message}`, 'success');
                    loadCharacters(); // Reload characters list
                } else {
                    showMessage('characters-container', `❌ ${data.error}`, 'error');
                }
            } catch (error) {
                showMessage('characters-container', `❌ Delete failed: ${error.message}`, 'error');
            }
        }
        
        // Test S3 Connection
        async function testS3Connection() {
            const statusEl = document.getElementById('s3-status');
            statusEl.textContent = 'Testing...';
            statusEl.className = 'status-indicator loading';
            
            try {
                const response = await fetch('/admin/test-s3');
                const data = await response.json();
                
                if (data.success) {
                    statusEl.textContent = '✅ S3 Connected';
                    statusEl.className = 'status-indicator success';
                    console.log('S3 Status:', data);
                } else {
                    statusEl.textContent = `❌ S3 Error`;
                    statusEl.className = 'status-indicator error';
                    console.error('S3 Error:', data);
                    alert(`S3 Connection Failed: ${data.error}`);
                }
            } catch (error) {
                statusEl.textContent = '❌ Network Error';
                statusEl.className = 'status-indicator error';
                console.error('S3 Test Error:', error);
                alert(`S3 Test Failed: ${error.message}`);
            }
        }
        
        // File upload drag & drop
        document.addEventListener('DOMContentLoaded', function() {
            const fileInput = document.querySelector('input[type="file"]');
            const fileLabel = document.querySelector('.file-upload-label');
            
            if (fileInput && fileLabel) {
                fileInput.addEventListener('change', function() {
                    if (this.files.length > 0) {
                        fileLabel.textContent = `📁 ${this.files[0].name}`;
                    }
                });
            }
            
            // Load initial data
            loadVoices();
            loadVoicesForSelect();
            
            // Test S3 connection on page load
            setTimeout(testS3Connection, 1000);
        });
    </script>
</body>
</html>
"""


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
    logger.info("  🔧 ADMIN INTERFACE:")
    logger.info("  GET  /admin                       - Admin web interface")
    logger.info("  GET  /admin/voices                - Admin voice management API")
    logger.info("  GET  /admin/characters            - Admin character management API")
    logger.info("  POST /admin/upload-voice          - Upload new voice audio")
    logger.info("  POST /admin/create-character      - Create new character")
    logger.info("  POST /admin/test-voice/<id>       - Test voice generation")
    logger.info("  GET  /admin/test-s3               - Test S3 connection")
    logger.info("  DELETE /admin/delete-voice/<id>   - Delete voice")
    logger.info("  DELETE /admin/delete-character/<id> - Delete character")
    logger.info("=" * 60)
    
    # Run server - production-ready configuration
    app.run(
        host='0.0.0.0',
        port=API_PORT,
        debug=False,
        use_reloader=False,
        threaded=True
    )
