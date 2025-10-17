// video-sequence-service.test.js - Tests for Video Sequence Service

const { VideoSequenceService, SequenceError } = require('../video-sequence-service');
const { VideoSequence } = require('../models');

// Mock dependencies
jest.mock('../models');
jest.mock('../veo3-service');
jest.mock('../ffmpeg-processor');
jest.mock('../storage-service');

describe('VideoSequenceService', () => {
  let sequenceService;
  let mockVeo3Service;
  let mockFFmpegProcessor;
  let mockStorageService;
  let mockSequence;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Mock Veo3Service
    mockVeo3Service = {
      generateVideo: jest.fn().mockResolvedValue({
        video: {
          url: 'https://storage.googleapis.com/test/video.mp4',
          format: 'video/mp4'
        },
        metadata: {
          estimatedCost: '$1.20',
          duration: 8
        }
      })
    };

    // Mock FFmpegProcessor
    mockFFmpegProcessor = {
      extractLastFrame: jest.fn().mockResolvedValue('/local/frame.jpg'),
      combineVideos: jest.fn().mockResolvedValue('/local/combined.mp4')
    };

    // Mock StorageService
    mockStorageService = {
      uploadLastFrame: jest.fn().mockResolvedValue({
        publicUrl: 'https://storage.googleapis.com/test/frame.jpg'
      }),
      uploadCombinedVideo: jest.fn().mockResolvedValue({
        publicUrl: 'https://storage.googleapis.com/test/combined.mp4'
      })
    };

    // Mock VideoSequence model
    mockSequence = {
      sequenceId: 'seq_test123',
      userId: 'test-user',
      title: 'Test Sequence',
      scenes: [],
      status: 'draft',
      save: jest.fn().mockResolvedValue(this),
      addScene: jest.fn().mockImplementation(function(sceneData) {
        const scene = {
          sceneNumber: this.scenes.length + 1,
          ...sceneData,
          status: 'pending',
          continuity: {
            usesLastFrame: this.scenes.length > 0,
            fromSceneNumber: this.scenes.length
          }
        };
        this.scenes.push(scene);
        return this.save();
      }),
      markSceneAsGenerating: jest.fn().mockResolvedValue(undefined),
      markSceneAsCompleted: jest.fn().mockResolvedValue(undefined),
      markSceneAsFailed: jest.fn().mockResolvedValue(undefined),
      markAsExporting: jest.fn().mockResolvedValue(undefined),
      markAsExported: jest.fn().mockResolvedValue(undefined),
      updateTotals: jest.fn()
    };

    VideoSequence.mockImplementation(() => mockSequence);
    VideoSequence.findOne = jest.fn().mockResolvedValue(mockSequence);
    VideoSequence.find = jest.fn().mockResolvedValue([mockSequence]);

    // Create service instance
    sequenceService = new VideoSequenceService(mockVeo3Service, {
      ffmpeg: {},
      storage: {}
    });

    // Inject mocks
    sequenceService.ffmpegProcessor = mockFFmpegProcessor;
    sequenceService.storageService = mockStorageService;
  });

  describe('createSequence()', () => {
    test('should create sequence with valid data', async () => {
      const data = {
        userId: 'test-user',
        title: 'My Sequence',
        description: 'Test description'
      };

      const result = await sequenceService.createSequence(data);

      expect(VideoSequence).toHaveBeenCalledWith(
        expect.objectContaining({
          userId: 'test-user',
          title: 'My Sequence'
        })
      );
      expect(mockSequence.save).toHaveBeenCalled();
    });

    test('should generate unique sequenceId', async () => {
      await sequenceService.createSequence({
        userId: 'user1',
        title: 'Sequence 1'
      });

      expect(VideoSequence).toHaveBeenCalledWith(
        expect.objectContaining({
          sequenceId: expect.stringMatching(/^seq_/)
        })
      );
    });
  });

  describe('getSequence()', () => {
    test('should retrieve sequence by ID', async () => {
      const result = await sequenceService.getSequence('seq_test123');

      expect(VideoSequence.findOne).toHaveBeenCalledWith({
        sequenceId: 'seq_test123'
      });
      expect(result).toEqual(mockSequence);
    });

    test('should throw error if sequence not found', async () => {
      VideoSequence.findOne.mockResolvedValue(null);

      await expect(
        sequenceService.getSequence('nonexistent')
      ).rejects.toThrow(SequenceError);
    });
  });

  describe('addScene()', () => {
    test('should add scene to sequence', async () => {
      const sceneData = {
        prompt: 'Test scene prompt',
        duration: 8,
        model: 'veo-3.1-fast-generate-preview'
      };

      const result = await sequenceService.addScene('seq_test123', sceneData);

      expect(mockSequence.addScene).toHaveBeenCalledWith(
        expect.objectContaining({
          prompt: 'Test scene prompt',
          duration: 8
        })
      );
    });

    test('should enable continuity for scene 2+', async () => {
      mockSequence.scenes = [
        { sceneNumber: 1, status: 'completed' }
      ];

      await sequenceService.addScene('seq_test123', {
        prompt: 'Scene 2',
        duration: 8
      });

      expect(mockSequence.addScene).toHaveBeenCalledWith(
        expect.objectContaining({
          prompt: 'Scene 2'
        })
      );
    });

    test('should enforce max scenes limit', async () => {
      mockSequence.scenes = new Array(12).fill({ sceneNumber: 1 });

      await expect(
        sequenceService.addScene('seq_test123', {
          prompt: 'Scene 13',
          duration: 8
        })
      ).rejects.toThrow(SequenceError);
    });
  });

  describe('generateScene()', () => {
    beforeEach(() => {
      mockSequence.scenes = [
        {
          sceneNumber: 1,
          prompt: 'Scene 1 prompt',
          model: 'veo-3.1-fast-generate-preview',
          config: { duration: 8, aspectRatio: '16:9', resolution: '1080p' },
          status: 'pending',
          continuity: { usesLastFrame: false }
        }
      ];
    });

    test('should generate scene successfully', async () => {
      const result = await sequenceService.generateScene('seq_test123', 1);

      expect(mockSequence.markSceneAsGenerating).toHaveBeenCalledWith(1);
      expect(mockVeo3Service.generateVideo).toHaveBeenCalledWith(
        expect.objectContaining({
          prompt: 'Scene 1 prompt',
          model: 'veo-3.1-fast-generate-preview',
          duration: 8
        })
      );
      expect(mockSequence.markSceneAsCompleted).toHaveBeenCalled();
    });

    test('should extract and upload last frame', async () => {
      await sequenceService.generateScene('seq_test123', 1);

      expect(mockFFmpegProcessor.extractLastFrame).toHaveBeenCalledWith(
        'https://storage.googleapis.com/test/video.mp4'
      );
      expect(mockStorageService.uploadLastFrame).toHaveBeenCalledWith(
        '/local/frame.jpg',
        'seq_test123',
        1
      );
    });

    test('should use continuity from previous scene', async () => {
      mockSequence.scenes = [
        {
          sceneNumber: 1,
          status: 'completed',
          result: {
            lastFrameUrl: 'https://storage.googleapis.com/test/frame1.jpg'
          }
        },
        {
          sceneNumber: 2,
          prompt: 'Scene 2 prompt',
          model: 'veo-3.1-fast-generate-preview',
          config: { duration: 8, aspectRatio: '16:9', resolution: '1080p' },
          status: 'pending',
          continuity: {
            usesLastFrame: true,
            fromSceneNumber: 1
          }
        }
      ];

      await sequenceService.generateScene('seq_test123', 2);

      expect(mockVeo3Service.generateVideo).toHaveBeenCalledWith(
        expect.objectContaining({
          lastFrame: {
            url: 'https://storage.googleapis.com/test/frame1.jpg'
          }
        })
      );
    });

    test('should mark scene as failed on error', async () => {
      mockVeo3Service.generateVideo.mockRejectedValue(new Error('Generation failed'));

      await expect(
        sequenceService.generateScene('seq_test123', 1)
      ).rejects.toThrow();

      expect(mockSequence.markSceneAsFailed).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          message: 'Generation failed'
        })
      );
    });
  });

  describe('generateAllScenes()', () => {
    beforeEach(() => {
      mockSequence.scenes = [
        {
          sceneNumber: 1,
          prompt: 'Scene 1',
          model: 'veo-3.1-fast-generate-preview',
          config: { duration: 8, aspectRatio: '16:9', resolution: '1080p' },
          status: 'pending',
          continuity: { usesLastFrame: false }
        },
        {
          sceneNumber: 2,
          prompt: 'Scene 2',
          model: 'veo-3.1-fast-generate-preview',
          config: { duration: 8, aspectRatio: '16:9', resolution: '1080p' },
          status: 'pending',
          continuity: { usesLastFrame: true, fromSceneNumber: 1 }
        }
      ];
    });

    test('should generate all scenes sequentially', async () => {
      // Make generateScene work properly
      sequenceService.generateScene = jest.fn().mockResolvedValue(mockSequence);

      const result = await sequenceService.generateAllScenes('seq_test123');

      expect(sequenceService.generateScene).toHaveBeenCalledTimes(2);
      expect(sequenceService.generateScene).toHaveBeenNthCalledWith(1, 'seq_test123', 1);
      expect(sequenceService.generateScene).toHaveBeenNthCalledWith(2, 'seq_test123', 2);
    });

    test('should stop on first failure', async () => {
      sequenceService.generateScene = jest.fn()
        .mockResolvedValueOnce(mockSequence)
        .mockRejectedValueOnce(new Error('Scene 2 failed'));

      const result = await sequenceService.generateAllScenes('seq_test123');

      expect(sequenceService.generateScene).toHaveBeenCalledTimes(2);
      expect(result.results).toHaveLength(2);
      expect(result.results[1].status).toBe('failed');
    });
  });

  describe('exportSequence()', () => {
    beforeEach(() => {
      mockSequence.scenes = [
        {
          sceneNumber: 1,
          status: 'completed',
          result: { videoUrl: 'https://storage.googleapis.com/test/video1.mp4' },
          config: { duration: 8 }
        },
        {
          sceneNumber: 2,
          status: 'completed',
          result: { videoUrl: 'https://storage.googleapis.com/test/video2.mp4' },
          config: { duration: 8 }
        }
      ];
    });

    test('should export sequence successfully', async () => {
      const result = await sequenceService.exportSequence('seq_test123');

      expect(mockSequence.markAsExporting).toHaveBeenCalled();
      expect(mockFFmpegProcessor.combineVideos).toHaveBeenCalledWith([
        'https://storage.googleapis.com/test/video1.mp4',
        'https://storage.googleapis.com/test/video2.mp4'
      ]);
      expect(mockStorageService.uploadCombinedVideo).toHaveBeenCalledWith(
        '/local/combined.mp4',
        'seq_test123'
      );
      expect(mockSequence.markAsExported).toHaveBeenCalledWith(
        expect.objectContaining({
          finalVideoUrl: 'https://storage.googleapis.com/test/combined.mp4',
          combinedDuration: 16
        })
      );
    });

    test('should throw error if scenes incomplete', async () => {
      mockSequence.scenes[1].status = 'pending';

      await expect(
        sequenceService.exportSequence('seq_test123')
      ).rejects.toThrow(SequenceError);

      expect(mockFFmpegProcessor.combineVideos).not.toHaveBeenCalled();
    });

    test('should handle export errors', async () => {
      mockFFmpegProcessor.combineVideos.mockRejectedValue(new Error('Combine failed'));

      await expect(
        sequenceService.exportSequence('seq_test123')
      ).rejects.toThrow(SequenceError);

      expect(mockSequence.status).toBe('failed');
    });
  });

  describe('calculateSequenceCost()', () => {
    test('should calculate total estimated cost', () => {
      mockSequence.scenes = [
        { config: { duration: 8 }, model: 'veo-3.1-fast-generate-preview' },
        { config: { duration: 8 }, model: 'veo-3.1-fast-generate-preview' }
      ];

      const cost = sequenceService.calculateSequenceCost(mockSequence);

      // Veo 3.1 Fast: $0.15/sec × 8sec = $1.20 per scene
      // 2 scenes = $2.40
      expect(parseFloat(cost)).toBeCloseTo(2.40, 2);
    });

    test('should handle different models', () => {
      mockSequence.scenes = [
        { config: { duration: 8 }, model: 'veo-3.1-generate-preview' },
        { config: { duration: 8 }, model: 'veo-3.1-fast-generate-preview' }
      ];

      const cost = sequenceService.calculateSequenceCost(mockSequence);

      // Veo 3.1: $0.40/sec × 8sec = $3.20
      // Veo 3.1 Fast: $0.15/sec × 8sec = $1.20
      // Total = $4.40
      expect(parseFloat(cost)).toBeCloseTo(4.40, 2);
    });
  });

  describe('getGenerationStatus()', () => {
    test('should return progress status', async () => {
      mockSequence.scenes = [
        { sceneNumber: 1, status: 'completed' },
        { sceneNumber: 2, status: 'generating' },
        { sceneNumber: 3, status: 'pending' },
        { sceneNumber: 4, status: 'pending' }
      ];
      mockSequence.progress = 25; // 1/4 = 25%

      const status = await sequenceService.getGenerationStatus('seq_test123');

      expect(status).toMatchObject({
        sequenceId: 'seq_test123',
        status: 'generating',
        progress: 25,
        totalScenes: 4,
        completedScenes: 1,
        currentScene: 2
      });
    });
  });
});
