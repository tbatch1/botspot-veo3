// ffmpeg-processor.js - Video Processing Service using FFmpeg
// Handles video frame extraction, thumbnails, and video concatenation

const ffmpeg = require('fluent-ffmpeg');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { promisify } = require('util');

const mkdir = promisify(fs.mkdir);
const writeFile = promisify(fs.writeFile);
const unlink = promisify(fs.unlink);
const access = promisify(fs.access);

// ============================================
// CUSTOM ERROR CLASSES
// ============================================

class FFmpegError extends Error {
  constructor(message, code = 'FFMPEG_ERROR', details = {}) {
    super(message);
    this.name = 'FFmpegError';
    this.code = code;
    this.details = details;
  }
}

// ============================================
// FFMPEG VIDEO PROCESSOR
// ============================================

class FFmpegProcessor {
  constructor(options = {}) {
    this.options = {
      tempDir: options.tempDir || path.join(__dirname, '../temp'),
      outputDir: options.outputDir || path.join(__dirname, '../output'),
      maxFileSizeMB: options.maxFileSizeMB || 100,
      timeout: options.timeout || 120000, // 2 minutes
      ...options
    };

    // Ensure directories exist
    this.ensureDirectories();
  }

  /**
   * Ensure temp and output directories exist
   */
  async ensureDirectories() {
    try {
      await mkdir(this.options.tempDir, { recursive: true });
      await mkdir(this.options.outputDir, { recursive: true });
      console.log('[FFmpegProcessor] Directories initialized:', {
        temp: this.options.tempDir,
        output: this.options.outputDir
      });
    } catch (error) {
      console.error('[FFmpegProcessor] Failed to create directories:', error);
    }
  }

  /**
   * Download video from URL to local temp file
   */
  async downloadVideo(videoUrl, outputPath) {
    try {
      console.log(`[FFmpegProcessor] Downloading video from: ${videoUrl}`);

      const response = await axios({
        method: 'GET',
        url: videoUrl,
        responseType: 'stream',
        timeout: this.options.timeout
      });

      // Check file size
      const contentLength = parseInt(response.headers['content-length'] || '0');
      const fileSizeMB = contentLength / (1024 * 1024);

      if (fileSizeMB > this.options.maxFileSizeMB) {
        throw new FFmpegError(
          `Video file too large: ${fileSizeMB.toFixed(2)}MB (max ${this.options.maxFileSizeMB}MB)`,
          'FILE_TOO_LARGE'
        );
      }

      // Stream to file
      const writer = fs.createWriteStream(outputPath);
      response.data.pipe(writer);

      return new Promise((resolve, reject) => {
        writer.on('finish', () => {
          console.log(`[FFmpegProcessor] Downloaded to: ${outputPath} (${fileSizeMB.toFixed(2)}MB)`);
          resolve(outputPath);
        });
        writer.on('error', reject);
      });

    } catch (error) {
      console.error('[FFmpegProcessor] Download failed:', error.message);
      throw new FFmpegError(
        'Failed to download video',
        'DOWNLOAD_ERROR',
        { videoUrl, error: error.message }
      );
    }
  }

  /**
   * Get video metadata (duration, resolution, format)
   */
  async getVideoMetadata(videoPath) {
    return new Promise((resolve, reject) => {
      ffmpeg.ffprobe(videoPath, (err, metadata) => {
        if (err) {
          reject(new FFmpegError(
            'Failed to read video metadata',
            'METADATA_ERROR',
            { error: err.message }
          ));
        } else {
          const videoStream = metadata.streams.find(s => s.codec_type === 'video');
          resolve({
            duration: metadata.format.duration,
            width: videoStream?.width,
            height: videoStream?.height,
            fps: eval(videoStream?.r_frame_rate || '30'),
            format: metadata.format.format_name,
            size: metadata.format.size,
            bitrate: metadata.format.bit_rate
          });
        }
      });
    });
  }

  /**
   * Extract last frame from video as image
   * Critical for Veo 3.1 continuity feature
   */
  async extractLastFrame(videoUrl, outputPath = null) {
    let tempVideoPath = null;

    try {
      // Generate temp paths
      const videoId = `video_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      tempVideoPath = path.join(this.options.tempDir, `${videoId}.mp4`);

      if (!outputPath) {
        outputPath = path.join(this.options.outputDir, `${videoId}_lastframe.jpg`);
      }

      console.log(`\n${'='.repeat(80)}`);
      console.log('[FFmpegProcessor] EXTRACTING LAST FRAME');
      console.log(`[FFmpegProcessor] Video URL: ${videoUrl}`);
      console.log(`[FFmpegProcessor] Output: ${outputPath}`);
      console.log(`${'='.repeat(80)}\n`);

      // Download video
      await this.downloadVideo(videoUrl, tempVideoPath);

      // Get video metadata to find duration
      const metadata = await this.getVideoMetadata(tempVideoPath);
      console.log('[FFmpegProcessor] Video metadata:', {
        duration: `${metadata.duration}s`,
        resolution: `${metadata.width}x${metadata.height}`,
        format: metadata.format
      });

      // Extract last frame (0.1s before end to avoid black frames)
      const seekTime = Math.max(0, metadata.duration - 0.1);

      return new Promise((resolve, reject) => {
        ffmpeg(tempVideoPath)
          .seekInput(seekTime)
          .outputOptions([
            '-vframes 1', // Extract single frame
            '-q:v 2',     // High quality JPEG
            '-f image2'   // Image format
          ])
          .output(outputPath)
          .on('start', (commandLine) => {
            console.log('[FFmpegProcessor] FFmpeg command:', commandLine);
          })
          .on('progress', (progress) => {
            console.log(`[FFmpegProcessor] Processing: ${progress.percent?.toFixed(1)}%`);
          })
          .on('end', async () => {
            console.log(`\n${'='.repeat(80)}`);
            console.log('[FFmpegProcessor] ✅ LAST FRAME EXTRACTED');
            console.log(`[FFmpegProcessor] Output: ${outputPath}`);
            console.log(`${'='.repeat(80)}\n`);

            // Clean up temp video
            try {
              await unlink(tempVideoPath);
              console.log('[FFmpegProcessor] Cleaned up temp video');
            } catch (err) {
              console.warn('[FFmpegProcessor] Failed to clean up temp file:', err.message);
            }

            resolve(outputPath);
          })
          .on('error', (err) => {
            console.error(`\n${'='.repeat(80)}`);
            console.error('[FFmpegProcessor] ❌ EXTRACTION FAILED');
            console.error(`[FFmpegProcessor] Error: ${err.message}`);
            console.error(`${'='.repeat(80)}\n`);

            reject(new FFmpegError(
              'Failed to extract last frame',
              'FRAME_EXTRACTION_ERROR',
              { videoUrl, error: err.message }
            ));
          })
          .run();
      });

    } catch (error) {
      // Clean up on error
      if (tempVideoPath) {
        try {
          await unlink(tempVideoPath);
        } catch (err) {
          // Ignore cleanup errors
        }
      }
      throw error;
    }
  }

  /**
   * Generate thumbnail from video (middle frame)
   */
  async generateThumbnail(videoUrl, outputPath = null, timePosition = '50%') {
    let tempVideoPath = null;

    try {
      // Generate temp paths
      const videoId = `video_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      tempVideoPath = path.join(this.options.tempDir, `${videoId}.mp4`);

      if (!outputPath) {
        outputPath = path.join(this.options.outputDir, `${videoId}_thumbnail.jpg`);
      }

      console.log('[FFmpegProcessor] Generating thumbnail:', { videoUrl, outputPath });

      // Download video
      await this.downloadVideo(videoUrl, tempVideoPath);

      // Get video metadata
      const metadata = await this.getVideoMetadata(tempVideoPath);

      // Calculate seek time
      let seekTime;
      if (typeof timePosition === 'string' && timePosition.endsWith('%')) {
        const percentage = parseInt(timePosition) / 100;
        seekTime = metadata.duration * percentage;
      } else {
        seekTime = parseFloat(timePosition);
      }

      return new Promise((resolve, reject) => {
        ffmpeg(tempVideoPath)
          .seekInput(seekTime)
          .outputOptions([
            '-vframes 1',
            '-q:v 2',
            '-vf scale=640:-1', // Scale to 640px width, maintain aspect ratio
            '-f image2'
          ])
          .output(outputPath)
          .on('end', async () => {
            console.log('[FFmpegProcessor] ✅ Thumbnail generated:', outputPath);

            // Clean up temp video
            try {
              await unlink(tempVideoPath);
            } catch (err) {
              console.warn('[FFmpegProcessor] Failed to clean up temp file:', err.message);
            }

            resolve(outputPath);
          })
          .on('error', (err) => {
            reject(new FFmpegError(
              'Failed to generate thumbnail',
              'THUMBNAIL_ERROR',
              { videoUrl, error: err.message }
            ));
          })
          .run();
      });

    } catch (error) {
      // Clean up on error
      if (tempVideoPath) {
        try {
          await unlink(tempVideoPath);
        } catch (err) {
          // Ignore cleanup errors
        }
      }
      throw error;
    }
  }

  /**
   * Combine multiple videos into one final video
   * Critical for sequence export feature
   */
  async combineVideos(videoUrls, outputPath = null) {
    const tempVideoPaths = [];
    const concatListPath = path.join(this.options.tempDir, `concat_${Date.now()}.txt`);

    try {
      if (!videoUrls || videoUrls.length === 0) {
        throw new FFmpegError('No videos provided for combination', 'VALIDATION_ERROR');
      }

      if (!outputPath) {
        const videoId = `combined_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        outputPath = path.join(this.options.outputDir, `${videoId}.mp4`);
      }

      console.log(`\n${'='.repeat(80)}`);
      console.log('[FFmpegProcessor] COMBINING VIDEOS');
      console.log(`[FFmpegProcessor] Total scenes: ${videoUrls.length}`);
      console.log(`[FFmpegProcessor] Output: ${outputPath}`);
      console.log(`${'='.repeat(80)}\n`);

      // Download all videos
      for (let i = 0; i < videoUrls.length; i++) {
        const videoId = `scene_${i + 1}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const tempPath = path.join(this.options.tempDir, `${videoId}.mp4`);

        console.log(`[FFmpegProcessor] Downloading scene ${i + 1}/${videoUrls.length}...`);
        await this.downloadVideo(videoUrls[i], tempPath);
        tempVideoPaths.push(tempPath);
      }

      // Create concat list file
      const concatList = tempVideoPaths
        .map(p => `file '${p.replace(/\\/g, '/')}'`)
        .join('\n');

      await writeFile(concatListPath, concatList);
      console.log('[FFmpegProcessor] Concat list created:', concatListPath);

      // Combine videos using concat demuxer
      return new Promise((resolve, reject) => {
        ffmpeg()
          .input(concatListPath)
          .inputOptions(['-f concat', '-safe 0'])
          .outputOptions([
            '-c copy', // Copy streams without re-encoding (fast)
            '-movflags +faststart' // Enable streaming
          ])
          .output(outputPath)
          .on('start', (commandLine) => {
            console.log('[FFmpegProcessor] FFmpeg command:', commandLine);
          })
          .on('progress', (progress) => {
            console.log(`[FFmpegProcessor] Combining: ${progress.percent?.toFixed(1)}%`);
          })
          .on('end', async () => {
            console.log(`\n${'='.repeat(80)}`);
            console.log('[FFmpegProcessor] ✅ VIDEOS COMBINED');
            console.log(`[FFmpegProcessor] Output: ${outputPath}`);
            console.log(`${'='.repeat(80)}\n`);

            // Clean up temp files
            try {
              for (const tempPath of tempVideoPaths) {
                await unlink(tempPath);
              }
              await unlink(concatListPath);
              console.log('[FFmpegProcessor] Cleaned up temp files');
            } catch (err) {
              console.warn('[FFmpegProcessor] Failed to clean up temp files:', err.message);
            }

            resolve(outputPath);
          })
          .on('error', (err) => {
            console.error(`\n${'='.repeat(80)}`);
            console.error('[FFmpegProcessor] ❌ COMBINATION FAILED');
            console.error(`[FFmpegProcessor] Error: ${err.message}`);
            console.error(`${'='.repeat(80)}\n`);

            reject(new FFmpegError(
              'Failed to combine videos',
              'COMBINATION_ERROR',
              { videoCount: videoUrls.length, error: err.message }
            ));
          })
          .run();
      });

    } catch (error) {
      // Clean up temp files on error
      try {
        for (const tempPath of tempVideoPaths) {
          await unlink(tempPath);
        }
        if (await access(concatListPath).then(() => true).catch(() => false)) {
          await unlink(concatListPath);
        }
      } catch (err) {
        // Ignore cleanup errors
      }
      throw error;
    }
  }

  /**
   * Validate video file (check if accessible and valid format)
   */
  async validateVideo(videoUrl) {
    let tempVideoPath = null;

    try {
      console.log('[FFmpegProcessor] Validating video:', videoUrl);

      // Generate temp path
      const videoId = `validate_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      tempVideoPath = path.join(this.options.tempDir, `${videoId}.mp4`);

      // Download video
      await this.downloadVideo(videoUrl, tempVideoPath);

      // Get metadata to validate format
      const metadata = await this.getVideoMetadata(tempVideoPath);

      // Clean up temp file
      await unlink(tempVideoPath);

      console.log('[FFmpegProcessor] ✅ Video is valid:', {
        duration: `${metadata.duration}s`,
        resolution: `${metadata.width}x${metadata.height}`,
        format: metadata.format
      });

      return {
        valid: true,
        metadata
      };

    } catch (error) {
      // Clean up temp file on error
      if (tempVideoPath) {
        try {
          await unlink(tempVideoPath);
        } catch (err) {
          // Ignore cleanup errors
        }
      }

      console.error('[FFmpegProcessor] ❌ Video validation failed:', error.message);

      return {
        valid: false,
        error: error.message
      };
    }
  }

  /**
   * Clean up old temporary files
   */
  async cleanupTempFiles(maxAgeHours = 24) {
    try {
      const files = fs.readdirSync(this.options.tempDir);
      const now = Date.now();
      const maxAgeMs = maxAgeHours * 60 * 60 * 1000;
      let deletedCount = 0;

      for (const file of files) {
        const filePath = path.join(this.options.tempDir, file);
        const stats = fs.statSync(filePath);
        const age = now - stats.mtimeMs;

        if (age > maxAgeMs) {
          await unlink(filePath);
          deletedCount++;
        }
      }

      console.log(`[FFmpegProcessor] Cleaned up ${deletedCount} old temp files`);
      return deletedCount;

    } catch (error) {
      console.error('[FFmpegProcessor] Cleanup failed:', error.message);
      return 0;
    }
  }
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  FFmpegProcessor,
  FFmpegError
};
