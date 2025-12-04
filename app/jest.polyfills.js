// Ensure Node globals expected by MSW/undici exist before tests run
if (typeof global.TextEncoder === 'undefined') {
  const { TextEncoder, TextDecoder } = require('util');
  global.TextEncoder = TextEncoder;
  global.TextDecoder = TextDecoder;
}

if (typeof global.ReadableStream === 'undefined') {
  const { ReadableStream } = require('stream/web');
  global.ReadableStream = ReadableStream;
}

const { Headers, Request, Response } = require('undici');

if (typeof global.Headers === 'undefined') {
  global.Headers = Headers;
}
if (typeof global.Request === 'undefined') {
  global.Request = Request;
}
if (typeof global.Response === 'undefined') {
  global.Response = Response;
}

if (typeof global.BroadcastChannel === 'undefined') {
  global.BroadcastChannel = class BroadcastChannel {
    constructor() {}
    postMessage() {}
    close() {}
    addEventListener() {}
    removeEventListener() {}
  };
}
