'use client';

import React, { useState } from 'react';
import { RefreshCw, Music, Video, Wand2, Settings2, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import { useStore } from '@/lib/store';

interface ControlDeckProps {
    selectedSceneId: number | null;
    onRecompose: () => void;
    onRegenerateScene: (sceneId: number) => void;
}

export default function ControlDeck({ selectedSceneId, onRecompose, onRegenerateScene }: ControlDeckProps) {
    const { project, isLoading } = useStore();
    const [mood, setMood] = useState("Cinematic");

    // Derived state
    const isReady = project?.status === 'completed' || project?.status === 'assembled';
    const hasSelection = selectedSceneId !== null;

    return (
        <div className="flex flex-col h-full bg-black/90 backdrop-blur-xl border-l border-slate-800/50 p-4 font-mono">
            {/* Header */}
            <div className="mb-6 flex items-center gap-2 text-cyan-400/80 uppercase tracking-widest text-xs border-b border-slate-800/50 pb-2">
                <Settings2 className="w-3 h-3" />
                <span>Director's Console</span>
            </div>

            {/* Context Aware Controls */}
            <div className="flex-1 space-y-8">

                {/* 0. SMART PRESETS */}
                <div className="space-y-3">
                    <h3 className="text-xs text-slate-500 uppercase flex items-center gap-2">
                        <Wand2 className="w-3 h-3" />
                        Smart Presets
                    </h3>
                    <div className="grid grid-cols-2 gap-2">
                        <button className="px-2 py-2 text-[10px] bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-cyan-500 text-slate-300 hover:text-cyan-400 rounded transition-all text-left">
                            🎬 Netflix Doc
                        </button>
                        <button className="px-2 py-2 text-[10px] bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-pink-500 text-slate-300 hover:text-pink-400 rounded transition-all text-left">
                            📱 TikTok Viral
                        </button>
                        <button className="px-2 py-2 text-[10px] bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-amber-500 text-slate-300 hover:text-amber-400 rounded transition-all text-left">
                            🎞️ Kodak Film
                        </button>
                        <button className="px-2 py-2 text-[10px] bg-slate-800/50 hover:bg-slate-800 border border-slate-700 hover:border-violet-500 text-slate-300 hover:text-violet-400 rounded transition-all text-left">
                            🟣 Cyberpunk
                        </button>
                    </div>
                </div>

                {/* 1. SELECTION CONTEXT */}
                <div className="space-y-3">
                    <h3 className="text-xs text-slate-500 uppercase">Selection Context</h3>
                    {hasSelection ? (
                        <div className="p-3 rounded-lg bg-slate-900/50 border border-slate-800">
                            <div className="flex justify-between items-center mb-2">
                                <span className="text-white font-bold">SCENE {selectedSceneId}</span>
                                <span className="text-[10px] text-cyan-500 bg-cyan-900/20 px-1.5 py-0.5 rounded">ACTIVE</span>
                            </div>
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={() => onRegenerateScene(selectedSceneId)}
                                    disabled={isLoading}
                                    className="col-span-2 flex items-center justify-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs rounded transition-colors disabled:opacity-50"
                                >
                                    <RefreshCw className="w-3 h-3" />
                                    Re-Shoot Scene
                                </button>
                                <button className="flex items-center justify-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-800 text-slate-300 text-xs rounded transition-colors">
                                    <Video className="w-3 h-3" />
                                    Motion
                                </button>
                                <button className="flex items-center justify-center gap-2 px-3 py-2 bg-slate-800/50 hover:bg-slate-800 text-slate-300 text-xs rounded transition-colors">
                                    <Wand2 className="w-3 h-3" />
                                    Prompt
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="p-4 rounded-lg border border-slate-800 border-dashed text-center">
                            <span className="text-slate-600 text-xs">No Scene Selected</span>
                        </div>
                    )}
                </div>

                {/* 2. GLOBAL CONTEXT */}
                <div className="space-y-3">
                    <h3 className="text-xs text-slate-500 uppercase">Global Mastering</h3>

                    {/* Vibe Mixer */}
                    <div className="space-y-2">
                        <label className="text-xs text-slate-400">Atmosphere / Music</label>
                        <div className="grid grid-cols-2 gap-2">
                            {['Cinematic', 'High Energy', 'Dark', 'Corporate'].map((m) => (
                                <button
                                    key={m}
                                    onClick={() => setMood(m)}
                                    className={clsx(
                                        "px-2 py-1.5 text-[10px] rounded border transition-all",
                                        mood === m
                                            ? "bg-cyan-500/20 border-cyan-500 text-cyan-400"
                                            : "bg-slate-900/50 border-slate-800 text-slate-500 hover:border-slate-700"
                                    )}
                                >
                                    {m}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button
                        onClick={onRecompose}
                        disabled={isLoading || !isReady}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded shadow-lg shadow-indigo-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Music className="w-4 h-4" />
                        RE-MIX VIDEO (FAST)
                    </button>
                    <p className="text-[10px] text-slate-500 text-center">
                        *Updates music & editing rhythm only. No video cost.
                    </p>
                </div>
            </div>

            {/* Footer Actions */}
            <div className="mt-auto pt-4 border-t border-slate-800/50">
                <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-900 text-slate-500 text-xs rounded hover:bg-red-900/20 hover:text-red-400 transition-colors">
                    <Trash2 className="w-3 h-3" />
                    Reset Project
                </button>
            </div>
        </div>
    );
}
