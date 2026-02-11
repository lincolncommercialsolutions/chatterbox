/**
 * Vercel API Route: /api/voice/characters
 * Get list of available TTS characters
 */

import type { NextRequest } from 'next/server';

const TTS_API_URL = process.env.TTS_API_URL || 'http://35.174.4.196:5000';

export const config = {
  runtime: 'edge',
};

export default async function handler(req: NextRequest) {
  try {
    const response = await fetch(`${TTS_API_URL}/characters`, {
      method: 'GET',
      signal: AbortSignal.timeout(10000), // 10 second timeout
    });

    const data = await response.json();

    return new Response(
      JSON.stringify(data),
      { 
        status: 200, 
        headers: { 
          'Content-Type': 'application/json',
          'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
        } 
      }
    );

  } catch (error: any) {
    console.error('Characters API Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to fetch characters',
        details: error.message,
      }),
      { 
        status: 500, 
        headers: { 
          'Content-Type': 'application/json',
        } 
      }
    );
  }
}
