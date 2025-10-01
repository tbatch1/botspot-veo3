// server.js - Express REST API for Veo 3 Service
// Install: npm install express express-rate-limit helmet cors morgan multer

const express = require('express');
const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const cors = require('cors');
const morgan = require('morgan');
const multer = require('multer');
const { Veo3Service, ValidationError, APIError, TimeoutError } = require('./veo3-service');

const app = express();
const PORT = process.env.PORT || 3000;

// ============================================
// MIDDLEWARE SETUP
// ============================================

// Security headers
app.use(helmet());

// CORS configuration
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  methods: ['GET', 'POST', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

// Request parsing
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging
app.use(morgan('combined'));

// Rate limiting
const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', apiLimiter);

// ============================================
// INITIALIZE VEO3 SERVICE
// ============================================

const veo3Service = new Veo3Service(process.env.GEMINI_API_KEY, {
  maxRetries: 3,
  timeout: 600000,
  pollInterval: 10000
});

// ============================================
// ERROR HANDLING MIDDLEWARE
// ============================================

const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

const errorHandler = (err, req, res, next) => {
  console.error('Error:', err);

  if (err instanceof ValidationError) {
    return res.status(400).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details
      }
    });
  }

  if (err instanceof APIError) {
    return res.status(502).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details
      }
    });
  }

  if (err instanceof TimeoutError) {
    return res.status(504).json({
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details
      }
    });
  }

  // Default error
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
      details: process.env.NODE_ENV === 'development' ? err.message : {}
    }
  });
};

// ============================================
// ROUTES
// ============================================

/**
 * @route   GET /
 * @desc    API info
 * @access  Public
 */
app.get('/', (req, res) => {
  res.json({
    name: 'Botspot Veo 3 API',
    version: '1.0.0',
    description: 'Video generation API powered by Google Veo 3',
    endpoints: {
      health: 'GET /api/health',
      generate: 'POST /api/videos/generate',
      status: 'GET /api/videos/:requestId',
      cost: 'POST /api/videos/estimate-cost'
    }
  });
});

/**
 * @route   GET /api/health
 * @desc    Health check endpoint
 * @access  Public
 */
app.get('/api/health', asyncHandler(async (req, res) => {
  const health = await veo3Service.healthCheck();
  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
}));

/**
 * @route   POST /api/videos/generate
 * @desc    Generate a video with Veo 3
 * @access  Public (should be authenticated in production)
 */
app.post('/api/videos/generate', asyncHandler(async (req, res) => {
  const { prompt, model, aspectRatio, resolution, duration, userId } = req.body;

  // Generate unique request ID
  const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Start generation (will return immediately, video generates async)
  const result = await veo3Service.generateVideo({
    prompt,
    model,
    aspectRatio,
    resolution,
    duration,
    userId: userId || 'anonymous',
    requestId
  });

  res.status(202).json({
    success: true,
    message: 'Video generation completed',
    data: result
  });
}));

/**
 * @route   POST /api/videos/estimate-cost
 * @desc    Estimate cost for video generation
 * @access  Public
 */
app.post('/api/videos/estimate-cost', asyncHandler(async (req, res) => {
  const { duration, model } = req.body;

  if (!duration || !model) {
    return res.status(400).json({
      success: false,
      error: 'Duration and model are required'
    });
  }

  const cost = veo3Service.calculateCost(duration, model);

  res.json({
    success: true,
    data: {
      duration,
      model,
      estimatedCost: `$${cost}`,
      pricePerSecond: model.includes('fast') ? '$0.40' : '$0.50'
    }
  });
}));

/**
 * @route   GET /api/models
 * @desc    List available Veo 3 models
 * @access  Public
 */
app.get('/api/models', (req, res) => {
  res.json({
    success: true,
    data: {
      models: [
        {
          id: 'veo-3-fast-generate-001',
          name: 'Veo 3 Fast',
          description: 'Faster generation, optimized for quick iterations',
          pricePerSecond: '$0.40',
          maxDuration: 8,
          resolutions: ['720p', '1080p'],
          aspectRatios: ['16:9', '9:16']
        },
        {
          id: 'veo-3.0-generate-001',
          name: 'Veo 3 Standard',
          description: 'Higher quality, best for final production',
          pricePerSecond: '$0.50',
          maxDuration: 8,
          resolutions: ['720p', '1080p'],
          aspectRatios: ['16:9', '9:16']
        }
      ]
    }
  });
});

/**
 * @route   POST /api/videos/batch
 * @desc    Generate multiple videos in batch
 * @access  Public
 */
app.post('/api/videos/batch', asyncHandler(async (req, res) => {
  const { videos, userId } = req.body;

  if (!Array.isArray(videos) || videos.length === 0) {
    return res.status(400).json({
      success: false,
      error: 'Videos array is required'
    });
  }

  if (videos.length > 10) {
    return res.status(400).json({
      success: false,
      error: 'Maximum 10 videos per batch request'
    });
  }

  const results = [];
  const errors = [];

  for (let i = 0; i < videos.length; i++) {
    try {
      const video = videos[i];
      const requestId = `batch_${Date.now()}_${i}`;
      
      const result = await veo3Service.generateVideo({
        ...video,
        userId: userId || 'anonymous',
        requestId
      });

      results.push({
        index: i,
        success: true,
        data: result
      });
    } catch (error) {
      errors.push({
        index: i,
        success: false,
        error: {
          code: error.code || 'UNKNOWN_ERROR',
          message: error.message
        }
      });
    }
  }

  res.status(207).json({
    success: true,
    message: `Generated ${results.length} of ${videos.length} videos`,
    results,
    errors
  });
}));

/**
 * @route   GET /api/templates
 * @desc    Get pre-built prompt templates
 * @access  Public
 */
app.get('/api/templates', (req, res) => {
  res.json({
    success: true,
    data: {
      templates: [
        {
          id: 'launch-intro',
          name: 'Launch Intro',
          category: 'intro',
          prompt: 'Dramatic reveal of trading platform with rising cryptocurrency charts, professional cinematic lighting, camera push in effect, synchronized keyboard typing sounds',
          tags: ['cinematic', 'intro', 'trading'],
          estimatedCost: '$3.20'
        },
        {
          id: 'profit-viz',
          name: 'Profit Visualization',
          category: 'celebration',
          prompt: 'Green candlesticks rising rapidly with dollar signs floating upward, gold coins falling like rain, celebration mood, triumphant music',
          tags: ['celebration', 'profit', 'energetic'],
          estimatedCost: '$3.20'
        },
        {
          id: 'trader-closeup',
          name: 'Professional Trader',
          category: 'corporate',
          prompt: 'Close-up hands typing on mechanical keyboard with trading charts reflected in glasses, professional office setting, ambient office sounds',
          tags: ['corporate', 'professional', 'closeup'],
          estimatedCost: '$3.20'
        },
        {
          id: 'speed-transition',
          name: 'Speed Transition',
          category: 'transition',
          prompt: 'Fast-paced montage of trading indicators flashing, numbers changing rapidly, high-energy tech aesthetic, electronic swoosh sounds',
          tags: ['transition', 'fast', 'tech'],
          estimatedCost: '$2.00'
        }
      ]
    }
  });
});

// ============================================
// ERROR HANDLING
// ============================================

app.use(errorHandler);

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: {
      code: 'NOT_FOUND',
      message: 'Endpoint not found'
    }
  });
});

// ============================================
// SERVER STARTUP
// ============================================

const server = app.listen(PORT, () => {
  console.log(`
╔═══════════════════════════════════════════╗
║   Botspot Veo 3 API Server Running       ║
╠═══════════════════════════════════════════╣
║   Port: ${PORT}                            
║   Environment: ${process.env.NODE_ENV || 'development'}
║   API Key: ${process.env.GEMINI_API_KEY ? '✓ Set' : '✗ Missing'}
╚═══════════════════════════════════════════╝

📚 API Documentation:
   Health Check:    GET  http://localhost:${PORT}/api/health
   Generate Video:  POST http://localhost:${PORT}/api/videos/generate
   Estimate Cost:   POST http://localhost:${PORT}/api/videos/estimate-cost
   List Models:     GET  http://localhost:${PORT}/api/models
   Templates:       GET  http://localhost:${PORT}/api/templates
   Batch Generate:  POST http://localhost:${PORT}/api/videos/batch
  `);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  console.log('SIGINT signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

module.exports = app;