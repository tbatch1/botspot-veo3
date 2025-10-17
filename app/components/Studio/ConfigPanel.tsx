'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings, Zap, Star, DollarSign } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { calculateCost, formatCurrency, cn } from '@/lib/utils';
import { log } from '@/lib/logger';

interface ConfigPanelProps {
  model: string;
  duration: number;
  aspectRatio: string;
  resolution: string;
  onModelChange: (model: string) => void;
  onDurationChange: (duration: number) => void;
  onAspectRatioChange: (ratio: string) => void;
  onResolutionChange: (resolution: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
  canGenerate: boolean;
  liveMode: boolean;
  onToggleLiveMode: (live: boolean) => void;
}

export function ConfigPanel({
  model,
  duration,
  aspectRatio,
  resolution,
  onModelChange,
  onDurationChange,
  onAspectRatioChange,
  onResolutionChange,
  onGenerate,
  isGenerating,
  canGenerate,
  liveMode,
  onToggleLiveMode,
}: ConfigPanelProps) {
  const cost = calculateCost(duration, model);

  const models = [
    {
      id: 'veo-3.0-fast-generate-001',
      name: 'Veo 3 Fast',
      description: 'Optimized for speed',
      price: '$0.15/sec',
      icon: <Zap className="w-5 h-5" />,
      color: 'from-blue-500 to-blue-600',
    },
    {
      id: 'veo-3.0-generate-001',
      name: 'Veo 3 Standard',
      description: 'Best quality output',
      price: '$0.40/sec',
      icon: <Star className="w-5 h-5" />,
      color: 'from-purple-500 to-purple-600',
    },
  ];

  const handleGenerate = () => {
    log.info('Generate button clicked', {
      model,
      duration,
      aspectRatio,
      resolution,
      estimatedCost: cost,
    });
    onGenerate();
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-blue-600" />
          Configuration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Model selection */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-3 block">
            Model
          </label>
          <div className="grid gap-3">
            {models.map((m) => (
              <motion.button
                key={m.id}
                onClick={() => onModelChange(m.id)}
                className={cn(
                  'relative p-4 rounded-xl border-2 text-left transition-all duration-200',
                  model === m.id
                    ? 'border-blue-500 bg-blue-50 shadow-lg'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {model === m.id && (
                  <div className="absolute top-2 right-2">
                    <Badge variant="default" className="text-xs">Selected</Badge>
                  </div>
                )}
                <div className="flex items-start gap-3">
                  <div className={cn(
                    'w-12 h-12 rounded-lg bg-gradient-to-br flex items-center justify-center text-white',
                    m.color
                  )}>
                    {m.icon}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{m.name}</h4>
                    <p className="text-sm text-gray-600">{m.description}</p>
                    <p className="text-sm font-medium text-blue-600 mt-1">{m.price}</p>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Duration slider */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-medium text-gray-700">
              Duration
            </label>
            <Badge variant="secondary">{duration} seconds</Badge>
          </div>
          <input
            type="range"
            min="8"
            max="8"
            step="1"
            value={duration}
            onChange={(e) => onDurationChange(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
            disabled
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>4s</span>
            <span>6s</span>
            <span>8s</span>
          </div>
        </div>

        {/* Aspect ratio */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-3 block">
            Aspect Ratio
          </label>
          <div className="grid grid-cols-1 gap-3">
            {[
              { value: '16:9', label: 'Landscape', icon: '▬' },
            ].map((ratio) => (
              <button
                key={ratio.value}
                onClick={() => onAspectRatioChange(ratio.value)}
                className={cn(
                  'p-3 rounded-lg border-2 text-center transition-all duration-200',
                  aspectRatio === ratio.value
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <div className="text-2xl mb-1">{ratio.icon}</div>
                <div className="text-sm font-medium">{ratio.label}</div>
                <div className="text-xs text-gray-500">{ratio.value}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Resolution */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-3 block">
            Resolution
          </label>
          <div className="grid grid-cols-2 gap-3">
            {['720p', '1080p'].map((res) => (
              <button
                key={res}
                onClick={() => onResolutionChange(res)}
                className={cn(
                  'p-3 rounded-lg border-2 text-center transition-all duration-200',
                  resolution === res
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                )}
              >
                <div className="text-sm font-semibold">{res}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Cost estimate */}
        <div className="p-4 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl border-2 border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2 text-gray-700">
              <DollarSign className="w-5 h-5 text-blue-600" />
              <span className="font-medium">Estimated Cost</span>
            </div>
          </div>
          <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
            {formatCurrency(cost)}
          </div>
          <div className="text-xs text-gray-600 mt-1">
            {duration}s × {model === 'veo-3.0-fast-generate-001' ? '$0.15' : '$0.40'}/sec
          </div>
        </div>

        {/* Live/Test toggle */}
        <div className="mt-4 p-4 rounded-xl border-2" style={{ borderColor: liveMode ? '#22c55e' : '#cbd5e1', background: liveMode ? '#ecfdf5' : '#f8fafc' }}>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium text-gray-800">Live mode</div>
              <div className="text-xs text-gray-600">{liveMode ? 'Real API calls will incur cost.' : 'Safe test mode with mock videos (no cost).'}
              </div>
            </div>
            <button
              type="button"
              onClick={() => onToggleLiveMode(!liveMode)}
              className={cn(
                'inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none',
                liveMode ? 'bg-green-500' : 'bg-gray-300'
              )}
              aria-pressed={liveMode}
              aria-label="Toggle live mode"
            >
              <span
                className={cn(
                  'inline-block h-5 w-5 transform rounded-full bg-white transition-transform',
                  liveMode ? 'translate-x-5' : 'translate-x-1'
                )}
              />
            </button>
          </div>
        </div>
      </CardContent>

      <CardFooter>
        <Button
          onClick={handleGenerate}
          disabled={!canGenerate || isGenerating}
          loading={isGenerating}
          size="xl"
          className="w-full"
        >
          {isGenerating ? 'Generating...' : 'Generate Video'}
        </Button>
      </CardFooter>

      <style jsx global>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 20px;
          height: 20px;
          background: linear-gradient(135deg, #0066FF, #6B46FF);
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 2px 8px rgba(0, 102, 255, 0.4);
        }
        .slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          background: linear-gradient(135deg, #0066FF, #6B46FF);
          cursor: pointer;
          border-radius: 50%;
          box-shadow: 0 2px 8px rgba(0, 102, 255, 0.4);
          border: none;
        }
      `}</style>
    </Card>
  );
}
