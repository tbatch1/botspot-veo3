'use client';

import React, { useRef, useState, useEffect } from 'react';
import type { Scene } from '../../types/sequence';

interface PreviewPlayerProps {
  scenes: Scene[];
  currentSceneNumber?: number;
  onSceneChange?: (sceneNumber: number) => void;
  className?: string;
}

export function PreviewPlayer({
  scenes,
  currentSceneNumber,
  onSceneChange,
  className = '',
}: PreviewPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.8);
  const [isMuted, setIsMuted] = useState(false);

  const completedScenes = scenes.filter((s) => s.status === 'completed' && s.result?.videoUrl);
  const currentScene = currentSceneNumber
    ? completedScenes.find((s) => s.sceneNumber === currentSceneNumber)
    : completedScenes[0];

  // Update video source when scene changes
  useEffect(() => {
    if (videoRef.current && currentScene?.result?.videoUrl) {
      videoRef.current.src = currentScene.result.videoUrl;
      videoRef.current.load();
    }
  }, [currentScene]);

  // Update volume
  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.volume = volume;
      videoRef.current.muted = isMuted;
    }
  }, [volume, isMuted]);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    }
  };

  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = Number(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const handleNextScene = () => {
    if (currentScene) {
      const currentIndex = completedScenes.findIndex((s) => s.sceneNumber === currentScene.sceneNumber);
      if (currentIndex < completedScenes.length - 1) {
        const nextScene = completedScenes[currentIndex + 1];
        onSceneChange?.(nextScene.sceneNumber);
      }
    }
  };

  const handlePrevScene = () => {
    if (currentScene) {
      const currentIndex = completedScenes.findIndex((s) => s.sceneNumber === currentScene.sceneNumber);
      if (currentIndex > 0) {
        const prevScene = completedScenes[currentIndex - 1];
        onSceneChange?.(prevScene.sceneNumber);
      }
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  if (completedScenes.length === 0) {
    return (
      <div className={`bg-gray-900 rounded-lg flex items-center justify-center ${className}`} style={{ minHeight: '400px' }}>
        <div className="text-center text-gray-400">
          <svg className="mx-auto h-16 w-16 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <p className="text-lg font-medium">No videos to preview yet</p>
          <p className="text-sm mt-2">Generate scenes to see them here</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-gray-900 rounded-lg overflow-hidden ${className}`}>
      {/* Video Player */}
      <div className="relative bg-black" style={{ aspectRatio: currentScene?.config.aspectRatio === '9:16' ? '9/16' : currentScene?.config.aspectRatio === '1:1' ? '1/1' : '16/9' }}>
        <video
          ref={videoRef}
          className="w-full h-full"
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={() => setIsPlaying(false)}
        />

        {/* Scene Info Overlay */}
        <div className="absolute top-4 left-4 bg-black bg-opacity-75 text-white px-3 py-2 rounded-lg text-sm">
          <p className="font-semibold">Scene {currentScene?.sceneNumber}</p>
          <p className="text-xs opacity-75">{currentScene?.config.duration}s · {currentScene?.config.resolution}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-800 p-4">
        {/* Progress Bar */}
        <div className="mb-3">
          <input
            type="range"
            min="0"
            max={duration || 0}
            step="0.1"
            value={currentTime}
            onChange={handleSeek}
            className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
            style={{
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${(currentTime / duration) * 100}%, #4b5563 ${(currentTime / duration) * 100}%, #4b5563 100%)`,
            }}
          />
          <div className="flex items-center justify-between text-xs text-gray-400 mt-1">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Playback Controls */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Previous Scene */}
            <button
              onClick={handlePrevScene}
              disabled={!currentScene || completedScenes.findIndex((s) => s.sceneNumber === currentScene.sceneNumber) === 0}
              className="p-2 text-white hover:bg-gray-700 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              title="Previous scene"
            >
              <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                <path d="M11.5 8.5a.5.5 0 0 1-.5.5H6.707l2.147 2.146a.5.5 0 0 1-.708.708l-3-3a.5.5 0 0 1 0-.708l3-3a.5.5 0 1 1 .708.708L6.707 8H11a.5.5 0 0 1 .5.5z" />
              </svg>
            </button>

            {/* Play/Pause */}
            <button
              onClick={handlePlayPause}
              className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? (
                <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M5.5 3.5A1.5 1.5 0 0 1 7 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5zm5 0A1.5 1.5 0 0 1 12 5v6a1.5 1.5 0 0 1-3 0V5a1.5 1.5 0 0 1 1.5-1.5z" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                  <path d="m11.596 8.697-6.363 3.692c-.54.313-1.233-.066-1.233-.697V4.308c0-.63.692-1.01 1.233-.696l6.363 3.692a.802.802 0 0 1 0 1.393z" />
                </svg>
              )}
            </button>

            {/* Next Scene */}
            <button
              onClick={handleNextScene}
              disabled={!currentScene || completedScenes.findIndex((s) => s.sceneNumber === currentScene.sceneNumber) === completedScenes.length - 1}
              className="p-2 text-white hover:bg-gray-700 rounded transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
              title="Next scene"
            >
              <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                <path d="M4.5 7.5a.5.5 0 0 0 0 1h4.793l-2.147 2.146a.5.5 0 0 0 .708.708l3-3a.5.5 0 0 0 0-.708l-3-3a.5.5 0 1 0-.708.708L9.293 8H4.5z" />
              </svg>
            </button>
          </div>

          {/* Volume Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMuted(!isMuted)}
              className="p-2 text-white hover:bg-gray-700 rounded transition-colors"
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              {isMuted || volume === 0 ? (
                <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06zM10.5 5.5a.5.5 0 0 1 .707 0l1.146 1.147 1.146-1.147a.5.5 0 0 1 .708.708L12.707 7.5l1.5 1.5a.5.5 0 0 1-.708.708l-1.146-1.147-1.146 1.147a.5.5 0 0 1-.708-.708l1.147-1.146-1.147-1.147a.5.5 0 0 1 0-.707z" />
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                  <path d="M11.536 14.01A8.473 8.473 0 0 0 14.026 8a8.473 8.473 0 0 0-2.49-6.01l-.708.707A7.476 7.476 0 0 1 13.025 8c0 2.071-.84 3.946-2.197 5.303l.708.707z" />
                  <path d="M10.121 12.596A6.48 6.48 0 0 0 12.025 8a6.48 6.48 0 0 0-1.904-4.596l-.707.707A5.483 5.483 0 0 1 11.025 8a5.483 5.483 0 0 1-1.61 3.89l.706.706z" />
                  <path d="M8.707 11.182A4.486 4.486 0 0 0 10.025 8a4.486 4.486 0 0 0-1.318-3.182L8 5.525A3.489 3.489 0 0 1 9.025 8 3.49 3.49 0 0 1 8 10.475l.707.707zM6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06z" />
                </svg>
              )}
            </button>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={isMuted ? 0 : volume}
              onChange={(e) => {
                setVolume(Number(e.target.value));
                if (Number(e.target.value) > 0) setIsMuted(false);
              }}
              className="w-20 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>

        {/* Scene Navigation */}
        {completedScenes.length > 1 && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-400 mb-2">Quick Scene Navigation</p>
            <div className="flex gap-2 overflow-x-auto">
              {completedScenes.map((scene) => (
                <button
                  key={scene.sceneNumber}
                  onClick={() => onSceneChange?.(scene.sceneNumber)}
                  className={`
                    flex-shrink-0 px-3 py-1 rounded text-xs font-medium transition-colors
                    ${currentScene?.sceneNumber === scene.sceneNumber
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'}
                  `}
                >
                  Scene {scene.sceneNumber}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
