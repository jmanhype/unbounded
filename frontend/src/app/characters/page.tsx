'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { charactersApi } from '@/lib/api';
import type { Character } from '@/lib/types';

export default function CharactersPage() {
  const router = useRouter();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCharacters = async () => {
      try {
        const data = await charactersApi.list();
        setCharacters(data);
      } catch (err: any) {
        console.error('Error fetching characters:', err);
        setError(err.response?.data?.detail || 'Failed to load characters');
      } finally {
        setLoading(false);
      }
    };

    fetchCharacters();
  }, []);

  const handleCreateCharacter = () => {
    router.push('/characters/create');
  };

  const handleCharacterClick = (id: string) => {
    router.push(`/characters/${id}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">Loading characters...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Your Characters</h1>
          <button
            onClick={handleCreateCharacter}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Create Character
          </button>
        </div>

        {characters.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No characters yet. Create your first one!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {characters.map((character) => (
              <div
                key={character.id}
                onClick={() => handleCharacterClick(character.id)}
                className="bg-white overflow-hidden shadow rounded-lg cursor-pointer hover:shadow-md transition-shadow duration-200"
              >
                {character.image_url && (
                  <div className="aspect-w-16 aspect-h-9">
                    <img
                      src={character.image_url}
                      alt={character.name}
                      className="object-cover"
                    />
                  </div>
                )}
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg font-medium text-gray-900">{character.name}</h3>
                  <p className="mt-1 text-sm text-gray-500 line-clamp-3">
                    {character.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 