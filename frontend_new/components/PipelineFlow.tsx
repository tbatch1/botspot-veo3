'use client';

import React from 'react';
import ReactFlow, { Node, Edge, Background, Controls, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { useStore } from '@/lib/store';
import clsx from 'clsx';
import { Brain, Globe, Clapperboard, Video, Music, Wand2, MonitorPlay } from 'lucide-react';

// Custom Node Styling Helper
const getNodeStyle = (isActive: boolean, isCompleted: boolean) => ({
    background: isActive ? '#0891b2' : isCompleted ? '#0f172a' : '#1e293b',
    color: '#fff',
    border: isActive ? '2px solid #22d3ee' : isCompleted ? '1px solid #22d3ee' : '1px solid #475569',
    borderRadius: '12px',
    padding: '12px',
    width: '180px',
    fontSize: '12px',
    fontWeight: 'bold',
    boxShadow: isActive ? '0 0 20px rgba(34, 211, 238, 0.4)' : 'none',
    transition: 'all 0.3s ease'
});

export default function PipelineFlow() {
    const { project, isLoading } = useStore();

    // Determine status of each node based on approval workflow
    const status = project?.status || 'idle';
    const logs = project?.logs || [];

    // Approval workflow stages
    const isPlanning = status === 'planning';
    const isPlanned = status === 'planned';
    const isGeneratingImages = status === 'generating_images';
    const isImagesComplete = status === 'images_complete';
    const isGeneratingVideos = status === 'generating_videos';
    const isVideosComplete = status === 'videos_complete';
    const isAssembling = status === 'assembling';
    const isCompleted = status === 'completed';

    // Heuristics for node activation based on logs
    const hasResearch = logs.some(l => l.includes("[URL]") || l.includes("[RESEARCH]"));
    const hasStrategy = logs.some(l => l.includes("[STRATEGY]"));
    const hasVisuals = logs.some(l => l.includes("[VISUALS]") || l.includes("Generating Image"));
    const hasMotion = logs.some(l => l.includes("[PHASE 4]") || l.includes("Animating") || l.includes("[VIDEO]"));
    const hasAudio = logs.some(l => l.includes("ElevenLabs") || l.includes("audio"));

    const nodes: Node[] = [
        {
            id: 'input',
            type: 'input',
            data: { label: 'Creative Brief' },
            position: { x: 0, y: 150 },
            style: getNodeStyle(false, true) // Always completed if started
        },
        {
            id: 'researcher',
            data: { label: 'Market Research' },
            position: { x: 200, y: 50 },
            style: getNodeStyle(isPlanning && !hasStrategy, hasResearch || isPlanned || isGeneratingImages || isImagesComplete || isGeneratingVideos || isVideosComplete || isAssembling || isCompleted)
        },
        {
            id: 'strategist',
            data: { label: 'Brand Strategy' },
            position: { x: 200, y: 250 }, // Parallel to Researcher
            style: getNodeStyle(isPlanning && hasResearch, hasStrategy || isPlanned || isGeneratingImages || isImagesComplete || isGeneratingVideos || isVideosComplete || isAssembling || isCompleted)
        },
        {
            id: 'gemini',
            data: { label: 'Creative Direction' },
            position: { x: 450, y: 150 }, // Converge here
            style: getNodeStyle(isPlanning && hasStrategy, isPlanned || isGeneratingImages || isImagesComplete || isGeneratingVideos || isVideosComplete || isAssembling || isCompleted)
        },
        {
            id: 'flux',
            data: { label: 'Visual Production' },
            position: { x: 700, y: 50 },
            style: getNodeStyle(isGeneratingImages, hasVisuals || isImagesComplete || isGeneratingVideos || isVideosComplete || isAssembling || isCompleted)
        },
        {
            id: 'elevenlabs',
            data: { label: 'Sound Design' },
            position: { x: 700, y: 150 },
            style: getNodeStyle(isGeneratingImages, hasAudio || isImagesComplete || isGeneratingVideos || isVideosComplete || isAssembling || isCompleted)
        },
        {
            id: 'runway',
            data: { label: 'Animation' },
            position: { x: 950, y: 50 },
            style: getNodeStyle(isGeneratingVideos, hasMotion || isVideosComplete || isAssembling || isCompleted)
        },
        {
            id: 'composer',
            data: { label: 'Final Cut' },
            position: { x: 1200, y: 150 },
            style: getNodeStyle(isAssembling, isCompleted)
        },
        {
            id: 'output',
            type: 'output',
            data: { label: 'Distribution Ready' },
            position: { x: 1450, y: 150 },
            style: getNodeStyle(false, isCompleted)
        }
    ];

    const edges: Edge[] = [
        { id: 'e1', source: 'input', target: 'researcher', animated: isPlanning, style: { stroke: '#475569' } },
        { id: 'e2', source: 'input', target: 'strategist', animated: isPlanning, style: { stroke: '#475569' } },
        { id: 'e3', source: 'researcher', target: 'gemini', animated: isPlanning, style: { stroke: '#475569' } },
        { id: 'e4', source: 'strategist', target: 'gemini', animated: isPlanning, style: { stroke: '#475569' } },
        { id: 'e5', source: 'gemini', target: 'flux', animated: isGeneratingImages || isImagesComplete, style: { stroke: '#475569' } },
        { id: 'e6', source: 'gemini', target: 'elevenlabs', animated: isGeneratingImages || isImagesComplete, style: { stroke: '#475569' } },
        { id: 'e7', source: 'flux', target: 'runway', animated: isGeneratingVideos || isVideosComplete, style: { stroke: '#475569' } },
        { id: 'e8', source: 'runway', target: 'composer', animated: isAssembling || isCompleted, style: { stroke: '#475569' } },
        { id: 'e9', source: 'elevenlabs', target: 'composer', animated: isAssembling || isCompleted, style: { stroke: '#475569' } },
        { id: 'e10', source: 'composer', target: 'output', animated: isCompleted, style: { stroke: '#22d3ee', strokeWidth: 2 } }
    ];

    return (
        <div className="w-full h-[400px] bg-slate-950 border border-slate-800 rounded-xl overflow-hidden shadow-2xl mt-12 relative">
            <div className="absolute top-0 left-0 right-0 z-10 px-4 py-2 bg-slate-900/90 backdrop-blur-sm border-b border-slate-800 text-xs font-mono text-slate-400 flex justify-between items-center">
                <span className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-cyan-500" />
                    PRODUCTION_ROADMAP_V1
                </span>
                <span className="flex items-center gap-2">
                    <span className={clsx("w-2 h-2 rounded-full",
                        (isLoading || isPlanning || isGeneratingImages || isGeneratingVideos || isAssembling)
                            ? "bg-cyan-500 animate-pulse"
                            : isCompleted
                                ? "bg-emerald-500"
                                : "bg-slate-600"
                    )}></span>
                    {isCompleted ? 'COMPLETE' : status.toUpperCase().replace(/_/g, ' ')}
                </span>
            </div>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                fitView
                className="bg-slate-950"
                proOptions={{ hideAttribution: true }}
                minZoom={0.5}
                maxZoom={1.5}
            >
                <Background color="#334155" gap={20} size={1} />
                <Controls className="!bg-slate-900 !border-slate-800 !fill-slate-400" />
            </ReactFlow>
        </div >
    );
}
