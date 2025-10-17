'use client';

import React from 'react';
import type { Scene } from '../../types/sequence';

interface SceneCardProps {
  scene: Scene;
  onEdit: () => void;
  onDelete: () => void;
  onRegenerate: () => void;
  isSelected: boolean;
  className?: string;
}

export function SceneCard({
  scene,
  onEdit,
  onDelete,
  onRegenerate,
  isSelected,
  className = '',
}: SceneCardProps) {
  const getStatusBadge = () => {
    switch (scene.status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✓ Completed
          </span>
        );
      case 'generating':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 animate-pulse">
            ⏳ Generating...
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
            ✗ Failed
          </span>
        );
      case 'pending':
      default:
        return (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            ○ Pending
          </span>
        );
    }
  };

  const formatCost = (cost?: { estimated: number; actual: number }) => {
    if (!cost) return 'N/A';
    const amount = cost.actual > 0 ? cost.actual : cost.estimated;
    return `$${amount.toFixed(4)}`;
  };

  return (
    <div
      className={`
        relative rounded-lg border-2 bg-white shadow-sm transition-all duration-200
        ${isSelected ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'}
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-start justify-between p-4 border-b border-gray-100">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              Scene {scene.sceneNumber}
            </h3>
            {getStatusBadge()}
          </div>

          {/* Continuity Info */}
          {scene.continuity.usesLastFrame && scene.sceneNumber > 1 && (
            <div className="flex items-center gap-1 text-xs text-blue-600 mb-2">
              <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 0L6 2h4L8 0z" />
              </svg>
              <span>Uses last frame from Scene {scene.continuity.fromSceneNumber}</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={onEdit}
            disabled={scene.status === 'generating'}
            className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Edit scene"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M12.854.146a.5.5 0 0 0-.707 0L10.5 1.793 14.207 5.5l1.647-1.646a.5.5 0 0 0 0-.708l-3-3zm.646 4.646L9.793 1.085 3.293 7.585a.5.5 0 0 0-.134.234l-1 4a.5.5 0 0 0 .613.613l4-1a.5.5 0 0 0 .234-.134l6.5-6.5z" />
            </svg>
          </button>
          {scene.status === 'failed' && (
            <button
              onClick={onRegenerate}
              className="p-2 text-gray-600 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
              title="Regenerate scene"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 3a5 5 0 1 0 4.546 2.914.5.5 0 0 1 .908-.417A6 6 0 1 1 8 2v1z" />
                <path d="M8 4.466V.534a.25.25 0 0 1 .41-.192l2.36 1.966c.12.1.12.284 0 .384L8.41 4.658A.25.25 0 0 1 8 4.466z" />
              </svg>
            </button>
          )}
          <button
            onClick={onDelete}
            disabled={scene.status === 'generating'}
            className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            title="Delete scene"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z" />
              <path fillRule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Prompt */}
        <div className="mb-3">
          <p className="text-sm font-medium text-gray-700 mb-1">Prompt:</p>
          <p className="text-sm text-gray-900 bg-gray-50 p-2 rounded line-clamp-3">
            {scene.prompt}
          </p>
        </div>

        {/* Video Preview */}
        {scene.result?.videoUrl && (
          <div className="mb-3">
            <video
              src={scene.result.videoUrl}
              controls
              className="w-full rounded-lg"
              style={{ maxHeight: '200px' }}
            />
          </div>
        )}

        {/* Error Message */}
        {scene.error && (
          <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm font-medium text-red-800 mb-1">Error:</p>
            <p className="text-xs text-red-700">{scene.error}</p>
          </div>
        )}

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-gray-500 text-xs mb-1">Duration</p>
            <p className="font-medium text-gray-900">{scene.config.duration}s</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Model</p>
            <p className="font-medium text-gray-900 text-xs truncate">
              {scene.model === 'veo-3.1-generate-preview' ? 'Veo 3.1' : 'Veo 3.1 Fast'}
            </p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Aspect Ratio</p>
            <p className="font-medium text-gray-900">{scene.config.aspectRatio}</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Resolution</p>
            <p className="font-medium text-gray-900">{scene.config.resolution}</p>
          </div>
          <div>
            <p className="text-gray-500 text-xs mb-1">Cost</p>
            <p className="font-medium text-gray-900">{formatCost(scene.cost)}</p>
          </div>
          {scene.result?.duration && (
            <div>
              <p className="text-gray-500 text-xs mb-1">Actual Duration</p>
              <p className="font-medium text-gray-900">{scene.result.duration.toFixed(1)}s</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-50 border-t border-gray-100 rounded-b-lg">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Updated: {new Date(scene.updatedAt).toLocaleString()}</span>
          {scene.status === 'generating' && (
            <span className="text-blue-600 font-medium">⏳ Processing...</span>
          )}
        </div>
      </div>
    </div>
  );
}
