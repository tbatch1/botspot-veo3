'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import { PromptPanel } from './PromptPanel';
import { CanvasPanel } from './CanvasPanel';
import { ConfigPanel } from './ConfigPanel';
import type { Template } from '@/data/templates';
import { validatePrompt } from '@/lib/utils';
import { log } from '@/lib/logger';
import { apiClient } from '@/lib/api-client';

export function Studio() {
  const [prompt, setPrompt] = useState('');
  const [model, setModel] = useState('veo-3.0-fast-generate-001');
  const [duration, setDuration] = useState(8);
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [resolution, setResolution] = useState('1080p');
  const [status, setStatus] = useState<'idle' | 'generating' | 'success' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [videoUrl, setVideoUrl] = useState<string>();
  const [error, setError] = useState<string>();
  const [backendOnline, setBackendOnline] = useState(false);
  const [liveMode, setLiveMode] = useState(true);

  // Check backend health on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const health = await apiClient.checkHealth();
        setBackendOnline(health.status === 'healthy' || health.status === 'partial');

        if (health.apiKey === 'missing') {
          toast.warning('API Key Not Configured', {
            description: 'Video generation will use demo mode. Add GEMINI_API_KEY to enable real generation.',
            duration: 5000,
          });
        }

        log.info('Backend health check', { status: health.status, apiKey: health.apiKey });
      } catch (err) {
        setBackendOnline(false);
        toast.error('Backend Offline', {
          description: 'Could not connect to API server. Make sure backend is running on port 4000.',
          duration: 10000,
        });
        log.error('Backend health check failed', { error: err });
      }
    };

    checkBackend();
  }, []);

  const handleTemplateSelect = (template: Template) => {
    log.info('Template applied', { template });
    setPrompt(template.prompt);
    setDuration(template.duration);
    setModel(template.model);
  };

  const handleGenerate = async () => {
    // Validate prompt
    const validation = validatePrompt(prompt);
    if (!validation.valid) {
      setError(validation.error);
      setStatus('error');
      toast.error('Invalid Prompt', { description: validation.error });
      return;
    }

    // Check backend connection
    if (!backendOnline) {
      toast.error('Backend Offline', {
        description: 'Cannot generate video. Please ensure the backend server is running.',
      });
      return;
    }

    log.info('Video generation started', {
      prompt: prompt.substring(0, 100),
      model,
      duration,
      aspectRatio,
      resolution,
    });

    setStatus('generating');
    setProgress(0);
    setError(undefined);

    // Show generating toast
    toast.info('Generating Video', {
      description: 'Your trading bot demo video is being created...',
    });

    // Simulate progress with gradual increases
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 95) {
          clearInterval(progressInterval);
          return 95;
        }
        return prev + Math.random() * 8;
      });
    }, 600);

    try {
      // Call real API
      const response = await apiClient.generateVideo({
        prompt,
        model: model as any,
        aspectRatio: aspectRatio as any,
        resolution: resolution as any,
        duration,
        optimizePrompt: true,
        mock: !liveMode,
        userId: 'demo-user',
      });

      clearInterval(progressInterval);
      setProgress(100);

      // Set video URL from response
      setVideoUrl(response.data.video.url);
      setStatus('success');

      toast.success('Video Generated!', {
        description: `Your ${duration}s trading bot demo is ready to view.`,
      });

      log.info('Video generation complete', {
        requestId: response.data.requestId,
        videoUrl: response.data.video.url,
      });
    } catch (err: any) {
      clearInterval(progressInterval);
      const errorMessage = err.response?.data?.error?.message || err.message || 'Failed to generate video';
      setError(errorMessage);
      setStatus('error');

      toast.error('Generation Failed', {
        description: errorMessage,
        duration: 8000,
      });

      log.error('Video generation failed', { error: err });
    }
  };

  const handleRetry = () => {
    setStatus('idle');
    setProgress(0);
    setError(undefined);
    setVideoUrl(undefined);
  };

  const canGenerate = validatePrompt(prompt).valid;

  return (
    <section className="py-12 px-4 bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            Video Generation Studio
          </h2>
          <p className="text-lg text-gray-600">
            Create professional trading bot demo videos in seconds
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left panel - Prompt Builder */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="lg:col-span-3"
          >
            <PromptPanel
              prompt={prompt}
              onPromptChange={setPrompt}
              onTemplateSelect={handleTemplateSelect}
            />
          </motion.div>

          {/* Center panel - Canvas */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-6"
          >
            <CanvasPanel
              status={status}
              progress={progress}
              videoUrl={videoUrl}
              error={error}
              onRetry={handleRetry}
            />
          </motion.div>

          {/* Right panel - Configuration */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="lg:col-span-3"
          >
            <ConfigPanel
              model={model}
              duration={duration}
              aspectRatio={aspectRatio}
              resolution={resolution}
              onModelChange={setModel}
              onDurationChange={setDuration}
              onAspectRatioChange={setAspectRatio}
              onResolutionChange={setResolution}
              onGenerate={handleGenerate}
              isGenerating={status === 'generating'}
              canGenerate={canGenerate}
              liveMode={liveMode}
              onToggleLiveMode={setLiveMode}
            />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
