// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Mock fetch for tests
if (typeof global.fetch === 'undefined') {
  global.fetch = jest.fn();
} else {
  const originalFetch = global.fetch;
  global.fetch = jest.fn(originalFetch.bind(global));
}
