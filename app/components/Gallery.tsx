'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Video, Play, Download, Share2, Filter, Search, X } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { log } from '@/lib/logger';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';

interface VideoItem {
  id: string;
  title: string;
  thumbnail: string;
  videoUrl: string;
  duration: number;
  model: string;
  category: string;
  createdAt: Date;
  views: number;
}

// Production: Empty until real videos are generated
const mockVideos: VideoItem[] = [];

const categories = [
  { id: 'all', name: 'All Videos' },
  { id: 'bull-market', name: 'Bull Market' },
  { id: 'bear-market', name: 'Bear Market' },
  { id: 'risk-management', name: 'Risk Management' },
  { id: 'algo-trading', name: 'Algo Trading' },
  { id: 'market-analysis', name: 'Market Analysis' },
];

export function Gallery() {
  const [videos, setVideos] = useState<VideoItem[]>(mockVideos);
  const [filteredVideos, setFilteredVideos] = useState<VideoItem[]>(mockVideos);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    log.info('Gallery component mounted', { videoCount: videos.length });

    // Fetch videos from API
    const fetchVideos = async () => {
      try {
        setLoading(true);
        const fetchedVideos = await apiClient.getVideos(undefined, 50);
        setVideos(fetchedVideos);
        log.info('Videos loaded from API', { count: fetchedVideos.length });
      } catch (error) {
        log.error('Failed to load videos', { error });
      } finally {
        setLoading(false);
      }
    };

    fetchVideos();
  }, []);

  useEffect(() => {
    let filtered = videos;

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((v) => v.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter((v) =>
        v.title.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredVideos(filtered);
    log.debug('Gallery filtered', {
      category: selectedCategory,
      search: searchQuery,
      resultCount: filtered.length,
    });
  }, [selectedCategory, searchQuery, videos]);

  const handleVideoClick = (video: VideoItem) => {
    log.info('Video selected', { videoId: video.id, title: video.title });
    setSelectedVideo(video);
  };

  const handleShare = async (video: VideoItem) => {
    const shareUrl = `${window.location.origin}/videos/${video.id}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
      log.info('Video URL copied', { videoId: video.id, shareUrl });
      toast.success('Link Copied!', {
        description: 'Video URL copied to clipboard',
      });
    } catch (err) {
      log.error('Failed to copy URL', { error: err, videoId: video.id });
      toast.error('Copy Failed', {
        description: 'Could not copy video URL to clipboard',
      });
    }
  };

  const handleDownload = (video: VideoItem) => {
    try {
      log.info('Video download initiated', { videoId: video.id, videoUrl: video.videoUrl });
      window.open(video.videoUrl, '_blank');
      toast.success('Download Started', {
        description: 'Opening video in new tab',
      });
    } catch (err) {
      log.error('Video download failed', { error: err, videoId: video.id });
      toast.error('Download Failed', {
        description: 'Could not open video',
      });
    }
  };

  return (
    <section className="py-12 px-4 bg-white">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
            Video Gallery
          </h2>
          <p className="text-lg text-gray-600">
            Browse your generated trading bot demo videos
          </p>
        </motion.div>

        {/* Filters */}
        <div className="mb-8 space-y-4">
          {/* Search */}
          <div className="relative max-w-md mx-auto">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search videos..."
              className="pl-10"
            />
          </div>

          {/* Category filters */}
          <div className="flex flex-wrap gap-2 justify-center">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        <div className="mb-6 text-center">
          <Badge variant="secondary" className="text-sm">
            {filteredVideos.length} {filteredVideos.length === 1 ? 'video' : 'videos'}
          </Badge>
        </div>

        {/* Video grid */}
        <motion.div
          layout
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          <AnimatePresence>
            {filteredVideos.map((video, index) => (
              <motion.div
                key={video.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
              >
                <Card className="overflow-hidden hover:shadow-xl transition-shadow duration-300 cursor-pointer group">
                  {/* Thumbnail */}
                  <div
                    className="relative aspect-video bg-gray-900 overflow-hidden"
                    onClick={() => handleVideoClick(video)}
                  >
                    <img
                      src={video.thumbnail}
                      alt={video.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                      <div className="w-16 h-16 bg-white/90 rounded-full flex items-center justify-center">
                        <Play className="w-8 h-8 text-blue-600 ml-1" />
                      </div>
                    </div>
                    <div className="absolute bottom-2 right-2 bg-black/80 text-white px-2 py-1 rounded text-xs">
                      {video.duration}s
                    </div>
                  </div>

                  {/* Info */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
                      {video.title}
                    </h3>
                    <div className="flex items-center justify-between text-sm text-gray-600 mb-3">
                      <span>{video.views} views</span>
                      <span>{new Date(video.createdAt).toLocaleDateString()}</span>
                    </div>
                    <div className="flex items-center gap-2 mb-3">
                      <Badge variant={video.model.includes('fast') ? 'default' : 'secondary'}>
                        {video.model.includes('fast') ? 'Fast' : 'Standard'}
                      </Badge>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleShare(video);
                        }}
                      >
                        <Share2 className="w-4 h-4 mr-1" />
                        Share
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(video);
                        }}
                      >
                        <Download className="w-4 h-4 mr-1" />
                        Download
                      </Button>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>

        {/* Empty state */}
        {filteredVideos.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16"
          >
            <Video className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No videos yet</h3>
            <p className="text-gray-600 mb-4">
              {searchQuery || selectedCategory !== 'all'
                ? 'No videos match your filters. Try adjusting your search or category.'
                : 'Start generating trading bot demo videos in the Studio!'}
            </p>
            {!searchQuery && selectedCategory === 'all' && (
              <Button
                onClick={() => window.location.href = '/'}
                className="mt-4"
              >
                Go to Studio
              </Button>
            )}
          </motion.div>
        )}
      </div>

      {/* Video modal */}
      <AnimatePresence>
        {selectedVideo && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedVideo(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="relative w-full max-w-4xl bg-gray-900 rounded-xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setSelectedVideo(null)}
                className="absolute top-4 right-4 z-10 w-10 h-10 bg-black/50 hover:bg-black/70 rounded-full flex items-center justify-center text-white transition-colors"
              >
                <X className="w-6 h-6" />
              </button>

              <video
                src={selectedVideo.videoUrl}
                controls
                autoPlay
                className="w-full aspect-video"
              />

              <div className="p-6 bg-gray-900 text-white">
                <h3 className="text-2xl font-bold mb-2">{selectedVideo.title}</h3>
                <div className="flex items-center gap-4 text-sm text-gray-400 mb-4">
                  <span>{selectedVideo.views} views</span>
                  <span>•</span>
                  <span>{new Date(selectedVideo.createdAt).toLocaleDateString()}</span>
                  <span>•</span>
                  <span>{selectedVideo.duration}s</span>
                </div>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => handleShare(selectedVideo)}
                  >
                    <Share2 className="w-4 h-4 mr-2" />
                    Share
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => handleDownload(selectedVideo)}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
