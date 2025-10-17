import axios, { AxiosInstance, AxiosError } from 'axios';
import { log } from './logger';

// API Client Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4000';

export interface VideoGenerationRequest {
  prompt: string;
  model: 'veo-3.0-generate-001' | 'veo-3.0-fast-generate-001';
  aspectRatio?: '16:9' | '9:16';
  resolution?: '720p' | '1080p';
  duration?: number;
  // When true, backend will attempt prompt optimization
  optimizePrompt?: boolean;
  // When true, force mock mode for this request; when false, force live; undefined uses server default
  mock?: boolean;
  userId: string;
}

export interface VideoGenerationResponse {
  success: boolean;
  data: {
    requestId: string;
    video: {
      url: string;
      format: string;
      duration: number;
      resolution: string;
      aspectRatio: string;
    };
    metadata: {
      model: string;
      prompt: string;
      estimatedCost: string;
      generationTimeMs: number;
    };
    timestamp: string;
  };
}

export interface CostEstimateResponse {
  success: boolean;
  data: {
    duration: number;
    model: string;
    estimatedCost: string;
    pricePerSecond: string;
  };
}

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
  apiKey: string;
  canGenerateVideos: boolean | null;
  message: string;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  pricePerSecond: string;
  maxDuration: number;
  resolutions: string[];
  aspectRatios: string[];
}

class APIClient {
  private client: AxiosInstance;
  private retryCount: number = 3;
  private retryDelay: number = 1000; // ms

  constructor(baseURL: string = API_BASE_URL) {
    this.client = axios.create({
      baseURL,
      timeout: 120000, // 2 minutes for video generation
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        log.info('API Request', {
          method: config.method?.toUpperCase(),
          url: config.url,
          data: config.data ? JSON.stringify(config.data).substring(0, 200) : undefined,
        });
        return config;
      },
      (error) => {
        log.error('API Request Error', { error: error.message });
        return Promise.reject(error);
      }
    );

    // Response interceptor for logging
    this.client.interceptors.response.use(
      (response) => {
        log.info('API Response', {
          status: response.status,
          url: response.config.url,
        });
        return response;
      },
      (error: AxiosError) => {
        log.error('API Response Error', {
          status: error.response?.status,
          url: error.config?.url,
          message: error.message,
          data: error.response?.data,
        });
        return Promise.reject(error);
      }
    );
  }

  // Retry logic with exponential backoff
  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    retries: number = this.retryCount
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error: any) {
      if (retries > 0 && this.isRetryableError(error)) {
        const delay = this.retryDelay * (this.retryCount - retries + 1);
        log.warn('Retrying request', { retriesLeft: retries, delayMs: delay });
        await this.sleep(delay);
        return this.retryRequest(requestFn, retries - 1);
      }
      throw error;
    }
  }

  private isRetryableError(error: any): boolean {
    // Retry on network errors or 5xx server errors
    return (
      !error.response ||
      error.code === 'ECONNABORTED' ||
      error.code === 'ETIMEDOUT' ||
      (error.response.status >= 500 && error.response.status < 600)
    );
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // Health check
  async checkHealth(): Promise<HealthResponse> {
    const response = await this.retryRequest(() =>
      this.client.get<HealthResponse>('/api/health')
    );
    return response.data;
  }

  // Generate video
  async generateVideo(request: VideoGenerationRequest): Promise<VideoGenerationResponse> {
    log.info('Generating video', {
      model: request.model,
      duration: request.duration,
      promptLength: request.prompt.length
    });

    const response = await this.client.post<VideoGenerationResponse>(
      '/api/videos/generate',
      request
    );

    log.info('Video generation complete', {
      requestId: response.data.data.requestId,
      videoUrl: response.data.data.video.url
    });

    return response.data;
  }

  // Estimate cost
  async estimateCost(duration: number, model: string): Promise<CostEstimateResponse> {
    const response = await this.retryRequest(() =>
      this.client.post<CostEstimateResponse>('/api/videos/estimate-cost', {
        duration,
        model,
      })
    );
    return response.data;
  }

  // Get available models
  async getModels(): Promise<ModelInfo[]> {
    const response = await this.retryRequest(() =>
      this.client.get<{ success: boolean; data: ModelInfo[] }>('/api/models')
    );
    return response.data.data;
  }

  // Get templates (if backend supports it)
  async getTemplates(): Promise<any[]> {
    try {
      const response = await this.retryRequest(() =>
        this.client.get<{ success: boolean; data: any[] }>('/api/templates')
      );
      return response.data.data;
    } catch (error) {
      // Fallback to local templates if API doesn't support it
      log.warn('Templates API not available, using local templates');
      return [];
    }
  }

  // Get platform stats
  async getStats(): Promise<{ videosGenerated: number; botsActive: number; totalRevenue: number }> {
    try {
      const response = await this.retryRequest(() =>
        this.client.get<{
          success: boolean;
          data: {
            videosGenerated: number;
            botsActive: number;
            totalRevenue: number;
          }
        }>('/api/stats')
      );
      log.info('Stats fetched', response.data.data);
      return response.data.data;
    } catch (error) {
      log.error('Failed to fetch stats', { error });
      // Return zeros on error
      return {
        videosGenerated: 0,
        botsActive: 0,
        totalRevenue: 0
      };
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for testing
export { APIClient };
