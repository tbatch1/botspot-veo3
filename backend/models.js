// models.js - MongoDB/Mongoose Database Models
// Install: npm install mongoose

const mongoose = require('mongoose');

// ============================================
// VIDEO GENERATION SCHEMA
// ============================================

const VideoGenerationSchema = new mongoose.Schema({
  requestId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  userId: {
    type: String,
    required: true,
    index: true
  },
  status: {
    type: String,
    enum: ['pending', 'processing', 'completed', 'failed'],
    default: 'pending',
    index: true
  },
  prompt: {
    type: String,
    required: true,
    maxlength: 2000
  },
  model: {
    type: String,
    required: true,
    enum: ['veo-3.0-generate-001', 'veo-3.0-fast-generate-001']
  },
  config: {
    aspectRatio: {
      type: String,
      enum: ['16:9'],
      default: '16:9'
    },
    resolution: {
      type: String,
      enum: ['720p', '1080p'],
      default: '720p'
    },
    duration: {
      type: Number,
      min: 8,
      max: 8,
      default: 8
    }
  },
  result: {
    videoUrl: String,
    format: String,
    fileSize: Number,
    downloadUrl: String
  },
  cost: {
    estimated: {
      type: Number,
      required: true
    },
    actual: Number,
    currency: {
      type: String,
      default: 'USD'
    }
  },
  timing: {
    requestedAt: {
      type: Date,
      default: Date.now
    },
    startedAt: Date,
    completedAt: Date,
    durationMs: Number
  },
  metadata: {
    ipAddress: String,
    userAgent: String,
    apiVersion: String
  },
  error: {
    code: String,
    message: String,
    details: mongoose.Schema.Types.Mixed
  }
}, {
  timestamps: true,
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// Indexes for performance
VideoGenerationSchema.index({ userId: 1, createdAt: -1 });
VideoGenerationSchema.index({ status: 1, createdAt: -1 });
VideoGenerationSchema.index({ 'timing.requestedAt': -1 });

// Virtual for generation time
VideoGenerationSchema.virtual('generationTime').get(function() {
  if (this.timing.completedAt && this.timing.startedAt) {
    return this.timing.completedAt - this.timing.startedAt;
  }
  return null;
});

// Methods
VideoGenerationSchema.methods.markAsProcessing = function() {
  this.status = 'processing';
  this.timing.startedAt = new Date();
  return this.save();
};

VideoGenerationSchema.methods.markAsCompleted = function(result, actualCost) {
  this.status = 'completed';
  this.timing.completedAt = new Date();
  this.timing.durationMs = this.timing.completedAt - this.timing.startedAt;
  this.result = result;
  this.cost.actual = actualCost;
  return this.save();
};

VideoGenerationSchema.methods.markAsFailed = function(error) {
  this.status = 'failed';
  this.timing.completedAt = new Date();
  this.error = {
    code: error.code,
    message: error.message,
    details: error.details
  };
  return this.save();
};

// Statics
VideoGenerationSchema.statics.getByUserId = function(userId, limit = 10) {
  return this.find({ userId })
    .sort({ createdAt: -1 })
    .limit(limit);
};

VideoGenerationSchema.statics.getStats = async function(userId) {
  const stats = await this.aggregate([
    { $match: { userId } },
    {
      $group: {
        _id: '$status',
        count: { $sum: 1 },
        totalCost: { $sum: '$cost.actual' },
        avgDuration: { $avg: '$timing.durationMs' }
      }
    }
  ]);

  return stats.reduce((acc, stat) => {
    acc[stat._id] = {
      count: stat.count,
      totalCost: stat.totalCost || 0,
      avgDuration: stat.avgDuration || 0
    };
    return acc;
  }, {});
};

const VideoGeneration = mongoose.model('VideoGeneration', VideoGenerationSchema);

// ============================================
// USER SCHEMA
// ============================================

const UserSchema = new mongoose.Schema({
  userId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true
  },
  apiKey: {
    type: String,
    unique: true,
    sparse: true
  },
  subscription: {
    plan: {
      type: String,
      enum: ['free', 'basic', 'pro', 'enterprise'],
      default: 'free'
    },
    status: {
      type: String,
      enum: ['active', 'cancelled', 'expired'],
      default: 'active'
    },
    limits: {
      videosPerMonth: {
        type: Number,
        default: 10
      },
      maxDuration: {
        type: Number,
        default: 8
      }
    },
    usage: {
      videosThisMonth: {
        type: Number,
        default: 0
      },
      totalSpent: {
        type: Number,
        default: 0
      },
      resetDate: {
        type: Date,
        default: () => new Date(new Date().setMonth(new Date().getMonth() + 1))
      }
    }
  },
  stats: {
    totalVideos: {
      type: Number,
      default: 0
    },
    successfulVideos: {
      type: Number,
      default: 0
    },
    failedVideos: {
      type: Number,
      default: 0
    },
    totalCost: {
      type: Number,
      default: 0
    }
  },
  lastActivity: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Methods
UserSchema.methods.canGenerateVideo = function() {
  if (this.subscription.status !== 'active') {
    return { allowed: false, reason: 'Subscription not active' };
  }
  
  if (this.subscription.usage.videosThisMonth >= this.subscription.limits.videosPerMonth) {
    return { allowed: false, reason: 'Monthly limit reached' };
  }
  
  return { allowed: true };
};

UserSchema.methods.incrementUsage = function(cost) {
  this.subscription.usage.videosThisMonth += 1;
  this.subscription.usage.totalSpent += cost;
  this.stats.totalVideos += 1;
  this.lastActivity = new Date();
  return this.save();
};

UserSchema.methods.resetMonthlyUsage = function() {
  this.subscription.usage.videosThisMonth = 0;
  this.subscription.usage.resetDate = new Date(new Date().setMonth(new Date().getMonth() + 1));
  return this.save();
};

const User = mongoose.model('User', UserSchema);

// ============================================
// TEMPLATE SCHEMA
// ============================================

const TemplateSchema = new mongoose.Schema({
  templateId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  name: {
    type: String,
    required: true
  },
  category: {
    type: String,
    required: true,
    index: true
  },
  prompt: {
    type: String,
    required: true
  },
  config: {
    model: String,
    aspectRatio: String,
    resolution: String,
    duration: Number
  },
  tags: [String],
  usage: {
    count: {
      type: Number,
      default: 0
    },
    lastUsed: Date
  },
  isPublic: {
    type: Boolean,
    default: true
  },
  createdBy: {
    type: String,
    default: 'system'
  }
}, {
  timestamps: true
});

TemplateSchema.index({ tags: 1 });
TemplateSchema.index({ category: 1, isPublic: 1 });

TemplateSchema.methods.incrementUsage = function() {
  this.usage.count += 1;
  this.usage.lastUsed = new Date();
  return this.save();
};

const Template = mongoose.model('Template', TemplateSchema);

// ============================================
// DATABASE CONNECTION
// ============================================

class Database {
  constructor() {
    this.connection = null;
  }

  async connect(uri) {
    try {
      this.connection = await mongoose.connect(uri, {
        useNewUrlParser: true,
        useUnifiedTopology: true
      });

      console.log('✅ MongoDB connected successfully');

      // Handle connection events
      mongoose.connection.on('error', (err) => {
        console.error('MongoDB connection error:', err);
      });

      mongoose.connection.on('disconnected', () => {
        console.log('MongoDB disconnected');
      });

      return this.connection;
    } catch (error) {
      console.error('MongoDB connection failed:', error);
      throw error;
    }
  }

  async disconnect() {
    if (this.connection) {
      await mongoose.disconnect();
      console.log('MongoDB disconnected');
    }
  }

  async healthCheck() {
    try {
      if (mongoose.connection.readyState === 1) {
        await mongoose.connection.db.admin().ping();
        return { status: 'healthy', connected: true };
      }
      return { status: 'unhealthy', connected: false };
    } catch (error) {
      return { 
        status: 'unhealthy', 
        connected: false, 
        error: error.message 
      };
    }
  }
}

// ============================================
// SEED DATA
// ============================================

async function seedTemplates() {
  const templates = [
    {
      templateId: 'launch-intro',
      name: 'Launch Intro',
      category: 'intro',
      prompt: 'Dramatic reveal of trading platform with rising cryptocurrency charts, professional cinematic lighting, camera push in effect',
      config: {
        model: 'veo-3.0-fast-generate-001',
        aspectRatio: '16:9',
        resolution: '1080p',
        duration: 8
      },
      tags: ['intro', 'cinematic', 'trading']
    },
    {
      templateId: 'profit-viz',
      name: 'Profit Visualization',
      category: 'celebration',
      prompt: 'Green candlesticks rising rapidly with dollar signs floating upward, gold coins falling like rain',
      config: {
        model: 'veo-3.0-fast-generate-001',
        aspectRatio: '16:9',
        resolution: '1080p',
        duration: 8
      },
      tags: ['celebration', 'profit', 'success']
    },
    {
      templateId: 'professional-trader',
      name: 'Professional Trader',
      category: 'corporate',
      prompt: 'Close-up hands typing on mechanical keyboard with trading charts reflected in glasses',
      config: {
        model: 'veo-3.0-fast-generate-001',
        aspectRatio: '16:9',
        resolution: '1080p',
        duration: 8
      },
      tags: ['corporate', 'professional', 'closeup']
    }
  ];

  for (const template of templates) {
    await Template.findOneAndUpdate(
      { templateId: template.templateId },
      template,
      { upsert: true, new: true }
    );
  }

  console.log(`✅ Seeded ${templates.length} templates`);
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  Database,
  VideoGeneration,
  User,
  Template,
  seedTemplates,
  mongoose
};

// Example usage
if (require.main === module) {
  const db = new Database();
  const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/botspot-veo3';
  
  db.connect(MONGO_URI)
    .then(() => seedTemplates())
    .then(() => {
      console.log('✅ Database setup complete');
      process.exit(0);
    })
    .catch((error) => {
      console.error('❌ Database setup failed:', error);
      process.exit(1);
    });
}