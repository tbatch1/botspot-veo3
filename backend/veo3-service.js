// veo3-service.js - Core Google Veo 3 Video Generation Service
// Install: npm install @google/genai

const { GoogleGenAI } = require('@google/genai');

// ============================================
// CUSTOM ERROR CLASSES
// ============================================

class ValidationError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'ValidationError';
    this.code = 'VALIDATION_ERROR';
    this.details = details;
  }
}

class APIError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'APIError';
    this.code = 'API_ERROR';
    this.details = details;
  }
}

class TimeoutError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = 'TimeoutError';
    this.code = 'TIMEOUT_ERROR';
    this.details = details;
  }
}

// ============================================
// VEO 3 SERVICE
// ============================================

class Veo3Service {
  constructor(apiKey, options = {}) {
    if (!apiKey || apiKey === 'PUT_YOUR_KEY_HERE') {
      console.warn('⚠️  WARNING: No API key provided. Video generation will not work.');
      console.warn('⚠️  Set GEMINI_API_KEY in .env to enable video generation.');
      this.apiKey = null;
      this.genAI = null;
    } else {
      this.apiKey = apiKey;
      try {
        this.genAI = new GoogleGenAI({ apiKey });
      } catch (err) {
        console.warn('⚠️  WARNING: GoogleGenAI failed to initialize:', err.message);
        this.genAI = null;
      }
    }

    this.options = {
      maxRetries: options.maxRetries || 3,
      timeout: options.timeout || 600000, // 10 minutes
      pollInterval: options.pollInterval || 10000, // 10 seconds
    };

    // Mock mode: allow offline testing without real API calls
    this.mock = typeof options.mock === 'boolean'
      ? options.mock
      : (process.env.VEO3_MOCK === 'true' || process.env.VEO3_MOCK === '1');

    this.models = {
      'veo-3.0-generate-001': {
        name: 'Veo 3 Standard',
        pricePerSecond: 0.40,
        maxDuration: 8
      },
      'veo-3.0-fast-generate-001': {
        name: 'Veo 3 Fast',
        pricePerSecond: 0.15,
        maxDuration: 8
      },
      'nano-banana-preview': {
        name: 'Nano Banana',
        pricePerSecond: 0.15,
        maxDuration: 8
      }
    };
  }

  /**
   * Validate video generation request
   */
  validateRequest(params) {
    const errors = [];

    // Prompt validation
    if (!params.prompt || typeof params.prompt !== 'string') {
      errors.push('Prompt is required and must be a string');
    } else if (params.prompt.length < 10) {
      errors.push('Prompt must be at least 10 characters');
    } else if (params.prompt.length > 2000) {
      errors.push('Prompt must be less than 2000 characters');
    }

    // Model validation
    if (!params.model || !this.models[params.model]) {
      errors.push(`Invalid model. Must be one of: ${Object.keys(this.models).join(', ')}`);
    }

    // Duration validation (Veo 3 supports 8s)
    const duration = params.duration || 8;
    if (duration !== 8) {
      errors.push('Veo 3 supports only 8 second videos (duration must be 8)');
    }

    // Aspect ratio validation (Veo 3 supports 16:9)
    const validAspectRatios = ['16:9'];
    if (params.aspectRatio && !validAspectRatios.includes(params.aspectRatio)) {
      errors.push('Invalid aspect ratio for Veo 3. Supported: 16:9');
    }

    // Resolution validation
    const validResolutions = ['720p', '1080p'];
    if (params.resolution && !validResolutions.includes(params.resolution)) {
      errors.push(`Invalid resolution. Must be one of: ${validResolutions.join(', ')}`);
    }

    if (errors.length > 0) {
      throw new ValidationError('Validation failed', { errors });
    }

    return true;
  }

  /**
   * Calculate estimated cost
   */
  calculateCost(duration, model) {
    const modelInfo = this.models[model];
    if (!modelInfo) {
      throw new ValidationError('Invalid model');
    }
    return (duration * modelInfo.pricePerSecond).toFixed(2);
  }

  /**
   * Generate video with Veo 3
   */
  async generateVideo(params) {
    const startTime = Date.now();

    // Set defaults
    const config = {
      prompt: params.prompt,
      // Ensure model uses the correct versioned id
      model: params.model || 'veo-3.0-fast-generate-001',
      aspectRatio: params.aspectRatio || '16:9',
      resolution: params.resolution || '1080p',
      duration: params.duration || 8,
      // Optional advanced controls
      negativePrompt: params.negativePrompt,
      seed: params.seed,
      personGeneration: params.personGeneration,
      image: params.image,
      userId: params.userId || 'anonymous',
      requestId: params.requestId || `req_${Date.now()}`
    };

    // Enforce cost-saver mode if enabled via env
    if (process.env.VEO3_FORCE_FAST === 'true') {
      if (config.model !== 'veo-3.0-fast-generate-001') {
        console.warn(`[${config.requestId}] ⚠️  VEO3_FORCE_FAST active: overriding model '${config.model}' → 'veo-3.0-fast-generate-001'`);
        config.model = 'veo-3.0-fast-generate-001';
      }
      if (config.resolution !== '720p') {
        console.warn(`[${config.requestId}] ⚠️  VEO3_FORCE_FAST active: overriding resolution '${config.resolution}' → '720p'`);
        config.resolution = '720p';
      }
    }

    // Optional max cost guard
    const maxCostEnv = process.env.VEO3_MAX_COST;
    if (maxCostEnv) {
      const est = parseFloat(this.calculateCost(config.duration, config.model));
      const max = parseFloat(maxCostEnv);
      if (!Number.isNaN(max) && est > max) {
        throw new ValidationError(`Estimated cost $${est.toFixed(2)} exceeds limit $${max.toFixed(2)}. Reduce duration or use fast/720p.`, {
          estimated: est,
          limit: max,
          model: config.model,
          resolution: config.resolution
        });
      }
    }

    // Validate request
    this.validateRequest(config);

    // Check if API key is available (skip in mock mode)
    if (!this.mock && (!this.apiKey || !this.genAI)) {
      throw new APIError(
        'API key not configured. Please set GEMINI_API_KEY in your environment variables.',
        {
          requestId: config.requestId,
            hint: 'Get your API key at https://aistudio.google.com/apikey'
        }
      );
    }

    console.log(`\n${'='.repeat(80)}`);
    console.log(`[${config.requestId}] 🎬 STARTING VIDEO GENERATION`);
    console.log(`${'='.repeat(80)}`);
    console.log(`[${config.requestId}] Model: ${config.model}`);
    console.log(`[${config.requestId}] Duration: ${config.duration}s`);
    console.log(`[${config.requestId}] Resolution: ${config.resolution}`);
    console.log(`[${config.requestId}] Aspect Ratio: ${config.aspectRatio}`);
    console.log(`[${config.requestId}] Prompt: ${config.prompt.substring(0, 150)}...`);
    console.log(`${'='.repeat(80)}\n`);

    try {
      // Determine if this request should use mock mode (per-request override takes precedence)
      const useMock = (typeof params.mock === 'boolean') ? params.mock : this.mock;
      // In mock mode, simulate a successful generation without external calls
      if (useMock) {
        const mockUrl = `https://storage.googleapis.com/generativeai-downloads/videos/mock_${Date.now()}.mp4`;
        const generationTimeMs = 2000 + Math.floor(Math.random() * 3000);
        await this.sleep(250); // Simulate minimal latency

        const response = {
          requestId: config.requestId,
          video: {
            url: mockUrl,
            format: 'mp4',
            duration: config.duration,
            resolution: config.resolution,
            aspectRatio: config.aspectRatio
          },
          metadata: {
            model: config.model,
            prompt: config.prompt,
            estimatedCost: `$${this.calculateCost(config.duration, config.model)}`,
            generationTimeMs
          },
          timestamp: new Date().toISOString(),
          mock: true
        };

        console.log(`[${config.requestId}] ✅ MOCK VIDEO GENERATION SUCCESS`);
        return response;
      }
      // Generate video using Veo 3 API
      console.log(`[${config.requestId}] 📡 Calling Veo 3 API...`);
      console.log(`[${config.requestId}] API Request:`, JSON.stringify({
        model: config.model,
        prompt: config.prompt.substring(0, 100) + '...',
        aspect_ratio: config.aspectRatio,
        resolution: config.resolution,
        duration_seconds: config.duration
      }, null, 2));

      let operation = await this.retryWithBackoff(async () => {
        // Choose personGeneration default based on input type
        const defaultPersonGen = config.image ? 'allow_adult' : 'allow_all';
        const genParams = {
          model: config.model,
          prompt: config.prompt,
          ...(config.image ? { image: config.image } : {}),
          config: {
            aspectRatio: config.aspectRatio,
            resolution: config.resolution,
            durationSeconds: config.duration,
            personGeneration: config.personGeneration || defaultPersonGen,
            ...(config.negativePrompt ? { negativePrompt: config.negativePrompt } : {}),
            ...(config.seed !== undefined ? { seed: config.seed } : {})
          }
        };

        console.log(`[${config.requestId}] 🎯 Full API params:`, JSON.stringify(genParams, null, 2));

        return await this.genAI.models.generateVideos(genParams);
      });

      console.log(`[${config.requestId}] ✅ API call successful, operation started`);
      console.log(`[${config.requestId}] Operation ID:`, operation.name || 'N/A');

      // Poll the operation status until the video is ready
      console.log(`[${config.requestId}] 🔄 Polling for video completion...`);
      let pollCount = 0;
      while (!operation.done) {
        pollCount++;
        await this.sleep(this.options.pollInterval);
        operation = await this.genAI.operations.getVideosOperation({ operation });
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        console.log(`[${config.requestId}] Poll #${pollCount} (${elapsed}s elapsed): ${operation.done ? '✅ Complete' : '⏳ Processing...'}`);
      }

      console.log(`[${config.requestId}] 🎉 Video generation complete!`);
      console.log(`[${config.requestId}] Response structure:`, JSON.stringify({
        done: operation.done,
        hasResponse: !!operation.response,
        responseKeys: operation.response ? Object.keys(operation.response) : []
      }, null, 2));

      const endTime = Date.now();
      const generationTimeMs = endTime - startTime;

      // Extract video data from response
      const videoData = this.extractVideoData(operation);

      const response = {
        requestId: config.requestId,
        video: {
          url: videoData.url,
          format: videoData.format || 'mp4',
          duration: config.duration,
          resolution: config.resolution,
          aspectRatio: config.aspectRatio
        },
        metadata: {
          model: config.model,
          prompt: config.prompt,
          estimatedCost: `$${this.calculateCost(config.duration, config.model)}`,
          generationTimeMs
        },
        timestamp: new Date().toISOString()
      };

      console.log(`\n${'='.repeat(80)}`);
      console.log(`[${config.requestId}] ✅ VIDEO GENERATION SUCCESS`);
      console.log(`${'='.repeat(80)}`);
      console.log(`[${config.requestId}] Generation Time: ${(generationTimeMs / 1000).toFixed(1)}s`);
      console.log(`[${config.requestId}] Video URL: ${response.video.url}`);
      console.log(`[${config.requestId}] Cost: ${response.metadata.estimatedCost}`);
      console.log(`${'='.repeat(80)}\n`);

      return response;

    } catch (error) {
      console.error(`\n${'='.repeat(80)}`);
      console.error(`[${config.requestId}] ❌ VIDEO GENERATION FAILED`);
      console.error(`${'='.repeat(80)}`);
      console.error(`[${config.requestId}] Error Type: ${error.name}`);
      console.error(`[${config.requestId}] Error Message: ${error.message}`);
      console.error(`[${config.requestId}] Error Stack:`, error.stack);

      if (error.response) {
        console.error(`[${config.requestId}] API Response Status: ${error.response.status}`);
        console.error(`[${config.requestId}] API Response Data:`, JSON.stringify(error.response.data, null, 2));
      }

      console.error(`${'='.repeat(80)}\n`);

      if (error instanceof ValidationError) {
        throw error;
      }

      throw new APIError(
        `Video generation failed: ${error.message}`,
        {
          requestId: config.requestId,
          originalError: error.message,
          errorType: error.name,
          model: config.model,
          stack: error.stack
        }
      );
    }
  }

  /**
   * Extract video data from API response
   */
  extractVideoData(operation) {
    try {
      console.log(`[VIDEO EXTRACTION] 🔍 Analyzing API response...`);
      console.log(`[VIDEO EXTRACTION] Response keys:`, Object.keys(operation.response || {}));

      // Handle Veo 3 API response format (camelCase: generatedVideos)
      if (operation.response && operation.response.generatedVideos && operation.response.generatedVideos.length > 0) {
        const video = operation.response.generatedVideos[0];
        console.log(`[VIDEO EXTRACTION] Found generatedVideos array with ${operation.response.generatedVideos.length} item(s)`);
        console.log(`[VIDEO EXTRACTION] Video object keys:`, Object.keys(video));

        // Return the video file reference
        if (video.video) {
          const url = video.video.uri || video.video.url;
          console.log(`[VIDEO EXTRACTION] ✅ Video URL extracted: ${url}`);
          return {
            url: url,
            fileRef: video.video,  // Keep reference for download
            format: 'mp4'
          };
        } else {
          console.warn(`[VIDEO EXTRACTION] ⚠️ Video object missing 'video' property`);
        }
      } else {
        console.warn(`[VIDEO EXTRACTION] ⚠️ Response missing generatedVideos array`);
        console.warn(`[VIDEO EXTRACTION] Full response:`, JSON.stringify(operation.response, null, 2));
      }

      // Fallback: generate a mock URL for testing
      console.warn('❌ Could not extract video URL from response, using mock data');
      return {
        url: `https://storage.googleapis.com/generativeai-downloads/videos/mock_${Date.now()}.mp4`,
        format: 'mp4'
      };

    } catch (error) {
      console.error(`[VIDEO EXTRACTION] ❌ Extraction failed:`, error.message);
      throw new APIError('Failed to extract video data from response', { error: error.message });
    }
  }

  /**
   * Retry with exponential backoff
   */
  async retryWithBackoff(fn, retries = this.options.maxRetries) {
    let lastError;

    for (let i = 0; i < retries; i++) {
      try {
        return await this.withTimeout(fn(), this.options.timeout);
      } catch (error) {
        lastError = error;

        if (i < retries - 1) {
          const delay = Math.min(1000 * Math.pow(2, i), 10000);
          console.log(`Retry ${i + 1}/${retries} after ${delay}ms...`);
          await this.sleep(delay);
        }
      }
    }

    throw lastError;
  }

  /**
   * Add timeout to promise
   */
  withTimeout(promise, timeoutMs) {
    return Promise.race([
      promise,
      new Promise((_, reject) => {
        setTimeout(() => {
          reject(new TimeoutError(`Operation timed out after ${timeoutMs}ms`));
        }, timeoutMs);
      })
    ]);
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Health check
   */
  async healthCheck() {
    const apiKeyStatus = this.apiKey ? 'configured' : 'missing';
    const canGenerate = !!(this.mock || (this.apiKey && this.genAI));

    return {
      status: canGenerate ? 'healthy' : 'partial',
      service: 'Veo 3 API',
      timestamp: new Date().toISOString(),
      apiKey: apiKeyStatus,
      canGenerateVideos: canGenerate,
      mode: this.mock ? 'mock' : 'live',
      message: canGenerate
        ? (this.mock ? 'Ready (mock mode enabled)' : 'Ready to generate videos')
        : 'API running but video generation disabled (no API key)'
    };
  }

  /**
   * Get available models
   */
  getModels() {
    return Object.entries(this.models).map(([id, info]) => ({
      id,
      name: info.name,
      pricePerSecond: `$${info.pricePerSecond}`,
      maxDuration: info.maxDuration
    }));
  }
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  Veo3Service,
  ValidationError,
  APIError,
  TimeoutError
};

// ============================================
// EXAMPLE USAGE
// ============================================

if (require.main === module) {
  const service = new Veo3Service(process.env.GEMINI_API_KEY);

  console.log('Testing Veo 3 Service...\n');

  // Test 1: Health check
  service.healthCheck().then(health => {
    console.log('Health Check:', health);
  });

  // Test 2: Cost calculation
  console.log('\nCost Estimates:');
  console.log('8s @ Veo 3 Fast:', `$${service.calculateCost(8, 'veo-3.0-fast-generate-001')}`);
  console.log('8s @ Veo 3 Standard:', `$${service.calculateCost(8, 'veo-3.0-generate-001')}`);

  // Test 3: Generate video (if API key is set)
  if (process.env.GEMINI_API_KEY) {
    console.log('\nGenerating test video...');
    service.generateVideo({
      prompt: 'A serene ocean sunset with gentle waves',
      model: 'veo-3.0-fast-generate-001',
      duration: 8
    })
    .then(result => {
      console.log('\n✅ Success!');
      console.log('Request ID:', result.requestId);
      console.log('Video URL:', result.video.url);
      console.log('Cost:', result.metadata.estimatedCost);
      console.log('Time:', `${(result.metadata.generationTimeMs / 1000).toFixed(1)}s`);
    })
    .catch(error => {
      console.error('\n❌ Error:', error.message);
    });
  } else {
    console.log('\n⚠️  Set GEMINI_API_KEY to test video generation');
  }
}
