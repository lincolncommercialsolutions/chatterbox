/**
 * Example React Component: Voice and Character Selector
 * 
 * This example shows how to:
 * - Load available voices and characters
 * - Display a selector UI
 * - Generate audio with voice selection
 * - Change character voices at runtime
 */

'use client'; // For Next.js App Router

import React, { useState, useEffect } from 'react';
import { ChatterboxTTSClient, Voice, CharacterDetails } from '@/lib/chatterbox-tts-client';

interface VoiceSelectorProps {
  apiUrl: string;
  onAudioGenerated?: (audio: Blob, duration: number) => void;
}

export function VoiceAndCharacterSelector({ apiUrl, onAudioGenerated }: VoiceSelectorProps) {
  const [client] = useState(() => new ChatterboxTTSClient(apiUrl));
  
  // State for voices and characters
  const [voices, setVoices] = useState<Voice[]>([]);
  const [characters, setCharacters] = useState<any[]>([]);
  const [selectedCharacter, setSelectedCharacter] = useState<string>('narrator');
  const [selectedVoice, setSelectedVoice] = useState<string>('');
  const [characterDetails, setCharacterDetails] = useState<CharacterDetails | null>(null);
  
  // State for text and generation
  const [text, setText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Load voices and characters on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const [voicesData, charactersData] = await Promise.all([
          client.getVoices(),
          client.getCharacters(),
        ]);
        
        setVoices(voicesData);
        setCharacters(charactersData);
        
        // Load details for default character
        const details = await client.getCharacterDetails('narrator');
        setCharacterDetails(details);
        setSelectedVoice(''); // Use default voice
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load voices and characters');
      }
    };

    loadData();
  }, [client]);

  // Handle character change
  const handleCharacterChange = async (characterId: string) => {
    try {
      setSelectedCharacter(characterId);
      const details = await client.getCharacterDetails(characterId);
      setCharacterDetails(details);
      setSelectedVoice(''); // Reset to character's default voice
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load character details');
    }
  };

  // Handle voice change for character
  const handleSetCharacterVoice = async (voiceId: string) => {
    try {
      const result = await client.setCharacterVoice(selectedCharacter, voiceId);
      
      // Reload character details
      const details = await client.getCharacterDetails(selectedCharacter);
      setCharacterDetails(details);
      
      setError(null);
      console.log(`Updated ${selectedCharacter} to use ${result.voice_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change voice');
    }
  };

  // Generate audio with current selections
  const handleGenerateAudio = async () => {
    if (!text.trim()) {
      setError('Please enter some text');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      // Generate with optional voice override
      const { blob, duration } = await client.generateAudioBlob({
        text,
        character: selectedCharacter,
        voiceId: selectedVoice || undefined, // Only send if explicitly selected
      });

      const url = client.createAudioUrl(blob);
      setAudioUrl(url);

      // Call parent callback if provided
      onAudioGenerated?.(blob, duration);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate audio');
    } finally {
      setIsGenerating(false);
    }
  };

  // Cleanup audio URL on unmount
  useEffect(() => {
    return () => {
      if (audioUrl) {
        client.revokeAudioUrl(audioUrl);
      }
    };
  }, [audioUrl, client]);

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '20px' }}>
      <h1>Voice & Character Selector</h1>

      {/* Error Display */}
      {error && (
        <div style={{ color: 'red', marginBottom: '10px', padding: '10px', backgroundColor: '#ffeeee', borderRadius: '4px' }}>
          {error}
        </div>
      )}

      {/* Character Selector */}
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="character-select">
          <strong>Select Character:</strong>
        </label>
        <select
          id="character-select"
          value={selectedCharacter}
          onChange={(e) => handleCharacterChange(e.target.value)}
          style={{ display: 'block', width: '100%', padding: '8px', marginTop: '8px' }}
        >
          {characters.map(char => (
            <option key={char.id} value={char.id}>
              {char.name} ({char.id})
            </option>
          ))}
        </select>

        {/* Character Details */}
        {characterDetails && (
          <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
            <p><strong>Name:</strong> {characterDetails.name}</p>
            <p><strong>Description:</strong> {characterDetails.description}</p>
            <p><strong>Current Voice:</strong> {characterDetails.voice_id}</p>
            
            {characterDetails.parameters && (
              <div>
                <p><strong>Generation Parameters:</strong></p>
                <ul style={{ margin: '5px 0', paddingLeft: '20px' }}>
                  <li>Exaggeration: {characterDetails.parameters.exaggeration}</li>
                  <li>Temperature: {characterDetails.parameters.temperature}</li>
                  <li>CFG Weight: {characterDetails.parameters.cfg_weight}</li>
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Voice Override Selector */}
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="voice-select">
          <strong>Override Voice (optional):</strong>
        </label>
        <select
          id="voice-select"
          value={selectedVoice}
          onChange={(e) => setSelectedVoice(e.target.value)}
          style={{ display: 'block', width: '100%', padding: '8px', marginTop: '8px' }}
        >
          <option value="">Use Character's Default Voice</option>
          {voices.map(voice => (
            <option key={voice.id} value={voice.id}>
              {voice.name} ({voice.id})
            </option>
          ))}
        </select>

        {selectedVoice && (
          <button
            onClick={() => handleSetCharacterVoice(selectedVoice)}
            style={{
              marginTop: '8px',
              padding: '8px 12px',
              backgroundColor: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Update {selectedCharacter}'s Default Voice
          </button>
        )}
      </div>

      {/* Text Input */}
      <div style={{ marginBottom: '20px' }}>
        <label htmlFor="text-input">
          <strong>Text to Convert:</strong>
        </label>
        <textarea
          id="text-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to convert to speech..."
          style={{
            display: 'block',
            width: '100%',
            padding: '8px',
            marginTop: '8px',
            minHeight: '100px',
            fontFamily: 'monospace'
          }}
        />
        <small>{text.length} / 500 characters</small>
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerateAudio}
        disabled={isGenerating}
        style={{
          width: '100%',
          padding: '12px',
          backgroundColor: isGenerating ? '#ccc' : '#2196F3',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: isGenerating ? 'not-allowed' : 'pointer',
          fontSize: '16px',
          fontWeight: 'bold'
        }}
      >
        {isGenerating ? 'Generating Audio...' : 'Generate Audio'}
      </button>

      {/* Audio Player */}
      {audioUrl && (
        <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#e3f2fd', borderRadius: '4px' }}>
          <h3>Generated Audio</h3>
          <audio
            src={audioUrl}
            controls
            autoPlay
            style={{ width: '100%' }}
          />
        </div>
      )}

      {/* Voice List Reference */}
      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
        <h3>Available Voices</h3>
        {voices.length > 0 ? (
          <ul style={{ marginLeft: '20px' }}>
            {voices.map(voice => (
              <li key={voice.id}>
                <strong>{voice.name}</strong> ({voice.id}): {voice.description}
                {voice.tags && <small> - {voice.tags.join(', ')}</small>}
              </li>
            ))}
          </ul>
        ) : (
          <p>Loading voices...</p>
        )}
      </div>
    </div>
  );
}

/**
 * Alternative: Simple Voice Selector Hook
 * 
 * For simpler use cases, use this hook instead
 */
export function useVoiceSelector(apiUrl: string) {
  const [client] = useState(() => new ChatterboxTTSClient(apiUrl));
  const [voices, setVoices] = useState<Voice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<string>('narrator');

  useEffect(() => {
    client.getVoices().then(setVoices).catch(console.error);
  }, [client]);

  const generateWithVoice = async (text: string, voiceId?: string) => {
    return client.generateAudioBlob({
      text,
      character: 'narrator', // Or your default character
      voiceId: voiceId || selectedVoice,
    });
  };

  return {
    voices,
    selectedVoice,
    setSelectedVoice,
    generateWithVoice,
  };
}

/**
 * Example Usage:
 * 
 * import { VoiceAndCharacterSelector } from '@/components/VoiceSelector.example';
 * 
 * export default function Page() {
 *   return (
 *     <VoiceAndCharacterSelector
 *       apiUrl={process.env.NEXT_PUBLIC_TTS_API_URL || 'http://localhost:5000'}
 *       onAudioGenerated={(blob, duration) => {
 *         console.log(`Generated ${duration}s of audio`);
 *       }}
 *     />
 *   );
 * }
 */
