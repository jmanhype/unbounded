'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { charactersApi } from '@/lib/api';

type CreationStep = 'idle' | 'creating' | 'generating-image' | 'generating-backstory' | 'initializing' | 'complete';

type BackstoryTone = 'dark' | 'light' | 'balanced' | 'heroic' | 'tragic' | 'mysterious';
type BackstoryLength = 'short' | 'medium' | 'long';

export default function CreateCharacterPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [tone, setTone] = useState<BackstoryTone>('balanced');
  const [length, setLength] = useState<BackstoryLength>('medium');
  const [themes, setThemes] = useState<string[]>(['adventure', 'mystery', 'friendship']);
  const [step, setStep] = useState<CreationStep>('idle');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setStep('creating');

    try {
      const character = await charactersApi.createFullCharacter({
        name,
        description,
        imageOptions: {
          width: 512,
          height: 512,
          num_inference_steps: 50,
          guidance_scale: 7.5,
          negative_prompt: "blurry, low quality, bad anatomy, extra limbs, poorly drawn face"
        },
        backstoryOptions: {
          tone,
          length,
          themes
        },
        onProgress: (currentStep) => {
          setStep(currentStep);
        }
      });
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      router.push(`/characters/${character.id}`);
    } catch (err: any) {
      console.error('Error creating character:', err);
      const errorMessage = err.message || err.response?.data?.detail || 'Failed to create character';
      setError(errorMessage);
      setStep('idle');
    }
  };

  const getStepMessage = () => {
    switch (step) {
      case 'creating':
        return 'Creating your character...';
      case 'generating-image':
        return 'Generating character portrait...';
      case 'generating-backstory':
        return 'Writing character backstory...';
      case 'initializing':
        return 'Initializing character state...';
      case 'complete':
        return 'Character created! Redirecting...';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Create New Character</h1>
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="rounded-md bg-red-50 p-4">
                  <div className="text-sm text-red-700">{error}</div>
                </div>
              )}
              
              {/* Basic Info Section */}
              <div className="space-y-4">
                <h2 className="text-lg font-medium text-gray-900">Basic Information</h2>
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Name
                  </label>
                  <div className="mt-1">
                    <input
                      type="text"
                      id="name"
                      name="name"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Enter character name"
                      disabled={step !== 'idle'}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <div className="mt-1">
                    <textarea
                      id="description"
                      name="description"
                      required
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      rows={4}
                      className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                      placeholder="Describe your character"
                      disabled={step !== 'idle'}
                    />
                  </div>
                </div>
              </div>

              {/* Backstory Options Section */}
              <div className="space-y-4">
                <h2 className="text-lg font-medium text-gray-900">Backstory Options</h2>
                <div>
                  <label htmlFor="tone" className="block text-sm font-medium text-gray-700">
                    Tone
                  </label>
                  <select
                    id="tone"
                    name="tone"
                    value={tone}
                    onChange={(e) => setTone(e.target.value as BackstoryTone)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    disabled={step !== 'idle'}
                  >
                    <option value="dark">Dark</option>
                    <option value="light">Light</option>
                    <option value="balanced">Balanced</option>
                    <option value="heroic">Heroic</option>
                    <option value="tragic">Tragic</option>
                    <option value="mysterious">Mysterious</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="length" className="block text-sm font-medium text-gray-700">
                    Length
                  </label>
                  <select
                    id="length"
                    name="length"
                    value={length}
                    onChange={(e) => setLength(e.target.value as BackstoryLength)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                    disabled={step !== 'idle'}
                  >
                    <option value="short">Short</option>
                    <option value="medium">Medium</option>
                    <option value="long">Long</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Themes
                  </label>
                  <div className="mt-2 space-y-2">
                    {['adventure', 'mystery', 'friendship', 'romance', 'tragedy', 'redemption'].map((theme) => (
                      <label key={theme} className="inline-flex items-center mr-4">
                        <input
                          type="checkbox"
                          checked={themes.includes(theme)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setThemes([...themes, theme]);
                            } else {
                              setThemes(themes.filter(t => t !== theme));
                            }
                          }}
                          className="form-checkbox h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                          disabled={step !== 'idle'}
                        />
                        <span className="ml-2 text-sm text-gray-700 capitalize">{theme}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {step !== 'idle' && (
                <div className="rounded-md bg-blue-50 p-4">
                  <div className="flex">
                    <div className="flex-shrink-0">
                      <svg className="animate-spin h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-blue-800">
                        {getStepMessage()}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => router.back()}
                  disabled={step !== 'idle'}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={step !== 'idle'}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                >
                  {step === 'idle' ? 'Create Character' : 'Creating...'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
} 