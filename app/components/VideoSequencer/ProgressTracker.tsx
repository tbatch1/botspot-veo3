'use client';

import React from 'react';
import type { Sequence, Scene } from '../../types/sequence';

interface ProgressTrackerProps {
  sequence: Sequence;
  onCancelGeneration?: () => void;
  className?: string;
}

export function ProgressTracker({
  sequence,
  onCancelGeneration,
  className = '',
}: ProgressTrackerProps) {
  const totalScenes = sequence.scenes.length;
  const completedScenes = sequence.scenes.filter((s) => s.status === 'completed').length;
  const generatingScenes = sequence.scenes.filter((s) => s.status === 'generating');
  const failedScenes = sequence.scenes.filter((s) => s.status === 'failed').length;
  const pendingScenes = sequence.scenes.filter((s) => s.status === 'pending').length;

  const isGenerating = sequence.status === 'generating' || generatingScenes.length > 0;
  const progress = totalScenes > 0 ? (completedScenes / totalScenes) * 100 : 0;

  const getStatusColor = (scene: Scene) => {
    switch (scene.status) {
      case 'completed':
        return 'bg-green-500';
      case 'generating':
        return 'bg-blue-500 animate-pulse';
      case 'failed':
        return 'bg-red-500';
      case 'pending':
      default:
        return 'bg-gray-300';
    }
  };

  const getStatusIcon = (scene: Scene) => {
    switch (scene.status) {
      case 'completed':
        return (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-green-600">
            <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z" />
          </svg>
        );
      case 'generating':
        return (
          <svg className="animate-spin h-4 w-4 text-blue-600" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        );
      case 'failed':
        return (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-red-600">
            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z" />
          </svg>
        );
      case 'pending':
      default:
        return (
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-gray-400">
            <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
            <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z" />
          </svg>
        );
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Generation Progress</h3>
          {isGenerating && onCancelGeneration && (
            <button
              onClick={onCancelGeneration}
              className="px-3 py-1 text-sm text-red-600 border border-red-300 rounded hover:bg-red-50 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>

        {/* Overall Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-gray-700">
              {completedScenes} of {totalScenes} scenes completed
            </p>
            <p className="text-sm font-bold text-gray-900">{Math.round(progress)}%</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Status Summary */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          <div className="bg-green-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-700">{completedScenes}</div>
            <div className="text-xs text-green-600 mt-1">Completed</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-700">{generatingScenes.length}</div>
            <div className="text-xs text-blue-600 mt-1">Generating</div>
          </div>
          <div className="bg-gray-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-gray-700">{pendingScenes}</div>
            <div className="text-xs text-gray-600 mt-1">Pending</div>
          </div>
          <div className="bg-red-50 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-700">{failedScenes}</div>
            <div className="text-xs text-red-600 mt-1">Failed</div>
          </div>
        </div>

        {/* Scene Status List */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700 mb-3">Scene Status</p>
          <div className="max-h-64 overflow-y-auto space-y-2">
            {sequence.scenes.map((scene) => (
              <div
                key={scene.sceneNumber}
                className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                {/* Status Indicator */}
                <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center">
                  {getStatusIcon(scene)}
                </div>

                {/* Scene Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-gray-900">
                      Scene {scene.sceneNumber}
                    </p>
                    {scene.continuity.usesLastFrame && scene.sceneNumber > 1 && (
                      <span className="text-xs text-blue-600">
                        (Continuity)
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 truncate mt-0.5">
                    {scene.prompt.substring(0, 60)}
                    {scene.prompt.length > 60 ? '...' : ''}
                  </p>
                  {scene.error && (
                    <p className="text-xs text-red-600 mt-1">{scene.error}</p>
                  )}
                </div>

                {/* Duration & Cost */}
                <div className="flex-shrink-0 text-right">
                  <p className="text-xs text-gray-500">{scene.config.duration}s</p>
                  {scene.cost && (
                    <p className="text-xs text-gray-600 font-medium">
                      ${(scene.cost.actual || scene.cost.estimated).toFixed(4)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Estimated Time Remaining (for generating scenes) */}
        {isGenerating && generatingScenes.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg">
              <svg className="animate-spin h-5 w-5 text-blue-600 mt-0.5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-900">Generation in Progress</p>
                <p className="text-xs text-blue-700 mt-1">
                  Currently generating scene{generatingScenes.length > 1 ? 's' : ''}{' '}
                  {generatingScenes.map((s) => s.sceneNumber).join(', ')}
                </p>
                <p className="text-xs text-blue-600 mt-2">
                  Estimated time: ~{pendingScenes + generatingScenes.length * 2}-
                  {(pendingScenes + generatingScenes.length) * 3} minutes
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Success Message */}
        {completedScenes === totalScenes && totalScenes > 0 && !isGenerating && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-start gap-3 p-4 bg-green-50 rounded-lg">
              <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" className="text-green-600 mt-0.5">
                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">All Scenes Generated!</p>
                <p className="text-xs text-green-700 mt-1">
                  Your sequence is complete. You can now export the final video.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Summary */}
        {failedScenes > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
              <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" className="text-red-600 mt-0.5">
                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900">{failedScenes} Scene{failedScenes !== 1 ? 's' : ''} Failed</p>
                <p className="text-xs text-red-700 mt-1">
                  Some scenes failed to generate. Try regenerating them individually.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
