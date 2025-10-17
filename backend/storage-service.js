// storage-service.js - Google Cloud Storage Integration
// Handles file uploads for frames, videos, and thumbnails

const { Storage } = require('@google-cloud/storage');
const fs = require('fs').promises;
const path = require('path');

// ============================================
// CUSTOM ERROR CLASSES
// ============================================

class StorageError extends Error {
  constructor(message, code = 'STORAGE_ERROR', details = {}) {
    super(message);
    this.name = 'StorageError';
    this.code = code;
    this.details = details;
  }
}

// ============================================
// GOOGLE CLOUD STORAGE SERVICE
// ============================================

class StorageService {
  constructor(options = {}) {
    this.options = {
      bucketName: options.bucketName || process.env.GCS_BUCKET_NAME || 'botspot-veo3',
      projectId: options.projectId || process.env.GCS_PROJECT_ID || process.env.GOOGLE_CLOUD_PROJECT,
      keyFilename: options.keyFilename || process.env.GCS_KEY_FILE,
      makePublic: options.makePublic !== false, // Default true
      ...options
    };

    // Initialize Google Cloud Storage client
    try {
      const storageConfig = {
        projectId: this.options.projectId
      };

      // Use key file if provided, otherwise use application default credentials
      if (this.options.keyFilename) {
        storageConfig.keyFilename = this.options.keyFilename;
      }

      this.storage = new Storage(storageConfig);
      this.bucket = this.storage.bucket(this.options.bucketName);

      console.log('[StorageService] ✅ Initialized');
      console.log(`[StorageService] Project: ${this.options.projectId}`);
      console.log(`[StorageService] Bucket: ${this.options.bucketName}`);
    } catch (error) {
      console.error('[StorageService] ❌ Initialization failed:', error.message);
      throw new StorageError(
        'Failed to initialize Google Cloud Storage',
        'INIT_ERROR',
        { error: error.message }
      );
    }
  }

  /**
   * Upload file to Google Cloud Storage
   * @param {string} localPath - Path to local file
   * @param {string} destinationPath - Path in GCS bucket (e.g., 'frames/scene1.jpg')
   * @param {object} options - Upload options
   * @returns {object} - { url, bucket, file, publicUrl }
   */
  async uploadFile(localPath, destinationPath, options = {}) {
    try {
      console.log(`\n${'='.repeat(80)}`);
      console.log('[STORAGE] 📤 Uploading file to Google Cloud Storage');
      console.log(`${'='.repeat(80)}`);
      console.log(`[STORAGE] Local: ${localPath}`);
      console.log(`[STORAGE] Destination: gs://${this.options.bucketName}/${destinationPath}`);

      // Check if local file exists
      try {
        await fs.access(localPath);
      } catch (error) {
        throw new StorageError(
          `Local file not found: ${localPath}`,
          'FILE_NOT_FOUND'
        );
      }

      // Get file stats
      const stats = await fs.stat(localPath);
      const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
      console.log(`[STORAGE] File Size: ${fileSizeMB}MB`);

      // Detect content type from file extension
      const ext = path.extname(localPath).toLowerCase();
      const contentTypes = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.mp4': 'video/mp4',
        '.mov': 'video/quicktime',
        '.webm': 'video/webm'
      };
      const contentType = contentTypes[ext] || 'application/octet-stream';
      console.log(`[STORAGE] Content-Type: ${contentType}`);

      // Upload to GCS
      console.log('[STORAGE] 🚀 Uploading...');
      const uploadOptions = {
        destination: destinationPath,
        metadata: {
          contentType,
          cacheControl: options.cacheControl || 'public, max-age=31536000', // 1 year
        },
        ...options
      };

      await this.bucket.upload(localPath, uploadOptions);

      const file = this.bucket.file(destinationPath);

      // Make file public if enabled
      let publicUrl = null;
      if (this.options.makePublic) {
        await file.makePublic();
        publicUrl = `https://storage.googleapis.com/${this.options.bucketName}/${destinationPath}`;
        console.log('[STORAGE] 🌐 File made public');
      }

      // Generate signed URL (valid for 7 days) as fallback
      const [signedUrl] = await file.getSignedUrl({
        version: 'v4',
        action: 'read',
        expires: Date.now() + 7 * 24 * 60 * 60 * 1000 // 7 days
      });

      console.log('[STORAGE] ✅ Upload successful!');
      console.log(`[STORAGE] Public URL: ${publicUrl || signedUrl}`);
      console.log(`${'='.repeat(80)}\n`);

      return {
        bucket: this.options.bucketName,
        file: destinationPath,
        publicUrl: publicUrl || signedUrl,
        url: publicUrl || signedUrl, // Alias for convenience
        signedUrl,
        contentType,
        sizeBytes: stats.size,
        localPath
      };

    } catch (error) {
      console.error(`\n${'='.repeat(80)}`);
      console.error('[STORAGE] ❌ Upload failed');
      console.error(`${'='.repeat(80)}`);
      console.error(`[STORAGE] Error: ${error.message}`);
      console.error(`${'='.repeat(80)}\n`);

      throw new StorageError(
        `Failed to upload file: ${error.message}`,
        'UPLOAD_ERROR',
        { localPath, destinationPath, error: error.message }
      );
    }
  }

  /**
   * Upload extracted last frame for Veo 3.1 continuity
   * @param {string} localPath - Path to extracted frame
   * @param {string} sequenceId - Sequence ID
   * @param {number} sceneNumber - Scene number
   * @returns {object} - Upload result with public URL
   */
  async uploadLastFrame(localPath, sequenceId, sceneNumber) {
    const fileName = `${sequenceId}_scene${sceneNumber}_lastframe.jpg`;
    const destinationPath = `frames/${fileName}`;

    console.log(`[STORAGE] 🎬 Uploading last frame for Scene ${sceneNumber}`);

    return await this.uploadFile(localPath, destinationPath, {
      metadata: {
        contentType: 'image/jpeg',
        cacheControl: 'public, max-age=31536000',
        metadata: {
          sequenceId,
          sceneNumber: sceneNumber.toString(),
          type: 'lastFrame',
          uploadedAt: new Date().toISOString()
        }
      }
    });
  }

  /**
   * Upload thumbnail for timeline preview
   * @param {string} localPath - Path to thumbnail
   * @param {string} sequenceId - Sequence ID
   * @param {number} sceneNumber - Scene number
   * @returns {object} - Upload result with public URL
   */
  async uploadThumbnail(localPath, sequenceId, sceneNumber) {
    const fileName = `${sequenceId}_scene${sceneNumber}_thumbnail.jpg`;
    const destinationPath = `thumbnails/${fileName}`;

    console.log(`[STORAGE] 🖼️  Uploading thumbnail for Scene ${sceneNumber}`);

    return await this.uploadFile(localPath, destinationPath, {
      metadata: {
        contentType: 'image/jpeg',
        cacheControl: 'public, max-age=31536000',
        metadata: {
          sequenceId,
          sceneNumber: sceneNumber.toString(),
          type: 'thumbnail',
          uploadedAt: new Date().toISOString()
        }
      }
    });
  }

  /**
   * Upload combined final video
   * @param {string} localPath - Path to combined video
   * @param {string} sequenceId - Sequence ID
   * @returns {object} - Upload result with public URL
   */
  async uploadCombinedVideo(localPath, sequenceId) {
    const fileName = `combined_${sequenceId}.mp4`;
    const destinationPath = `videos/${fileName}`;

    console.log(`[STORAGE] 🎬 Uploading combined video for sequence ${sequenceId}`);

    return await this.uploadFile(localPath, destinationPath, {
      metadata: {
        contentType: 'video/mp4',
        cacheControl: 'public, max-age=31536000',
        metadata: {
          sequenceId,
          type: 'combinedVideo',
          uploadedAt: new Date().toISOString()
        }
      }
    });
  }

  /**
   * Delete file from GCS
   * @param {string} destinationPath - Path in bucket
   */
  async deleteFile(destinationPath) {
    try {
      console.log(`[STORAGE] 🗑️  Deleting: gs://${this.options.bucketName}/${destinationPath}`);

      await this.bucket.file(destinationPath).delete();

      console.log(`[STORAGE] ✅ File deleted: ${destinationPath}`);
      return true;
    } catch (error) {
      console.error(`[STORAGE] ❌ Delete failed:`, error.message);

      // Don't throw error if file doesn't exist (404)
      if (error.code === 404) {
        console.log(`[STORAGE] ⚠️  File not found (already deleted): ${destinationPath}`);
        return false;
      }

      throw new StorageError(
        `Failed to delete file: ${error.message}`,
        'DELETE_ERROR',
        { destinationPath, error: error.message }
      );
    }
  }

  /**
   * Delete all files for a sequence (cleanup)
   * @param {string} sequenceId - Sequence ID
   */
  async deleteSequenceFiles(sequenceId) {
    try {
      console.log(`[STORAGE] 🗑️  Deleting all files for sequence: ${sequenceId}`);

      // List all files matching sequence ID
      const [files] = await this.bucket.getFiles({
        prefix: `frames/${sequenceId}`,
      });

      const [videoFiles] = await this.bucket.getFiles({
        prefix: `videos/combined_${sequenceId}`,
      });

      const [thumbnailFiles] = await this.bucket.getFiles({
        prefix: `thumbnails/${sequenceId}`,
      });

      const allFiles = [...files, ...videoFiles, ...thumbnailFiles];

      console.log(`[STORAGE] Found ${allFiles.length} file(s) to delete`);

      // Delete all files
      await Promise.all(allFiles.map(file => file.delete()));

      console.log(`[STORAGE] ✅ Deleted ${allFiles.length} file(s)`);
      return allFiles.length;

    } catch (error) {
      console.error(`[STORAGE] ❌ Cleanup failed:`, error.message);
      throw new StorageError(
        `Failed to delete sequence files: ${error.message}`,
        'CLEANUP_ERROR',
        { sequenceId, error: error.message }
      );
    }
  }

  /**
   * Get file metadata
   * @param {string} destinationPath - Path in bucket
   */
  async getFileMetadata(destinationPath) {
    try {
      const file = this.bucket.file(destinationPath);
      const [metadata] = await file.getMetadata();

      return {
        name: metadata.name,
        bucket: metadata.bucket,
        contentType: metadata.contentType,
        size: metadata.size,
        updated: metadata.updated,
        created: metadata.timeCreated,
        publicUrl: `https://storage.googleapis.com/${metadata.bucket}/${metadata.name}`
      };
    } catch (error) {
      throw new StorageError(
        `Failed to get file metadata: ${error.message}`,
        'METADATA_ERROR',
        { destinationPath, error: error.message }
      );
    }
  }

  /**
   * Check if bucket exists, create if not
   */
  async ensureBucket() {
    try {
      console.log(`[STORAGE] Checking bucket: ${this.options.bucketName}`);

      const [exists] = await this.bucket.exists();

      if (!exists) {
        console.log(`[STORAGE] Creating bucket: ${this.options.bucketName}`);

        await this.storage.createBucket(this.options.bucketName, {
          location: 'US',
          storageClass: 'STANDARD',
        });

        console.log(`[STORAGE] ✅ Bucket created: ${this.options.bucketName}`);
      } else {
        console.log(`[STORAGE] ✅ Bucket exists: ${this.options.bucketName}`);
      }

      return true;
    } catch (error) {
      console.error(`[STORAGE] ❌ Bucket check/create failed:`, error.message);
      throw new StorageError(
        `Failed to ensure bucket exists: ${error.message}`,
        'BUCKET_ERROR',
        { bucketName: this.options.bucketName, error: error.message }
      );
    }
  }

  /**
   * List files in bucket (with optional prefix)
   * @param {string} prefix - Filter by prefix (e.g., 'frames/')
   */
  async listFiles(prefix = '') {
    try {
      console.log(`[STORAGE] 📋 Listing files with prefix: ${prefix || '(all)'}`);

      const [files] = await this.bucket.getFiles({ prefix });

      console.log(`[STORAGE] Found ${files.length} file(s)`);

      return files.map(file => ({
        name: file.name,
        bucket: file.bucket.name,
        publicUrl: `https://storage.googleapis.com/${file.bucket.name}/${file.name}`,
        metadata: file.metadata
      }));
    } catch (error) {
      throw new StorageError(
        `Failed to list files: ${error.message}`,
        'LIST_ERROR',
        { prefix, error: error.message }
      );
    }
  }

  /**
   * Get storage statistics
   */
  async getStats() {
    try {
      const [files] = await this.bucket.getFiles();

      const totalSize = files.reduce((sum, file) => {
        return sum + parseInt(file.metadata.size || 0);
      }, 0);

      const filesByType = files.reduce((acc, file) => {
        const contentType = file.metadata.contentType || 'unknown';
        acc[contentType] = (acc[contentType] || 0) + 1;
        return acc;
      }, {});

      return {
        bucket: this.options.bucketName,
        totalFiles: files.length,
        totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2),
        filesByType
      };
    } catch (error) {
      throw new StorageError(
        `Failed to get storage stats: ${error.message}`,
        'STATS_ERROR',
        { error: error.message }
      );
    }
  }
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  StorageService,
  StorageError
};
