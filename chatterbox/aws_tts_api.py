"""
Chatterbox AWS-Optimized TTS API Server
- GPU-optimized for AWS EC2 instances
- Streaming support for low-latency audio generation
- Integrated with OpenRouter/frontend chatbot service
- Production-ready with proper error handling and monitoring
"""

import torch
import numpy as np
import json
import uuid
import base64
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
import logging
import traceback
import os
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import io
import soundfile as sf

try:
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES
except ImportError:
    from mtl_tts import ChatterboxMultilingualTTS, SUPPORTED_LANGUAGES

# ============ Configuration ============
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Performance settings for AWS
BATCH_SIZE = 1  # Adjust based on GPU VRAM
MAX_CONCURRENT_REQUESTS = 4
ENABLE_FLASH_ATTENTION = True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# AWS/Production specific headers
CORS_ORIGINS = [
    "https://*.vercel.app",
    "https://*.vercel.sh",
    "http://localhost:3000",  # Local dev
    "http://localhost:8000",  # Local dev
]

# Character voice profiles - customize these with your character voices
CHARACTER_VOICES = {
    "narrator": {
        "name": "Narrator",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "exaggeration": 0.5,
        "temperature": 0.7,
        "cfg_weight": 0.6,
        "description": "Professional narrator voice",
        "character_name": "Narrator"
    },
    "assistant": {
        "name": "AI Assistant",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "exaggeration": 0.6,
        "temperature": 0.8,
        "cfg_weight": 0.5,
        "description": "Friendly AI assistant voice",
        "character_name": "Assistant"
    },
    "expert": {
        "name": "Expert",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "exaggeration": 0.4,
        "temperature": 0.6,
        "cfg_weight": 0.7,
        "description": "Knowledgeable expert voice",
        "character_name": "Expert"
    },
    "friendly": {
        "name": "Friendly Character",
        "language": "en",
        "audio_url": "https://storage.googleapis.com/chatterbox-demo-samples/mtl_prompts/en_f1.flac",
        "exaggeration": 0.7,
        "temperature": 0.9,
        "cfg_weight": 0.5,
        "description": "Warm and friendly voice",
        "character_name": "Friendly"
    }
}

# Initialize Flask app
app = Flask(__name__)

# Configure CORS for Vercel frontend
cors_config = {
    "origins": CORS_ORIGINS,
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Type", "X-Request-ID"],
    "supports_credentials": True,
    "max_age": 3600
}
CORS(app, resources={r"/api/*": cors_config})

# Global model instance
MODEL = None
EXECUTOR = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS)
ACTIVE_REQUESTS = 0
REQUEST_QUEUE: List[Dict] = []


def get_or_load_model():
    """Load the Chatterbox model if not already loaded."""
    global MODEL
    if MODEL is None:
        logger.info(f"Loading Chatterbox model on device: {DEVICE}")
        try:
            # Optimize model loading
            if DEVICE == "cuda":
                torch.cuda.empty_cache()
                torch.backends.cudnn.benchmark = True
                if ENABLE_FLASH_ATTENTION:
                    torch.backends.cuda.enable_flash_sdp(True)
            
            MODEL = ChatterboxMultilingualTTS.from_pretrained(DEVICE)
            logger.info(f"Model loaded successfully. Device: {MODEL.device}")
            
            # Log GPU info
            if DEVICE == "cuda":
                logger.info(f"GPU: {torch.cuda.get_device_name()}")
                logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            traceback.print_exc()
            raise
    return MODEL


def generate_audio_bytes(
    text: str,
    character_id: str = "narrator",
    max_tokens: int = 400,
    language_override: Optional[str] = None
) -> Tuple[bytes, int, float]:
    """
    Generate audio from text using a character voice profile.
    
    Returns: (audio_bytes, sample_rate, duration_seconds)
    """
    try:
        model = get_or_load_model()
        
        # Get character profile
        if character_id not in CHARACTER_VOICES:
            raise ValueError(
                f"Unknown character: {character_id}. "
                f"Available: {list(CHARACTER_VOICES.keys())}"
            )
        
        character = CHARACTER_VOICES[character_id]
        language = language_override or character["language"]
        
        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            language = character["language"]
            logger.warning(f"Language {language_override} not supported, using {language}")
        
        logger.info(
            f"Generating audio - Character: {character_id}, "
            f"Language: {language}, Text length: {len(text)}"
        )
        
        # Generate speech with proper error handling
        try:
            wav = model.generate(
                text=text[:300],
                language_id=language,
                audio_prompt_path=character["audio_url"],
                exaggeration=character["exaggeration"],
                temperature=character["temperature"],
                cfg_weight=character["cfg_weight"],
                max_new_tokens=max_tokens,
            )
        except Exception as e:
            logger.error(f"Model generation failed: {e}")
            raise
        
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
        
        logger.info(
            f"Audio generated successfully - "
            f"Size: {len(audio_bytes)} bytes, Duration: {duration:.1f}s"
        )
        return audio_bytes, model.sr, duration
        
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        traceback.print_exc()
        raise


# ============ API Routes ============

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for AWS load balancers."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "device": DEVICE,
        "model_loaded": MODEL is not None,
        "active_requests": ACTIVE_REQUESTS,
        "queue_length": len(REQUEST_QUEUE)
    })


@app.route('/api/v1/health', methods=['GET'])
def health_v1():
    """Health check endpoint for Vercel frontend."""
    gpu_info = {}
    if DEVICE == "cuda":
        gpu_info = {
            "gpu_available": True,
            "gpu_name": torch.cuda.get_device_name(),
            "vram_total_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
            "vram_allocated_gb": torch.cuda.memory_allocated() / 1e9,
            "vram_reserved_gb": torch.cuda.memory_reserved() / 1e9,
        }
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "device": DEVICE,
        "model_loaded": MODEL is not None,
        "active_requests": ACTIVE_REQUESTS,
        "queue_length": len(REQUEST_QUEUE),
        "gpu": gpu_info
    })


@app.route('/api/v1/characters', methods=['GET'])
def list_characters():
    """List all available character voice profiles."""
    characters = []
    for char_id, config in CHARACTER_VOICES.items():
        characters.append({
            "id": char_id,
            "name": config["name"],
            "character_name": config.get("character_name", config["name"]),
            "language": config["language"],
            "description": config["description"]
        })
    
    return jsonify({
        "characters": characters,
        "total": len(characters)
    })


@app.route('/api/v1/characters/<character_id>', methods=['GET'])
def get_character(character_id: str):
    """Get details about a specific character."""
    if character_id not in CHARACTER_VOICES:
        return jsonify({"error": f"Character '{character_id}' not found"}), 404
    
    config = CHARACTER_VOICES[character_id]
    return jsonify({
        "id": character_id,
        "name": config["name"],
        "character_name": config.get("character_name", config["name"]),
        "language": config["language"],
        "description": config["description"],
        "parameters": {
            "exaggeration": config["exaggeration"],
            "temperature": config["temperature"],
            "cfg_weight": config["cfg_weight"]
        }
    })


@app.route('/api/v1/languages', methods=['GET'])
def list_languages():
    """List all supported languages."""
    return jsonify({
        "languages": SUPPORTED_LANGUAGES,
        "total": len(SUPPORTED_LANGUAGES)
    })


@app.route('/api/v1/tts', methods=['POST'])
def generate_tts():
    """
    Generate TTS audio from text (returns WAV file).
    
    Request JSON:
    {
        "text": "Hello world",
        "character_id": "narrator",  // optional
        "language": "en",  // optional
        "max_tokens": 400,  // optional
        "format": "wav"  // optional: wav, base64
    }
    
    Response: WAV audio file or JSON with base64 audio
    """
    global ACTIVE_REQUESTS
    
    try:
        ACTIVE_REQUESTS += 1
        data = request.get_json()
        
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text = str(data["text"]).strip()
        if not text:
            return jsonify({"error": "Text cannot be empty"}), 400
        
        if len(text) > 500:
            return jsonify({
                "error": "Text too long (max 500 characters)",
                "text_length": len(text)
            }), 400
        
        character_id = data.get("character_id", "narrator")
        language = data.get("language")
        max_tokens = int(data.get("max_tokens", 400))
        max_tokens = max(100, min(max_tokens, 1000))
        response_format = data.get("format", "wav").lower()
        
        # Generate audio
        audio_bytes, sample_rate, duration = generate_audio_bytes(
            text=text,
            character_id=character_id,
            max_tokens=max_tokens,
            language_override=language
        )
        
        if response_format == "base64":
            # Return as JSON with base64 encoded audio
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            return jsonify({
                "success": True,
                "audio": audio_base64,
                "audio_format": "wav",
                "sample_rate": int(sample_rate),
                "duration_seconds": round(duration, 2),
                "character_id": character_id,
                "text_length": len(text)
            })
        else:
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
    finally:
        ACTIVE_REQUESTS -= 1


@app.route('/api/v1/tts-json', methods=['POST'])
def generate_tts_json():
    """
    Generate TTS audio and return as JSON with base64 encoded audio.
    
    Request JSON:
    {
        "text": "Hello world",
        "character_id": "narrator",  // optional
        "language": "en",  // optional
        "max_tokens": 400  // optional
    }
    
    Response JSON:
    {
        "success": true,
        "audio": "base64_encoded_wav_data",
        "audio_format": "wav",
        "sample_rate": 24000,
        "duration_seconds": 2.5,
        "character_id": "narrator",
        "text_length": 12
    }
    """
    return generate_tts()  # Just call with format=base64


@app.route('/api/v1/tts-batch', methods=['POST'])
def generate_tts_batch():
    """
    Generate TTS audio for multiple texts (batch processing).
    
    Request JSON:
    {
        "requests": [
            {
                "id": "msg_1",
                "text": "Hello world",
                "character_id": "narrator"
            },
            {
                "id": "msg_2",
                "text": "How are you?",
                "character_id": "assistant"
            }
        ],
        "format": "base64"  // optional
    }
    
    Response JSON:
    {
        "success": true,
        "results": [
            {
                "id": "msg_1",
                "success": true,
                "audio": "base64...",
                "duration_seconds": 1.2
            },
            {
                "id": "msg_2",
                "success": true,
                "audio": "base64...",
                "duration_seconds": 1.8
            }
        ]
    }
    """
    try:
        data = request.get_json()
        if not data or "requests" not in data:
            return jsonify({"error": "Missing 'requests' field"}), 400
        
        requests_list = data.get("requests", [])
        response_format = data.get("format", "base64").lower()
        
        results = []
        for req in requests_list:
            try:
                req_id = req.get("id", str(uuid.uuid4().hex[:8]))
                text = str(req.get("text", "")).strip()
                character_id = req.get("character_id", "narrator")
                
                if not text:
                    results.append({
                        "id": req_id,
                        "success": False,
                        "error": "Text cannot be empty"
                    })
                    continue
                
                audio_bytes, sample_rate, duration = generate_audio_bytes(
                    text=text,
                    character_id=character_id,
                    max_tokens=400
                )
                
                if response_format == "base64":
                    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                    results.append({
                        "id": req_id,
                        "success": True,
                        "audio": audio_base64,
                        "duration_seconds": round(duration, 2)
                    })
                else:
                    results.append({
                        "id": req_id,
                        "success": True,
                        "audio_size_bytes": len(audio_bytes),
                        "duration_seconds": round(duration, 2)
                    })
                    
            except Exception as e:
                logger.error(f"Batch request {req.get('id')} failed: {e}")
                results.append({
                    "id": req.get("id", "unknown"),
                    "success": False,
                    "error": str(e)
                })
        
        return jsonify({
            "success": True,
            "results": results,
            "total": len(results)
        })
        
    except Exception as e:
        logger.error(f"Batch TTS generation error: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/tts-stream', methods=['POST'])
def stream_tts():
    """
    Stream TTS generation with chunked response.
    Useful for progressive audio playback in frontend.
    
    Request JSON:
    {
        "text": "Hello world",
        "character_id": "narrator"
    }
    
    Response: Streaming WAV audio
    """
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' field"}), 400
        
        text = str(data["text"]).strip()
        character_id = data.get("character_id", "narrator")
        max_tokens = int(data.get("max_tokens", 400))
        
        # Generate audio
        audio_bytes, sample_rate, duration = generate_audio_bytes(
            text=text,
            character_id=character_id,
            max_tokens=max_tokens
        )
        
        # Stream response
        def generate():
            chunk_size = 8192  # 8KB chunks
            for i in range(0, len(audio_bytes), chunk_size):
                yield audio_bytes[i:i + chunk_size]
        
        return Response(
            generate(),
            mimetype='audio/wav',
            headers={
                'Content-Disposition': f'attachment; filename="audio_{uuid.uuid4().hex[:8]}.wav"',
                'X-Duration-Seconds': str(duration),
                'X-Sample-Rate': str(sample_rate)
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming TTS error: {e}")
        return jsonify({"error": "Internal server error"}), 500


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"error": "Request body too large"}), 413


def create_app():
    """Application factory."""
    logger.info("=" * 60)
    logger.info("Initializing Chatterbox AWS TTS API Server")
    logger.info("=" * 60)
    logger.info(f"Device: {DEVICE}")
    logger.info(f"Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    logger.info(f"Flash Attention enabled: {ENABLE_FLASH_ATTENTION}")
    logger.info(f"Available characters: {list(CHARACTER_VOICES.keys())}")
    logger.info(f"Supported languages: {len(SUPPORTED_LANGUAGES)}")
    logger.info("=" * 60)
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Load model on startup
    try:
        get_or_load_model()
    except Exception as e:
        logger.error(f"Failed to load model on startup: {e}")
        logger.error("Server starting without model - will attempt lazy load on first request")
    
    # Run server
    # For production, use gunicorn instead:
    # gunicorn --workers 1 --threads 4 --worker-class gthread --bind 0.0.0.0:5000 aws_tts_api:app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        threaded=True
    )
