'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Sparkles, Film, Lightbulb, Pencil, Save, X, Target, Eye, Camera } from 'lucide-react';

interface Strategy {
    core_concept?: string;
    visual_language?: string;
    narrative_arc?: string;
    audience_hook?: string;
    cinematic_direction?: Record<string, unknown>;
}

interface Scene {
    id: number;
    visual_prompt: string;
    motion_prompt: string;
    duration: number;
}

interface ScriptLine {
    speaker: string;
    text: string;
    time_range: string;
}

interface Script {
    scenes: Scene[];
    lines: ScriptLine[];
    mood: string;
}

interface StrategyReviewCardProps {
    strategy: Strategy;
    script: Script;
    onApprove: (modifiedScript?: Script, modifiedStrategy?: Strategy) => void;
    isVisible: boolean;
}

// AI Control Toggle Component - defined outside to prevent re-render issues
const AIControlToggle = ({ 
    mode, 
    onToggle 
}: { 
    mode: 'exact' | 'enhance'; 
    onToggle: () => void; 
}) => (
    <button
        onClick={(e) => { e.stopPropagation(); onToggle(); }}
        className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs rounded-full transition-all ${
            mode === 'enhance' 
                ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50' 
                : 'bg-slate-700/50 text-slate-400 border border-slate-600/50 hover:border-slate-500'
        }`}
        title={mode === 'enhance' ? 'AI will enhance this content' : 'Using exact content as written'}
    >
        <Sparkles className={`w-3 h-3 ${mode === 'enhance' ? 'text-purple-400' : 'text-slate-500'}`} />
        {mode === 'enhance' ? 'AI Enhance' : 'Use Exact'}
    </button>
);

export default function StrategyReviewCard({ strategy, script, onApprove, isVisible }: StrategyReviewCardProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [editedStrategy, setEditedStrategy] = useState<Strategy>({ ...strategy });
    const [editedScenes, setEditedScenes] = useState<Scene[]>(script.scenes || []);
    const [editedLines, setEditedLines] = useState<ScriptLine[]>(script.lines || []);
    const [expandedScene, setExpandedScene] = useState<number | null>(null);
    
    // AI Control Mode: 'exact' = use exactly as written, 'enhance' = let AI improve
    const [sceneAIModes, setSceneAIModes] = useState<{[key: number]: {visual: 'exact' | 'enhance', motion: 'exact' | 'enhance'}}>({});
    const [voAIMode, setVoAIMode] = useState<'exact' | 'enhance'>('exact');

    const toggleSceneVisualMode = (idx: number) => {
        setSceneAIModes(prev => ({
            ...prev,
            [idx]: {
                ...prev[idx],
                visual: prev[idx]?.visual === 'enhance' ? 'exact' : 'enhance'
            }
        }));
    };

    const toggleSceneMotionMode = (idx: number) => {
        setSceneAIModes(prev => ({
            ...prev,
            [idx]: {
                ...prev[idx],
                motion: prev[idx]?.motion === 'enhance' ? 'exact' : 'enhance'
            }
        }));
    };

    if (!isVisible) return null;

    const handleSaveEdits = () => {
        setIsEditing(false);
    };

    const handleCancelEdits = () => {
        setEditedStrategy({ ...strategy });
        setEditedScenes(script.scenes || []);
        setEditedLines(script.lines || []);
        setIsEditing(false);
    };

    const handleApprove = () => {
        // Pass modified data including edited scenes
        const modifiedScript = { ...script, scenes: editedScenes, lines: editedLines };
        onApprove(modifiedScript, editedStrategy);
    };

    const updateLineText = (index: number, newText: string) => {
        const newLines = [...editedLines];
        newLines[index] = { ...newLines[index], text: newText };
        setEditedLines(newLines);
    };

    const updateScenePrompt = (index: number, newPrompt: string) => {
        const newScenes = [...editedScenes];
        newScenes[index] = { ...newScenes[index], visual_prompt: newPrompt };
        setEditedScenes(newScenes);
    };

    const updateSceneMotion = (index: number, newMotion: string) => {
        const newScenes = [...editedScenes];
        newScenes[index] = { ...newScenes[index], motion_prompt: newMotion };
        setEditedScenes(newScenes);
    };

    // Calculate total duration
    const totalDuration = editedScenes.reduce((sum, s) => sum + s.duration, 0);

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="w-full max-w-5xl mx-auto p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl border border-cyan-500/30 rounded-lg shadow-2xl"
        >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-700/50">
                <Sparkles className="w-6 h-6 text-cyan-400" />
                <h2 className="text-2xl font-bold text-white">AI Strategy Review</h2>
                
                {/* Edit Toggle Button */}
                {!isEditing ? (
                    <button
                        onClick={() => setIsEditing(true)}
                        className="ml-4 flex items-center gap-2 px-3 py-1.5 bg-amber-500/20 text-amber-400 text-sm rounded border border-amber-500/30 hover:bg-amber-500/30 transition-colors"
                    >
                        <Pencil className="w-3 h-3" />
                        Edit Strategy
                    </button>
                ) : (
                    <div className="ml-4 flex items-center gap-2">
                        <button
                            onClick={handleSaveEdits}
                            className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/20 text-emerald-400 text-sm rounded border border-emerald-500/30 hover:bg-emerald-500/30 transition-colors"
                        >
                            <Save className="w-3 h-3" />
                            Done Editing
                        </button>
                        <button
                            onClick={handleCancelEdits}
                            className="flex items-center gap-2 px-3 py-1.5 bg-red-500/20 text-red-400 text-sm rounded border border-red-500/30 hover:bg-red-500/30 transition-colors"
                        >
                            <X className="w-3 h-3" />
                            Cancel
                        </button>
                    </div>
                )}
                
                <span className="ml-auto px-3 py-1 bg-cyan-500/20 text-cyan-400 text-sm rounded-full border border-cyan-500/30">
                    Approval Gate 1
                </span>
            </div>

            {/* CREATIVE THESIS - New prominent summary */}
            <div className="mb-6 p-5 bg-gradient-to-r from-purple-900/40 to-blue-900/40 rounded-xl border border-purple-500/30">
                <div className="flex items-center gap-2 mb-3">
                    <Target className="w-5 h-5 text-purple-400" />
                    <h3 className="text-lg font-bold text-purple-300">Creative Thesis</h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                        <Film className="w-4 h-4 text-cyan-400" />
                        <span className="text-slate-400">Style:</span>
                        <span className="text-white font-medium">{script.mood || 'Cinematic'}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Camera className="w-4 h-4 text-emerald-400" />
                        <span className="text-slate-400">Scenes:</span>
                        <span className="text-white font-medium">{editedScenes.length} shots</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Eye className="w-4 h-4 text-amber-400" />
                        <span className="text-slate-400">Duration:</span>
                        <span className="text-white font-medium">{totalDuration}s</span>
                    </div>
                </div>
                {editedStrategy.core_concept && (
                    <p className="mt-3 text-slate-300 italic border-l-2 border-purple-500/50 pl-3">
                        &ldquo;{editedStrategy.core_concept}&rdquo;
                    </p>
                )}
            </div>

            {/* Strategy Overview */}
            <div className="space-y-4 mb-6">
                {(strategy.core_concept || isEditing) && (
                    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700/30">
                        <div className="flex items-center gap-2 mb-2">
                            <Lightbulb className="w-4 h-4 text-amber-400" />
                            <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wide">Core Concept</h3>
                        </div>
                        {isEditing ? (
                            <textarea
                                value={editedStrategy.core_concept || ''}
                                onChange={(e) => setEditedStrategy({ ...editedStrategy, core_concept: e.target.value })}
                                className="w-full p-2 bg-slate-900/50 border border-amber-500/30 rounded text-slate-300 text-sm resize-none focus:outline-none focus:border-amber-500"
                                rows={2}
                                placeholder="What's the main idea of this commercial?"
                            />
                        ) : (
                            <p className="text-slate-300 leading-relaxed">{editedStrategy.core_concept}</p>
                        )}
                    </div>
                )}

                {(strategy.visual_language || isEditing) && (
                    <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700/30">
                        <div className="flex items-center gap-2 mb-2">
                            <Film className="w-4 h-4 text-purple-400" />
                            <h3 className="text-sm font-semibold text-purple-400 uppercase tracking-wide">Visual Language</h3>
                        </div>
                        {isEditing ? (
                            <textarea
                                value={editedStrategy.visual_language || ''}
                                onChange={(e) => setEditedStrategy({ ...editedStrategy, visual_language: e.target.value })}
                                className="w-full p-2 bg-slate-900/50 border border-purple-500/30 rounded text-slate-300 text-sm resize-none focus:outline-none focus:border-purple-500"
                                rows={2}
                                placeholder="Describe the visual style (camera, lighting, mood...)"
                            />
                        ) : (
                            <p className="text-slate-300 leading-relaxed">{editedStrategy.visual_language}</p>
                        )}
                    </div>
                )}
            </div>

            {/* Scene Breakdown - Now with editable prompts */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-lg font-semibold text-white">Scene Breakdown</h3>
                    {isEditing && (
                        <span className="text-xs text-amber-400">Click a scene to edit its visual prompt</span>
                    )}
                </div>
                <div className="space-y-3">
                    {editedScenes.map((scene, idx) => (
                        <div
                            key={scene.id}
                            className={`p-4 bg-slate-800/30 rounded-lg border transition-all cursor-pointer ${
                                expandedScene === idx 
                                    ? 'border-cyan-500/50 bg-slate-800/50' 
                                    : 'border-slate-700/20 hover:border-cyan-500/30'
                            }`}
                            onClick={() => isEditing && setExpandedScene(expandedScene === idx ? null : idx)}
                        >
                            {/* Scene Header */}
                            <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center gap-3">
                                    <span className="px-2 py-1 bg-cyan-500/20 text-cyan-400 text-xs font-bold rounded">
                                        Scene {scene.id}
                                    </span>
                                    <span className="text-xs text-slate-500">{scene.duration}s</span>
                                </div>
                                {isEditing && (
                                    <Pencil className="w-3 h-3 text-amber-400" />
                                )}
                            </div>
                            
                            {/* Visual Prompt */}
                            <div className="mb-2">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs text-emerald-400 uppercase tracking-wide">Image Prompt:</span>
                                    <AIControlToggle 
                                        mode={sceneAIModes[idx]?.visual || 'exact'} 
                                        onToggle={() => toggleSceneVisualMode(idx)}
                                    />
                                </div>
                                {isEditing && expandedScene === idx ? (
                                    <textarea
                                        value={scene.visual_prompt}
                                        onChange={(e) => {
                                            e.stopPropagation();
                                            updateScenePrompt(idx, e.target.value);
                                        }}
                                        onClick={(e) => e.stopPropagation()}
                                        className="w-full mt-1 p-2 bg-slate-900/50 border border-emerald-500/30 rounded text-slate-300 text-sm resize-none focus:outline-none focus:border-emerald-500"
                                        rows={3}
                                        placeholder="Describe what should appear in this scene..."
                                    />
                                ) : (
                                    <p className="text-sm text-slate-400 mt-1">{scene.visual_prompt}</p>
                                )}
                            </div>

                            {/* Motion Prompt (shown when expanded) */}
                            {(expandedScene === idx || !isEditing) && scene.motion_prompt && (
                                <div>
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-xs text-blue-400 uppercase tracking-wide">Motion:</span>
                                        <AIControlToggle 
                                            mode={sceneAIModes[idx]?.motion || 'exact'} 
                                            onToggle={() => toggleSceneMotionMode(idx)}
                                        />
                                    </div>
                                    {isEditing && expandedScene === idx ? (
                                        <textarea
                                            value={scene.motion_prompt}
                                            onChange={(e) => {
                                                e.stopPropagation();
                                                updateSceneMotion(idx, e.target.value);
                                            }}
                                            onClick={(e) => e.stopPropagation()}
                                            className="w-full mt-1 p-2 bg-slate-900/50 border border-blue-500/30 rounded text-slate-300 text-sm resize-none focus:outline-none focus:border-blue-500"
                                            rows={2}
                                            placeholder="Describe camera movement and action..."
                                        />
                                    ) : (
                                        <p className="text-xs text-slate-500 mt-1 line-clamp-2">{scene.motion_prompt}</p>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* Voiceover Preview - Editable */}
            {editedLines && editedLines.length > 0 && (
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-semibold text-white">
                            Voiceover Script
                            {isEditing && <span className="text-xs text-amber-400 ml-2">(Click to edit)</span>}
                        </h3>
                        <AIControlToggle 
                            mode={voAIMode} 
                            onToggle={() => setVoAIMode(voAIMode === 'enhance' ? 'exact' : 'enhance')}
                        />
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                        {editedLines.map((line, idx) => (
                            <div key={idx} className="p-2 bg-slate-800/20 rounded border-l-2 border-cyan-500/50">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs text-cyan-400 font-mono">{line.time_range}</span>
                                    <span className="text-xs text-slate-500">•</span>
                                    <span className="text-xs text-slate-500">{line.speaker}</span>
                                </div>
                                {isEditing ? (
                                    <textarea
                                        value={line.text}
                                        onChange={(e) => updateLineText(idx, e.target.value)}
                                        className="w-full p-2 bg-slate-900/50 border border-cyan-500/30 rounded text-slate-300 text-sm resize-none focus:outline-none focus:border-cyan-500"
                                        rows={2}
                                        placeholder="Enter voiceover text..."
                                        aria-label={`Voiceover line ${idx + 1}`}
                                    />
                                ) : (
                                    <p className="text-sm text-slate-300">{line.text}</p>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Approve Button */}
            <div className="flex items-center justify-center pt-6 border-t border-slate-700/50">
                <button
                    onClick={handleApprove}
                    disabled={isEditing}
                    className={`group flex items-center gap-3 px-8 py-4 font-bold rounded-lg shadow-lg transition-all ${
                        isEditing
                            ? 'bg-slate-600 text-slate-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white hover:shadow-cyan-500/50'
                    }`}
                >
                    <CheckCircle2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                    <span>Approve Strategy & Generate Images</span>
                </button>
            </div>

            {/* Info Notice */}
            <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded text-center">
                <p className="text-sm text-blue-300">
                    {isEditing 
                        ? "Finish editing before approving. Click 'Done Editing' to save changes."
                        : `Clicking approve will start generating ${editedScenes.length} images in parallel (~20-30 seconds)`
                    }
                </p>
            </div>
        </motion.div>
    );
}
