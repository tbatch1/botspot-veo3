'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Image as ImageIcon, PlayCircle, RefreshCw, Pencil, X, AlertCircle, Sparkles, Upload } from 'lucide-react';
import { api } from '@/lib/api';

interface Scene {
    id: number;
    visual_prompt: string;
    motion_prompt: string;
    duration: number;
    image_path?: string;
    video_path?: string;
    image_source?: string; // "ai" or "upload:{filename}"
}

interface UploadedFile {
    filename: string;
    mode: 'reference' | 'direct';
    previewUrl: string;
}

interface ImageGenerationPanelProps {
    scenes: Scene[];
    status: string;
    projectId: string;
    onApproveImages: () => void;
    onRegenerateScene?: (sceneId: number, newPrompt?: string) => void;
    availableUploads?: UploadedFile[];
    isVisible: boolean;
}

export default function ImageGenerationPanel({
    scenes,
    status,
    projectId,
    onApproveImages,
    onRegenerateScene,
    availableUploads = [],
    isVisible
}: ImageGenerationPanelProps) {
    const [editingScene, setEditingScene] = useState<number | null>(null);
    const [editedPrompt, setEditedPrompt] = useState<string>('');
    const [regeneratingScene, setRegeneratingScene] = useState<number | null>(null);
    const [sceneSources, setSceneSources] = useState<{[key: number]: string}>({});

    const handleSourceChange = async (sceneId: number, source: string) => {
        setSceneSources(prev => ({ ...prev, [sceneId]: source }));
        try {
            await api.updateSceneSource(projectId, sceneId, source);
        } catch (error) {
            console.error('Failed to update scene source:', error);
        }
    };

    const getSceneSource = (scene: Scene) => {
        return sceneSources[scene.id] || scene.image_source || 'ai';
    };

    if (!isVisible) return null;

    const completedImages = scenes.filter(s => s.image_path).length;
    const totalScenes = scenes.length;
    const progress = (completedImages / totalScenes) * 100;
    const isGenerating = status === 'generating_images';
    const isComplete = status === 'images_complete';

    const handleStartEdit = (scene: Scene) => {
        setEditingScene(scene.id);
        setEditedPrompt(scene.visual_prompt);
    };

    const handleCancelEdit = () => {
        setEditingScene(null);
        setEditedPrompt('');
    };

    const handleRegenerate = async (sceneId: number) => {
        setRegeneratingScene(sceneId);
        
        if (onRegenerateScene) {
            await onRegenerateScene(sceneId, editingScene === sceneId ? editedPrompt : undefined);
        } else {
            // Fallback: call API directly
            try {
                await api.regenerateScene(projectId, sceneId, editingScene === sceneId ? editedPrompt : undefined);
            } catch (error) {
                console.error('Regeneration failed:', error);
            }
        }
        
        setEditingScene(null);
        setEditedPrompt('');
        setRegeneratingScene(null);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="w-full max-w-6xl mx-auto p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl border border-purple-500/30 rounded-lg shadow-2xl"
        >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-700/50">
                <ImageIcon className="w-6 h-6 text-purple-400" />
                <h2 className="text-2xl font-bold text-white">Image Generation</h2>
                {isGenerating && (
                    <Loader2 className="w-5 h-5 text-purple-400 animate-spin ml-2" />
                )}
                <span className="ml-auto px-3 py-1 bg-purple-500/20 text-purple-400 text-sm rounded-full border border-purple-500/30">
                    Approval Gate 2
                </span>
            </div>

            {/* Progress Bar */}
            <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-400">
                        {isGenerating ? 'Generating images...' : 'All images generated'}
                    </span>
                    <span className="text-sm font-bold text-purple-400">
                        {completedImages} / {totalScenes}
                    </span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${progress}%` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500"
                    />
                </div>
            </div>

            {/* Regeneration Help */}
            {isComplete && (
                <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-amber-400" />
                    <p className="text-sm text-amber-300">
                        Don't like an image? Click the <RefreshCw className="w-3 h-3 inline" /> button to regenerate with the same or edited prompt.
                    </p>
                </div>
            )}

            {/* Image Grid */}
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
                                {regeneratingScene === scene.id ? (
                                    <div className="w-full h-full flex flex-col items-center justify-center bg-purple-900/20">
                                        <Loader2 className="w-8 h-8 text-amber-400 animate-spin mb-2" />
                                        <span className="text-xs text-amber-400">Regenerating...</span>
                                    </div>
                                ) : scene.image_path ? (
                                    <>
                                        <img
                                            src={api.getAssetUrl(scene.image_path)}
                                            alt={`Scene ${scene.id}`}
                                            className="w-full h-full object-cover"
                                        />
                                        <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-1 bg-emerald-500/90 rounded text-xs font-bold text-white">
                                            <CheckCircle2 className="w-3 h-3" />
                                            Complete
                                        </div>
                                        
                                        {/* Action Buttons - Show on hover */}
                                        <div className="absolute bottom-2 right-2 flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => handleStartEdit(scene)}
                                                className="p-2 bg-amber-500/90 hover:bg-amber-500 rounded-lg text-white text-xs font-medium flex items-center gap-1"
                                                title="Edit prompt and regenerate"
                                            >
                                                <Pencil className="w-3 h-3" />
                                            </button>
                                            <button
                                                onClick={() => handleRegenerate(scene.id)}
                                                className="p-2 bg-cyan-500/90 hover:bg-cyan-500 rounded-lg text-white text-xs font-medium flex items-center gap-1"
                                                title="Regenerate with same prompt"
                                            >
                                                <RefreshCw className="w-3 h-3" />
                                            </button>
                                        </div>
                                    </>
                                ) : (
                                    <div className="w-full h-full flex flex-col items-center justify-center">
                                        <Loader2 className="w-8 h-8 text-purple-400 animate-spin mb-2" />
                                        <span className="text-xs text-slate-500">Generating...</span>
                                    </div>
                                )}
                            </div>

                            {/* Scene Info */}
                            <div className="mt-2 px-2">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-xs font-bold text-purple-400">Scene {scene.id}</span>
                                    <span className="text-xs text-slate-500">{scene.duration}s</span>
                                </div>

                                {/* Source Toggle - Show when there are direct uploads available */}
                                {availableUploads.length > 0 && isComplete && (
                                    <div className="mb-2">
                                        <select
                                            value={getSceneSource(scene)}
                                            onChange={(e) => handleSourceChange(scene.id, e.target.value)}
                                            className="w-full text-xs bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-300 focus:outline-none focus:border-purple-500"
                                        >
                                            <option value="ai">
                                                AI Generated
                                            </option>
                                            {availableUploads.map(upload => (
                                                <option key={upload.filename} value={`upload:${upload.filename}`}>
                                                    Upload: {upload.filename}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                )}

                                {/* Editing Mode */}
                                {editingScene === scene.id ? (
                                    <div className="mt-2">
                                        <textarea
                                            value={editedPrompt}
                                            onChange={(e) => setEditedPrompt(e.target.value)}
                                            className="w-full p-2 bg-slate-900/80 border border-amber-500/50 rounded text-slate-300 text-xs resize-none focus:outline-none focus:border-amber-500"
                                            rows={3}
                                            placeholder="Edit the image prompt..."
                                        />
                                        <div className="flex gap-2 mt-2">
                                            <button
                                                onClick={() => handleRegenerate(scene.id)}
                                                className="flex-1 flex items-center justify-center gap-1 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-medium rounded"
                                            >
                                                <RefreshCw className="w-3 h-3" />
                                                Regenerate
                                            </button>
                                            <button
                                                onClick={handleCancelEdit}
                                                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-medium rounded"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </div>
                                    </div>
                                ) : (
                                    <p className="text-xs text-slate-400 line-clamp-2">{scene.visual_prompt}</p>
                                )}
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            {/* Approve Button - Only show when complete */}
            {isComplete && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-center pt-6 border-t border-slate-700/50"
                >
                    <button
                        onClick={onApproveImages}
                        className="group flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold rounded-lg shadow-lg hover:shadow-purple-500/50 transition-all"
                    >
                        <PlayCircle className="w-5 h-5 group-hover:scale-110 transition-transform" />
                        <span>Approve Images & Generate Videos</span>
                    </button>
                </motion.div>
            )}

            {/* Info Notice */}
            {isComplete && (
                <div className="mt-4 p-3 bg-purple-500/10 border border-purple-500/30 rounded text-center">
                    <p className="text-sm text-purple-300">
                        Clicking approve will animate these images into videos (~60-90 seconds)
                    </p>
                </div>
            )}
        </motion.div>
    );
}
