/**
 * Vercel API Route: /api/voice/tts
 * Proxies TTS requests to EC2 backend with proper error handling
 */

import type { NextRequest } from 'next/server';

const TTS_API_URL = process.env.TTS_API_URL || 'http://35.174.4.196:5000';
const REQUEST_TIMEOUT = 35000; // 35 seconds (EC2 has 30s timeout)

export const config = {
  runtime: 'edge', // Use edge runtime for better performance and longer timeout
  maxDuration: 60, // Maximum execution time in seconds
};

export default async function handler(req: NextRequest) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return new Response(
      JSON.stringify({ success: false, error: 'Method not allowed' }),
      { status: 405, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    const body = await req.json();

    // Validate request
    if (!body.text || typeof body.text !== 'string') {
      return new Response(
        JSON.stringify({ success: false, error: 'Missing or invalid text field' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Forward to EC2 TTS server
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
      const response = await fetch(`${TTS_API_URL}/tts-json`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: body.text,
          character: body.character || 'andrew_tate',
          language: body.language || 'en',
          max_tokens: body.max_tokens || 400,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Get response body
      const data = await response.json();

      // If EC2 returned 429 (rate limited), pass it through
      if (response.status === 429) {
        return new Response(
          JSON.stringify({
            success: false,
            error: data.error || 'Server overloaded. Please retry in a few seconds.',
            error_type: 'rate_limit',
            retry_after: 3, // Seconds to wait before retry
          }),
          { 
            status: 429, 
            headers: { 
              'Content-Type': 'application/json',
              'Retry-After': '3',
            } 
          }
        );
      }

      // If EC2 returned an error, pass it through
      if (!response.ok) {
        console.error('TTS API Error:', response.status, data);
        return new Response(
          JSON.stringify({
            success: false,
            error: data.error || 'TTS generation failed',
          }),
          { status: response.status, headers: { 'Content-Type': 'application/json' } }
        );
      }

      // Success - return the audio
      return new Response(
        JSON.stringify(data),
        { 
          status: 200, 
          headers: { 
            'Content-Type': 'application/json',
            'Cache-Control': 'public, max-age=7200', // Cache for 2 hours
          } 
        }
      );

    } catch (error: any) {
      clearTimeout(timeoutId);

      if (error.name === 'AbortError') {
        console.error('TTS request timeout after', REQUEST_TIMEOUT, 'ms');
        return new Response(
          JSON.stringify({
            success: false,
            error: 'Request timeout - TTS server is overloaded',
            error_type: 'timeout',
          }),
          { status: 504, headers: { 'Content-Type': 'application/json' } }
        );
      }

      throw error; // Re-throw for outer catch
    }

  } catch (error: any) {
    console.error('Vercel TTS API Error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: 'Internal server error',
        details: process.env.NODE_ENV === 'development' ? error.message : undefined,
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
