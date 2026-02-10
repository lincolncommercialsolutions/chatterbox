/**
 * Chatterbox TTS Client SDK for Vercel Frontend
 * 
 * Usage:
 * const client = new ChatterboxClient({
 *   apiUrl: 'https://your-api.example.com'
 * });
 * 
 * const audio = await client.generateTTS('Hello world', 'narrator');
 */

export interface CharacterVoice {
  id: string;
  name: string;
  character_name: string;
  language: string;
  description: string;
}

export interface TTSOptions {
  characterId?: string;
  language?: string;
  maxTokens?: number;
  format?: 'wav' | 'base64';
}

export interface TTSResponse {
  success: boolean;
  audio?: string | ArrayBuffer;
  audio_format?: string;
  sample_rate?: number;
  duration_seconds?: number;
  character_id?: string;
  text_length?: number;
  error?: string;
}

export interface BatchTTSRequest {
  id: string;
  text: string;
  character_id?: string;
}

export interface BatchTTSResponse {
  success: boolean;
  results: Array<{
    id: string;
    success: boolean;
    audio?: string;
    duration_seconds?: number;
    error?: string;
  }>;
  total?: number;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  device: string;
  model_loaded: boolean;
  active_requests: number;
  queue_length: number;
  gpu?: {
    gpu_available: boolean;
    gpu_name: string;
    vram_total_gb: number;
    vram_allocated_gb: number;
    vram_reserved_gb: number;
  };
}

export class ChatterboxClient {
  private apiUrl: string;
  private apiKey?: string;
  private timeout: number = 60000; // 60 seconds
  private retryAttempts: number = 3;
  private retryDelay: number = 1000; // 1 second

  constructor(config: {
    apiUrl: string;
    apiKey?: string;
    timeout?: number;
    retryAttempts?: number;
    retryDelay?: number;
  }) {
    this.apiUrl = config.apiUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = config.apiKey;
    if (config.timeout) this.timeout = config.timeout;
    if (config.retryAttempts) this.retryAttempts = config.retryAttempts;
    if (config.retryDelay) this.retryDelay = config.retryDelay;
  }

  /**
   * Check API health status
   */
  async health(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/api/v1/health', 'GET');
  }

  /**
   * Get list of available characters
   */
  async getCharacters(): Promise<CharacterVoice[]> {
    const response = await this.request<{ characters: CharacterVoice[] }>(
      '/api/v1/characters',
      'GET'
    );
    return response.characters;
  }

  /**
   * Get details about a specific character
   */
  async getCharacter(characterId: string): Promise<CharacterVoice> {
    return this.request<CharacterVoice>(
      `/api/v1/characters/${characterId}`,
      'GET'
    );
  }

  /**
   * Get supported languages
   */
  async getLanguages(): Promise<Record<string, string>> {
    const response = await this.request<{ languages: Record<string, string> }>(
      '/api/v1/languages',
      'GET'
    );
    return response.languages;
  }

  /**
   * Generate TTS audio from text
   * 
   * @param text - Text to convert to speech
   * @param options - Generation options
   * @returns Audio as ArrayBuffer or base64 string depending on format option
   */
  async generateTTS(
    text: string,
    options: TTSOptions = {}
  ): Promise<TTSResponse> {
    const {
      characterId = 'narrator',
      language,
      maxTokens = 400,
      format = 'base64'
    } = options;

    const requestBody = {
      text,
      character_id: characterId,
      ...(language && { language }),
      max_tokens: maxTokens,
      format
    };

    try {
      const response = await this.request<TTSResponse>(
        '/api/v1/tts',
        'POST',
        requestBody
      );

      if (format === 'wav' && response instanceof ArrayBuffer) {
        // If requesting WAV format, convert to base64 for consistency
        return {
          success: true,
          audio: this.arrayBufferToBase64(response),
          audio_format: 'wav'
        };
      }

      return response;
    } catch (error) {
      return {
        success: false,
        error: `Failed to generate TTS: ${error instanceof Error ? error.message : String(error)}`
      };
    }
  }

  /**
   * Generate TTS audio and stream it
   * Returns a blob that can be played directly
   */
  async generateTTSStream(
    text: string,
    options: TTSOptions = {}
  ): Promise<Blob> {
    const { characterId = 'narrator', maxTokens = 400 } = options;

    const requestBody = {
      text,
      character_id: characterId,
      max_tokens: maxTokens
    };

    const response = await fetch(`${this.apiUrl}/api/v1/tts-stream`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }

    return response.blob();
  }

  /**
   * Generate TTS for multiple texts in batch
   */
  async generateBatchTTS(
    requests: BatchTTSRequest[],
    format: 'base64' | 'json' = 'base64'
  ): Promise<BatchTTSResponse> {
    const requestBody = {
      requests: requests.map(req => ({
        id: req.id,
        text: req.text,
        character_id: req.character_id || 'narrator'
      })),
      format
    };

    try {
      const response = await this.request<BatchTTSResponse>(
        '/api/v1/tts-batch',
        'POST',
        requestBody
      );
      return response;
    } catch (error) {
      return {
        success: false,
        results: [],
        total: 0
      };
    }
  }

  /**
   * Play audio blob in browser
   */
  playAudio(audioBlob: Blob, onPlay?: () => void): HTMLAudioElement {
    const url = URL.createObjectURL(audioBlob);
    const audio = new Audio(url);
    
    if (onPlay) {
      audio.addEventListener('play', onPlay);
    }

    audio.addEventListener('ended', () => {
      URL.revokeObjectURL(url);
    });

    audio.play();
    return audio;
  }

  /**
   * Convert base64 audio to blob for playback
   */
  base64ToBlob(base64: string, mimeType: string = 'audio/wav'): Blob {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }

  /**
   * Convert ArrayBuffer to base64
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    
    return btoa(binary);
  }

  /**
   * Internal request method with retry logic
   */
  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' = 'GET',
    body?: any,
    attempt: number = 1
  ): Promise<T> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.apiUrl}${endpoint}`, {
        method,
        headers: this.getHeaders(),
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.error || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      // Check if response is JSON or binary (for WAV files)
      const contentType = response.headers.get('content-type');
      if (contentType?.includes('application/json')) {
        return response.json();
      } else if (contentType?.includes('audio')) {
        return (await response.arrayBuffer()) as T;
      } else {
        return response.json();
      }
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('AbortError')) {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }

      // Retry logic for network errors
      if (attempt < this.retryAttempts && this.isRetryableError(error)) {
        await this.delay(this.retryDelay * attempt);
        return this.request<T>(endpoint, method, body, attempt + 1);
      }

      throw error;
    }
  }

  /**
   * Check if error is retryable
   */
  private isRetryableError(error: unknown): boolean {
    if (error instanceof TypeError) {
      const message = error.message.toLowerCase();
      return (
        message.includes('network') ||
        message.includes('failed to fetch') ||
        message.includes('timeout')
      );
    }
    return false;
  }

  /**
   * Delay helper
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Get request headers
   */
  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    return headers;
  }
}

// Export for use in React components
export default ChatterboxClient;
