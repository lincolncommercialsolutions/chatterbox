/**
 * Vercel API Route: /api/voice/health
 * Health check endpoint for TTS service
 */

import type { NextRequest } from 'next/server';

const TTS_API_URL = process.env.TTS_API_URL || 'http://35.174.4.196:5000';

export const config = {
  runtime: 'edge',
};

export default async function handler(req: NextRequest) {
  try {
    const response = await fetch(`${TTS_API_URL}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(5000), // 5 second timeout
    });

    const data = await response.json();

    return new Response(
      JSON.stringify({
        vercel: 'healthy',
        tts_backend: data,
        api_url: TTS_API_URL,
      }),
      { 
        status: 200, 
        headers: { 
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
        } 
      }
    );

  } catch (error: any) {
    console.error('Health check failed:', error);
    return new Response(
      JSON.stringify({
        vercel: 'healthy',
        tts_backend: 'unreachable',
        error: error.message,
        api_url: TTS_API_URL,
      }),
      { 
        status: 503, 
        headers: { 
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
        } 
      }
    );
  }
}
