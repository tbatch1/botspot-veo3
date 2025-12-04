import { APIClient } from '@/lib/api-client';

const API_BASE_URL = 'http://localhost:3000';

describe('APIClient', () => {
  let client: APIClient;
  let mockGet: jest.SpyInstance;
  let mockPost: jest.SpyInstance;

  beforeEach(() => {
    client = new APIClient(API_BASE_URL);
    const axiosInstance = (client as any).client;
    mockGet = jest.spyOn(axiosInstance, 'get');
    mockPost = jest.spyOn(axiosInstance, 'post');
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('checkHealth', () => {
    it('should return health status', async () => {
      mockGet.mockResolvedValue({
        data: {
          status: 'healthy',
          service: 'Veo 3 API',
          timestamp: new Date().toISOString(),
          apiKey: 'configured',
          canGenerateVideos: true,
          message: 'API is running',
        },
      });

      const health = await client.checkHealth();

      expect(mockGet).toHaveBeenCalledWith('/api/health');
      expect(health.status).toBe('healthy');
      expect(health.service).toBe('Veo 3 API');
    });

    it('should handle health check failure', async () => {
      mockGet.mockRejectedValue(new Error('Server error'));
      (client as any).retryCount = 1;
      (client as any).retryDelay = 0;

      await expect(client.checkHealth()).rejects.toThrow('Server error');
    });
  });

  describe('generateVideo', () => {
    it('should generate video successfully', async () => {
      const request = {
        prompt: 'Test trading bot video',
        model: 'veo-3.1-fast-generate-preview' as const,
        duration: 6,
        aspectRatio: '16:9' as const,
        resolution: '1080p' as const,
        userId: 'test-user',
      };

      const mockResponse = {
        success: true,
        data: {
          requestId: 'test-request-123',
          video: {
            url: 'https://example.com/video.mp4',
            format: 'mp4',
            duration: 6,
            resolution: '1080p',
            aspectRatio: '16:9',
          },
          metadata: {
            model: 'veo-3.1-fast-generate-preview',
            prompt: 'Test prompt',
            estimatedCost: '$2.40',
            generationTimeMs: 5000,
          },
          timestamp: new Date().toISOString(),
        },
      };

      mockPost.mockResolvedValue({ data: mockResponse });

      const response = await client.generateVideo(request);

      expect(mockPost).toHaveBeenCalledWith('/api/videos/generate', request);
      expect(response.success).toBe(true);
      expect(response.data.requestId).toBe('test-request-123');
    });

    it('should handle generation errors', async () => {
      mockPost.mockRejectedValue(new Error('API key missing'));

      const request = {
        prompt: 'Test',
        model: 'veo-3.1-fast-generate-preview' as const,
        userId: 'test-user',
      };

      await expect(client.generateVideo(request)).rejects.toThrow('API key missing');
    });
  });

  describe('estimateCost', () => {
    it('should estimate cost for fast model', async () => {
      const mockResponse = {
        success: true,
        data: {
          duration: 5,
          model: 'veo-3.1-fast-generate-preview',
          estimatedCost: '$1.75',
          pricePerSecond: '$0.35',
        },
      };

      mockPost.mockResolvedValue({ data: mockResponse });

      const response = await client.estimateCost(5, 'veo-3.1-fast-generate-preview');

      expect(mockPost).toHaveBeenCalledWith('/api/videos/estimate-cost', {
        duration: 5,
        model: 'veo-3.1-fast-generate-preview',
      });
      expect(response.data.estimatedCost).toBe('$1.75');
      expect(response.data.pricePerSecond).toBe('$0.35');
    });

    it('should estimate cost for standard model', async () => {
      const mockResponse = {
        success: true,
        data: {
          duration: 5,
          model: 'veo-3.0-generate-001',
          estimatedCost: '$2.00',
          pricePerSecond: '$0.4',
        },
      };

      mockPost.mockResolvedValue({ data: mockResponse });

      const response = await client.estimateCost(5, 'veo-3.0-generate-001');

      expect(response.data.estimatedCost).toBe('$2.00');
      expect(response.data.pricePerSecond).toBe('$0.4');
    });
  });

  describe('retry logic', () => {
    it('should retry on network errors', async () => {
      mockGet
        .mockRejectedValueOnce(new Error('Temporary network issue'))
        .mockResolvedValueOnce({
          data: {
            status: 'healthy',
            service: 'Veo 3 API',
            timestamp: new Date().toISOString(),
            apiKey: 'configured',
            canGenerateVideos: true,
            message: 'API is running',
          },
        });

      const health = await client.checkHealth();

      expect(mockGet).toHaveBeenCalledTimes(2);
      expect(health.status).toBe('healthy');
    });
  });
});
