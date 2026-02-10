# Chatterbox TTS - Vercel Frontend Integration Guide

Complete guide for integrating Chatterbox TTS API with your Vercel/Next.js character chatbot frontend powered by OpenRouter.

## Table of Contents
1. [Quick Start](#quick-start)
2. [TypeScript Client](#typescript-client)
3. [React Integration](#react-integration)
4. [OpenRouter Integration](#openrouter-integration)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install the Client

Copy `chatterbox-tts-client.ts` to your Next.js project:

```bash
# Copy to your utilities folder
cp chatterbox-tts-client.ts ./lib/chatterbox-tts-client.ts
```

### 2. Setup Environment Variables

Add to `.env.local`:

```env
NEXT_PUBLIC_TTS_API_URL=https://chatterbox-api.charcat.chat
```

### 3. Basic Usage

```typescript
import { createTTSClient } from '@/lib/chatterbox-tts-client';

const ttsClient = createTTSClient(
  process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000'
);

// Generate audio
const response = await ttsClient.generateAudio({
  text: "Hello, I'm a character voice!",
  character: 'narrator',
});

console.log(`Generated ${response.duration}s of audio`);
```

---

## TypeScript Client

### `ChatterboxTTSClient`

Main client class for the TTS API.

#### Constructor

```typescript
const client = new ChatterboxTTSClient(apiUrl, {
  timeout: 30000,      // Request timeout in ms
  retryAttempts: 3,    // Number of retries
});
```

#### Methods

##### `healthCheck()`
Check if the API is available and GPU status:

```typescript
const health = await client.healthCheck();
console.log(health.status);        // "healthy"
console.log(health.device);        // "cuda" or "cpu"
console.log(health.gpu?.memory_allocated); // "2.5GB"
```

##### `getCharacters()`
Get available voice profiles:

```typescript
const characters = await client.getCharacters();
characters.forEach(char => {
  console.log(`${char.id}: ${char.name} (${char.language})`);
});
// Output:
// narrator: Narrator (en)
// assistant: AI Assistant (en)
// expert: Expert (en)
// friendly: Friendly Character (en)
```

##### `generateAudio()`
Generate audio with base64 response:

```typescript
const response = await client.generateAudio({
  text: "Your AI response here",
  character: 'narrator',        // optional
  returnFormat: 'base64',       // 'base64' or 'url'
  maxTokens: 400,               // optional
});

// Response
{
  success: true,
  audio: "UklGRi4...",           // base64 encoded WAV
  sample_rate: 24000,
  duration: 2.5,
  character: "narrator",
  generation_time_ms: 1234
}
```

##### `generateAudioBlob()`
Generate audio and return as Blob (easier for playback):

```typescript
const { blob, duration } = await client.generateAudioBlob({
  text: "Listen to this!",
  character: 'friendly',
});

// Create audio element
const audio = new Audio();
audio.src = URL.createObjectURL(blob);
audio.play();
```

##### `generatePlayableAudio()`
Generate audio with managed URL lifecycle:

```typescript
const { url, duration, revoke } = await client.generatePlayableAudio({
  text: "Perfect for React!",
  character: 'assistant',
});

// Use the URL in audio element
<audio src={url} controls />

// Clean up when done
revoke();
```

---

## React Integration

### Using the Hook

The easiest way to use TTS in React:

```typescript
import { useChatterboxTTS } from '@/lib/chatterbox-tts-client';

export function ChatMessage({ message, character }) {
  const { generateAudio, isLoading, error, audioUrl, duration } = 
    useChatterboxTTS(process.env.NEXT_PUBLIC_TTS_API_URL);

  const handlePlayAudio = () => {
    generateAudio(message, character);
  };

  return (
    <div>
      <p>{message}</p>
      
      <button onClick={handlePlayAudio} disabled={isLoading}>
        {isLoading ? 'Generating...' : '🔊 Play'}
      </button>

      {audioUrl && (
        <audio src={audioUrl} controls autoPlay />
      )}

      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
    </div>
  );
}
```

### Complete Chat Component Example

```typescript
'use client'; // For App Router

import React, { useState } from 'react';
import { useChatterboxTTS } from '@/lib/chatterbox-tts-client';

interface ChatMessage {
  id: string;
  text: string;
  character: string;
  role: 'user' | 'assistant';
}

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { generateAudio, isLoading, audioUrl } = useChatterboxTTS(
    process.env.NEXT_PUBLIC_TTS_API_URL
  );

  const handleSendMessage = async (userMessage: string) => {
    // 1. Send to OpenRouter
    const openRouterResponse = await fetch('/api/openrouter', {
      method: 'POST',
      body: JSON.stringify({ text: userMessage }),
    });

    const { response: aiText, character: aiCharacter } = 
      await openRouterResponse.json();

    // 2. Generate audio for AI response
    await generateAudio(aiText, aiCharacter);

    // 3. Add messages to chat
    setMessages(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        text: userMessage,
        character: 'user',
        role: 'user'
      },
      {
        id: (Date.now() + 1).toString(),
        text: aiText,
        character: aiCharacter,
        role: 'assistant'
      }
    ]);
  };

  return (
    <div>
      <div className="messages">
        {messages.map(msg => (
          <div key={msg.id} className={msg.role}>
            <p>{msg.text}</p>
            {msg.role === 'assistant' && audioUrl && (
              <audio src={audioUrl} controls />
            )}
          </div>
        ))}
      </div>

      <input 
        type="text" 
        placeholder="Type your message..."
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleSendMessage(e.currentTarget.value);
            e.currentTarget.value = '';
          }
        }}
      />
    </div>
  );
}
```

---

## OpenRouter Integration

### Setup Character Mapping

Map your AI character names to TTS voices:

```typescript
import { createOpenRouterIntegration } from '@/lib/chatterbox-tts-client';

const ttsIntegration = createOpenRouterIntegration(
  process.env.NEXT_PUBLIC_TTS_API_URL,
  'narrator'  // default voice
);

// Map AI characters to TTS voices
ttsIntegration.mapCharacter('Elara', 'friendly');
ttsIntegration.mapCharacter('Sage', 'expert');
ttsIntegration.mapCharacter('Luna', 'narrator');
```

### Process AI Responses

```typescript
async function handleOpenRouterResponse(aiResponse: string, characterName: string) {
  try {
    const audioData = await ttsIntegration.processAIResponse(
      aiResponse,
      characterName
    );

    // Use the audio URL
    playAudio(audioData.audioUrl);

    // Clean up later
    setTimeout(() => audioData.revoke(), audioData.duration * 1000);
  } catch (error) {
    console.error('Failed to generate audio:', error);
    // Fallback: just show text
  }
}
```

### Batch Processing Multiple Responses

```typescript
const responses = [
  { text: "First response", character: "Elara" },
  { text: "Second response", character: "Sage" },
  { text: "Third response", character: "Luna" },
];

const audioData = await ttsIntegration.processBatch(responses);

audioData.forEach(item => {
  if (!item.error) {
    console.log(`${item.character}: ${item.duration}s audio ready`);
  } else {
    console.error(`${item.character}: ${item.error}`);
  }
});
```

---

## Advanced Usage

### Custom Audio Processing

```typescript
// Get raw audio blob for custom processing
async function processAudioCustom(text: string) {
  const client = new ChatterboxTTSClient(apiUrl);
  const { blob } = await client.generateAudioBlob({ text });

  // Convert to different format
  const arrayBuffer = await blob.arrayBuffer();
  const audioContext = new AudioContext();
  const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

  // Apply effects, etc.
  return audioBuffer;
}
```

### Streaming Response Handling

```typescript
// For long AI responses, generate audio for segments
async function streamLongResponse(text: string, character: string) {
  const sentences = text.split(/[.!?]+/).filter(s => s.trim());

  for (const sentence of sentences) {
    try {
      await generateAudio(sentence, character);
      // Wait for audio to be ready before next sentence
      // This prevents overlapping generation
    } catch (error) {
      console.warn(`Failed for sentence: ${sentence}`, error);
    }
  }
}
```

### Caching Responses

```typescript
// Cache generated audio to avoid re-generation
const audioCache = new Map<string, string>();

async function generateAudioCached(text: string, character: string) {
  const cacheKey = `${text}|${character}`;

  if (audioCache.has(cacheKey)) {
    return audioCache.get(cacheKey);
  }

  const { url } = await client.generatePlayableAudio({
    text,
    character,
  });

  audioCache.set(cacheKey, url);
  return url;
}
```

### Error Handling Strategy

```typescript
async function generateAudioWithFallback(
  text: string,
  character: string
) {
  try {
    return await client.generateAudio({ text, character });
  } catch (error) {
    console.error('Primary TTS failed:', error);

    // Fallback options:
    // 1. Try default character
    try {
      return await client.generateAudio({ 
        text, 
        character: 'narrator' 
      });
    } catch (e2) {
      console.error('Fallback TTS also failed:', e2);

      // 2. Use browser's Web Speech API as last resort
      const utterance = new SpeechSynthesisUtterance(text);
      window.speechSynthesis.speak(utterance);

      return null;
    }
  }
}
```

---

## API Endpoint Reference

### `/generate-audio` (Primary Endpoint)

Used by frontend for OpenRouter AI responses:

```bash
curl -X POST https://api.yourdomain.com/generate-audio \
  -H "Content-Type: application/json" \
  -d '{
    "text": "The AI response text",
    "character": "narrator",
    "return_format": "base64"
  }'
```

Response:
```json
{
  "success": true,
  "audio": "UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB8AAAB...",
  "sample_rate": 24000,
  "duration": 2.45,
  "character": "narrator",
  "generation_time_ms": 1234
}
```

### `/health` (Health Check)

```bash
curl https://api.yourdomain.com/health
```

Response:
```json
{
  "status": "healthy",
  "device": "cuda",
  "model_loaded": true,
  "gpu": {
    "cuda_available": true,
    "device": "Tesla V100",
    "memory_allocated": "4.2GB",
    "memory_reserved": "8.0GB"
  }
}
```

### `/characters` (List Voices)

```bash
curl https://api.yourdomain.com/characters
```

---

## Next.js API Route Integration

### Example: `/api/chat` endpoint

```typescript
// pages/api/chat.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { userMessage, characterId } = await req.json();

  // 1. Call OpenRouter
  const openRouterResponse = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.OPENROUTER_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: userMessage }],
    }),
  });

  const { choices } = await openRouterResponse.json();
  const aiResponse = choices[0].message.content;

  // 2. Generate audio via TTS API
  const ttsResponse = await fetch(
    `${process.env.NEXT_PUBLIC_TTS_API_URL}/generate-audio`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: aiResponse,
        character: characterId,
        return_format: 'base64',
      }),
    }
  );

  const audioData = await ttsResponse.json();

  // 3. Return combined response
  return NextResponse.json({
    text: aiResponse,
    audio: audioData.audio,
    duration: audioData.duration,
    characterId,
  });
}
```

---

## Configuration Examples

### Multiple Character Setup

```typescript
// lib/characters.ts
export const CHARACTERS = {
  elara: {
    name: 'Elara',
    ttsVoice: 'friendly',
    systemPrompt: 'You are Elara, a warm and friendly character...',
  },
  sage: {
    name: 'Sage',
    ttsVoice: 'expert',
    systemPrompt: 'You are Sage, a knowledgeable expert...',
  },
  luna: {
    name: 'Luna',
    ttsVoice: 'narrator',
    systemPrompt: 'You are Luna, a mysterious narrator...',
  },
};

// Usage in component
import { CHARACTERS } from '@/lib/characters';

const character = CHARACTERS.elara;
await generateAudio(aiText, character.ttsVoice);
```

### Environment-Specific Setup

```typescript
// lib/tts.ts
const getTTSApiUrl = () => {
  if (process.env.NODE_ENV === 'development') {
    return process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000';
  }
  return process.env.NEXT_PUBLIC_TTS_API_URL || 'https://api.yourdomain.com';
};

export const ttsClient = new ChatterboxTTSClient(getTTSApiUrl());
```

---

## Performance Optimization

### 1. Preload Characters on App Load

```typescript
export async function preloadCharacters() {
  const characters = await ttsClient.getCharacters();
  // Cache locally for quick access
  sessionStorage.setItem('tts_characters', JSON.stringify(characters));
}
```

### 2. Request Batching

```typescript
// Generate multiple audio files in parallel
async function generateMultipleAudio(messages: Array<{text: string, char: string}>) {
  return Promise.allSettled(
    messages.map(m => generateAudio(m.text, m.char))
  );
}
```

### 3. Audio Blob Reuse

```typescript
// Avoid creating new blobs for same text
const blobCache = new Map<string, Blob>();

async function getCachedAudioBlob(text: string, character: string) {
  const key = `${text}|${character}`;
  if (blobCache.has(key)) {
    return blobCache.get(key)!;
  }
  const { blob } = await generateAudioBlob({ text, character });
  blobCache.set(key, blob);
  return blob;
}
```

---

## Troubleshooting

### Issue: CORS Errors
**Solution**: Ensure your Vercel domain is in the API's CORS_ORIGINS environment variable

### Issue: Audio Not Playing
**Solution**: Check audio format (should be WAV), verify blob URL is valid
```typescript
console.log('Audio URL:', audioUrl);
console.log('Audio URL valid:', audioUrl?.startsWith('blob:'));
```

### Issue: Slow Generation
**Solution**: Check GPU availability via health endpoint
```typescript
const health = await ttsClient.healthCheck();
console.log('Using GPU:', health.device === 'cuda');
```

### Issue: Timeout Errors
**Solution**: Increase timeout for longer texts
```typescript
const client = new ChatterboxTTSClient(apiUrl, {
  timeout: 60000, // 60 seconds
});
```

---

## Best Practices

1. **Error Boundaries**: Wrap TTS calls in try-catch
2. **Loading States**: Show loading indicator during generation
3. **Cleanup**: Revoke object URLs when done to prevent memory leaks
4. **Caching**: Reuse audio for repeated text
5. **Fallbacks**: Have text-only fallback if TTS fails
6. **Testing**: Test with different text lengths and characters

---

## Support

For issues or questions:
- Check API health: `/health` endpoint
- Review logs in AWS CloudWatch
- Test locally first: `http://localhost:5000`
- Enable debug logging in client:
  ```typescript
  console.log = (...args) => original.log('[TTS]', ...args);
  ```
