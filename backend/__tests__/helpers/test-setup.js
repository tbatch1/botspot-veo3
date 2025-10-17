// test-setup.js - Jest Test Setup and Global Mocks

// Increase test timeout for slow operations
jest.setTimeout(30000);

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(), // Mock console.log
  error: jest.fn(), // Mock console.error
  warn: jest.fn(), // Mock console.warn
  info: jest.fn(), // Mock console.info
};

// Suppress MongoDB warnings in tests
process.env.NODE_ENV = 'test';

// Mock environment variables for tests
process.env.GEMINI_API_KEY = 'test_api_key_mock';
process.env.MONGO_URI = 'mongodb://localhost:27017/botspot-veo3-test';
process.env.GCS_PROJECT_ID = 'test-project';
process.env.GCS_BUCKET_NAME = 'test-bucket';
process.env.PORT = '4001'; // Different port for tests

// Global test helpers
global.testHelpers = {
  // Create mock video generation result
  mockVideoResult: () => ({
    video: {
      url: 'https://storage.googleapis.com/test/video.mp4',
      format: 'video/mp4'
    },
    metadata: {
      estimatedCost: '$1.20',
      duration: 8,
      resolution: '1080p'
    }
  }),

  // Create mock sequence data
  mockSequenceData: () => ({
    userId: 'test-user-123',
    title: 'Test Sequence',
    description: 'Test description'
  }),

  // Create mock scene data
  mockSceneData: () => ({
    prompt: 'Test scene prompt with detailed description',
    duration: 8,
    model: 'veo-3.1-fast-generate-preview'
  }),

  // Sleep helper for async tests
  sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms))
};

// Clean up after all tests
afterAll(async () => {
  // Close any open handles
  await new Promise(resolve => setTimeout(resolve, 500));
});
