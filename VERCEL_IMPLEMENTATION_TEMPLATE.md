# Vercel Implementation Template

Copy-paste ready code for integrating Chatterbox TTS into your Vercel Next.js app.

## 📁 Directory Structure

```
your-vercel-project/
├── .env.local                          # Add TTS_API_URL
├── lib/
│   ├── chatterbox-tts-client.ts       # Copy from chatterbox/frontend/
│   ├── tts-service.ts                 # New file (see below)
│   └── openrouter-service.ts          # Your OpenRouter integration
├── components/
│   ├── ChatWithAudio.tsx              # New component (see below)
│   └── VoiceSelector.tsx              # Optional (copy from VoiceSelector.example.tsx)
├── pages/
│   └── api/
│       ├── chat.ts                    # Your OpenRouter endpoint
│       └── tts-health.ts              # Optional health check
└── app/
    └── page.tsx                       # Main page using ChatWithAudio
```

---

## 1️⃣ Environment Variables

**File:** `.env.local`

```env
# TTS API Configuration
NEXT_PUBLIC_TTS_API_URL=https://your-deployed-api.com
# For local development:
# NEXT_PUBLIC_TTS_API_URL=http://localhost:5000

# OpenRouter (if not already configured)
OPENROUTER_API_KEY=your-openrouter-key-here
```

---

## 2️⃣ Copy TTS Client

**File:** `lib/chatterbox-tts-client.ts`

Copy from: `/home/linkl0n/chatterbox/frontend/chatterbox-tts-client.ts`

```bash
cp /home/linkl0n/chatterbox/frontend/chatterbox-tts-client.ts lib/
```

---

## 3️⃣ Create TTS Service Module

**File:** `lib/tts-service.ts`

```typescript
import { ChatterboxTTSClient } from './chatterbox-tts-client';

const apiUrl = process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000';

export const ttsClient = new ChatterboxTTSClient(apiUrl);

/**
 * Generate audio for a message
 * @param text - The text to convert to speech
 * @param characterId - The character/voice to use (default: "assistant")
 * @returns Object with URL and duration, or null on error
 */
export async function generateAudioForMessage(
  text: string,
  characterId: string = 'assistant'
): Promise<{ url: string; duration: number; revoke: () => void } | null> {
  if (!text || text.trim().length === 0) {
    console.warn('Empty text provided to generateAudioForMessage');
    return null;
  }

  try {
    console.log(
      `[TTS] Generating audio for "${text.substring(0, 50)}..." with character "${characterId}"`
    );

    const startTime = performance.now();

    const result = await ttsClient.generatePlayableAudio({
      text,
      character: characterId,
    });

    const duration = (performance.now() - startTime) / 1000;
    console.log(`[TTS] Audio generated in ${duration.toFixed(2)}s`);

    return result;
  } catch (error) {
    console.error('[TTS] Audio generation failed:', error);
    // Return null instead of throwing - allows chat to continue without audio
    return null;
  }
}

/**
 * Get all available characters
 */
export async function getAvailableCharacters() {
  try {
    const characters = await ttsClient.getCharacters();
    console.log(`[TTS] Loaded ${characters.length} characters`);
    return characters;
  } catch (error) {
    console.error('[TTS] Failed to get characters:', error);
    return [];
  }
}

/**
 * Get all available voices
 */
export async function getAvailableVoices() {
  try {
    const voices = await ttsClient.getVoices();
    console.log(`[TTS] Loaded ${voices.length} voices`);
    return voices;
  } catch (error) {
    console.error('[TTS] Failed to get voices:', error);
    return [];
  }
}

/**
 * Check if TTS API is available
 */
export async function checkTTSHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${apiUrl}/health`);
    return response.ok;
  } catch (error) {
    console.error('[TTS] Health check failed:', error);
    return false;
  }
}
```

---

## 4️⃣ Create OpenRouter Service

**File:** `lib/openrouter-service.ts`

```typescript
export interface OpenRouterMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface OpenRouterResponse {
  id: string;
  model: string;
  choices: {
    message: {
      role: string;
      content: string;
    };
  }[];
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/**
 * Call OpenRouter API
 * @param messages - Array of messages
 * @param character - Character/system context (optional)
 * @returns Response text
 */
export async function callOpenRouter(
  messages: OpenRouterMessage[],
  character: string = 'assistant'
): Promise<string> {
  const apiKey = process.env.OPENROUTER_API_KEY;

  if (!apiKey) {
    throw new Error('OPENROUTER_API_KEY not configured');
  }

  // Add system prompt for character
  const systemPrompt = getSystemPrompt(character);
  const messagesWithSystem: OpenRouterMessage[] = [
    { role: 'system', content: systemPrompt },
    ...messages,
  ];

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'HTTP-Referer': typeof window !== 'undefined' ? window.location.href : 'http://localhost:3000',
        'X-Title': 'Chatterbox TTS Chat',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'gpt-3.5-turbo',
        messages: messagesWithSystem,
        temperature: 0.8,
        max_tokens: 400,
      }),
    });

    if (!response.ok) {
      throw new Error(`OpenRouter API error: ${response.status}`);
    }

    const data: OpenRouterResponse = await response.json();

    if (!data.choices || data.choices.length === 0) {
      throw new Error('No response from OpenRouter');
    }

    return data.choices[0].message.content;
  } catch (error) {
    console.error('[OpenRouter] API call failed:', error);
    throw error;
  }
}

/**
 * Get system prompt for character
 */
function getSystemPrompt(character: string): string {
  const prompts: Record<string, string> = {
    narrator:
      'You are a clear, professional narrator. Speak clearly and deliver information in an engaging way.',
    assistant:
      'You are a friendly and helpful AI assistant. Be warm, approachable, and easy to talk to.',
    expert:
      'You are an authoritative subject matter expert. Provide knowledgeable, detailed responses.',
    luna: 'You are Luna, an enigmatic and mysterious character. Be intriguing and thought-provoking.',
    sage:
      'You are Sage, a calm and wise mentor. Speak thoughtfully and provide balanced perspectives.',
    elara:
      'You are Elara, a warm and approachable character. Be friendly, encouraging, and supportive.',
  };

  return (
    prompts[character] ||
    'You are a helpful assistant. Respond naturally and helpfully to the user.'
  );
}
```

---

## 5️⃣ Create Chat Component with Audio

**File:** `components/ChatWithAudio.tsx`

```typescript
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { generateAudioForMessage, getAvailableCharacters } from '@/lib/tts-service';
import { callOpenRouter } from '@/lib/openrouter-service';

interface Message {
  id: string;
  text: string;
  audioUrl?: string;
  duration?: number;
  character: string;
  role: 'user' | 'assistant';
  error?: string;
}

interface Character {
  id: string;
  name: string;
  description: string;
}

export function ChatWithAudio() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [selectedCharacter, setSelectedCharacter] = useState<string>('assistant');
  const [isLoading, setIsLoading] = useState(false);
  const [characters, setCharacters] = useState<Character[]>([]);
  const audioRefs = useRef<Record<string, HTMLAudioElement>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load characters on mount
  useEffect(() => {
    loadCharacters();
  }, []);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function loadCharacters() {
    try {
      const chars = await getAvailableCharacters();
      setCharacters(chars);
      if (chars.length > 0) {
        setSelectedCharacter(chars[0].id);
      }
    } catch (error) {
      console.error('Failed to load characters:', error);
    }
  }

  async function handleSendMessage() {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      text: input,
      character: 'user',
      role: 'user',
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Get response from OpenRouter
      console.log('[Chat] Calling OpenRouter with character:', selectedCharacter);
      const responseText = await callOpenRouter(
        messages.filter(m => m.role !== 'user').map(m => ({
          role: m.role,
          content: m.text,
        })).concat({
          role: 'user',
          content: userMessage.text,
        }),
        selectedCharacter
      );

      // Generate audio for response
      console.log('[Chat] Generating audio for response');
      const audioData = await generateAudioForMessage(responseText, selectedCharacter);

      const aiMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        text: responseText,
        audioUrl: audioData?.url,
        duration: audioData?.duration,
        character: selectedCharacter,
        role: 'assistant',
      };

      setMessages((prev) => [...prev, aiMessage]);

      // Auto-play audio if available
      if (audioData?.url && audioRefs.current[aiMessage.id]) {
        setTimeout(() => {
          audioRefs.current[aiMessage.id]?.play().catch((e) => {
            console.warn('Auto-play failed:', e);
            // Browser might prevent auto-play - user can click play button
          });
        }, 100);
      }
    } catch (error) {
      console.error('[Chat] Error:', error);
      const errorMessage: Message = {
        id: `msg-${Date.now() + 2}`,
        text: '',
        character: selectedCharacter,
        role: 'assistant',
        error: `Failed to get response: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto bg-white">
      {/* Header with Character Selector */}
      <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4">
        <h1 className="text-2xl font-bold mb-2">Chatterbox TTS</h1>
        <select
          value={selectedCharacter}
          onChange={(e) => setSelectedCharacter(e.target.value)}
          className="px-3 py-2 rounded text-black font-medium w-full sm:w-auto"
        >
          {characters.map((char) => (
            <option key={char.id} value={char.id}>
              {char.name}
            </option>
          ))}
        </select>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <p className="text-lg">👋 Start a conversation!</p>
            <p className="text-sm">Your messages will be read aloud.</p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white border border-gray-200 text-gray-900'
              }`}
            >
              {msg.error ? (
                <p className="text-red-600 text-sm font-semibold">
                  ❌ {msg.error}
                </p>
              ) : (
                <>
                  <p className="text-sm leading-relaxed">{msg.text}</p>

                  {msg.audioUrl && msg.role === 'assistant' && (
                    <div className="mt-2 pt-2 border-t border-gray-300">
                      <audio
                        ref={(el) => {
                          if (el) audioRefs.current[msg.id] = el;
                        }}
                        src={msg.audioUrl}
                        controls
                        className="w-full"
                      />
                      {msg.duration && (
                        <p className="text-xs text-gray-600 mt-1">
                          Duration: {msg.duration.toFixed(1)}s
                        </p>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 text-gray-900 px-4 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full"></div>
                <p className="text-sm">Generating response and audio...</p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !input.trim()}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              isLoading || !input.trim()
                ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600 active:bg-blue-700'
            }`}
          >
            {isLoading ? 'Loading...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## 6️⃣ Create API Endpoint (Optional)

**File:** `pages/api/chat.ts`

Use this if you want the chat to go through your Next.js backend instead of directly to OpenRouter.

```typescript
import type { NextApiRequest, NextApiResponse } from 'next';
import { callOpenRouter } from '@/lib/openrouter-service';
import { generateAudioForMessage } from '@/lib/tts-service';

type ResponseData = {
  text?: string;
  audio?: string | null;
  duration?: number;
  character?: string;
  error?: string;
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { messages, character = 'assistant' } = req.body;

    if (!messages || !Array.isArray(messages)) {
      return res.status(400).json({ error: 'Invalid messages format' });
    }

    // Get OpenRouter response
    const lastMessage = messages[messages.length - 1];
    const responseText = await callOpenRouter(
      messages.map((m: any) => ({
        role: m.role,
        content: m.text,
      })),
      character
    );

    // Generate audio
    const audioData = await generateAudioForMessage(responseText, character);

    return res.status(200).json({
      text: responseText,
      audio: audioData?.url || null,
      duration: audioData?.duration,
      character,
    });
  } catch (error) {
    console.error('Chat error:', error);
    return res.status(500).json({
      error: `Failed to process chat: ${error instanceof Error ? error.message : 'Unknown error'}`,
    });
  }
}
```

---

## 7️⃣ Update Main Page

**File:** `app/page.tsx` (or `pages/index.tsx`)

```typescript
import { ChatWithAudio } from '@/components/ChatWithAudio';

export default function Home() {
  return (
    <main>
      <ChatWithAudio />
    </main>
  );
}
```

---

## 8️⃣ TypeScript Types (Optional)

**File:** `lib/types.ts`

```typescript
export interface Character {
  id: string;
  name: string;
  description: string;
  voice_id?: string;
}

export interface Voice {
  id: string;
  description: string;
  language?: string;
  audio_url?: string;
}

export interface AudioGenerationOptions {
  text: string;
  character?: string;
  voice_id?: string;
  max_tokens?: number;
}

export interface GenerationResponse {
  url: string;
  duration: number;
  revoke: () => void;
}

export interface ChatMessage {
  id: string;
  text: string;
  audioUrl?: string;
  duration?: number;
  character: string;
  role: 'user' | 'assistant';
  error?: string;
}
```

---

## 🧪 Testing Checklist

### Before Deployment
```bash
# 1. Copy TTS client
cp /home/linkl0n/chatterbox/frontend/chatterbox-tts-client.ts lib/

# 2. Install dependencies (if any)
npm install

# 3. Set environment variables
cp .env.local.example .env.local
# Edit .env.local with your values

# 4. Start dev server
npm run dev

# 5. Test in browser at http://localhost:3000
```

### Testing Steps
- [ ] Page loads without errors
- [ ] Character dropdown shows characters
- [ ] Can type and send messages
- [ ] OpenRouter response appears
- [ ] Audio element appears below message
- [ ] Audio plays when clicked
- [ ] Audio sounds match selected character
- [ ] Changing character produces different audio
- [ ] Error handling works (gracefully handles failures)
- [ ] Console shows helpful debug logs

### Common Issues

**Issue:** CORS error
```
Access to XMLHttpRequest blocked by CORS policy
```
**Fix:** Make sure `NEXT_PUBLIC_TTS_API_URL` points to correct deployed API with CORS enabled

**Issue:** No characters loading
```typescript
// Test in browser console:
import { getAvailableCharacters } from '@/lib/tts-service';
const chars = await getAvailableCharacters();
console.log(chars);
```

**Issue:** Audio not generating
```bash
# Check TTS API is running and accessible:
curl https://your-api-url/health
curl https://your-api-url/characters
```

---

## 🚀 Deployment

1. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add Chatterbox TTS integration"
   git push
   ```

2. **Vercel auto-deploys from git**

3. **Verify environment variables in Vercel dashboard:**
   - Settings → Environment Variables
   - Add: `NEXT_PUBLIC_TTS_API_URL`
   - Add: `OPENROUTER_API_KEY`

4. **Test deployed version**
   ```bash
   curl https://your-vercel-url.com
   # Should load without errors
   ```

---

## 📚 Reference

- Copy TTS Client from: `chatterbox/frontend/chatterbox-tts-client.ts`
- Voice Config: `chatterbox/voices_config.json`
- Full API docs: `chatterbox/README.md`
- Integration guide: `chatterbox/FRONTEND_INTEGRATION.md`

---

## ✅ Quick Checklist

- [ ] `.env.local` has `NEXT_PUBLIC_TTS_API_URL`
- [ ] `lib/chatterbox-tts-client.ts` copied
- [ ] `lib/tts-service.ts` created
- [ ] `lib/openrouter-service.ts` created
- [ ] `components/ChatWithAudio.tsx` created
- [ ] `app/page.tsx` imports ChatWithAudio
- [ ] `npm run dev` works locally
- [ ] Can send messages and get responses
- [ ] Audio generates for each response
- [ ] Different characters sound different
- [ ] Deployed to Vercel
- [ ] Environment variables set in Vercel
- [ ] Works on production URL

---

That's it! You're ready to go. 🎉
