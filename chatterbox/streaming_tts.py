"""
Streaming TTS utilities for chunked audio generation
Dramatically reduces perceived latency by generating and playing audio in chunks
"""

import re
import json
import base64
from typing import List, Generator, Tuple
import logging

logger = logging.getLogger(__name__)


def split_text_into_chunks(text: str, max_chars: int = 150, max_sentences: int = 3) -> List[str]:
    """
    Split text into optimal chunks for TTS generation.
    
    Strategy:
    1. Split by sentences (. ! ?)
    2. Group sentences until reaching max_chars or max_sentences
    3. Ensure each chunk is meaningful (not too short)
    
    Args:
        text: Input text to split
        max_chars: Maximum characters per chunk (default 150)
        max_sentences: Maximum sentences per chunk (default 3)
    
    Returns:
        List of text chunks ready for TTS generation
    """
    # Split into sentences (preserve punctuation)
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(sentence_pattern, text.strip())
    
    if not sentences:
        return []
    
    chunks = []
    current_chunk = ""
    sentence_count = 0
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        # Check if adding this sentence would exceed limits
        potential_chunk = (current_chunk + " " + sentence).strip()
        
        if len(potential_chunk) > max_chars or sentence_count >= max_sentences:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
            sentence_count = 1
        else:
            # Add to current chunk
            current_chunk = potential_chunk
            sentence_count += 1
    
    # Add final chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    # Log chunking statistics
    logger.info(f"Split text into {len(chunks)} chunks (avg {sum(len(c) for c in chunks) // len(chunks) if chunks else 0} chars/chunk)")
    
    return chunks


def generate_streaming_tts(
    text: str,
    character_id: str,
    generate_audio_fn,
    max_chunk_chars: int = 150
) -> Generator[dict, None, None]:
    """
    Generate TTS audio in chunks and yield as ready.
    
    This allows frontend to start playing audio immediately while
    subsequent chunks are still generating.
    
    Args:
        text: Full text to convert to speech
        character_id: Character voice to use
        generate_audio_fn: Function to generate audio bytes
        max_chunk_chars: Maximum characters per chunk
    
    Yields:
        dict with chunk metadata and audio data:
        {
            "chunk_index": 0,
            "total_chunks": 3,
            "text": "First sentence.",
            "audio": "base64_encoded_wav",
            "sample_rate": 24000,
            "duration": 1.5,
            "is_final": false
        }
    """
    # Split text into chunks
    chunks = split_text_into_chunks(text, max_chars=max_chunk_chars)
    
    if not chunks:
        logger.warning("No chunks generated from text")
        return
    
    total_chunks = len(chunks)
    logger.info(f"Streaming {total_chunks} chunks for character '{character_id}'")
    
    # Generate and yield each chunk
    for i, chunk_text in enumerate(chunks):
        try:
            logger.info(f"Generating chunk {i+1}/{total_chunks}: '{chunk_text[:50]}...'")
            
            # Generate audio for this chunk
            audio_bytes, sample_rate, duration = generate_audio_fn(
                text=chunk_text,
                character_id=character_id,
                use_cache=True  # Cache individual chunks
            )
            
            # Encode to base64
            audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # Yield chunk data
            chunk_data = {
                "chunk_index": i,
                "total_chunks": total_chunks,
                "text": chunk_text,
                "audio": audio_b64,
                "sample_rate": int(sample_rate),
                "duration": round(duration, 2),
                "is_final": (i == total_chunks - 1)
            }
            
            logger.info(f"Chunk {i+1}/{total_chunks} ready: {duration:.2f}s, {len(audio_bytes)} bytes")
            
            yield chunk_data
            
        except Exception as e:
            logger.error(f"Error generating chunk {i+1}/{total_chunks}: {e}")
            # Yield error chunk
            yield {
                "chunk_index": i,
                "total_chunks": total_chunks,
                "text": chunk_text,
                "error": str(e),
                "is_final": (i == total_chunks - 1)
            }


def estimate_generation_time(text_length: int, concurrency_factor: float = 1.0) -> float:
    """
    Estimate total generation time based on text length and concurrency.
    
    Args:
        text_length: Length of text in characters
        concurrency_factor: Multiplier for concurrent generation (0.33 for 3 models)
    
    Returns:
        Estimated time in seconds
    """
    # Empirical: ~25 chars/second generation rate on CPU
    base_time = text_length / 25.0
    
    # Apply concurrency factor
    estimated_time = base_time * concurrency_factor
    
    return max(2.0, estimated_time)  # Minimum 2 seconds


def create_chunk_metadata(chunks: List[str]) -> dict:
    """
    Create metadata about text chunks for frontend planning.
    
    Returns:
        {
            "total_chunks": 3,
            "chunks": [
                {"index": 0, "text_preview": "First...", "char_count": 120},
                {"index": 1, "text_preview": "Second...", "char_count": 95},
                ...
            ],
            "estimated_total_time": 15.5
        }
    """
    return {
        "total_chunks": len(chunks),
        "chunks": [
            {
                "index": i,
                "text_preview": chunk[:50] + ("..." if len(chunk) > 50 else ""),
                "char_count": len(chunk)
            }
            for i, chunk in enumerate(chunks)
        ],
        "estimated_total_time": estimate_generation_time(sum(len(c) for c in chunks))
    }
