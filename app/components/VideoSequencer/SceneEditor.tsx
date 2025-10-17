'use client';

import React, { useState, useEffect } from 'react';
import type { Scene, VideoModel, AspectRatio, Resolution, AddSceneRequest, UpdateSceneRequest } from '../../types/sequence';

interface SceneEditorProps {
  scene?: Scene; // If provided, edit mode; otherwise, create mode
  onSave: (data: AddSceneRequest | UpdateSceneRequest) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

export function SceneEditor({ scene, onSave, onCancel, isLoading = false }: SceneEditorProps) {
  const isEditMode = !!scene;

  const [prompt, setPrompt] = useState(scene?.prompt || '');
  const [duration, setDuration] = useState(scene?.config.duration || 5);
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>(scene?.config.aspectRatio || '16:9');
  const [resolution, setResolution] = useState<Resolution>(scene?.config.resolution || '720p');
  const [model, setModel] = useState<VideoModel>(scene?.model || 'veo-3.1-generate-preview');

  const [estimatedCost, setEstimatedCost] = useState<number | null>(null);

  // Calculate estimated cost
  useEffect(() => {
    const basePricePerSecond = model === 'veo-3.1-generate-preview' ? 0.10 : 0.05;
    const resolutionMultiplier = resolution === '1080p' ? 1.5 : 1.0;
    const cost = duration * basePricePerSecond * resolutionMultiplier;
    setEstimatedCost(cost);
  }, [duration, model, resolution]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const data = {
      prompt: prompt.trim(),
      duration,
      aspectRatio,
      resolution,
      model,
    };

    onSave(data);
  };

  const isValid = prompt.trim().length >= 10 && prompt.trim().length <= 2000;

  return (
    <div className="bg-white rounded-lg shadow-lg border border-gray-200">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-900">
          {isEditMode ? `Edit Scene ${scene.sceneNumber}` : 'Add New Scene'}
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          {isEditMode ? 'Update scene details below' : 'Create a new scene for your video sequence'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="p-6 space-y-6">
        {/* Prompt */}
        <div>
          <label htmlFor="prompt" className="block text-sm font-medium text-gray-700 mb-2">
            Prompt *
          </label>
          <textarea
            id="prompt"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you want to see in this scene... (10-2000 characters)"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            disabled={isLoading}
          />
          <div className="flex items-center justify-between mt-1">
            <p className="text-xs text-gray-500">
              {prompt.length} / 2000 characters {prompt.length < 10 && '(minimum 10)'}
            </p>
            {!isValid && prompt.length > 0 && (
              <p className="text-xs text-red-600">
                {prompt.length < 10 ? 'Too short' : 'Too long'}
              </p>
            )}
          </div>
        </div>

        {/* Model Selection */}
        <div>
          <label htmlFor="model" className="block text-sm font-medium text-gray-700 mb-2">
            Model
          </label>
          <select
            id="model"
            value={model}
            onChange={(e) => setModel(e.target.value as VideoModel)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          >
            <option value="veo-3.1-generate-preview">Veo 3.1 (High Quality)</option>
            <option value="veo-3.1-fast-generate-preview">Veo 3.1 Fast (Lower Cost)</option>
          </select>
          <p className="text-xs text-gray-500 mt-1">
            {model === 'veo-3.1-generate-preview'
              ? 'Best quality, ~$0.10/sec'
              : 'Faster generation, ~$0.05/sec'}
          </p>
        </div>

        {/* Duration, Aspect Ratio, Resolution Grid */}
        <div className="grid grid-cols-3 gap-4">
          {/* Duration */}
          <div>
            <label htmlFor="duration" className="block text-sm font-medium text-gray-700 mb-2">
              Duration
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                id="duration"
                min="1"
                max="8"
                step="1"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                className="flex-1"
                disabled={isLoading}
              />
              <span className="text-sm font-medium text-gray-900 w-8">{duration}s</span>
            </div>
            <p className="text-xs text-gray-500 mt-1">1-8 seconds</p>
          </div>

          {/* Aspect Ratio */}
          <div>
            <label htmlFor="aspectRatio" className="block text-sm font-medium text-gray-700 mb-2">
              Aspect Ratio
            </label>
            <select
              id="aspectRatio"
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value as AspectRatio)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            >
              <option value="16:9">16:9 (Landscape)</option>
              <option value="9:16">9:16 (Portrait)</option>
              <option value="1:1">1:1 (Square)</option>
            </select>
          </div>

          {/* Resolution */}
          <div>
            <label htmlFor="resolution" className="block text-sm font-medium text-gray-700 mb-2">
              Resolution
            </label>
            <select
              id="resolution"
              value={resolution}
              onChange={(e) => setResolution(e.target.value as Resolution)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            >
              <option value="720p">720p (HD)</option>
              <option value="1080p">1080p (Full HD)</option>
            </select>
          </div>
        </div>

        {/* Estimated Cost */}
        {estimatedCost !== null && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-900">Estimated Cost</p>
                <p className="text-xs text-blue-700 mt-1">
                  Based on {duration}s at {resolution} using {model === 'veo-3.1-generate-preview' ? 'standard' : 'fast'} model
                </p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-blue-900">${estimatedCost.toFixed(4)}</p>
              </div>
            </div>
          </div>
        )}

        {/* Continuity Info (Edit Mode) */}
        {isEditMode && scene.continuity.usesLastFrame && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" className="text-yellow-600 mt-0.5">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-yellow-900">Continuity Enabled</p>
                <p className="text-xs text-yellow-700 mt-1">
                  This scene uses the last frame from Scene {scene.continuity.fromSceneNumber} for seamless transitions
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!isValid || isLoading}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isLoading && (
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            )}
            {isLoading ? 'Saving...' : isEditMode ? 'Update Scene' : 'Add Scene'}
          </button>
        </div>
      </form>
    </div>
  );
}
