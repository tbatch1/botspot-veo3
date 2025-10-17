// storage-service.test.js - Tests for Google Cloud Storage Service

const { StorageService, StorageError } = require('../storage-service');
const { Storage } = require('@google-cloud/storage');

// Mock @google-cloud/storage
jest.mock('@google-cloud/storage');

describe('StorageService', () => {
  let storageService;
  let mockBucket;
  let mockFile;
  let mockStorage;

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();

    // Mock file operations
    mockFile = {
      makePublic: jest.fn().mockResolvedValue(undefined),
      getSignedUrl: jest.fn().mockResolvedValue(['https://signed-url.com/file.jpg']),
      delete: jest.fn().mockResolvedValue(undefined),
      getMetadata: jest.fn().mockResolvedValue([{
        name: 'test-file.jpg',
        bucket: 'test-bucket',
        contentType: 'image/jpeg',
        size: 1024,
        updated: '2025-01-01',
        timeCreated: '2025-01-01'
      }])
    };

    // Mock bucket operations
    mockBucket = {
      upload: jest.fn().mockResolvedValue(undefined),
      file: jest.fn().mockReturnValue(mockFile),
      exists: jest.fn().mockResolvedValue([true]),
      getFiles: jest.fn().mockResolvedValue([[]])
    };

    // Mock Storage client
    mockStorage = {
      bucket: jest.fn().mockReturnValue(mockBucket),
      createBucket: jest.fn().mockResolvedValue(undefined)
    };

    Storage.mockImplementation(() => mockStorage);

    // Create StorageService instance
    storageService = new StorageService({
      projectId: 'test-project',
      bucketName: 'test-bucket'
    });
  });

  describe('Initialization', () => {
    test('should initialize with valid config', () => {
      expect(storageService).toBeDefined();
      expect(storageService.options.bucketName).toBe('test-bucket');
      expect(storageService.options.projectId).toBe('test-project');
    });

    test('should use default bucket name from env', () => {
      process.env.GCS_BUCKET_NAME = 'env-bucket';
      const service = new StorageService();
      expect(service.options.bucketName).toBe('env-bucket');
    });
  });

  describe('uploadFile()', () => {
    beforeEach(() => {
      // Mock fs module
      const fs = require('fs');
      fs.promises = {
        access: jest.fn().mockResolvedValue(undefined),
        stat: jest.fn().mockResolvedValue({ size: 1024 * 1024 }) // 1MB
      };
    });

    test('should upload file successfully', async () => {
      const result = await storageService.uploadFile(
        '/local/path/test.jpg',
        'frames/test.jpg'
      );

      expect(mockBucket.upload).toHaveBeenCalledWith(
        '/local/path/test.jpg',
        expect.objectContaining({
          destination: 'frames/test.jpg'
        })
      );

      expect(mockFile.makePublic).toHaveBeenCalled();
      expect(result).toMatchObject({
        bucket: 'test-bucket',
        file: 'frames/test.jpg',
        publicUrl: expect.stringContaining('storage.googleapis.com')
      });
    });

    test('should throw error if local file not found', async () => {
      const fs = require('fs');
      fs.promises.access.mockRejectedValue(new Error('File not found'));

      await expect(
        storageService.uploadFile('/nonexistent/file.jpg', 'frames/test.jpg')
      ).rejects.toThrow(StorageError);
    });

    test('should handle upload errors', async () => {
      mockBucket.upload.mockRejectedValue(new Error('Upload failed'));

      await expect(
        storageService.uploadFile('/local/test.jpg', 'frames/test.jpg')
      ).rejects.toThrow(StorageError);
    });
  });

  describe('uploadLastFrame()', () => {
    test('should upload last frame with correct path', async () => {
      const fs = require('fs');
      fs.promises = {
        access: jest.fn().mockResolvedValue(undefined),
        stat: jest.fn().mockResolvedValue({ size: 500000 })
      };

      const result = await storageService.uploadLastFrame(
        '/local/frame.jpg',
        'seq_abc123',
        2
      );

      expect(mockBucket.upload).toHaveBeenCalledWith(
        '/local/frame.jpg',
        expect.objectContaining({
          destination: 'frames/seq_abc123_scene2_lastframe.jpg'
        })
      );

      expect(result.file).toBe('frames/seq_abc123_scene2_lastframe.jpg');
    });

    test('should include metadata for last frame', async () => {
      const fs = require('fs');
      fs.promises = {
        access: jest.fn().mockResolvedValue(undefined),
        stat: jest.fn().mockResolvedValue({ size: 500000 })
      };

      await storageService.uploadLastFrame('/local/frame.jpg', 'seq_abc', 1);

      expect(mockBucket.upload).toHaveBeenCalledWith(
        '/local/frame.jpg',
        expect.objectContaining({
          metadata: expect.objectContaining({
            metadata: expect.objectContaining({
              sequenceId: 'seq_abc',
              sceneNumber: '1',
              type: 'lastFrame'
            })
          })
        })
      );
    });
  });

  describe('uploadCombinedVideo()', () => {
    test('should upload combined video with correct path', async () => {
      const fs = require('fs');
      fs.promises = {
        access: jest.fn().mockResolvedValue(undefined),
        stat: jest.fn().mockResolvedValue({ size: 50000000 }) // 50MB
      };

      const result = await storageService.uploadCombinedVideo(
        '/local/combined.mp4',
        'seq_xyz789'
      );

      expect(mockBucket.upload).toHaveBeenCalledWith(
        '/local/combined.mp4',
        expect.objectContaining({
          destination: 'videos/combined_seq_xyz789.mp4'
        })
      );

      expect(result.file).toBe('videos/combined_seq_xyz789.mp4');
    });
  });

  describe('deleteFile()', () => {
    test('should delete file successfully', async () => {
      const result = await storageService.deleteFile('frames/test.jpg');

      expect(mockBucket.file).toHaveBeenCalledWith('frames/test.jpg');
      expect(mockFile.delete).toHaveBeenCalled();
      expect(result).toBe(true);
    });

    test('should handle 404 errors gracefully', async () => {
      const error = new Error('Not found');
      error.code = 404;
      mockFile.delete.mockRejectedValue(error);

      const result = await storageService.deleteFile('frames/nonexistent.jpg');

      expect(result).toBe(false);
    });

    test('should throw error for other delete failures', async () => {
      const error = new Error('Permission denied');
      error.code = 403;
      mockFile.delete.mockRejectedValue(error);

      await expect(
        storageService.deleteFile('frames/test.jpg')
      ).rejects.toThrow(StorageError);
    });
  });

  describe('deleteSequenceFiles()', () => {
    test('should delete all files for a sequence', async () => {
      const mockFiles = [
        { name: 'frames/seq_abc_scene1.jpg', delete: jest.fn().mockResolvedValue(undefined) },
        { name: 'frames/seq_abc_scene2.jpg', delete: jest.fn().mockResolvedValue(undefined) },
        { name: 'videos/combined_seq_abc.mp4', delete: jest.fn().mockResolvedValue(undefined) }
      ];

      mockBucket.getFiles
        .mockResolvedValueOnce([mockFiles.slice(0, 2)]) // frames
        .mockResolvedValueOnce([[mockFiles[2]]]) // videos
        .mockResolvedValueOnce([[]]); // thumbnails

      const count = await storageService.deleteSequenceFiles('seq_abc');

      expect(mockBucket.getFiles).toHaveBeenCalledTimes(3);
      expect(mockFiles[0].delete).toHaveBeenCalled();
      expect(mockFiles[1].delete).toHaveBeenCalled();
      expect(mockFiles[2].delete).toHaveBeenCalled();
      expect(count).toBe(3);
    });

    test('should handle cleanup errors', async () => {
      mockBucket.getFiles.mockRejectedValue(new Error('List failed'));

      await expect(
        storageService.deleteSequenceFiles('seq_abc')
      ).rejects.toThrow(StorageError);
    });
  });

  describe('getFileMetadata()', () => {
    test('should return file metadata', async () => {
      const metadata = await storageService.getFileMetadata('frames/test.jpg');

      expect(mockBucket.file).toHaveBeenCalledWith('frames/test.jpg');
      expect(mockFile.getMetadata).toHaveBeenCalled();
      expect(metadata).toMatchObject({
        name: 'test-file.jpg',
        bucket: 'test-bucket',
        contentType: 'image/jpeg',
        size: 1024
      });
    });

    test('should throw error if metadata fetch fails', async () => {
      mockFile.getMetadata.mockRejectedValue(new Error('Not found'));

      await expect(
        storageService.getFileMetadata('frames/test.jpg')
      ).rejects.toThrow(StorageError);
    });
  });

  describe('ensureBucket()', () => {
    test('should not create bucket if it exists', async () => {
      mockBucket.exists.mockResolvedValue([true]);

      const result = await storageService.ensureBucket();

      expect(mockBucket.exists).toHaveBeenCalled();
      expect(mockStorage.createBucket).not.toHaveBeenCalled();
      expect(result).toBe(true);
    });

    test('should create bucket if it does not exist', async () => {
      mockBucket.exists.mockResolvedValue([false]);

      const result = await storageService.ensureBucket();

      expect(mockBucket.exists).toHaveBeenCalled();
      expect(mockStorage.createBucket).toHaveBeenCalledWith(
        'test-bucket',
        expect.objectContaining({
          location: 'US',
          storageClass: 'STANDARD'
        })
      );
      expect(result).toBe(true);
    });

    test('should throw error if bucket creation fails', async () => {
      mockBucket.exists.mockResolvedValue([false]);
      mockStorage.createBucket.mockRejectedValue(new Error('Permission denied'));

      await expect(
        storageService.ensureBucket()
      ).rejects.toThrow(StorageError);
    });
  });

  describe('listFiles()', () => {
    test('should list all files', async () => {
      const mockFiles = [
        { name: 'frames/file1.jpg', bucket: { name: 'test-bucket' }, metadata: {} },
        { name: 'frames/file2.jpg', bucket: { name: 'test-bucket' }, metadata: {} }
      ];

      mockBucket.getFiles.mockResolvedValue([mockFiles]);

      const files = await storageService.listFiles();

      expect(mockBucket.getFiles).toHaveBeenCalledWith({ prefix: '' });
      expect(files).toHaveLength(2);
      expect(files[0]).toMatchObject({
        name: 'frames/file1.jpg',
        bucket: 'test-bucket'
      });
    });

    test('should list files with prefix filter', async () => {
      mockBucket.getFiles.mockResolvedValue([[]]);

      await storageService.listFiles('frames/');

      expect(mockBucket.getFiles).toHaveBeenCalledWith({ prefix: 'frames/' });
    });
  });

  describe('getStats()', () => {
    test('should calculate storage statistics', async () => {
      const mockFiles = [
        { metadata: { contentType: 'image/jpeg', size: '1024' } },
        { metadata: { contentType: 'image/jpeg', size: '2048' } },
        { metadata: { contentType: 'video/mp4', size: '10240' } }
      ];

      mockBucket.getFiles.mockResolvedValue([mockFiles]);

      const stats = await storageService.getStats();

      expect(stats).toMatchObject({
        bucket: 'test-bucket',
        totalFiles: 3,
        totalSizeMB: expect.any(String),
        filesByType: {
          'image/jpeg': 2,
          'video/mp4': 1
        }
      });
    });
  });
});
