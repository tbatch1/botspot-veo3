// veo3-sdk.ts - Frontend SDK for Veo 3 API
// Install: npm install axios

import axios, { AxiosInstance, AxiosError } from 'axios';

// ============================================
// TYPES
// ============================================

export interface Veo3Config {
  apiUrl: string;
  apiKey?: string;
  timeout?: number;
}

export interface VideoGenerationRequest {
  prompt: string;
  model?: 'veo-3.0-generate-001' | 'veo-3-fast-generate-001';
  aspectRatio?: '16:9' | '9:16';
  resolution?: '720p' | '1080p';
  duration?: number;
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

export interface CostEstimateRequest {
  duration: number;
  model: string;
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

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
  pricePerSecond: string;
  maxDuration: number;
  resolutions: string[];
  aspectRatios: string[];
}

export interface Template {
  id: string;
  name: string;
  category: string;
  prompt: string;
  tags: string[];
  estimatedCost: string;
}

// ============================================
// ERROR CLASSES
// ============================================

export class Veo3SDKError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'Veo3SDKError';
  }
}

// ============================================
// VEO 3 SDK CLIENT
// ============================================

export class Veo3Client {
  private client: AxiosInstance;
  private config: Veo3Config;

  constructor(config: Veo3Config) {
    this.config = {
      timeout: 30000,
      ...config
    };

    this.client = axios.create({
      baseURL: this.config.apiUrl,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
      }
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        return this.handleError(error);
      }
    );
  }

  /**
   * Handle API errors
   */
  private handleError(error: AxiosError): never {
    if (error.response) {
      const data: any = error.response.data;
      throw new Veo3SDKError(
        data.error?.message || 'API request failed',
        data.error?.code || 'API_ERROR',
        error.response.status,
        data.error?.details
      );
    } else if (error.request) {
      throw new Veo3SDKError(
        'No response from server',
        'NETWORK_ERROR',
        undefined,
        { originalError: error.message }
      );
    } else {
      throw new Veo3SDKError(
        error.message,
        'REQUEST_ERROR',
        undefined,
        { originalError: error.message }
      );
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<any> {
    const response = await this.client.get('/api/health');
    return response.data;
  }

  /**
   * Generate a video
   */
  async generateVideo(request: VideoGenerationRequest): Promise<VideoGenerationResponse> {
    const response = await this.client.post('/api/videos/generate', request);
    return response.data;
  }

  /**
   * Estimate cost
   */
  async estimateCost(request: CostEstimateRequest): Promise<CostEstimateResponse> {
    const response = await this.client.post('/api/videos/estimate-cost', request);
    return response.data;
  }

  /**
   * Get available models
   */
  async getModels(): Promise<{ success: boolean; data: { models: ModelInfo[] } }> {
    const response = await this.client.get('/api/models');
    return response.data;
  }

  /**
   * Get templates
   */
  async getTemplates(): Promise<{ success: boolean; data: { templates: Template[] } }> {
    const response = await this.client.get('/api/templates');
    return response.data;
  }

  /**
   * Batch generate videos
   */
  async batchGenerate(videos: VideoGenerationRequest[], userId: string): Promise<any> {
    const response = await this.client.post('/api/videos/batch', {
      videos,
      userId
    });
    return response.data;
  }
}

// ============================================
// REACT HOOKS
// ============================================

import { useState, useEffect, useCallback } from 'react';

export interface UseVeo3Options {
  apiUrl: string;
  apiKey?: string;
  userId: string;
}

export interface UseVeo3Return {
  generateVideo: (request: Omit<VideoGenerationRequest, 'userId'>) => Promise<VideoGenerationResponse>;
  estimateCost: (duration: number, model: string) => Promise<CostEstimateResponse>;
  loading: boolean;
  error: Veo3SDKError | null;
  progress: number;
  result: VideoGenerationResponse | null;
}

/**
 * React hook for Veo 3 integration
 */
export function useVeo3(options: UseVeo3Options): UseVeo3Return {
  const [client] = useState(() => new Veo3Client({
    apiUrl: options.apiUrl,
    apiKey: options.apiKey
  }));

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Veo3SDKError | null>(null);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<VideoGenerationResponse | null>(null);

  const generateVideo = useCallback(async (request: Omit<VideoGenerationRequest, 'userId'>) => {
    setLoading(true);
    setError(null);
    setProgress(0);
    setResult(null);

    try {
      // Simulate progress during generation
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 3000);

      const response = await client.generateVideo({
        ...request,
        userId: options.userId
      });

      clearInterval(progressInterval);
      setProgress(100);
      setResult(response);
      setLoading(false);

      return response;
    } catch (err) {
      setError(err as Veo3SDKError);
      setLoading(false);
      setProgress(0);
      throw err;
    }
  }, [client, options.userId]);

  const estimateCost = useCallback(async (duration: number, model: string) => {
    try {
      return await client.estimateCost({ duration, model });
    } catch (err) {
      setError(err as Veo3SDKError);
      throw err;
    }
  }, [client]);

  return {
    generateVideo,
    estimateCost,
    loading,
    error,
    progress,
    result
  };
}

// ============================================
// REACT COMPONENT EXAMPLE
// ============================================

import React from 'react';

export const Veo3Generator: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState<'veo-3.0-generate-001' | 'veo-3-fast-generate-001'>('veo-3-fast-generate-001');
  const [duration, setDuration] = useState(8);
  const [estimatedCost, setEstimatedCost] = useState<string>('');

  const {
    generateVideo,
    estimateCost,
    loading,
    error,
    progress,
    result
  } = useVeo3({
    apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:3000',
    userId: 'user123' // Replace with actual user ID
  });

  // Auto-calculate cost when duration or model changes
  useEffect(() => {
    estimateCost(duration, model)
      .then(response => setEstimatedCost(response.data.estimatedCost))
      .catch(() => setEstimatedCost('Error'));
  }, [duration, model, estimateCost]);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      alert('Please enter a prompt');
      return;
    }

    try {
      await generateVideo({
        prompt,
        model,
        duration,
        aspectRatio: '16:9',
        resolution: '1080p'
      });
    } catch (err) {
      console.error('Generation failed:', err);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6">Generate Video with Veo 3</h2>

      {/* Prompt Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Video Prompt
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe your video scene..."
          className="w-full px-4 py-2 border rounded-lg"
          rows={4}
          disabled={loading}
        />
      </div>

      {/* Model Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Model
        </label>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value as any)}
          className="w-full px-4 py-2 border rounded-lg"
          disabled={loading}
        >
          <option value="veo-3-fast-generate-001">Veo 3 Fast ($0.40/sec)</option>
          <option value="veo-3.0-generate-001">Veo 3 Standard ($0.50/sec)</option>
        </select>
      </div>

      {/* Duration Slider */}
      <div className="mb-4">
        <label className="block text-sm font-medium mb-2">
          Duration: {duration} seconds
        </label>
        <input
          type="range"
          min="4"
          max="8"
          value={duration}
          onChange={(e) => setDuration(Number(e.target.value))}
          className="w-full"
          disabled={loading}
        />
      </div>

      {/* Cost Estimate */}
      <div className="mb-6 p-4 bg-gray-100 rounded-lg">
        <div className="text-sm text-gray-600">Estimated Cost</div>
        <div className="text-2xl font-bold text-green-600">{estimatedCost}</div>
      </div>

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={loading || !prompt.trim()}
        className="w-full py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {loading ? 'Generating...' : 'Generate Video'}
      </button>

      {/* Progress Bar */}
      {loading && (
        <div className="mt-4">
          <div className="flex justify-between text-sm mb-1">
            <span>Progress</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-4 p-4 bg-red-100 border border-red-400 rounded-lg">
          <div className="font-medium text-red-800">Error: {error.code}</div>
          <div className="text-sm text-red-600">{error.message}</div>
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="mt-6 p-4 bg-green-100 border border-green-400 rounded-lg">
          <div className="font-medium text-green-800 mb-2">✓ Video Generated!</div>
          <video
            src={result.data.video.url}
            controls
            className="w-full rounded-lg"
          />
          <div className="mt-4 text-sm">
            <div>Duration: {result.data.video.duration}s</div>
            <div>Resolution: {result.data.video.resolution}</div>
            <div>Cost: {result.data.metadata.estimatedCost}</div>
            <div>Generation Time: {(result.data.metadata.generationTimeMs / 1000).toFixed(1)}s</div>
          </div>
          <a
            href={result.data.video.url}
            download
            className="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Download Video
          </a>
        </div>
      )}
    </div>
  );
};

// ============================================
// VANILLA JS EXAMPLE (No React)
// ============================================

export class Veo3Manager {
  private client: Veo3Client;
  private callbacks: {
    onProgress?: (progress: number) => void;
    onSuccess?: (result: VideoGenerationResponse) => void;
    onError?: (error: Veo3SDKError) => void;
  };

  constructor(config: Veo3Config, callbacks = {}) {
    this.client = new Veo3Client(config);
    this.callbacks = callbacks;
  }

  async generate(request: VideoGenerationRequest) {
    try {
      // Simulate progress updates
      let progress = 0;
      const interval = setInterval(() => {
        progress = Math.min(progress + 10, 90);
        this.callbacks.onProgress?.(progress);
      }, 3000);

      const result = await this.client.generateVideo(request);

      clearInterval(interval);
      this.callbacks.onProgress?.(100);
      this.callbacks.onSuccess?.(result);

      return result;
    } catch (error) {
      this.callbacks.onError?.(error as Veo3SDKError);
      throw error;
    }
  }
}

// Example vanilla JS usage:
/*
const veo3 = new Veo3Manager(
  { apiUrl: 'http://localhost:3000' },
  {
    onProgress: (progress) => {
      document.getElementById('progress').style.width = progress + '%';
    },
    onSuccess: (result) => {
      document.getElementById('video').src = result.data.video.url;
    },
    onError: (error) => {
      alert('Error: ' + error.message);
    }
  }
);

veo3.generate({
  prompt: 'Trading charts rising',
  userId: 'user123'
});
*/

export default Veo3Client;