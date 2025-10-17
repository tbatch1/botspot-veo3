// jest.config.js - Jest Testing Configuration

module.exports = {
  // Test environment
  testEnvironment: 'node',

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.test.js',
    '**/?(*.)+(spec|test).js'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    '**/*.js',
    '!**/node_modules/**',
    '!**/__tests__/**',
    '!**/coverage/**',
    '!jest.config.js'
  ],

  // Coverage thresholds (aim for 80%+)
  coverageThresholds: {
    global: {
      branches: 70,
      functions: 75,
      lines: 80,
      statements: 80
    }
  },

  // Coverage reporters
  coverageReporters: ['text', 'lcov', 'html'],

  // Test timeout (some tests may take time with FFmpeg/MongoDB)
  testTimeout: 30000,

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/__tests__/helpers/test-setup.js'],

  // Clear mocks between tests
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true,

  // Verbose output
  verbose: true,

  // Module paths
  modulePaths: ['<rootDir>'],

  // Transform (if needed for ES modules)
  transform: {},

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/coverage/'
  ],

  // Global setup/teardown
  // globalSetup: '<rootDir>/__tests__/helpers/global-setup.js',
  // globalTeardown: '<rootDir>/__tests__/helpers/global-teardown.js',
};
