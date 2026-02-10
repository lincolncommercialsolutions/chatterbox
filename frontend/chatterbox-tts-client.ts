/**
 * Chatterbox TTS Client for Vercel/Next.js Frontend
 * Seamless integration with OpenRouter AI character responses
 */

interface AudioGenerationOptions {
  text: string;
  character?: string;
  voiceId?: string;  // Optional voice override for character
  returnFormat?: 'base64' | 'url';
  maxTokens?: number;
}

interface AudioGenerationResponse {
  success: boolean;
  audio?: string; // base64 encoded
  audio_url?: string; // if returnFormat is 'url'
  sample_rate: number;
  duration: number;
  character: string;
  text_length: number;
  generation_time_ms: number;
  error?: string;
}

interface HealthCheckResponse {
  status: string;
  timestamp: string;
  device: string;
  model_loaded: boolean;
  gpu?: {
    cuda_available: boolean;
    device?: string;
    memory_allocated?: string;
    memory_reserved?: string;
  };
  cache_enabled: boolean;
  cache_size: number;
}

interface Character {
  id: string;
  name: string;
  language: string;
  description: string;
}

interface Voice {
  id: string;
  name: string;
  language: string;
  description: string;
  quality?: string;
  tags?: string[];
}

interface CharacterDetails extends Character {
  voice_id: string;
  parameters?: {
    exaggeration: number;
    temperature: number;
    cfg_weight: number;
  };
}

interface VoiceDetails extends Voice {
  used_by_characters: string[];
}

/**
 * Main Chatterbox TTS Client
 */
export class ChatterboxTTSClient {
  private apiUrl: string;
  private timeout: number;
  private retryAttempts: number;

  constructor(
    apiUrl: string,
    options?: {
      timeout?: number;
      retryAttempts?: number;
    }
  ) {
    this.apiUrl = apiUrl.replace(/\/$/, ''); // Remove trailing slash
    this.timeout = options?.timeout ?? 30000;
    this.retryAttempts = options?.retryAttempts ?? 3;
  }

  /**
   * Check API health and GPU availability
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    try {
      const response = await this.fetch('/health', {
        method: 'GET',
      });
      return response;
    } catch (error) {
      throw new Error(`Health check failed: ${error}`);
    }
  }

  /**
   * Get list of available character voices
   */
  async getCharacters(): Promise<Character[]> {
    try {
      const response = await this.fetch('/characters', {
        method: 'GET',
      });
      return response.characters || [];
    } catch (error) {
      throw new Error(`Failed to get characters: ${error}`);
    }
  }

  /**
   * Get details about a specific character
   */
  async getCharacterDetails(characterId: string): Promise<CharacterDetails> {
    try {
      const response = await this.fetch(`/characters/${characterId}`, {
        method: 'GET',
      });
      return response;
    } catch (error) {
      throw new Error(`Failed to get character details: ${error}`);
    }
  }

  /**
   * Get list of available voices
   */
  async getVoices(): Promise<Voice[]> {
    try {
      const response = await this.fetch('/voices', {
        method: 'GET',
      });
      return response.voices || [];
    } catch (error) {
      throw new Error(`Failed to get voices: ${error}`);
    }
  }

  /**
   * Get details about a specific voice
   */
  async getVoiceDetails(voiceId: string): Promise<VoiceDetails> {
    try {
      const response = await this.fetch(`/voices/${voiceId}`, {
        method: 'GET',
      });
      return response;
    } catch (error) {
      throw new Error(`Failed to get voice details: ${error}`);
    }
  }

  /**
   * Change a character's voice
   */
  async setCharacterVoice(
    characterId: string,
    voiceId: string
  ): Promise<{ success: boolean; character: string; voice_id: string }> {
    try {
      const response = await this.fetch(
        `/characters/${characterId}/voice`,
        {
          method: 'POST',
          body: JSON.stringify({ voice_id: voiceId }),
        }
      );
      return response;
    } catch (error) {
      throw new Error(
        `Failed to set character voice: ${error}`
      );
    }
  }

  /**
   * Generate audio for text (main OpenRouter integration endpoint)
   */
  async generateAudio(
    options: AudioGenerationOptions
  ): Promise<AudioGenerationResponse> {
    const {
      text,
      character = 'narrator',
      voiceId,
      returnFormat = 'base64',
      maxTokens = 400,
    } = options;

    if (!text || !text.trim()) {
      throw new Error('Text cannot be empty');
    }

    const payload: any = {
      text,
      character,
      return_format: returnFormat,
      max_tokens: maxTokens,
    };

    // Include voice_id if provided
    if (voiceId) {
      payload.voice_id = voiceId;
    }

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const response = await this.fetch('/generate-audio', {
          method: 'POST',
          body: JSON.stringify(payload),
        });

        if (response.success) {
          return response;
        } else {
          throw new Error(response.error || 'Generation failed');
        }
      } catch (error) {
        if (attempt === this.retryAttempts) {
          throw new Error(
            `Audio generation failed after ${this.retryAttempts} attempts: ${error}`
          );
        }

        // Wait before retry (exponential backoff)
        const waitTime = Math.pow(2, attempt - 1) * 1000;
        await new Promise((resolve) => setTimeout(resolve, waitTime));
      }
    }

    throw new Error('Max retry attempts exceeded');
  }

  /**
   * Generate audio and return as WAV Blob
   */
  async generateAudioBlob(
    options: AudioGenerationOptions
  ): Promise<{ blob: Blob; duration: number }> {
    const result = await this.generateAudio({
      ...options,
      returnFormat: 'base64',
    });

    if (!result.audio) {
      throw new Error('No audio data received');
    }

    // Decode base64 to blob
    const binary = atob(result.audio);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    const blob = new Blob([bytes], { type: 'audio/wav' });
    return { blob, duration: result.duration };
  }

  /**
   * Get playable audio URL from blob
   */
  createAudioUrl(blob: Blob): string {
    return URL.createObjectURL(blob);
  }

  /**
   * Clean up audio URL
   */
  revokeAudioUrl(url: string): void {
    URL.revokeObjectURL(url);
  }

  /**
   * Generate audio and get playable URL
   */
  async generatePlayableAudio(
    options: AudioGenerationOptions
  ): Promise<{ url: string; duration: number; revoke: () => void }> {
    const { blob, duration } = await this.generateAudioBlob(options);
    const url = this.createAudioUrl(blob);

    return {
      url,
      duration,
      revoke: () => this.revokeAudioUrl(url),
    };
  }

  /**
   * Internal fetch wrapper with error handling
   */
  private async fetch(
    endpoint: string,
    options: RequestInit
  ): Promise<any> {
    const url = `${this.apiUrl}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(
          error.error || `HTTP ${response.status}: ${response.statusText}`
        );
      }

      return await response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

/**
 * OpenRouter Integration - Higher level API for AI character responses
 */
export class OpenRouterTTSIntegration {
  private client: ChatterboxTTSClient;
  private characterMap: Map<string, string> = new Map();
  private defaultCharacter: string;

  constructor(apiUrl: string, defaultCharacter: string = 'narrator') {
    this.client = new ChatterboxTTSClient(apiUrl);
    this.defaultCharacter = defaultCharacter;
  }

  /**
   * Map AI character names to TTS voices
   */
  mapCharacter(aiCharacterName: string, voiceId: string): void {
    this.characterMap.set(aiCharacterName.toLowerCase(), voiceId);
  }

  /**
   * Get TTS voice for an AI character
   */
  private getVoiceForCharacter(aiCharacterName: string): string {
    return (
      this.characterMap.get(aiCharacterName.toLowerCase()) ||
      this.defaultCharacter
    );
  }

  /**
   * Process OpenRouter AI response and generate audio
   */
  async processAIResponse(
    text: string,
    aiCharacterName: string
  ): Promise<{
    text: string;
    character: string;
    audioUrl: string;
    duration: number;
    revoke: () => void;
  }> {
    const voiceId = this.getVoiceForCharacter(aiCharacterName);

    try {
      const { url: audioUrl, duration, revoke } = await this.client.generatePlayableAudio({
        text,
        character: voiceId,
      });

      return {
        text,
        character: aiCharacterName,
        audioUrl,
        duration,
        revoke,
      };
    } catch (error) {
      throw new Error(
        `Failed to generate audio for character "${aiCharacterName}": ${error}`
      );
    }
  }

  /**
   * Batch process multiple AI responses
   */
  async processBatch(
    responses: Array<{ text: string; character: string }>
  ): Promise<
    Array<{
      text: string;
      character: string;
      audioUrl: string;
      duration: number;
      revoke: () => void;
      error?: string;
    }>
  > {
    return Promise.all(
      responses.map(async (response) => {
        try {
          return await this.processAIResponse(response.text, response.character);
        } catch (error) {
          return {
            text: response.text,
            character: response.character,
            audioUrl: '',
            duration: 0,
            revoke: () => {},
            error: error instanceof Error ? error.message : String(error),
          };
        }
      })
    );
  }
}

/**
 * React Hook for easy integration
 */
export function useChatterboxTTS(apiUrl: string) {
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [audioUrl, setAudioUrl] = React.useState<string | null>(null);
  const [duration, setDuration] = React.useState<number>(0);

  const clientRef = React.useRef<ChatterboxTTSClient | null>(null);

  React.useEffect(() => {
    clientRef.current = new ChatterboxTTSClient(apiUrl);

    return () => {
      if (audioUrl) {
        clientRef.current?.revokeAudioUrl(audioUrl);
      }
    };
  }, [apiUrl, audioUrl]);

  const generateAudio = React.useCallback(
    async (text: string, character: string = 'narrator') => {
      if (!clientRef.current) return;

      setIsLoading(true);
      setError(null);

      try {
        const { url, duration: dur } = await clientRef.current.generatePlayableAudio({
          text,
          character,
        });

        if (audioUrl) {
          clientRef.current.revokeAudioUrl(audioUrl);
        }

        setAudioUrl(url);
        setDuration(dur);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : 'Failed to generate audio'
        );
        setAudioUrl(null);
        setDuration(0);
      } finally {
        setIsLoading(false);
      }
    },
    [audioUrl]
  );

  return {
    generateAudio,
    isLoading,
    error,
    audioUrl,
    duration,
  };
}

/**
 * Export convenience factory functions
 */
export function createTTSClient(apiUrl: string): ChatterboxTTSClient {
  return new ChatterboxTTSClient(apiUrl);
}

export function createOpenRouterIntegration(
  apiUrl: string,
  defaultCharacter?: string
): OpenRouterTTSIntegration {
  return new OpenRouterTTSIntegration(apiUrl, defaultCharacter);
}

// Default export
export default ChatterboxTTSClient;
