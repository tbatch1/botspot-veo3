'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Video, Download } from 'lucide-react';
import { api } from '@/lib/api';

interface Scene {
    id: number;
    visual_prompt: string;
    motion_prompt: string;
    duration: number;
    image_path?: string;
    video_path?: string;
}

interface VideoGenerationPanelProps {
    scenes: Scene[];
    status: string;
    finalVideoPath?: string;
    onApproveFinal: () => void;
    isVisible: boolean;
}

export default function VideoGenerationPanel({
    scenes,
    status,
    finalVideoPath,
    onApproveFinal,
    isVisible
}: VideoGenerationPanelProps) {
    if (!isVisible) return null;

    const completedVideos = scenes.filter(s => s.video_path).length;
    const totalScenes = scenes.length;
    const progress = (completedVideos / totalScenes) * 100;
    const isGenerating = status === 'generating_videos';
    const isComplete = status === 'videos_complete';
    const isAssembling = status === 'assembling';
    const isFinalComplete = status === 'completed';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="w-full max-w-6xl mx-auto p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl border border-emerald-500/30 rounded-lg shadow-2xl"
        >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-700/50">
                <Video className="w-6 h-6 text-emerald-400" />
                <h2 className="text-2xl font-bold text-white">
                    {isFinalComplete ? 'Final Video' : 'Video Generation'}
                </h2>
                {(isGenerating || isAssembling) && (
                    <Loader2 className="w-5 h-5 text-emerald-400 animate-spin ml-2" />
                )}
                <span className="ml-auto px-3 py-1 bg-emerald-500/20 text-emerald-400 text-sm rounded-full border border-emerald-500/30">
                    {isFinalComplete ? 'Complete' : 'Approval Gate 3'}
                </span>
            </div>

            {/* Progress Bar */}
            {!isFinalComplete && (
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-slate-400">
                            {isGenerating ? 'Animating videos...' : isAssembling ? 'Assembling final video...' : 'All clips generated'}
                        </span>
                        {!isAssembling && (
                            <span className="text-sm font-bold text-emerald-400">
                                {completedVideos} / {totalScenes}
                            </span>
                        )}
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: isAssembling ? '100%' : `${progress}%` }}
                            transition={{ duration: 0.5, ease: 'easeOut' }}
                            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500"
                        />
                    </div>
                </div>
            )}

            {/* Final Video Player */}
            {isFinalComplete && finalVideoPath && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mb-6"
                >
                    <div className="relative aspect-video bg-black rounded-lg overflow-hidden border-2 border-emerald-500/50 shadow-2xl">
                        <video
                            controls
                            autoPlay
                            loop
                            className="w-full h-full"
                            src={api.getAssetUrl(finalVideoPath)}
                        >
                            Your browser does not support the video tag.
                        </video>
                    </div>

                    {/* Download Button */}
                    <div className="mt-4 flex justify-center">
                        <a
                            href={api.getAssetUrl(finalVideoPath)}
                            download
                            className="flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-lg shadow-lg transition-colors"
                        >
                            <Download className="w-5 h-5" />
                            Download Final Video
                        </a>
                    </div>
                </motion.div>
            )}

            {/* Video Clips Grid */}
            {!isFinalComplete && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                    <AnimatePresence mode="popLayout">
                        {scenes.map((scene) => (
                            <motion.div
                                key={scene.id}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                className="relative group"
                            >
                                <div className="aspect-video bg-slate-800/50 rounded-lg border border-slate-700/30 overflow-hidden">
                                    {scene.video_path ? (
                                        <>
                                            <video
                                                src={api.getAssetUrl(scene.video_path)}
                                                className="w-full h-full object-cover"
                                                muted
                                                loop
                                                onMouseEnter={(e) => e.currentTarget.play()}
                                                onMouseLeave={(e) => e.currentTarget.pause()}
                                            />
                                            <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-1 bg-emerald-500/90 rounded text-xs font-bold text-white">
                                                <CheckCircle2 className="w-3 h-3" />
                                                Complete
                                            </div>
                                        </>
                                    ) : (
                                        <div className="w-full h-full flex flex-col items-center justify-center">
                                            {scene.image_path ? (
                                                <>
                                                    <img
                                                        src={api.getAssetUrl(scene.image_path)}
                                                        alt={`Scene ${scene.id}`}
                                                        className="w-full h-full object-cover opacity-50"
                                                    />
                                                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/50">
                                                        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mb-2" />
                                                        <span className="text-xs text-slate-300">Animating...</span>
                                                    </div>
                                                </>
                                            ) : (
                                                <span className="text-xs text-slate-500">Waiting...</span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Scene Info */}
                                <div className="mt-2 px-2">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-xs font-bold text-emerald-400">Scene {scene.id}</span>
                                        <span className="text-xs text-slate-500">{scene.duration}s</span>
                                    </div>
                                    <p className="text-xs text-slate-400 line-clamp-2">{scene.motion_prompt}</p>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Approve Assembly Button - Only show when videos complete */}
            {isComplete && !isAssembling && !isFinalComplete && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-center pt-6 border-t border-slate-700/50"
                >
                    <button
                        onClick={onApproveFinal}
                        className="group flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-bold rounded-lg shadow-lg hover:shadow-emerald-500/50 transition-all"
                    >
                        <CheckCircle2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                        <span>Approve Videos & Assemble Final</span>
                    </button>
                </motion.div>
            )}

            {/* Info Notices */}
            {isComplete && !isFinalComplete && (
                <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-center">
                    <p className="text-sm text-emerald-300">
                        Clicking approve will combine all clips with audio into the final commercial (~15 seconds)
                    </p>
                </div>
            )}

            {isFinalComplete && (
                <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-center">
                    <p className="text-sm text-emerald-300">
                        Your commercial is ready! Preview above or download to share.
                    </p>
                </div>
            )}
        </motion.div>
    );
}
