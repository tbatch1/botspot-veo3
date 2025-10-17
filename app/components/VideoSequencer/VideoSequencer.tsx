'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../../lib/api-client';
import { log } from '../../lib/logger';
import type {
  Sequence,
  Scene,
  AddSceneRequest,
  UpdateSceneRequest,
} from '../../types/sequence';

import { Timeline } from './Timeline';
import { SceneCard } from './SceneCard';
import { SceneEditor } from './SceneEditor';
import { PreviewPlayer } from './PreviewPlayer';
import { ExportPanel } from './ExportPanel';
import { ProgressTracker } from './ProgressTracker';

interface VideoSequencerProps {
  userId: string;
  sequenceId?: string; // Optional: load existing sequence
  onSequenceCreated?: (sequence: Sequence) => void;
  className?: string;
}

export function VideoSequencer({
  userId,
  sequenceId: initialSequenceId,
  onSequenceCreated,
  className = '',
}: VideoSequencerProps) {
  // State
  const [sequence, setSequence] = useState<Sequence | null>(null);
  const [selectedSceneNumber, setSelectedSceneNumber] = useState<number | undefined>();
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editingScene, setEditingScene] = useState<Scene | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // Load sequence on mount
  useEffect(() => {
    if (initialSequenceId) {
      loadSequence(initialSequenceId);
    } else {
      createNewSequence();
    }

    return () => {
      if (pollingInterval) clearInterval(pollingInterval);
    };
  }, [initialSequenceId]);

  // Poll for status updates when generating
  useEffect(() => {
    if (sequence && sequence.status === 'generating') {
      startStatusPolling();
    } else {
      stopStatusPolling();
    }

    return () => stopStatusPolling();
  }, [sequence?.status]);

  // ===== API Methods =====

  const createNewSequence = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const newSequence = await apiClient.createSequence({
        userId,
        title: `Video Sequence ${new Date().toLocaleDateString()}`,
        description: 'Created with VideoSequencer',
      });

      setSequence(newSequence);
      onSequenceCreated?.(newSequence);
      log.info('New sequence created', { sequenceId: newSequence.sequenceId });
    } catch (err: any) {
      setError(err.message || 'Failed to create sequence');
      log.error('Failed to create sequence', { error: err });
    } finally {
      setIsLoading(false);
    }
  };

  const loadSequence = async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const loadedSequence = await apiClient.getSequence(id);
      setSequence(loadedSequence);
      log.info('Sequence loaded', { sequenceId: id });
    } catch (err: any) {
      setError(err.message || 'Failed to load sequence');
      log.error('Failed to load sequence', { error: err });
    } finally {
      setIsLoading(false);
    }
  };

  const refreshSequence = async () => {
    if (!sequence) return;
    await loadSequence(sequence.sequenceId);
  };

  const startStatusPolling = () => {
    if (pollingInterval) return;

    const interval = setInterval(async () => {
      if (sequence) {
        try {
          const status = await apiClient.getSequenceStatus(sequence.sequenceId);
          await refreshSequence();
        } catch (err) {
          log.error('Status polling error', { error: err });
        }
      }
    }, 5000); // Poll every 5 seconds

    setPollingInterval(interval);
  };

  const stopStatusPolling = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      setPollingInterval(null);
    }
  };

  // ===== Scene Management =====

  const handleAddScene = async (data: AddSceneRequest) => {
    if (!sequence) return;

    try {
      setIsLoading(true);
      setError(null);

      const updatedSequence = await apiClient.addScene(sequence.sequenceId, data);
      setSequence(updatedSequence);
      setIsEditorOpen(false);
      setEditingScene(undefined);

      log.info('Scene added', { sequenceId: sequence.sequenceId, totalScenes: updatedSequence.scenes.length });
    } catch (err: any) {
      setError(err.message || 'Failed to add scene');
      log.error('Failed to add scene', { error: err });
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateScene = async (data: UpdateSceneRequest) => {
    if (!sequence || !editingScene) return;

    try {
      setIsLoading(true);
      setError(null);

      const updatedSequence = await apiClient.updateScene(
        sequence.sequenceId,
        editingScene.sceneNumber,
        data
      );
      setSequence(updatedSequence);
      setIsEditorOpen(false);
      setEditingScene(undefined);

      log.info('Scene updated', { sequenceId: sequence.sequenceId, sceneNumber: editingScene.sceneNumber });
    } catch (err: any) {
      setError(err.message || 'Failed to update scene');
      log.error('Failed to update scene', { error: err });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteScene = async (sceneNumber: number) => {
    if (!sequence) return;
    if (!confirm(`Are you sure you want to delete Scene ${sceneNumber}?`)) return;

    try {
      setIsLoading(true);
      setError(null);

      const updatedSequence = await apiClient.deleteScene(sequence.sequenceId, sceneNumber);
      setSequence(updatedSequence);

      if (selectedSceneNumber === sceneNumber) {
        setSelectedSceneNumber(undefined);
      }

      log.info('Scene deleted', { sequenceId: sequence.sequenceId, sceneNumber });
    } catch (err: any) {
      setError(err.message || 'Failed to delete scene');
      log.error('Failed to delete scene', { error: err });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReorderScenes = async (sceneOrders: Array<{ sceneNumber: number; newPosition: number }>) => {
    if (!sequence) return;

    try {
      const updatedSequence = await apiClient.reorderScenes(sequence.sequenceId, { sceneOrders });
      setSequence(updatedSequence);
      log.info('Scenes reordered', { sequenceId: sequence.sequenceId });
    } catch (err: any) {
      setError(err.message || 'Failed to reorder scenes');
      log.error('Failed to reorder scenes', { error: err });
    }
  };

  const handleRegenerateScene = async (sceneNumber: number) => {
    if (!sequence) return;

    try {
      setIsLoading(true);
      setError(null);

      await apiClient.generateScene(sequence.sequenceId, sceneNumber);
      await refreshSequence();

      log.info('Scene regeneration started', { sequenceId: sequence.sequenceId, sceneNumber });
    } catch (err: any) {
      setError(err.message || 'Failed to regenerate scene');
      log.error('Failed to regenerate scene', { error: err });
    } finally {
      setIsLoading(false);
    }
  };

  // ===== Generation & Export =====

  const handleGenerateAll = async () => {
    if (!sequence) return;

    try {
      setIsLoading(true);
      setError(null);

      await apiClient.generateAllScenes(sequence.sequenceId);
      await refreshSequence();

      log.info('Sequence generation started', { sequenceId: sequence.sequenceId });
    } catch (err: any) {
      setError(err.message || 'Failed to start generation');
      log.error('Failed to start generation', { error: err });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancelGeneration = async () => {
    if (!sequence) return;

    try {
      await apiClient.cancelGeneration(sequence.sequenceId);
      await refreshSequence();
      log.info('Generation cancelled', { sequenceId: sequence.sequenceId });
    } catch (err: any) {
      setError(err.message || 'Failed to cancel generation');
      log.error('Failed to cancel generation', { error: err });
    }
  };

  const handleExport = async () => {
    if (!sequence) return;

    try {
      const exportedSequence = await apiClient.exportSequence(sequence.sequenceId);
      setSequence(exportedSequence);
      log.info('Sequence exported', { sequenceId: sequence.sequenceId });
    } catch (err: any) {
      throw new Error(err.message || 'Failed to export sequence');
    }
  };

  // ===== UI Handlers =====

  const openAddSceneEditor = () => {
    setEditingScene(undefined);
    setIsEditorOpen(true);
  };

  const openEditSceneEditor = (scene: Scene) => {
    setEditingScene(scene);
    setIsEditorOpen(true);
  };

  const closeEditor = () => {
    setIsEditorOpen(false);
    setEditingScene(undefined);
  };

  const handleSceneSave = (data: AddSceneRequest | UpdateSceneRequest) => {
    if (editingScene) {
      handleUpdateScene(data as UpdateSceneRequest);
    } else {
      handleAddScene(data as AddSceneRequest);
    }
  };

  // ===== Render =====

  if (isLoading && !sequence) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 text-blue-600 mx-auto mb-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-gray-600">Loading sequence...</p>
        </div>
      </div>
    );
  }

  if (error && !sequence) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <p className="text-red-800 font-medium">Error: {error}</p>
        <button
          onClick={createNewSequence}
          className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Try Creating New Sequence
        </button>
      </div>
    );
  }

  if (!sequence) return null;

  const selectedScene = selectedSceneNumber
    ? sequence.scenes.find((s) => s.sceneNumber === selectedSceneNumber)
    : sequence.scenes[0];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{sequence.title}</h1>
            {sequence.description && (
              <p className="text-gray-600 mt-1">{sequence.description}</p>
            )}
            <p className="text-sm text-gray-500 mt-2">ID: {sequence.sequenceId}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={openAddSceneEditor}
              disabled={isLoading || sequence.status === 'generating'}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z" />
              </svg>
              Add Scene
            </button>
            <button
              onClick={handleGenerateAll}
              disabled={
                isLoading ||
                sequence.scenes.length === 0 ||
                sequence.status === 'generating' ||
                sequence.scenes.every((s) => s.status === 'completed')
              }
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M11.251.068a.5.5 0 0 1 .227.58L9.677 6.5H13a.5.5 0 0 1 .364.843l-8 8.5a.5.5 0 0 1-.842-.49L6.323 9.5H3a.5.5 0 0 1-.364-.843l8-8.5a.5.5 0 0 1 .615-.09z" />
              </svg>
              Generate All
            </button>
          </div>
        </div>

        {/* Global Error */}
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
            <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor" className="text-red-600 mt-0.5">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z" />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-800">Error</p>
              <p className="text-xs text-red-700 mt-1">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-600 hover:text-red-800"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" />
              </svg>
            </button>
          </div>
        )}

        {/* Timeline */}
        <Timeline
          scenes={sequence.scenes}
          onReorder={handleReorderScenes}
          onSceneClick={setSelectedSceneNumber}
          selectedSceneNumber={selectedSceneNumber}
          className="mt-4"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Scene Details & Preview */}
        <div className="lg:col-span-2 space-y-6">
          {/* Preview Player */}
          <PreviewPlayer
            scenes={sequence.scenes}
            currentSceneNumber={selectedSceneNumber}
            onSceneChange={setSelectedSceneNumber}
          />

          {/* Selected Scene Card */}
          {selectedScene && (
            <SceneCard
              scene={selectedScene}
              onEdit={() => openEditSceneEditor(selectedScene)}
              onDelete={() => handleDeleteScene(selectedScene.sceneNumber)}
              onRegenerate={() => handleRegenerateScene(selectedScene.sceneNumber)}
              isSelected={true}
            />
          )}
        </div>

        {/* Right Column: Progress & Export */}
        <div className="space-y-6">
          <ProgressTracker
            sequence={sequence}
            onCancelGeneration={handleCancelGeneration}
          />
          <ExportPanel sequence={sequence} onExport={handleExport} />
        </div>
      </div>

      {/* Scene Editor Modal */}
      {isEditorOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <SceneEditor
              scene={editingScene}
              onSave={handleSceneSave}
              onCancel={closeEditor}
              isLoading={isLoading}
            />
          </div>
        </div>
      )}
    </div>
  );
}
