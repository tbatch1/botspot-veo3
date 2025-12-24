'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useStore } from '@/lib/store';
import NeuralNodeDropdown from './ui/NeuralNodeDropdown';
import PipelineFlow from './PipelineFlow';
import { motion } from 'framer-motion';
import { Play, Wand2, Loader2, Layers, Check, Image, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import axios from 'axios';
import TerminalLog from './TerminalLog';
import StrategyReviewCard from './StrategyReviewCard';
import ImageGenerationPanel from './ImageGenerationPanel';
import VideoGenerationPanel from './VideoGenerationPanel';

export default function OTTWorkflowCanvas() {
    const { project, currentStep, isLoading, approveStrategy, approveImages, approveVideos, remixVoiceover, updateScript, uploadedAssets, setUploadedAssets, loadProjectFromBackend, pollStatus } = useStore();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isUploading, setIsUploading] = useState(false);

    // Multi-Asset State with mode tracking
    interface UploadedFile {
        filename: string;
        mode: 'reference' | 'direct';
        previewUrl: string;
    }
    const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

    // Local state for the "New Project" flow
    const [config, setConfig] = useState({
        topic: '', // User input for product/topic
        url: '', // Website/Product URL
        style: ['Cinematic'], // Default as array
        duration: '15s',
        platform: ['Netflix'], // Multi-Select
        mood: ['Premium'], // Multi-Select
        transition: 'crossfade',
        camera_style: ['Auto'], // Multi-Select
        lighting_preference: 'auto',
        color_grade: 'auto',
        commercial_style: 'auto', // Iconic template selection
        image_guidance: 'i2i_only', // Reference image guidance mode
        player_mode: 'auto', // Final video player mode (advanced)
        video_model: 'auto' // Veo / Runway selection
    });

    const handleConfigChange = (key: string, value: any) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    };

    const handleLaunch = async () => {
        const userBrief = config.topic.trim();
        if (!userBrief) return;

        // Call the store action with the full config object
        const fullConfig = {
            ...config,
            // New v2 format with mode info
            uploaded_assets_v2: uploadedFiles.map(f => ({
                filename: f.filename,
                mode: f.mode
            })),
            // Legacy format for backwards compatibility
            uploaded_assets: uploadedFiles.map(f => f.filename),
            uploaded_asset: uploadedFiles[0]?.filename
        };
        await useStore.getState().createPlan(userBrief, fullConfig);

        // Note: With approval workflow, we DON'T auto-start generation
        // User must approve strategy first via StrategyReviewCard
    };

    const uploadFile = async (file: File, mode: 'reference' | 'direct' = 'reference') => {
        setIsUploading(true);
        const objectUrl = URL.createObjectURL(file);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', mode);

        try {
            const response = await axios.post('http://localhost:4000/api/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });

            if (response.data.status === 'success') {
                setUploadedFiles(prev => [...prev, {
                    filename: response.data.filename,
                    mode: response.data.mode || mode,
                    previewUrl: objectUrl
                }]);
            }
        } catch (error) {
            console.error('Upload failed:', error);
        } finally {
            setIsUploading(false);
        }
    };

    const updateFileMode = (index: number, newMode: 'reference' | 'direct') => {
        setUploadedFiles(prev => prev.map((f, i) =>
            i === index ? { ...f, mode: newMode } : f
        ));
    };

    const removeFile = (index: number) => {
        setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (files) {
            Array.from(files).forEach(file => uploadFile(file));
        }
    };

    // Restore state from store on mount (for page refresh persistence)
    useEffect(() => {
        // If we have a project that's in a generating state, resume polling
        if (project && (project.status === 'generating_images' || project.status === 'generating_videos' || project.status === 'assembling')) {
            pollStatus();
        }
        // Restore uploaded assets from store (without preview URLs since those can't be persisted)
        if (uploadedAssets.length > 0 && uploadedFiles.length === 0) {
            setUploadedFiles(uploadedAssets.map(a => ({
                filename: a.filename,
                mode: a.mode,
                previewUrl: `http://localhost:4000/api/assets/user_uploads/${a.filename}`
            })));
        }
    }, []);

    // Sync uploadedFiles to store for persistence
    useEffect(() => {
        setUploadedAssets(uploadedFiles.map(f => ({ filename: f.filename, mode: f.mode })));
    }, [uploadedFiles, setUploadedAssets]);

    // Handle Paste Events
    useEffect(() => {
        const handlePaste = (e: ClipboardEvent) => {
            const items = e.clipboardData?.items;
            if (!items) return;

            for (const item of items) {
                if (item.type.indexOf('image') !== -1 || item.type.indexOf('video') !== -1) {
                    const file = item.getAsFile();
                    if (file) {
                        uploadFile(file);
                        e.preventDefault(); // Prevent double-pasting into inputs
                    }
                }
            }
        };

        document.addEventListener('paste', handlePaste);
        return () => document.removeEventListener('paste', handlePaste);
    }, []);

    return (
        <div className="w-full max-w-[1600px] mx-auto px-4 md:px-8 pt-8 pb-32">
            {/* Header */}
            <div className="text-center mb-12 space-y-4">
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-mono"
                >
                    <Wand2 className="w-4 h-4" />
                    <span>NEURAL ARCHITECT V3.1</span>
                </motion.div>
                <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                    Configure Your Campaign Topology
                </h1>
                <p className="text-slate-400 max-w-2xl mx-auto">
                    Define the parameters for your OTT commercial. The neural engine will generate the script, visuals, and motion based on this topology.
                </p>
            </div>

            {/* Workflow Canvas */}
            <div className="relative">
                {/* Connecting Lines (Visual only) */}
                <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-900/50 to-transparent -z-10" />

                {/* Pipeline Visualization - Central Stage */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mb-12"
                >
                    <PipelineFlow />
                </motion.div>

                {/* Topic Input (ChatGPT-style) */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mb-8 max-w-3xl mx-auto relative z-40"
                >
                    <div className="relative">
                        <textarea
                            value={config.topic}
                            onChange={(e) => handleConfigChange('topic', e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    if (config.topic.trim() && !isLoading) {
                                        handleLaunch();
                                    }
                                }
                            }}
                            placeholder="Message OTT Ad Builder..."
                            rows={1}
                            className="w-full bg-slate-800/50 text-white border border-slate-700 rounded-3xl px-6 py-4 text-base focus:outline-none focus:border-slate-600 resize-none placeholder:text-slate-500 transition-all shadow-lg hover:bg-slate-800/70"
                            style={{
                                minHeight: '56px',
                                maxHeight: '200px',
                                overflow: 'auto'
                            }}
                        />
                    </div>
                    <div className="mt-2 text-center text-xs text-slate-500">
                        Press Enter to send • Shift + Enter for new line
                    </div>
                </motion.div>

                {/* URL Input (Secondary Node) */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.05 }}
                    className="mb-12 max-w-lg mx-auto relative z-40"
                >
                    <div className="relative group">
                        <input
                            type="text"
                            value={config.url}
                            onChange={(e) => handleConfigChange('url', e.target.value)}
                            placeholder="Optional: Landing Page / Product URL"
                            className="relative w-full bg-slate-900/80 text-cyan-100 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/50 placeholder:text-slate-500 transition-all text-center font-mono"
                        />
                    </div>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-5 gap-8 mb-8">
                    {/* Node 1: Style */}
                    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}>
                        <NeuralNodeDropdown
                            label="Visual Style"
                            value={config.style}
                            options={['Cinematic', 'Anime', '3D Render', 'Analog Film', 'Cyberpunk']}
                            onChange={(val) => handleConfigChange('style', val)}
                            multiSelect={true}
                        />
                        <div className="mt-2 text-center text-xs text-slate-500">Aesthetic Direction</div>
                    </motion.div>

                    {/* Node 2: Duration */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
                        <NeuralNodeDropdown
                            label="Duration"
                            value={config.duration}
                            options={['15s', '30s', '60s']}
                            onChange={(val) => handleConfigChange('duration', val)}
                        />
                        <div className="mt-2 text-center text-xs text-slate-500">Spot Length</div>
                    </motion.div>

                    {/* Node 3: Platform */}
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.3 }}>
                        <NeuralNodeDropdown
                            label="Target Platform"
                            value={config.platform}
                            options={['Netflix', 'Hulu', 'Prime Video', 'YouTube TV']}
                            onChange={(val) => handleConfigChange('platform', val)}
                            multiSelect={true}
                        />
                        <div className="mt-2 text-center text-xs text-slate-500">Delivery Format</div>
                    </motion.div>

                    {/* Node 4: Reference Image Guidance */}
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.35 }}>
                        <NeuralNodeDropdown
                            label="Reference Image Guidance"
                            value={config.image_guidance}
                            options={[
                                { value: "none", label: "None", description: "Ignore reference images (only use direct scene uploads)" },
                                { value: "i2i_only", label: "Image-Directed (I2I)", description: "Use reference image to guide look; no prompt analysis" },
                                { value: "prompt_only", label: "Prompt-Directed", description: "Extract palette/lighting into prompts; don't force I2I" },
                                { value: "prompt_and_i2i", label: "Prompt + I2I", description: "Best fidelity: prompt enrichment + image-directed look" },
                                { value: "veo_text_only", label: "Veo Max Prompt (Text-to-Video)", description: "Skip image generation; Veo generates from full scene prompt" },
                            ]}
                            onChange={(val) => handleConfigChange('image_guidance', val)}
                        />
                        <div className="mt-2 text-center text-xs text-slate-500">Consistency Control</div>
                    </motion.div>

                    {/* Node 5: Video Generator */}
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.4 }}>
                        <NeuralNodeDropdown
                            label="Video Generator"
                            value={config.video_model}
                            options={[
                                { value: "auto", label: "Auto (Recommended)", description: "Chooses the best model per run (falls back if needed)" },
                                { value: "veo", label: "Veo", description: "Highest quality; supports prompt-only (text-to-video) mode" },
                                { value: "runway", label: "Runway", description: "Great for high-motion I2V shots (requires source images)" },
                            ]}
                            onChange={(val) => handleConfigChange('video_model', val)}
                        />
                        <div className="mt-2 text-center text-xs text-slate-500">Generation Engine</div>
                    </motion.div>
                </div>

                {/* Commercial Style - Iconic Template Selection */}
                <motion.div 
                    initial={{ opacity: 0, y: 20 }} 
                    animate={{ opacity: 1, y: 0 }} 
                    transition={{ delay: 0.35 }}
                    className="mb-8 max-w-2xl mx-auto"
                >
                    <NeuralNodeDropdown
                        label="🎬 Commercial Style"
                        value={config.commercial_style}
                        options={[
                            { value: "auto", label: "Auto (Varied)", icon: "🎲", description: "Picks a different template + vibe per brand" },
                            { value: "mascot_story", label: "Mascot Story", icon: "🦎", description: "Geico/Progressive style character" },
                            { value: "sensory_metaphor", label: "Sensory Metaphor", icon: "🏔️", description: "Coors ice mountains feel" },
                            { value: "emotional_journey", label: "Emotional Journey", icon: "❤️", description: "eBay child heartstring" },
                            { value: "catchphrase_comedy", label: "Catchphrase Comedy", icon: "😂", description: "Bud Light Dilly Dilly" },
                            { value: "problem_solution", label: "Problem-Solution", icon: "✨", description: "OxiClean demo style" },
                            { value: "aspirational_lifestyle", label: "Aspirational Lifestyle", icon: "🌟", description: "Nike/Apple inspiration" },
                            { value: "tech_reveal", label: "Tech Product Reveal", icon: "📱", description: "Apple keynote energy" }
                        ]}
                        onChange={(val) => handleConfigChange('commercial_style', val)}
                    />
                    <div className="mt-2 text-center text-xs text-slate-500">Iconic Commercial Template - Drives GPT-5.2 Creative Strategy</div>
                </motion.div>

                {/* Advanced Cinematography Controls */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    {/* Mood */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
                        <NeuralNodeDropdown
                            label="Creative Mood"
                            value={config.mood}
                            options={['Premium', 'Authentic', 'Bold', 'Aspirational', 'Playful', 'Dramatic']}
                            onChange={(val) => handleConfigChange('mood', val)}
                            multiSelect={true}
                        />
                    </motion.div>

                    {/* Camera Style */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
                        <NeuralNodeDropdown
                            label="Camera Movement"
                            value={config.camera_style}
                            options={[
                                { value: "Auto", label: "Auto", icon: "🎲", description: "Varies camera language per scene" },
                                { value: "Steadicam", label: "Steadicam", icon: "🎥", description: "Smooth floating movement" },
                                { value: "Handheld", label: "Handheld", icon: "📹", description: "Raw documentary feel" },
                                { value: "Crane", label: "Crane/Jib", icon: "🏗️", description: "Sweeping vertical moves" },
                                { value: "Gimbal", label: "Gimbal", icon: "🎬", description: "Stabilized dynamic shots" },
                                { value: "Static", label: "Static/Tripod", icon: "🎞️", description: "Locked-off observational" },
                                { value: "Drone", label: "Aerial/Drone", icon: "🚁", description: "High altitude perspectives" }
                            ]}
                            onChange={(val) => handleConfigChange('camera_style', val)}
                            multiSelect={true}
                        />
                    </motion.div>

                    {/* Lighting */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.6 }}>
                        <NeuralNodeDropdown
                            label="Lighting Style"
                            value={config.lighting_preference}
                            options={[
                                { value: "auto", label: "Auto", preview: "Varies per scene" },
                                { value: "dramatic", label: "Dramatic", preview: "High contrast" },
                                { value: "natural", label: "Natural", preview: "Soft authentic" },
                                { value: "studio", label: "Studio", preview: "Clean 3-point" },
                                { value: "moody", label: "Moody", preview: "Atmospheric" },
                                { value: "bright", label: "High-Key", preview: "Bright & airy" }
                            ]}
                            onChange={(val) => handleConfigChange('lighting_preference', val)}
                        />
                    </motion.div>

                    {/* Color Grade */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7 }}>
                        <NeuralNodeDropdown
                            label="Color Grading"
                            value={config.color_grade}
                            options={[
                                { value: "auto", label: "Auto", description: "Varies per brand" },
                                { value: "hollywood_blockbuster", label: "Blockbuster", description: "Teal & orange" },
                                { value: "kodak_5219", label: "Kodak 5219", description: "Rich cinema film" },
                                { value: "fuji_film_stock", label: "Fuji Pro 400H", description: "Pastel tones" },
                                { value: "bleach_bypass", label: "Bleach Bypass", description: "Desaturated action" },
                                { value: "vintage_analog", label: "Vintage 70s", description: "Warm golden" },
                                { value: "neon_cyberpunk", label: "Cyberpunk", description: "Vibrant neon" }
                            ]}
                            onChange={(val) => handleConfigChange('color_grade', val)}
                        />
                    </motion.div>
                </div>

                {/* Footer Actions: Upload & Generate */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-col md:flex-row justify-between items-end mt-12 gap-6 relative z-40"
                >
                    {/* Asset Upload Zone - Multi-Asset Support with Mode Selection */}
                    <div className="w-full md:w-auto">
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            onChange={handleUpload}
                            accept="image/*,video/*"
                            multiple
                        />

                        {/* Show uploaded files with mode toggles */}
                        {uploadedFiles.length > 0 ? (
                            <div className="space-y-2">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs text-slate-400 uppercase tracking-wider">{uploadedFiles.length} Asset{uploadedFiles.length > 1 ? 's' : ''} Ready</span>
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="text-xs text-cyan-400 hover:text-cyan-300"
                                    >
                                        + Add More
                                    </button>
                                </div>
                                {uploadedFiles.map((file, index) => (
                                    <div key={index} className="flex items-center gap-3 p-2 bg-slate-800/50 rounded-lg border border-slate-700">
                                        <img
                                            src={file.previewUrl}
                                            alt={file.filename}
                                            className="w-12 h-12 object-cover rounded"
                                        />
                                        <div className="flex-1 min-w-0">
                                            <div className="text-xs text-slate-300 truncate">{file.filename}</div>
                                            <div className="flex gap-1 mt-1">
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); updateFileMode(index, 'reference'); }}
                                                    className={clsx(
                                                        "flex items-center gap-1 px-2 py-0.5 text-[10px] rounded transition-all",
                                                        file.mode === 'reference'
                                                            ? "bg-purple-500/30 text-purple-300 border border-purple-500/50"
                                                            : "bg-slate-700/50 text-slate-400 border border-slate-600/50 hover:border-slate-500"
                                                    )}
                                                >
                                                    <Sparkles className="w-3 h-3" />
                                                    AI Reference
                                                </button>
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); updateFileMode(index, 'direct'); }}
                                                    className={clsx(
                                                        "flex items-center gap-1 px-2 py-0.5 text-[10px] rounded transition-all",
                                                        file.mode === 'direct'
                                                            ? "bg-green-500/30 text-green-300 border border-green-500/50"
                                                            : "bg-slate-700/50 text-slate-400 border border-slate-600/50 hover:border-slate-500"
                                                    )}
                                                >
                                                    <Image className="w-3 h-3" />
                                                    Use Directly
                                                </button>
                                            </div>
                                        </div>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                                            className="text-slate-500 hover:text-red-400 text-xs"
                                        >
                                            X
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div
                                onClick={() => fileInputRef.current?.click()}
                                className={clsx(
                                    "relative w-full md:w-80 h-32 rounded-xl border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center gap-2 group backdrop-blur-sm overflow-hidden",
                                    isUploading
                                        ? "border-cyan-500 bg-cyan-900/40"
                                        : "border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800/80 bg-slate-900/20"
                                )}
                            >
                                <div className={clsx(
                                    "relative z-10 p-3 rounded-full transition-colors",
                                    isUploading
                                        ? "bg-cyan-500/20 text-cyan-400"
                                        : "bg-slate-800 text-slate-400 group-hover:text-cyan-400 group-hover:bg-cyan-500/10"
                                )}>
                                    {isUploading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Layers className="w-6 h-6" />}
                                </div>
                                <div className="relative z-10 text-center space-y-1">
                                    <span className="block text-xs font-bold tracking-wider text-slate-400 group-hover:text-cyan-400">
                                        {isUploading ? "UPLOADING..." : "DROP OR PASTE"}
                                    </span>
                                    <span className="block text-[10px] text-slate-500 uppercase tracking-widest">
                                        Multiple Files OK
                                    </span>
                                </div>
                                {!isUploading && (
                                    <div className="hidden group-hover:block absolute bottom-2 text-[9px] text-slate-600 font-mono transition-opacity animate-pulse">
                                        CTRL+V SUPPORTED
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Launch Button */}
                    <div className="relative">
                        <button
                            onClick={handleLaunch}
                            disabled={!config.topic.trim() || isLoading}
                            className={clsx(
                                "flex items-center gap-3 px-8 py-4 rounded-2xl font-bold text-lg shadow-2xl transition-all duration-300 group",
                                !config.topic.trim() || isLoading
                                    ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                                    : "bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:scale-105 hover:shadow-cyan-500/25"
                            )}
                        >
                            {isLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Wand2 className="w-6 h-6" />}
                            <span>GENERATE CAMPAIGN</span>
                        </button>
                        {!config.topic.trim() && (
                            <div className="absolute -top-8 right-0 text-xs text-slate-500 bg-slate-900/90 px-2 py-1 rounded">
                                ENTER TOPIC TO ENABLE
                            </div>
                        )}
                    </div>
                </motion.div>

                {/* Deployment Console - Live Logs */}
                <motion.div
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="mt-16 w-full max-w-4xl mx-auto h-64 rounded-xl overflow-hidden shadow-2xl border border-slate-800 relative z-40"
                >
                    <TerminalLog />
                </motion.div>

                {/* ============================================================================================= */}
                {/* APPROVAL WORKFLOW: Stage-Based UI Panels                                                     */}
                {/* ============================================================================================= */}

                {/* Stage 1: Strategy Review & Approval */}
                {currentStep === 'strategy' && project?.strategy && project?.script && (
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-12"
                    >
                        <StrategyReviewCard
                            strategy={project.strategy}
                            script={project.script}
                            onApprove={approveStrategy}
                            isVisible={true}
                        />
                    </motion.div>
                )}

                {/* Stage 2: Image Generation & Approval */}
                {(currentStep === 'images' || (project?.status === 'generating_images' || project?.status === 'images_complete')) && project?.script?.scenes && (
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-12"
                    >
                        <ImageGenerationPanel
                            scenes={project.script.scenes}
                            status={project.status}
                            projectId={project.id}
                            onApproveImages={approveImages}
                            availableUploads={uploadedFiles.filter(f => f.mode === 'direct')}
                            isVisible={true}
                        />
                    </motion.div>
                )}

                {/* Stage 3: Video Generation & Final Assembly */}
                {(currentStep === 'videos' || project?.status === 'generating_videos' || project?.status === 'videos_complete' || project?.status === 'assembling' || project?.status === 'completed') && project?.script?.scenes && (
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mt-12"
                    >
                        <VideoGenerationPanel
                            scenes={project.script.scenes}
                            status={project.status}
                            finalVideoPath={project.final_video_path}
                            playerMode={project.player_mode || (config as any).player_mode}
                            onApproveFinal={approveVideos}
                            script={project.script}
                            onUpdateScript={updateScript}
                            onRemixVoiceover={remixVoiceover}
                            isVisible={true}
                        />
                    </motion.div>
                )}
            </div>
        </div>
    );
}
