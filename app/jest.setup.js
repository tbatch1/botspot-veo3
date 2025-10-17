// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Polyfills for MSW and Node environment
if (typeof global.TextEncoder === 'undefined') {
  const { TextEncoder, TextDecoder } = require('util');
  global.TextEncoder = TextEncoder;
  global.TextDecoder = TextDecoder;
}

// Mock fetch for tests
global.fetch = jest.fn();
