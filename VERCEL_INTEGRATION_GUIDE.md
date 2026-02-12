# 🚀 Vercel Integration Guide

Complete guide for integrating Chatterbox TTS with your Vercel Next.js application.

## 📊 Current Production Setup

- **API URL:** `http://35.174.4.196:5000`
- **Instance:** AWS EC2 c6i.4xlarge (16 vCPU, compute-optimized)
- **Available Voices:** 4 custom voices
  - `andrew_tate` - Andrew Tate (confident, motivational)
  - `peter_griffin` - Peter Griffin (comedy, cartoon)
  - `lois_griffin` - Lois Griffin (female, comedy)
  - `trump` - Donald Trump (political impression)

---

## 🎯 Quick Start (5 Minutes)

### 1. Add Environment Variable

**In your Vercel dashboard:**

```
Settings → Environment Variables → Add New

Name:  NEXT_PUBLIC_TTS_API_URL
Value: http://35.174.4.196:5000
Environments: ✓ Production ✓ Preview ✓ Development
```

**For local development (`.env.local`):**

```env
NEXT_PUBLIC_TTS_API_URL=http://35.174.4.196:5000
```

### 2. Copy TTS Client to Your Project

```bash
# In your Vercel project root
mkdir -p lib
cp /path/to/chatterbox/frontend/chatterbox-tts-client.ts lib/
```

Or download directly from your repository.

### 3. Install Dependencies

```bash
npm install
# No additional dependencies needed - client uses native fetch
```

### 4. Test Connection

Create a quick test page to verify the connection:

```typescript
// app/test-tts/page.tsx
'use client';

import { ChatterboxTTSClient } from '@/lib/chatterbox-tts-client';
import { useState } from 'react';

export default function TestTTS() {
  const [status, setStatus] = useState('Not tested');
  
  const testConnection = async () => {
    try {
      const client = new ChatterboxTTSClient(process.env.NEXT_PUBLIC_TTS_API_URL!);
      const health = await client.checkHealth();
      setStatus(`✅ Connected! Model loaded: ${health.model_loaded}`);
      
      const characters = await client.getCharacters();
      console.log('Available voices:', characters);
    } catch (error) {
      setStatus(`❌ Failed: ${error}`);
    }
  };
  
  return (
    <div className="p-8">
      <h1>TTS Connection Test</h1>
      <button onClick={testConnection} className="bg-blue-500 px-4 py-2 rounded">
        Test Connection
      </button>
      <p className="mt-4">{status}</p>
    </div>
  );
}
```

Visit `/test-tts` and click the button. You should see "✅ Connected!"

---

## 📦 Complete Integration

### File Structure

```
your-vercel-project/
├── .env.local                      # Environment variables
├── lib/
│   ├── chatterbox-tts-client.ts   # TTS client (copied from chatterbox)
│   └── tts-service.ts             # Service wrapper
├── components/
│   ├── ChatMessage.tsx            # Chat message with audio
│   └── VoiceSelector.tsx          # Voice/character selector
├── hooks/
│   └── useTTS.ts                  # TTS React hook
└── app/
    └── chat/
        └── page.tsx               # Chat page with TTS
```

---

## 🔧 Implementation Files

### 1. TTS Service Module

**File:** `lib/tts-service.ts`

```typescript
import { ChatterboxTTSClient } from './chatterbox-tts-client';

const apiUrl = process.env.NEXT_PUBLIC_TTS_API_URL;

if (!apiUrl) {
  console.warn('⚠️ NEXT_PUBLIC_TTS_API_URL not set - TTS will not work');
}

export const ttsClient = new ChatterboxTTSClient(apiUrl || '');

/**
 * Generate audio for text with specific character voice
 */
export async function generateAudio(
  text: string,
  characterId: 'andrew_tate' | 'peter_griffin' | 'lois_griffin' | 'trump' = 'andrew_tate'
): Promise<{ url: string; duration: number; revoke: () => void } | null> {
  if (!text?.trim()) {
    console.warn('Empty text provided to generateAudio');
    return null;
  }

  try {
    console.log(`[TTS] Generating: "${text.substring(0, 50)}..." (${characterId})`);
    
    const result = await ttsClient.generatePlayableAudio({
      text,
      character: characterId,
    });
    
    console.log(`[TTS] ✓ Generated: ${result.duration}s`);
    return result;
    
  } catch (error) {
    console.error('[TTS] ✗ Failed:', error);
    return null;
  }
}

/**
 * Get list of available characters/voices
 */
export async function getAvailableVoices() {
  try {
    const characters = await ttsClient.getCharacters();
    return characters.map(char => ({
      id: char.id,
      name: char.name,
      description: char.description,
    }));
  } catch (error) {
    console.error('[TTS] Failed to fetch voices:', error);
    return [];
  }
}

/**
 * Check if TTS service is available
 */
export async function checkTTSHealth(): Promise<boolean> {
  try {
    const health = await ttsClient.checkHealth();
    return health.model_loaded === true;
  } catch (error) {
    console.error('[TTS] Health check failed:', error);
    return false;
  }
}
```

---

### 2. React Hook for TTS

**File:** `hooks/useTTS.ts`

```typescript
'use client';

import { useState, useCallback, useEffect } from 'react';
import { generateAudio, getAvailableVoices, checkTTSHealth } from '@/lib/tts-service';

type VoiceId = 'andrew_tate' | 'peter_griffin' | 'lois_griffin' | 'trump';

interface Voice {
  id: string;
  name: string;
  description: string;
}

interface UseTTSReturn {
  // State
  isGenerating: boolean;
  currentAudio: { url: string; duration: number } | null;
  selectedVoice: VoiceId;
  availableVoices: Voice[];
  isHealthy: boolean;
  
  // Actions
  generate: (text: string) => Promise<void>;
  stop: () => void;
  setVoice: (voiceId: VoiceId) => void;
  
  // Audio element ref
  audioRef: React.RefObject<HTMLAudioElement>;
}

export function useTTS(): UseTTSReturn {
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentAudio, setCurrentAudio] = useState<{ url: string; duration: number } | null>(null);
  const [selectedVoice, setSelectedVoice] = useState<VoiceId>('andrew_tate');
  const [availableVoices, setAvailableVoices] = useState<Voice[]>([]);
  const [isHealthy, setIsHealthy] = useState(true);
  const audioRef = React.useRef<HTMLAudioElement>(null);

  // Check health on mount
  useEffect(() => {
    checkTTSHealth().then(setIsHealthy);
    getAvailableVoices().then(setAvailableVoices);
  }, []);

  // Cleanup audio URL on unmount
  useEffect(() => {
    return () => {
      if (currentAudio?.url) {
        URL.revokeObjectURL(currentAudio.url);
      }
    };
  }, [currentAudio]);

  const generate = useCallback(async (text: string) => {
    if (!text?.trim()) return;
    
    setIsGenerating(true);
    
    try {
      // Cleanup previous audio
      if (currentAudio?.url) {
        URL.revokeObjectURL(currentAudio.url);
      }
      
      const result = await generateAudio(text, selectedVoice);
      
      if (result) {
        setCurrentAudio({ url: result.url, duration: result.duration });
        
        // Auto-play if audio element exists
        if (audioRef.current) {
          audioRef.current.src = result.url;
          audioRef.current.play().catch(console.error);
        }
      }
    } finally {
      setIsGenerating(false);
    }
  }, [selectedVoice, currentAudio]);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, []);

  const setVoice = useCallback((voiceId: VoiceId) => {
    setSelectedVoice(voiceId);
  }, []);

  return {
    isGenerating,
    currentAudio,
    selectedVoice,
    availableVoices,
    isHealthy,
    generate,
    stop,
    setVoice,
    audioRef,
  };
}
```

---

### 3. Chat Message Component with Audio

**File:** `components/ChatMessage.tsx`

```typescript
'use client';

import { useEffect, useRef, useState } from 'react';
import { generateAudio } from '@/lib/tts-service';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  voiceId?: 'andrew_tate' | 'peter_griffin' | 'lois_griffin' | 'trump';
  autoPlay?: boolean;
}

export function ChatMessage({ role, content, voiceId = 'andrew_tate', autoPlay = false }: ChatMessageProps) {
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    // Generate audio for assistant messages
    if (role === 'assistant' && content) {
      generateAudioForMessage();
    }
    
    // Cleanup
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, [content, role]);

  const generateAudioForMessage = async () => {
    setIsGenerating(true);
    
    try {
      const result = await generateAudio(content, voiceId);
      
      if (result) {
        setAudioUrl(result.url);
        
        // Auto-play if enabled
        if (autoPlay && audioRef.current) {
          setTimeout(() => {
            audioRef.current?.play().catch(console.error);
          }, 100);
        }
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const playAudio = () => {
    audioRef.current?.play();
  };

  const pauseAudio = () => {
    audioRef.current?.pause();
  };

  return (
    <div className={`flex ${role === 'user' ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] rounded-lg p-4 ${
        role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-900'
      }`}>
        <p className="whitespace-pre-wrap">{content}</p>
        
        {role === 'assistant' && (
          <div className="mt-2 flex items-center gap-2">
            {isGenerating ? (
              <span className="text-sm opacity-70">🎵 Generating audio...</span>
            ) : audioUrl ? (
              <>
                <audio ref={audioRef} src={audioUrl} />
                <button
                  onClick={playAudio}
                  className="text-sm px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  ▶️ Play
                </button>
                <button
                  onClick={pauseAudio}
                  className="text-sm px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600"
                >
                  ⏸️ Pause
                </button>
              </>
            ) : (
              <button
                onClick={generateAudioForMessage}
                className="text-sm px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                🔊 Generate Audio
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### 4. Voice Selector Component

**File:** `components/VoiceSelector.tsx`

```typescript
'use client';

import { useEffect, useState } from 'react';
import { getAvailableVoices } from '@/lib/tts-service';

interface Voice {
  id: string;
  name: string;
  description: string;
}

interface VoiceSelectorProps {
  selected: string;
  onChange: (voiceId: string) => void;
}

export function VoiceSelector({ selected, onChange }: VoiceSelectorProps) {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getAvailableVoices()
      .then(setVoices)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-500">Loading voices...</div>;
  }

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium">Choose Voice:</label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
      >
        {voices.map((voice) => (
          <option key={voice.id} value={voice.id}>
            {voice.name} - {voice.description}
          </option>
        ))}
      </select>
    </div>
  );
}
```

---

### 5. Complete Chat Page Example

**File:** `app/chat/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { ChatMessage } from '@/components/ChatMessage';
import { VoiceSelector } from '@/components/VoiceSelector';

type VoiceId = 'andrew_tate' | 'peter_griffin' | 'lois_griffin' | 'trump';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedVoice, setSelectedVoice] = useState<VoiceId>('andrew_tate');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Call your AI API (OpenRouter, OpenAI, etc.)
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: input,
          history: messages 
        }),
      });

      const data = await response.json();
      
      const assistantMessage: Message = { 
        role: 'assistant', 
        content: data.message 
      };
      
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (error) {
      console.error('Chat error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className="w-64 bg-gray-100 p-4 border-r">
        <h2 className="font-bold mb-4">Settings</h2>
        <VoiceSelector 
          selected={selectedVoice}
          onChange={(id) => setSelectedVoice(id as VoiceId)}
        />
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.map((msg, idx) => (
            <ChatMessage
              key={idx}
              role={msg.role}
              content={msg.content}
              voiceId={msg.role === 'assistant' ? selectedVoice : undefined}
              autoPlay={msg.role === 'assistant'}
            />
          ))}
          
          {isLoading && (
            <div className="text-center text-gray-500">Thinking...</div>
          )}
        </div>

        {/* Input */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Type your message..."
              className="flex-1 px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 🧪 Testing

### 1. Test API Connection

```bash
curl http://35.174.4.196:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cpu"
}
```

### 2. Test Voice Generation

```bash
curl -X POST http://35.174.4.196:5000/tts-json \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from Vercel!", "character_id": "andrew_tate"}' \
  | jq '{success, duration, audio_length: (.audio | length)}'
```

Expected response:
```json
{
  "success": true,
  "duration": 1.5,
  "audio_length": 95000
}
```

### 3. Test in Browser Console

```javascript
// In your deployed Vercel app, open console:
const response = await fetch(`${process.env.NEXT_PUBLIC_TTS_API_URL}/characters`);
const data = await response.json();
console.log('Available voices:', data.characters);
```

---

## 🚨 Troubleshooting

### API not reachable from Vercel

**Issue:** CORS error or connection timeout

**Solution:**
1. Verify EC2 security group allows traffic from Vercel IPs
2. Check if EC2 is running: `aws ec2 describe-instances --instance-ids i-01cc4c92d83a1b6da`
3. Test from local machine: `curl http://35.174.4.196:5000/health`

### Audio not playing

**Issue:** Audio generates but doesn't play

**Solution:**
```typescript
// Ensure audio element has proper src
audioRef.current.src = audioUrl;

// Add user interaction before playing (browser requirement)
audioRef.current.play().catch(err => {
  console.error('Playback failed:', err);
  // Show play button for user to click
});
```

### Slow audio generation

**Issue:** Takes >30 seconds

**Current:** ~1-2 seconds per request on c6i.4xlarge
**If slow:** Check EC2 instance is running and not under load

### Environment variable not working

```typescript
// Debug in component:
console.log('TTS URL:', process.env.NEXT_PUBLIC_TTS_API_URL);

// If undefined, redeploy Vercel:
vercel --prod
```

---

## 📊 Performance Tips

### 1. Cache Audio Files

```typescript
const audioCache = new Map<string, string>();

export async function generateAudioCached(text: string, voiceId: string) {
  const cacheKey = `${text}-${voiceId}`;
  
  if (audioCache.has(cacheKey)) {
    console.log('[TTS] Cache hit');
    return audioCache.get(cacheKey)!;
  }
  
  const result = await generateAudio(text, voiceId);
  if (result) {
    audioCache.set(cacheKey, result.url);
  }
  
  return result;
}
```

### 2. Generate Audio in Background

```typescript
// Start generation when message arrives, don't wait
useEffect(() => {
  if (role === 'assistant') {
    generateAudioForMessage(); // Don't await
  }
}, [content]);
```

### 3. Preload Common Phrases

```typescript
const COMMON_PHRASES = [
  "How can I help you?",
  "I understand.",
  "Let me think about that.",
];

// On app mount
useEffect(() => {
  COMMON_PHRASES.forEach(phrase => {
    generateAudioCached(phrase, 'andrew_tate');
  });
}, []);
```

---

## 🔐 Security Notes

1. **API is currently HTTP** - For production, consider:
   - Setting up HTTPS with SSL certificate
   - Adding API authentication
   - Rate limiting

2. **CORS Configuration** - EC2 API needs CORS enabled:
   ```python
   # In api_server.py
   CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
   ```

3. **Environment Variables** - Never commit `.env.local`:
   ```bash
   # Add to .gitignore
   .env.local
   .env*.local
   ```

---

## 📈 Monitoring

### Check EC2 Instance

```bash
# Check if running
aws ec2 describe-instances --instance-ids i-01cc4c92d83a1b6da \
  --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress]' \
  --output text

# View API logs
ssh ubuntu@35.174.4.196 "sudo journalctl -u chatterbox -n 50"
```

### Monitor from Vercel

Add health check endpoint in your Vercel app:

```typescript
// app/api/tts-health/route.ts
export async function GET() {
  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_TTS_API_URL}/health`);
    const data = await response.json();
    return Response.json(data);
  } catch (error) {
    return Response.json({ status: 'error', message: error.message }, { status: 500 });
  }
}
```

---

## 🎯 Next Steps

1. ✅ Copy `chatterbox-tts-client.ts` to your Vercel project
2. ✅ Add environment variable to Vercel dashboard
3. ✅ Create `lib/tts-service.ts`
4. ✅ Add chat component with audio
5. ✅ Test in development
6. ✅ Deploy to Vercel
7. ✅ Test production deployment

---

## 📞 Support

- **Current API:** http://35.174.4.196:5000
- **Instance:** c6i.4xlarge (16 vCPU) on AWS EC2
- **Voices:** andrew_tate, peter_griffin, lois_griffin, trump
- **Average Response:** 1-2 seconds per request

For issues, check EC2 instance status or API logs.
