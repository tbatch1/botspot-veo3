'use client';

import { useStore } from '@/lib/store';
import { Play, Image as ImageIcon, Music, Film, X, RotateCcw, Home } from 'lucide-react';
import { api } from '@/lib/api';

export default function Storyboard() {
    const { project, startGeneration, isLoading, error, stopPolling, reset } = useStore();

    if (!project || !project.script) return null;

    const hasError = !!error;
    const isCompleted = project.status === 'completed';
    const isFailed = project.status === 'failed';

    return (
        <div className="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            {/* Error Display */}
            {hasError && (
                <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4 text-red-200 flex items-start gap-3">
                    <div className="flex-1">
                        <h3 className="font-semibold mb-1">Generation Failed</h3>
                        <p className="text-sm text-red-300">{error}</p>
                    </div>
                    <button
                        onClick={() => reset()}
                        className="text-red-400 hover:text-red-300 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>
            )}

            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">Campaign Plan</h2>
                    <p className="text-slate-400">Review the script and scenes before production.</p>
                </div>

                {/* Action Buttons */}
                <div className="flex items-center gap-3">
                    {/* Start Over Button */}
                    <button
                        onClick={() => reset()}
                        className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 flex items-center gap-2"
                    >
                        <Home className="w-4 h-4" /> Start Over
                    </button>

                    {/* Cancel Button (show during production) */}
                    {isLoading && !hasError && (
                        <button
                            onClick={() => stopPolling()}
                            className="bg-red-600 hover:bg-red-500 text-white px-6 py-3 rounded-lg font-medium transition-all hover:scale-105 flex items-center gap-2"
                        >
                            <X className="w-4 h-4" /> Cancel
                        </button>
                    )}

                    {/* Main Production Button */}
                    {!isCompleted && (
                        <button
                            onClick={() => startGeneration()}
                            disabled={isLoading && !hasError}
                            className="bg-green-600 hover:bg-green-500 text-white px-8 py-3 rounded-lg font-bold shadow-lg shadow-green-900/20 transition-all hover:scale-105 disabled:opacity-50 disabled:scale-100 flex items-center gap-2"
                        >
                            {isLoading && !hasError ? (
                                <>Producing... <Film className="w-5 h-5 animate-pulse" /></>
                            ) : hasError ? (
                                <>Retry Production <RotateCcw className="w-5 h-5" /></>
                            ) : (
                                <>Start Production <Film className="w-5 h-5" /></>
                            )}
                        </button>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Script Panel */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-6 backdrop-blur-sm">
                    <div className="flex items-center gap-2 text-blue-400 mb-4">
                        <Music className="w-5 h-5" />
                        <h3 className="font-semibold">Script & Voiceover</h3>
                    </div>
                    <div className="space-y-4">
                        {project.script.lines.map((line, idx) => (
                            <div key={idx} className="p-4 rounded-lg bg-slate-950/50 border border-slate-800/50 hover:border-blue-500/30 transition-colors group">
                                <div className="flex justify-between text-xs text-slate-500 mb-1">
                                    <span className="font-mono text-blue-400">{line.speaker}</span>
                                    <span>{line.time_range}</span>
                                </div>
                                <p className="text-slate-200 leading-relaxed">{line.text}</p>
                                {line.audio_path && (
                                    <div className="mt-2">
                                        <audio controls src={api.getAssetUrl(line.audio_path)} className="w-full h-8 opacity-70 hover:opacity-100 transition-opacity" />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Visuals Panel */}
                <div className="space-y-6">
                    <div className="flex items-center gap-2 text-purple-400 mb-4">
                        <ImageIcon className="w-5 h-5" />
                        <h3 className="font-semibold">Visual Storyboard</h3>
                    </div>
                    <div className="grid gap-4">
                        {project.script.scenes.map((scene) => (
                            <div key={scene.id} className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden hover:border-purple-500/30 transition-all group">
                                <div className="aspect-video bg-slate-950 relative">
                                    {scene.image_path ? (
                                        <img
                                            src={api.getAssetUrl(scene.image_path)}
                                            alt={`Scene ${scene.id}`}
                                            className="w-full h-full object-cover"
                                        />
                                    ) : (
                                        <div className="absolute inset-0 flex items-center justify-center text-slate-700">
                                            <ImageIcon className="w-12 h-12 opacity-20" />
                                        </div>
                                    )}

                                    {/* Overlay Info */}
                                    <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent">
                                        <p className="text-sm text-white font-medium truncate">{scene.visual_prompt}</p>
                                        <div className="flex items-center gap-2 mt-1 text-xs text-slate-400">
                                            <span className="bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded">Veo: {scene.motion_prompt}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
