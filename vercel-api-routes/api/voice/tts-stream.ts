/**
 * Vercel Edge API Route for Streaming TTS
 * 
 * Proxies Server-Sent Events (SSE) from EC2 backend to frontend
 * Enables chunked audio generation with immediate playback
 * 
 * Environment Variables:
 * - TTS_API_URL: Backend URL (e.g., http://35.174.4.196:5000)
 */

export const config = {
  runtime: 'edge',
  maxDuration: 60, // Allow 60s for streaming multiple chunks
};

export default async function handler(req: Request) {
  // Only allow POST
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const backendUrl = process.env.TTS_API_URL || 'http://35.174.4.196:5000';

  try {
    // Parse request body
    const body = await req.json();
    const { text, character, max_chunk_chars = 150 } = body;

    if (!text || !character) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields: text, character' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Forward request to backend
    const response = await fetch(`${backendUrl}/tts-stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, character, max_chunk_chars }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Backend error:', response.status, errorText);
      
      return new Response(
        JSON.stringify({ 
          error: 'Backend TTS service unavailable',
          details: errorText,
          status: response.status
        }),
        { status: response.status, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Stream SSE events from backend to frontend
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();

    // Pipe response to client
    (async () => {
      try {
        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No response body');
        }

        const decoder = new TextDecoder();
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Forward SSE data to client
          await writer.write(value);
        }
      } catch (error) {
        console.error('Streaming error:', error);
      } finally {
        await writer.close();
      }
    })();

    // Return streaming response
    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no',
      },
    });

  } catch (error) {
    console.error('TTS streaming error:', error);
    
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: error instanceof Error ? error.message : String(error)
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
