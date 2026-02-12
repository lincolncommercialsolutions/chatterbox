/**
 * Streaming TTS Client for Chunked Audio Playback
 * 
 * Dramatically reduces perceived latency by:
 * 1. Receiving audio chunks as they're generated
 * 2. Playing first chunk immediately (1-2s vs 7-8s)
 * 3. Queueing subsequent chunks for seamless playback
 * 
 * Usage:
 * ```typescript
 * const stream = new StreamingTTSClient('http://localhost:5000');
 * 
 * await stream.generateStreaming(
 *   'Long text with multiple sentences...',
 *   'andrew_tate',
 *   {
 *     onChunk: (audio, metadata) => console.log(`Chunk ${metadata.chunk_index + 1}`),
 *     onStart: () => console.log('Started'),
 *     onComplete: () => console.log('Done'),
 *     onError: (error) => console.error(error)
 *   }
 * );
 * ```
 */

export interface StreamChunk {
  chunk_index: number;
  total_chunks: number;
  text: string;
  audio?: string; // Base64 WAV data
  sample_rate?: number;
  duration?: number;
  is_final: boolean;
  error?: string;
}

export interface StreamCallbacks {
  onChunk?: (audioData: string, metadata: StreamChunk) => void | Promise<void>;
  onStart?: (totalChunks: number) => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
  onProgress?: (current: number, total: number) => void;
}

export class StreamingTTSClient {
  private apiUrl: string;
  private audioQueue: AudioBuffer[] = [];
  private audioContext: AudioContext | null = null;
  private isPlaying = false;

  constructor(apiUrl: string) {
    this.apiUrl = apiUrl.replace(/\/$/, ''); // Remove trailing slash
  }

  /**
   * Generate TTS audio with streaming chunks
   * @returns Total duration of all chunks
   */
  async generateStreaming(
    text: string,
    character: string,
    callbacks: StreamCallbacks = {}
  ): Promise<number> {
    const url = `${this.apiUrl}/tts-stream`;
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          character,
          max_chunk_chars: 150,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let totalDuration = 0;
      let totalChunks = 0;
      let hasStarted = false;

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        // Decode and append to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || ''; // Keep incomplete message in buffer

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;

          try {
            const data = JSON.parse(line.substring(6)); // Remove 'data: ' prefix

            // Handle different event types
            if (data.event === 'complete') {
              callbacks.onComplete?.();
              break;
            }

            if (data.event === 'error') {
              throw new Error(data.error || 'Stream error');
            }

            // Handle chunk data
            const chunk = data as StreamChunk;

            if (!hasStarted) {
              totalChunks = chunk.total_chunks;
              callbacks.onStart?.(totalChunks);
              hasStarted = true;
            }

            if (chunk.error) {
              console.error(`Chunk ${chunk.chunk_index} error:`, chunk.error);
              continue;
            }

            if (chunk.audio && chunk.duration) {
              totalDuration += chunk.duration;
              
              // Call chunk callback
              await callbacks.onChunk?.(chunk.audio, chunk);
              
              // Update progress
              callbacks.onProgress?.(chunk.chunk_index + 1, totalChunks);
            }

          } catch (parseError) {
            console.error('Error parsing SSE data:', parseError, line);
          }
        }
      }

      return totalDuration;

    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      callbacks.onError?.(err);
      throw err;
    }
  }

  /**
   * Play streaming chunks with automatic queueing
   * Starts playback as soon as first chunk arrives
   */
  async playStreaming(
    text: string,
    character: string,
    onProgress?: (current: number, total: number) => void
  ): Promise<void> {
    // Initialize audio context
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }

    const audioQueue: HTMLAudioElement[] = [];
    let currentlyPlaying = 0;
    let totalChunks = 0;

    const playNext = () => {
      if (currentlyPlaying >= audioQueue.length) {
        this.isPlaying = false;
        return;
      }

      const audio = audioQueue[currentlyPlaying];
      audio.play().catch(err => console.error('Playback error:', err));
      
      audio.onended = () => {
        currentlyPlaying++;
        onProgress?.(currentlyPlaying, totalChunks);
        playNext();
      };
    };

    await this.generateStreaming(text, character, {
      onStart: (total) => {
        totalChunks = total;
        console.log(`🎵 Starting streaming playback: ${total} chunks`);
      },
      
      onChunk: async (audioData, metadata) => {
        console.log(`🎵 Received chunk ${metadata.chunk_index + 1}/${metadata.total_chunks}`);
        
        // Create audio element from base64 data
        const audio = new Audio(`data:audio/wav;base64,${audioData}`);
        audioQueue.push(audio);

        // Start playing first chunk immediately
        if (metadata.chunk_index === 0 && !this.isPlaying) {
          this.isPlaying = true;
          playNext();
        }
      },
      
      onError: (error) => {
        console.error('❌ Streaming playback error:', error);
        this.isPlaying = false;
      },
      
      onComplete: () => {
        console.log('✅ All chunks received');
      }
    });
  }

  /**
   * Preview how text will be chunked (without generating audio)
   */
  async previewChunks(text: string, maxChunkChars = 150): Promise<{
    total_chunks: number;
    chunks: Array<{index: number; text_preview: string; char_count: number}>;
    estimated_total_time: number;
  }> {
    const url = `${this.apiUrl}/tts-stream-preview`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text, max_chunk_chars: maxChunkChars }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  }
}

/**
 * React Hook for Streaming TTS
 */
export function useStreamingTTS(apiUrl: string) {
  const [isStreaming, setIsStreaming] = React.useState(false);
  const [progress, setProgress] = React.useState({ current: 0, total: 0 });
  const clientRef = React.useRef<StreamingTTSClient | null>(null);

  React.useEffect(() => {
    clientRef.current = new StreamingTTSClient(apiUrl);
  }, [apiUrl]);

  const playStreaming = React.useCallback(async (text: string, character: string) => {
    if (!clientRef.current) return;

    setIsStreaming(true);
    setProgress({ current: 0, total: 0 });

    try {
      await clientRef.current.playStreaming(text, character, (current, total) => {
        setProgress({ current, total });
      });
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const previewChunks = React.useCallback(async (text: string) => {
    if (!clientRef.current) return null;
    return clientRef.current.previewChunks(text);
  }, []);

  return {
    isStreaming,
    progress,
    playStreaming,
    previewChunks,
  };
}

// For non-React usage
export default StreamingTTSClient;
