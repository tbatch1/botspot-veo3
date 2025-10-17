import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { APIClient } from '@/lib/api-client';

const API_BASE_URL = 'http://localhost:3000';

// Mock handlers
const handlers = [
  http.get(`${API_BASE_URL}/api/health`, () => {
    return HttpResponse.json({
      status: 'healthy',
      service: 'Veo 3 API',
      timestamp: new Date().toISOString(),
      apiKey: 'configured',
      canGenerateVideos: true,
      message: 'API is running',
    });
  }),

  http.post(`${API_BASE_URL}/api/videos/generate`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      success: true,
      data: {
        requestId: 'test-request-123',
        video: {
          url: 'https://example.com/video.mp4',
          format: 'mp4',
          duration: (body as any).duration || 6,
          resolution: (body as any).resolution || '1080p',
          aspectRatio: (body as any).aspectRatio || '16:9',
        },
        metadata: {
          model: (body as any).model || 'veo-3-fast-generate-001',
          prompt: (body as any).prompt || 'Test prompt',
          estimatedCost: '$2.40',
          generationTimeMs: 5000,
        },
        timestamp: new Date().toISOString(),
      },
    });
  }),

  http.post(`${API_BASE_URL}/api/videos/estimate-cost`, async ({ request }) => {
    const body = await request.json();
    const { duration, model } = body as any;
    const pricePerSecond = model.includes('fast') ? 0.4 : 0.5;
    return HttpResponse.json({
      success: true,
      data: {
        duration,
        model,
        estimatedCost: `$${(duration * pricePerSecond).toFixed(2)}`,
        pricePerSecond: `$${pricePerSecond}`,
      },
    });
  }),
];

const server = setupServer(...handlers);

describe('APIClient', () => {
  let client: APIClient;

  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  beforeEach(() => {
    client = new APIClient(API_BASE_URL);
  });

  describe('checkHealth', () => {
    it('should return health status', async () => {
      const health = await client.checkHealth();

      expect(health.status).toBe('healthy');
      expect(health.service).toBe('Veo 3 API');
      expect(health.canGenerateVideos).toBe(true);
    });

    it('should handle health check failure', async () => {
      server.use(
        http.get(`${API_BASE_URL}/api/health`, () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      await expect(client.checkHealth()).rejects.toThrow();
    });
  });

  describe('generateVideo', () => {
    it('should generate video successfully', async () => {
      const request = {
        prompt: 'Test trading bot video',
        model: 'veo-3-fast-generate-001' as const,
        duration: 6,
        aspectRatio: '16:9' as const,
        resolution: '1080p' as const,
        userId: 'test-user',
      };

      const response = await client.generateVideo(request);

      expect(response.success).toBe(true);
      expect(response.data.requestId).toBe('test-request-123');
      expect(response.data.video.url).toBeTruthy();
      expect(response.data.video.duration).toBe(6);
      expect(response.data.metadata.model).toBe('veo-3-fast-generate-001');
    });

    it('should handle generation errors', async () => {
      server.use(
        http.post(`${API_BASE_URL}/api/videos/generate`, () => {
          return HttpResponse.json(
            { error: { message: 'API key missing' } },
            { status: 400 }
          );
        })
      );

      const request = {
        prompt: 'Test',
        model: 'veo-3-fast-generate-001' as const,
        userId: 'test-user',
      };

      await expect(client.generateVideo(request)).rejects.toThrow();
    });
  });

  describe('estimateCost', () => {
    it('should estimate cost for fast model', async () => {
      const response = await client.estimateCost(5, 'veo-3-fast-generate-001');

      expect(response.success).toBe(true);
      expect(response.data.estimatedCost).toBe('$2.00');
      expect(response.data.pricePerSecond).toBe('$0.4');
    });

    it('should estimate cost for standard model', async () => {
      const response = await client.estimateCost(5, 'veo-3.0-generate-001');

      expect(response.success).toBe(true);
      expect(response.data.estimatedCost).toBe('$2.50');
      expect(response.data.pricePerSecond).toBe('$0.5');
    });
  });

  describe('retry logic', () => {
    it('should retry on network errors', async () => {
      let attempts = 0;

      server.use(
        http.get(`${API_BASE_URL}/api/health`, () => {
          attempts++;
          if (attempts < 2) {
            return HttpResponse.error();
          }
          return HttpResponse.json({
            status: 'healthy',
            service: 'Veo 3 API',
            timestamp: new Date().toISOString(),
            apiKey: 'configured',
            canGenerateVideos: true,
            message: 'API is running',
          });
        })
      );

      const health = await client.checkHealth();

      expect(attempts).toBe(2);
      expect(health.status).toBe('healthy');
    });
  });
});
