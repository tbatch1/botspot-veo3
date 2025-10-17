// video-sequence-service.js - Video Sequence Management Service
// Handles multi-scene video generation with Veo 3.1 continuity features

const { VideoSequence } = require('./models');
const { Veo3Service } = require('./veo3-service');
const { FFmpegProcessor } = require('./ffmpeg-processor');
const { StorageService } = require('./storage-service');
const axios = require('axios');

// ============================================
// CUSTOM ERROR CLASSES
// ============================================

class SequenceError extends Error {
  constructor(message, code = 'SEQUENCE_ERROR', details = {}) {
    super(message);
    this.name = 'SequenceError';
    this.code = code;
    this.details = details;
  }
}

// ============================================
// VIDEO SEQUENCE SERVICE
// ============================================

class VideoSequenceService {
  constructor(veo3Service, options = {}) {
    this.veo3Service = veo3Service;
    this.ffmpegProcessor = new FFmpegProcessor(options.ffmpeg || {});
    this.storageService = new StorageService(options.storage || {});
    this.options = {
      maxScenes: options.maxScenes || 12,
      minScenes: options.minScenes || 2,
      maxRetries: options.maxRetries || 2,
      ...options
    };
  }

  /**
   * Create a new video sequence
   */
  async createSequence(data) {
    const { userId, title, description } = data;

    if (!userId || !title) {
      throw new SequenceError('userId and title are required', 'VALIDATION_ERROR');
    }

    const sequenceId = `seq_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const sequence = new VideoSequence({
      sequenceId,
      userId,
      title,
      description: description || '',
      status: 'draft',
      scenes: [],
      totalDuration: 0,
      totalCost: {
        estimated: 0,
        actual: 0,
        currency: 'USD'
      }
    });

    await sequence.save();

    console.log(`[VideoSequenceService] Created sequence: ${sequenceId}`);
    return sequence;
  }

  /**
   * Get sequence by ID
   */
  async getSequence(sequenceId) {
    const sequence = await VideoSequence.findOne({ sequenceId });
    if (!sequence) {
      throw new SequenceError(`Sequence not found: ${sequenceId}`, 'NOT_FOUND');
    }
    return sequence;
  }

  /**
   * List sequences for a user
   */
  async listSequences(userId, limit = 20) {
    const sequences = await VideoSequence.find({ userId })
      .sort({ createdAt: -1 })
      .limit(limit);
    return sequences;
  }

  /**
   * Update sequence metadata
   */
  async updateSequence(sequenceId, updates) {
    const sequence = await this.getSequence(sequenceId);

    // Only allow updating specific fields
    const allowedUpdates = ['title', 'description', 'status'];
    Object.keys(updates).forEach(key => {
      if (allowedUpdates.includes(key)) {
        sequence[key] = updates[key];
      }
    });

    await sequence.save();
    console.log(`[VideoSequenceService] Updated sequence: ${sequenceId}`);
    return sequence;
  }

  /**
   * Delete sequence
   */
  async deleteSequence(sequenceId) {
    const result = await VideoSequence.deleteOne({ sequenceId });
    if (result.deletedCount === 0) {
      throw new SequenceError(`Sequence not found: ${sequenceId}`, 'NOT_FOUND');
    }
    console.log(`[VideoSequenceService] Deleted sequence: ${sequenceId}`);
    return { success: true };
  }

  /**
   * Add a scene to the sequence
   */
  async addScene(sequenceId, sceneData) {
    const sequence = await this.getSequence(sequenceId);

    // Validate scene count
    if (sequence.scenes.length >= this.options.maxScenes) {
      throw new SequenceError(
        `Maximum ${this.options.maxScenes} scenes allowed`,
        'VALIDATION_ERROR'
      );
    }

    // Validate required fields
    if (!sceneData.prompt) {
      throw new SequenceError('Scene prompt is required', 'VALIDATION_ERROR');
    }

    // Calculate estimated cost
    const duration = sceneData.config?.duration || 8;
    const model = sceneData.model || 'veo-3.1-fast-generate-preview';
    const estimatedCost = parseFloat(this.veo3Service.calculateCost(duration, model));

    // Prepare scene data
    const newSceneData = {
      title: sceneData.title || `Scene ${sequence.scenes.length + 1}`,
      prompt: sceneData.prompt,
      model,
      config: {
        aspectRatio: sceneData.config?.aspectRatio || '16:9',
        resolution: sceneData.config?.resolution || '1080p',
        duration
      },
      status: 'pending',
      cost: {
        estimated: estimatedCost,
        actual: 0
      }
    };

    await sequence.addScene(newSceneData);
    console.log(`[VideoSequenceService] Added scene ${sequence.scenes.length} to ${sequenceId}`);

    return sequence;
  }

  /**
   * Update a scene
   */
  async updateScene(sequenceId, sceneNumber, updates) {
    const sequence = await this.getSequence(sequenceId);

    // Recalculate cost if duration or model changed
    if (updates.config?.duration || updates.model) {
      const duration = updates.config?.duration || sequence.scenes[sceneNumber - 1]?.config?.duration || 8;
      const model = updates.model || sequence.scenes[sceneNumber - 1]?.model;
      updates.cost = {
        ...sequence.scenes[sceneNumber - 1]?.cost,
        estimated: parseFloat(this.veo3Service.calculateCost(duration, model))
      };
    }

    await sequence.updateScene(sceneNumber, updates);
    console.log(`[VideoSequenceService] Updated scene ${sceneNumber} in ${sequenceId}`);

    return sequence;
  }

  /**
   * Delete a scene
   */
  async deleteScene(sequenceId, sceneNumber) {
    const sequence = await this.getSequence(sequenceId);

    await sequence.deleteScene(sceneNumber);
    console.log(`[VideoSequenceService] Deleted scene ${sceneNumber} from ${sequenceId}`);

    return sequence;
  }

  /**
   * Reorder scenes
   */
  async reorderScenes(sequenceId, newOrder) {
    const sequence = await this.getSequence(sequenceId);

    // Validate new order
    if (newOrder.length !== sequence.scenes.length) {
      throw new SequenceError('Invalid scene order', 'VALIDATION_ERROR');
    }

    await sequence.reorderScenes(newOrder);
    console.log(`[VideoSequenceService] Reordered scenes in ${sequenceId}`);

    return sequence;
  }

  /**
   * Extract last frame from a video URL and upload to Google Cloud Storage
   */
  async extractLastFrame(videoUrl, sequenceId, sceneNumber) {
    const fs = require('fs').promises;

    try {
      console.log(`[VideoSequenceService] Extracting last frame from: ${videoUrl}`);

      // Step 1: Extract last frame locally using FFmpeg
      const lastFramePath = await this.ffmpegProcessor.extractLastFrame(videoUrl);

      // Step 2: Upload to Google Cloud Storage
      console.log(`[VideoSequenceService] Uploading frame to Google Cloud Storage...`);
      const uploadResult = await this.storageService.uploadLastFrame(
        lastFramePath,
        sequenceId,
        sceneNumber
      );

      // Step 3: Clean up local file
      try {
        await fs.unlink(lastFramePath);
        console.log(`[VideoSequenceService] Cleaned up local file: ${lastFramePath}`);
      } catch (cleanupError) {
        console.warn(`[VideoSequenceService] Failed to clean up local file:`, cleanupError.message);
      }

      // Step 4: Return Google Cloud Storage public URL (accessible by Veo API)
      console.log(`[VideoSequenceService] ✅ Last frame uploaded: ${uploadResult.publicUrl}`);
      return uploadResult.publicUrl;

    } catch (error) {
      console.error(`[VideoSequenceService] Frame extraction/upload failed:`, error);
      throw new SequenceError(
        'Failed to extract and upload last frame',
        'FRAME_EXTRACTION_ERROR',
        { videoUrl, sequenceId, sceneNumber, error: error.message }
      );
    }
  }

  /**
   * Generate a single scene with continuity
   */
  async generateScene(sequenceId, sceneNumber) {
    const sequence = await this.getSequence(sequenceId);
    const scene = sequence.scenes.find(s => s.sceneNumber === sceneNumber);

    if (!scene) {
      throw new SequenceError(`Scene ${sceneNumber} not found`, 'NOT_FOUND');
    }

    console.log(`\n${'='.repeat(80)}`);
    console.log(`[VideoSequenceService] Generating Scene ${sceneNumber}/${sequence.scenes.length}`);
    console.log(`[VideoSequenceService] Sequence: ${sequenceId}`);
    console.log(`[VideoSequenceService] Prompt: ${scene.prompt.substring(0, 100)}...`);
    console.log(`${'='.repeat(80)}\n`);

    // Mark scene as generating
    await sequence.markSceneAsGenerating(sceneNumber);

    try {
      // Prepare generation params
      const genParams = {
        prompt: scene.prompt,
        model: scene.model,
        aspectRatio: scene.config.aspectRatio,
        resolution: scene.config.resolution,
        duration: scene.config.duration,
        userId: sequence.userId,
        requestId: `${sequenceId}_scene${sceneNumber}`
      };

      // Add continuity from previous scene if applicable
      if (scene.continuity.usesLastFrame && scene.continuity.fromSceneNumber) {
        const previousScene = sequence.scenes.find(
          s => s.sceneNumber === scene.continuity.fromSceneNumber
        );

        if (previousScene && previousScene.status === 'completed' && previousScene.result?.lastFrameUrl) {
          console.log(`[VideoSequenceService] Using continuity from Scene ${previousScene.sceneNumber}`);
          genParams.lastFrame = {
            url: previousScene.result.lastFrameUrl
          };
        } else {
          console.warn(`[VideoSequenceService] Previous scene not ready for continuity, generating without`);
        }
      }

      // Generate video using Veo3Service
      const result = await this.veo3Service.generateVideo(genParams);

      // Extract last frame for next scene
      let lastFrameUrl = null;
      try {
        lastFrameUrl = await this.extractLastFrame(result.video.url, sequenceId, sceneNumber);
      } catch (error) {
        console.warn(`[VideoSequenceService] Could not extract last frame:`, error.message);
        // Continue without last frame - not critical
      }

      // Mark scene as completed
      const sceneResult = {
        videoUrl: result.video.url,
        lastFrameUrl,
        thumbnailUrl: result.video.url, // TODO: Generate actual thumbnail
        format: result.video.format,
        fileSize: 0 // TODO: Get actual file size
      };

      const actualCost = parseFloat(result.metadata.estimatedCost.replace('$', ''));
      await sequence.markSceneAsCompleted(sceneNumber, sceneResult, actualCost);

      console.log(`\n${'='.repeat(80)}`);
      console.log(`[VideoSequenceService] ✅ Scene ${sceneNumber} COMPLETED`);
      console.log(`[VideoSequenceService] Video URL: ${sceneResult.videoUrl}`);
      console.log(`[VideoSequenceService] Cost: $${actualCost.toFixed(2)}`);
      console.log(`${'='.repeat(80)}\n`);

      return await this.getSequence(sequenceId);

    } catch (error) {
      console.error(`\n${'='.repeat(80)}`);
      console.error(`[VideoSequenceService] ❌ Scene ${sceneNumber} FAILED`);
      console.error(`[VideoSequenceService] Error: ${error.message}`);
      console.error(`${'='.repeat(80)}\n`);

      await sequence.markSceneAsFailed(sceneNumber, {
        code: error.code || 'GENERATION_ERROR',
        message: error.message
      });

      throw error;
    }
  }

  /**
   * Generate all scenes in sequence
   */
  async generateAllScenes(sequenceId) {
    const sequence = await this.getSequence(sequenceId);

    if (sequence.scenes.length < this.options.minScenes) {
      throw new SequenceError(
        `Sequence must have at least ${this.options.minScenes} scenes`,
        'VALIDATION_ERROR'
      );
    }

    console.log(`\n${'*'.repeat(80)}`);
    console.log(`[VideoSequenceService] GENERATING ALL SCENES`);
    console.log(`[VideoSequenceService] Sequence: ${sequenceId}`);
    console.log(`[VideoSequenceService] Total Scenes: ${sequence.scenes.length}`);
    console.log(`[VideoSequenceService] Total Duration: ${sequence.totalDuration}s`);
    console.log(`[VideoSequenceService] Estimated Cost: $${sequence.totalCost.estimated.toFixed(2)}`);
    console.log(`${'*'.repeat(80)}\n`);

    // Mark sequence as generating
    sequence.status = 'generating';
    await sequence.save();

    // Generate scenes sequentially (important for continuity)
    const results = [];
    for (let i = 0; i < sequence.scenes.length; i++) {
      const sceneNumber = i + 1;
      const scene = sequence.scenes[i];

      // Skip already completed scenes
      if (scene.status === 'completed') {
        console.log(`[VideoSequenceService] Scene ${sceneNumber} already completed, skipping`);
        results.push({ sceneNumber, status: 'skipped' });
        continue;
      }

      try {
        await this.generateScene(sequenceId, sceneNumber);
        results.push({ sceneNumber, status: 'completed' });
      } catch (error) {
        console.error(`[VideoSequenceService] Failed to generate scene ${sceneNumber}:`, error);
        results.push({ sceneNumber, status: 'failed', error: error.message });
        // Stop on first failure
        break;
      }
    }

    // Get updated sequence
    const updatedSequence = await this.getSequence(sequenceId);

    console.log(`\n${'*'.repeat(80)}`);
    console.log(`[VideoSequenceService] GENERATION COMPLETE`);
    console.log(`[VideoSequenceService] Completed: ${results.filter(r => r.status === 'completed').length}/${sequence.scenes.length}`);
    console.log(`[VideoSequenceService] Actual Cost: $${updatedSequence.totalCost.actual.toFixed(2)}`);
    console.log(`${'*'.repeat(80)}\n`);

    return {
      sequence: updatedSequence,
      results
    };
  }

  /**
   * Get generation status/progress
   */
  async getGenerationStatus(sequenceId) {
    const sequence = await this.getSequence(sequenceId);

    const status = {
      sequenceId: sequence.sequenceId,
      status: sequence.status,
      progress: sequence.progress,
      totalScenes: sequence.scenes.length,
      completedScenes: sequence.scenes.filter(s => s.status === 'completed').length,
      generatingScenes: sequence.scenes.filter(s => s.status === 'generating').length,
      failedScenes: sequence.scenes.filter(s => s.status === 'failed').length,
      pendingScenes: sequence.scenes.filter(s => s.status === 'pending').length,
      totalDuration: sequence.totalDuration,
      estimatedCost: sequence.totalCost.estimated,
      actualCost: sequence.totalCost.actual,
      scenes: sequence.scenes.map(s => ({
        sceneNumber: s.sceneNumber,
        title: s.title,
        status: s.status,
        duration: s.config.duration,
        videoUrl: s.result?.videoUrl,
        error: s.error?.message
      }))
    };

    return status;
  }

  /**
   * Calculate cost for sequence
   */
  calculateSequenceCost(scenes) {
    let totalCost = 0;
    scenes.forEach(scene => {
      const duration = scene.config?.duration || 8;
      const model = scene.model || 'veo-3.1-fast-generate-preview';
      const cost = parseFloat(this.veo3Service.calculateCost(duration, model));
      totalCost += cost;
    });
    return totalCost.toFixed(2);
  }

  /**
   * Validate sequence before generation
   */
  validateSequence(sequence) {
    const errors = [];

    if (sequence.scenes.length < this.options.minScenes) {
      errors.push(`Sequence must have at least ${this.options.minScenes} scenes`);
    }

    if (sequence.scenes.length > this.options.maxScenes) {
      errors.push(`Sequence cannot have more than ${this.options.maxScenes} scenes`);
    }

    sequence.scenes.forEach((scene, idx) => {
      if (!scene.prompt || scene.prompt.length < 10) {
        errors.push(`Scene ${idx + 1}: Prompt too short (min 10 characters)`);
      }
      if (scene.prompt && scene.prompt.length > 2000) {
        errors.push(`Scene ${idx + 1}: Prompt too long (max 2000 characters)`);
      }
    });

    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Export sequence - combine all scenes into final video
   */
  async exportSequence(sequenceId) {
    const sequence = await this.getSequence(sequenceId);

    // Validate all scenes are completed
    const incompleteScenes = sequence.scenes.filter(s => s.status !== 'completed');
    if (incompleteScenes.length > 0) {
      throw new SequenceError(
        `Cannot export: ${incompleteScenes.length} scene(s) not completed`,
        'EXPORT_ERROR',
        { incompleteScenes: incompleteScenes.map(s => s.sceneNumber) }
      );
    }

    console.log(`\n${'*'.repeat(80)}`);
    console.log('[VideoSequenceService] EXPORTING SEQUENCE');
    console.log(`[VideoSequenceService] Sequence: ${sequenceId}`);
    console.log(`[VideoSequenceService] Total Scenes: ${sequence.scenes.length}`);
    console.log(`${'*'.repeat(80)}\n`);

    // Mark sequence as exporting
    await sequence.markAsExporting();

    try {
      // Get all video URLs in order
      const videoUrls = sequence.scenes
        .sort((a, b) => a.sceneNumber - b.sceneNumber)
        .map(s => s.result.videoUrl);

      console.log('[VideoSequenceService] Combining videos:', videoUrls);

      // Combine videos using FFmpeg
      const combinedVideoPath = await this.ffmpegProcessor.combineVideos(videoUrls);

      // Upload combined video to Google Cloud Storage
      console.log('[VideoSequenceService] Uploading combined video to Google Cloud Storage...');
      const uploadResult = await this.storageService.uploadCombinedVideo(combinedVideoPath, sequenceId);

      // Clean up local file
      try {
        const fs = require('fs').promises;
        await fs.unlink(combinedVideoPath);
        console.log(`[VideoSequenceService] Cleaned up local file: ${combinedVideoPath}`);
      } catch (cleanupError) {
        console.warn(`[VideoSequenceService] Failed to clean up local file:`, cleanupError.message);
      }

      // Calculate total duration
      const combinedDuration = sequence.scenes.reduce((sum, s) => sum + s.config.duration, 0);

      // Mark as exported
      await sequence.markAsExported({
        finalVideoUrl: uploadResult.publicUrl,
        combinedDuration
      });

      console.log(`\n${'*'.repeat(80)}`);
      console.log('[VideoSequenceService] ✅ EXPORT COMPLETE');
      console.log(`[VideoSequenceService] Final Video: ${uploadResult.publicUrl}`);
      console.log(`[VideoSequenceService] Total Duration: ${combinedDuration}s`);
      console.log(`${'*'.repeat(80)}\n`);

      return await this.getSequence(sequenceId);

    } catch (error) {
      console.error('[VideoSequenceService] Export failed:', error);

      // Mark sequence as failed
      sequence.status = 'failed';
      await sequence.save();

      throw new SequenceError(
        'Failed to export sequence',
        'EXPORT_ERROR',
        { error: error.message }
      );
    }
  }
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  VideoSequenceService,
  SequenceError
};
