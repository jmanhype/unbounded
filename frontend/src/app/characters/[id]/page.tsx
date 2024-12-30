'use client';

import { useEffect, useState, FormEvent } from 'react';
import { useParams } from 'next/navigation';
import Image from 'next/image';
import { charactersApi, interactionsApi } from '@/lib/api';
import type { Character, Interaction, BackstoryResponse } from '@/lib/types';

export default function CharacterDetailPage() {
  const { id } = useParams();
  const [character, setCharacter] = useState<Character | null>(null);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [generatingImage, setGeneratingImage] = useState(false);
  const [generatingBackstory, setGeneratingBackstory] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const getImageUrl = (path: string | null): string => {
    if (!path) return '/placeholder.png';
    if (path.startsWith('http')) return path;
    return `${API_URL}/${path}`;
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        // First fetch character details
        const characterData = await charactersApi.get(id as string);
        setCharacter(characterData);
        
        try {
          // Then try to fetch interactions, but don't fail if they're not available
          const interactionsData = await interactionsApi.list(id as string);
          setInteractions(interactionsData || []);
        } catch (err) {
          console.log('No interactions available yet:', err);
          setInteractions([]);
        }
        
        setLoading(false);
      } catch (err: any) {
        console.error('Error fetching character data:', err);
        setError(err.message || 'Failed to load character');
        setLoading(false);
      }
    };

    if (id) {
      fetchData();
    }
  }, [id]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;

    setSending(true);
    try {
      const response = await interactionsApi.create(id as string, input);
      setInteractions([...interactions, response]);
      setInput('');
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSending(false);
    }
  };

  const generateImage = async () => {
    if (!character || generatingImage) return;
    
    setGeneratingImage(true);
    try {
      const updatedCharacter = await charactersApi.generateImage(id as string, {
        prompt: `Portrait of ${character.name}. ${character.description}`,
        width: 512,
        height: 512,
        num_inference_steps: 50,
        guidance_scale: 7.5
      });
      setCharacter(updatedCharacter);
    } catch (err) {
      console.error('Failed to generate image:', err);
    } finally {
      setGeneratingImage(false);
    }
  };

  const generateBackstory = async () => {
    if (!character || generatingBackstory) return;
    
    setGeneratingBackstory(true);
    try {
      // Generate the backstory
      await charactersApi.generateBackstory(id as string, {
        tone: 'balanced',
        length: 'medium',
        themes: ['adventure', 'mystery', 'friendship']
      });
      
      // Fetch the updated character data
      const updatedCharacter = await charactersApi.get(id as string);
      setCharacter(updatedCharacter);
      
      // Log the updated character data
      console.log('Updated character data:', updatedCharacter);
    } catch (err: any) {
      console.error('Failed to generate backstory:', err);
      setError(err.message || 'Failed to generate backstory');
    } finally {
      setGeneratingBackstory(false);
    }
  };

  if (loading) return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  if (error) return <div className="flex items-center justify-center min-h-screen text-red-500">Error: {error}</div>;
  if (!character) return <div className="flex items-center justify-center min-h-screen">Character not found</div>;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="flex flex-col md:flex-row gap-8 mb-8">
        {/* Character Info */}
        <div className="md:w-1/3">
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="relative w-full h-64 bg-gray-100">
              {character.image_url ? (
                <Image
                  src={getImageUrl(character.image_url)}
                  alt={character.name}
                  fill
                  className="object-cover"
                  unoptimized
                />
              ) : (
                <div className="absolute inset-0 flex items-center justify-center">
                  <button
                    onClick={generateImage}
                    disabled={generatingImage}
                    className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
                  >
                    {generatingImage ? 'Generating...' : 'Generate Image'}
                  </button>
                </div>
              )}
            </div>
            <div className="p-6 space-y-6">
              <div>
                <h1 className="text-2xl font-bold mb-2">{character.name}</h1>
                <p className="text-gray-600">{character.description}</p>
              </div>
              
              {character.backstory ? (
                <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
                  <h2 className="text-xl font-semibold mb-3">Backstory</h2>
                  <p className="text-gray-600 whitespace-pre-wrap leading-relaxed">{character.backstory}</p>
                </div>
              ) : (
                <div>
                  <button
                    onClick={generateBackstory}
                    disabled={generatingBackstory}
                    className="w-full bg-blue-500 text-white px-4 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 font-medium"
                  >
                    {generatingBackstory ? 'Generating Backstory...' : 'Generate Backstory'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Chat Interface */}
        <div className="md:w-2/3">
          <div className="bg-white rounded-lg shadow-lg h-[600px] flex flex-col">
            <div className="p-4 border-b">
              <h2 className="text-xl font-semibold">Chat with {character.name}</h2>
            </div>
            
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {interactions.length > 0 ? (
                interactions.map((interaction) => (
                  <div key={interaction.id} className="space-y-2">
                    <div className="flex justify-end">
                      <div className="bg-blue-500 text-white rounded-lg py-2 px-4 max-w-[80%]">
                        {interaction.content}
                      </div>
                    </div>
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg py-2 px-4 max-w-[80%]">
                        <p>{interaction.response.text}</p>
                        {interaction.response.emotion && (
                          <p className="text-sm text-gray-500 mt-1">Feeling: {interaction.response.emotion}</p>
                        )}
                        {interaction.response.action && (
                          <p className="text-sm text-gray-500">{interaction.response.action}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  {character.backstory ? 
                    "I'm ready to chat! Ask me anything about my backstory or let's start a new adventure!" :
                    "No interactions yet. Start a conversation!"
                  }
                </div>
              )}
            </div>
            
            {/* Input Form */}
            <form onSubmit={handleSubmit} className="p-4 border-t">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={character.backstory ? 
                    "Chat with me about my backstory or start a new adventure!" : 
                    "Type your message..."
                  }
                  className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:border-blue-500"
                  disabled={sending}
                />
                <button
                  type="submit"
                  disabled={sending || !input.trim()}
                  className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {sending ? 'Sending...' : 'Send'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
} 