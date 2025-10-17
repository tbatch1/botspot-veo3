/**
 * Type definitions for Video Sequencer
 * Used across VideoSequencer components for type safety
 */

export type SequenceStatus = 'draft' | 'generating' | 'completed' | 'failed' | 'exporting' | 'exported';
export type SceneStatus = 'pending' | 'generating' | 'completed' | 'failed';
export type VideoModel = 'veo-3.1-generate-preview' | 'veo-3.1-fast-generate-preview';
export type AspectRatio = '16:9' | '9:16' | '1:1';
export type Resolution = '720p' | '1080p';

export interface SceneConfig {
  duration: number;
  aspectRatio: AspectRatio;
  resolution: Resolution;
}

export interface SceneResult {
  videoUrl: string;
  lastFrameUrl?: string;
  thumbnailUrl?: string;
  duration: number;
}

export interface SceneContinuity {
  usesLastFrame: boolean;
  fromSceneNumber?: number;
  lastFrameUrl?: string;
}

export interface SceneCost {
  estimated: number;
  actual: number;
}

export interface Scene {
  sceneNumber: number;
  prompt: string;
  model: VideoModel;
  status: SceneStatus;
  config: SceneConfig;
  result?: SceneResult;
  continuity: SceneContinuity;
  cost?: SceneCost;
  error?: string;
  createdAt: string;
  updatedAt: string;
}

export interface SequenceCost {
  estimated: number;
  actual: number;
}

export interface SequenceExport {
  finalVideoUrl: string;
  combinedDuration: number;
  exportedAt: string;
}

export interface Sequence {
  sequenceId: string;
  userId: string;
  title: string;
  description?: string;
  scenes: Scene[];
  status: SequenceStatus;
  totalDuration: number;
  totalCost: SequenceCost;
  progress: number;
  export?: SequenceExport;
  createdAt: string;
  updatedAt: string;
}

export interface SequenceProgress {
  sequenceId: string;
  status: SequenceStatus;
  progress: number;
  completedScenes: number;
  totalScenes: number;
  currentScene?: number;
  estimatedTimeRemaining?: number;
  error?: string;
}

export interface CreateSequenceRequest {
  userId: string;
  title: string;
  description?: string;
}

export interface AddSceneRequest {
  prompt: string;
  duration?: number;
  aspectRatio?: AspectRatio;
  resolution?: Resolution;
  model?: VideoModel;
}

export interface UpdateSceneRequest {
  prompt?: string;
  duration?: number;
  aspectRatio?: AspectRatio;
  resolution?: Resolution;
  model?: VideoModel;
}

export interface ReorderScenesRequest {
  sceneOrders: Array<{
    sceneNumber: number;
    newPosition: number;
  }>;
}
