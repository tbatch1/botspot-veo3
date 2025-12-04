'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Video, Play, Download, Share2, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { log } from '@/lib/logger';

interface CanvasPanelProps {
  status: 'idle' | 'generating' | 'success' | 'error';
  progress: number;
  videoUrl?: string;
  error?: string;
  onRetry?: () => void;
}

export function CanvasPanel({ status, progress, videoUrl, error, onRetry }: CanvasPanelProps) {
  const handleDownload = () => {
    if (videoUrl) {
      log.info('Video download initiated', { videoUrl });
      window.open(videoUrl, '_blank');
    }
  };

  const handleShare = async () => {
    if (videoUrl) {
      log.info('Video share initiated', { videoUrl });
      try {
        await navigator.clipboard.writeText(videoUrl);
        alert('Video URL copied to clipboard!');
      } catch (err) {
        log.error('Failed to copy URL', { error: err });
      }
    }
  };

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Video className="w-5 h-5 text-blue-600" />
          Preview Canvas
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col h-[calc(100%-80px)]">
        <div className="flex-1 bg-gray-900 rounded-xl overflow-hidden relative flex items-center justify-center aspect-video max-h-[520px] mx-auto w-full">
          <AnimatePresence mode="wait">
            {/* Idle state */}
            {status === 'idle' && (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center p-8"
              >
                <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl flex items-center justify-center">
                  <Play className="w-12 h-12 text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  Ready to Create
                </h3>
                <p className="text-gray-400">
                  Configure your video and click Generate to begin
                </p>
              </motion.div>
            )}

            {/* Generating state */}
            {status === 'generating' && (
              <motion.div
                key="generating"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center p-8 w-full"
              >
                {/* Animated spinner */}
                <div className="relative w-32 h-32 mx-auto mb-6">
                  <motion.div
                    className="absolute inset-0 rounded-full bg-gradient-to-r from-blue-600 to-purple-600"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                    style={{
                      WebkitMask: 'radial-gradient(farthest-side,#0000 calc(100% - 8px),#000 0)',
                      mask: 'radial-gradient(farthest-side,#0000 calc(100% - 8px),#000 0)',
                    }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Video className="w-12 h-12 text-white" />
                  </div>
                </div>

                <h3 className="text-xl font-semibold text-white mb-4">
                  Generating Your Video
                </h3>

                {/* Progress bar */}
                <div className="max-w-md mx-auto mb-3">
                  <Progress value={progress} max={100} className="h-2" />
                </div>
                <p className="text-sm text-gray-400 mb-6">{progress}% Complete</p>

                {/* Status messages */}
                <div className="space-y-2 text-sm text-gray-300">
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: progress > 0 ? 1 : 0.3, x: 0 }}
                    className="flex items-center justify-center gap-2"
                  >
                    {progress > 20 ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <div className="w-4 h-4 border-2 border-gray-600 rounded-full" />
                    )}
                    Analyzing prompt...
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: progress > 20 ? 1 : 0.3, x: 0 }}
                    className="flex items-center justify-center gap-2"
                  >
                    {progress > 60 ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <div className="w-4 h-4 border-2 border-gray-600 rounded-full" />
                    )}
                    Generating frames...
                  </motion.div>
                  <motion.div
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: progress > 60 ? 1 : 0.3, x: 0 }}
                    className="flex items-center justify-center gap-2"
                  >
                    {progress > 90 ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : (
                      <div className="w-4 h-4 border-2 border-gray-600 rounded-full" />
                    )}
                    Finalizing video...
                  </motion.div>
                </div>
              </motion.div>
            )}

            {/* Success state */}
            {status === 'success' && videoUrl && (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full h-full"
              >
                <video
                  src={videoUrl}
                  controls
                  autoPlay
                  loop
                  className="w-full h-full object-contain"
                />
              </motion.div>
            )}

            {/* Error state */}
            {status === 'error' && (
              <motion.div
                key="error"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-center p-8 max-w-lg mx-auto"
              >
                <div className="w-24 h-24 mx-auto mb-6 bg-red-500/20 rounded-2xl flex items-center justify-center">
                  <AlertCircle className="w-12 h-12 text-red-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">
                  Generation Failed
                </h3>
                <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-4 mb-6">
                  <p className="text-red-200 text-sm mb-2 font-mono">
                    {error || 'An error occurred while generating your video'}
                  </p>
                  <p className="text-red-300/70 text-xs">
                    Check backend logs for detailed error information
                  </p>
                </div>
                {onRetry && (
                  <Button onClick={onRetry} variant="danger" size="lg">
                    <AlertCircle className="w-4 h-4 mr-2" />
                    Try Again
                  </Button>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Action buttons */}
        {status === 'success' && videoUrl && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3 mt-4"
          >
            <Button onClick={handleDownload} variant="outline" className="flex-1" size="lg">
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
            <Button onClick={handleShare} variant="outline" className="flex-1" size="lg">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}
