/**
 * TTS Request Throttling
 * 
 * Prevents overloading the TTS server by ensuring minimum time between requests.
 * The Chatterbox model is NOT thread-safe, so requests must queue sequentially.
 * 
 * Usage:
 *   import { throttledTTSRequest } from './tts-throttle';
 *   const audio = await throttledTTSRequest('Hello world', 'andrew_tate');
 */

const TTS_ENDPOINT = process.env.NEXT_PUBLIC_TTS_ENDPOINT || 'http://35.174.4.196:5000/tts-json';
const MIN_REQUEST_INTERVAL = 2000; // 2 seconds between requests

// Track last request time globally
let lastRequestTime = 0;
let activeRequests = 0;

interface TTSRequest {
  text: string;
  character: string;
  language?: string;
  max_tokens?: number;
}

interface TTSResponse {
  success: boolean;
  audio?: string;
  duration?: number;
  character_id?: string;
  sample_rate?: number;
  error?: string;
}

/**
 * Make a throttled TTS request with automatic queuing
 */
export async function throttledTTSRequest(
  text: string,
  character: string,
  options?: { language?: string; maxTokens?: number }
): Promise<TTSResponse> {
  // Calculate wait time
  const now = Date.now();
  const timeSinceLastRequest = now - lastRequestTime;
  const waitTime = Math.max(0, MIN_REQUEST_INTERVAL - timeSinceLastRequest);

  // Wait if needed
  if (waitTime > 0) {
    console.log(`[TTS Throttle] Waiting ${waitTime}ms before next request (${activeRequests} active)`);
    await new Promise(resolve => setTimeout(resolve, waitTime));
  }

  // Update tracking
  lastRequestTime = Date.now();
  activeRequests++;

  try {
    const requestBody: TTSRequest = {
      text,
      character,
      ...(options?.language && { language: options.language }),
      ...(options?.maxTokens && { max_tokens: options.maxTokens })
    };

    console.log(`[TTS Request] Generating audio for "${text.slice(0, 50)}..." (${character})`);
    const startTime = Date.now();

    const response = await fetch(TTS_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
      signal: AbortSignal.timeout(30000) // 30 second timeout
    });

    if (!response.ok) {
      throw new Error(`TTS server returned ${response.status}`);
    }

    const result: TTSResponse = await response.json();
    const totalTime = Date.now() - startTime;

    if (result.success) {
      console.log(`[TTS Success] Generated in ${totalTime}ms (server: ${result.duration}s)`);
    } else {
      console.error(`[TTS Error] ${result.error}`);
    }

    return result;
  } catch (error) {
    console.error('[TTS Error]', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  } finally {
    activeRequests--;
  }
}

/**
 * Batch multiple TTS requests with automatic queuing
 */
export async function batchTTSRequests(
  requests: Array<{ text: string; character: string }>
): Promise<TTSResponse[]> {
  const results: TTSResponse[] = [];

  console.log(`[TTS Batch] Processing ${requests.length} requests...`);
  const startTime = Date.now();

  for (const req of requests) {
    const result = await throttledTTSRequest(req.text, req.character);
    results.push(result);
  }

  const totalTime = Date.now() - startTime;
  const successCount = results.filter(r => r.success).length;
  
  console.log(`[TTS Batch] Completed ${successCount}/${requests.length} in ${totalTime}ms`);

  return results;
}

/**
 * Get current throttle status
 */
export function getThrottleStatus() {
  const now = Date.now();
  const timeSinceLastRequest = now - lastRequestTime;
  const canRequestNow = timeSinceLastRequest >= MIN_REQUEST_INTERVAL;
  const nextAvailableIn = canRequestNow ? 0 : MIN_REQUEST_INTERVAL - timeSinceLastRequest;

  return {
    canRequestNow,
    nextAvailableIn,
    activeRequests,
    lastRequestTime
  };
}

/**
 * React hook for TTS requests with loading state
 */
export function useTTS() {
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const generate = async (text: string, character: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await throttledTTSRequest(text, character);
      
      if (!result.success) {
        setError(result.error || 'Generation failed');
        return null;
      }

      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { generate, loading, error };
}

// For CommonJS environments
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    throttledTTSRequest,
    batchTTSRequests,
    getThrottleStatus,
    useTTS
  };
}
