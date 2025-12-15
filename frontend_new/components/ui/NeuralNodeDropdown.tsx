'use client';

import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
    Node,
    Edge,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    MarkerType,
    Handle,
    Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronDown, Zap } from 'lucide-react';
import clsx from 'clsx';

// --- Types ---

export interface NeuralOption {
    value: string;
    label: string;
    icon?: string;
    thumbnail?: string;
    description?: string;
    preview?: string;
}

// --- Custom Node Types ---

const OptionNode = ({ data, isConnectable }: any) => {
    return (
        <div className={clsx(
            "px-4 py-3 rounded-xl border-2 transition-all duration-300 min-w-[180px] text-left cursor-pointer relative group overflow-hidden",
            data.isSelected
                ? "bg-cyan-500/20 border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.5)]"
                : "bg-slate-900/90 border-slate-700 hover:border-cyan-500/50 hover:shadow-[0_0_10px_rgba(34,211,238,0.2)]"
        )}>
            <Handle type="target" position={Position.Left} isConnectable={isConnectable} className="!bg-cyan-500 !w-2 !h-2" />

            <div className="flex items-start gap-3">
                {/* Thumbnail or Icon */}
                {data.thumbnail && (
                    <div className="w-12 h-12 rounded-lg overflow-hidden flex-shrink-0 border border-slate-600">
                        <img src={data.thumbnail} alt={data.label} className="w-full h-full object-cover" />
                    </div>
                )}
                {!data.thumbnail && data.icon && (
                    <div className="text-2xl flex-shrink-0">{data.icon}</div>
                )}

                <div className="flex-1 min-w-0">
                    <div className={clsx(
                        "font-bold text-sm truncate",
                        data.isSelected ? "text-cyan-100" : "text-slate-200 group-hover:text-white"
                    )}>
                        {data.label}
                    </div>
                    {data.description && (
                        <div className="text-[10px] text-slate-400 leading-tight mt-1 line-clamp-2">
                            {data.description}
                        </div>
                    )}
                    {data.preview && (
                        <div className="text-[10px] text-slate-500 italic mt-1 truncate">
                            {data.preview}
                        </div>
                    )}
                </div>
            </div>

            {data.isSelected && (
                <div className="absolute inset-0 rounded-xl animate-pulse bg-cyan-400/5 pointer-events-none" />
            )}
        </div>
    );
};

const RootNode = ({ data }: any) => {
    return (
        <div className="px-4 py-2 rounded-lg bg-purple-600/20 border border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.4)] text-purple-100 font-bold text-sm min-w-[100px] text-center">
            {data.label}
            <Handle type="source" position={Position.Right} className="!bg-purple-500 !w-2 !h-2" />
        </div>
    );
};

const nodeTypes = {
    option: OptionNode,
    root: RootNode,
};

// --- Props ---

interface NeuralNodeDropdownProps {
    label: string;
    options: (string | NeuralOption)[];
    value: string | string[]; // Support array for multi-select
    onChange: (value: string | string[]) => void;
    color?: 'cyan' | 'purple' | 'green';
    multiSelect?: boolean;
}

export default function NeuralNodeDropdown({
    label,
    options,
    value,
    onChange,
    color = 'cyan',
    multiSelect = false
}: NeuralNodeDropdownProps) {
    const [isOpen, setIsOpen] = useState(false);

    // Normalize options to NeuralOption[]
    const normalizedOptions: NeuralOption[] = options.map(opt =>
        typeof opt === 'string' ? { value: opt, label: opt } : opt
    );

    // Helper to check if an option is selected
    const isSelected = (optValue: string) => {
        if (Array.isArray(value)) {
            return value.includes(optValue);
        }
        return value === optValue;
    };

    // --- Graph Construction ---
    const initialNodes: Node[] = [
        {
            id: 'root',
            type: 'root',
            position: { x: 50, y: 20 },
            data: { label: label }
        },
        ...normalizedOptions.map((opt, idx) => ({
            id: opt.value,
            type: 'option',
            position: { x: 250, y: 100 + idx * 70 }, // Tighter X (250 vs 350), slightly more Y spacing
            data: {
                ...opt,
                isSelected: isSelected(opt.value)
            },
        }))
    ];

    const initialEdges: Edge[] = normalizedOptions.map((opt) => ({
        id: `e-root-${opt.value}`,
        source: 'root',
        target: opt.value,
        animated: isSelected(opt.value),
        style: {
            stroke: isSelected(opt.value) ? '#22d3ee' : '#475569',
            strokeWidth: isSelected(opt.value) ? 2 : 1,
        },
        markerEnd: {
            type: MarkerType.ArrowClosed,
            color: isSelected(opt.value) ? '#22d3ee' : '#475569',
        },
    }));

    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    // Update graph when value changes or opens
    useEffect(() => {
        if (isOpen) {
            setNodes((nds) => nds.map((node) => {
                if (node.type === 'option') {
                    return { ...node, data: { ...node.data, isSelected: isSelected(node.id) } };
                }
                return node;
            }));

            setEdges((eds) => eds.map((edge) => {
                const selected = isSelected(edge.target);
                return {
                    ...edge,
                    animated: selected,
                    style: {
                        stroke: selected ? '#22d3ee' : '#475569',
                        strokeWidth: selected ? 2 : 1,
                        opacity: selected ? 1 : 0.3
                    },
                    markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: selected ? '#22d3ee' : '#475569',
                    },
                };
            }));
        }
    }, [value, isOpen, setNodes, setEdges]);

    const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
        if (node.type === 'option') {
            if (multiSelect) {
                const currentValues = Array.isArray(value) ? value : [value];
                const newValue = currentValues.includes(node.id)
                    ? currentValues.filter(v => v !== node.id) // Deselect
                    : [...currentValues, node.id]; // Select
                onChange(newValue);
            } else {
                onChange(node.id);
                // Optional: Close on select after a delay?
                // setTimeout(() => setIsOpen(false), 500); 
            }
        }
    }, [onChange, value, multiSelect]);

    // Format display value
    const displayValue = Array.isArray(value)
        ? value.length > 0 ? `${value.length} selected` : "Select..."
        : normalizedOptions.find(o => o.value === value)?.label || value || "Select...";

    // --- Portal Logic ---
    const [mounted, setMounted] = useState(false);
    useEffect(() => {
        setMounted(true);
        return () => setMounted(false);
    }, []);

    // Use Portal if mounted, otherwise null (SSR safety)
    const { createPortal } = require('react-dom');

    const dropdownContent = (
        <AnimatePresence>
            {isOpen && (
                <div className="fixed inset-0 z-[9999] flex items-center justify-center pointer-events-none">
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setIsOpen(false)}
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm pointer-events-auto"
                    />

                    {/* Graph Container - Modal Mode */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        className="relative w-[800px] h-[600px] bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden ring-1 ring-cyan-500/20 pointer-events-auto"
                    >
                        <div className="absolute top-4 right-4 z-10">
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 rounded-full bg-slate-900/80 text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="w-full h-full bg-[url('/grid.svg')] bg-repeat opacity-20 pointer-events-none absolute inset-0" />

                        <ReactFlow
                            nodes={nodes}
                            edges={edges}
                            onNodesChange={onNodesChange}
                            onEdgesChange={onEdgesChange}
                            onNodeClick={onNodeClick}
                            nodeTypes={nodeTypes}
                            fitView
                            attributionPosition="bottom-right"
                            className="bg-slate-950"
                        >
                            <Background color="#334155" gap={20} size={1} />
                            <Controls className="!bg-slate-900 !border-slate-800 !fill-slate-400" />
                        </ReactFlow>

                        <div className="absolute bottom-4 left-4 right-4 pointer-events-none">
                            <p className="text-center text-xs text-slate-500 font-mono">
                                NEURAL LINK ACTIVE // {multiSelect ? "MULTI-SELECT ENABLED" : "SELECT NODE TO CONFIGURE"}
                            </p>
                        </div>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );





    return (
        <div className={clsx("relative", isOpen ? "z-50" : "z-10")}>
            {/* Trigger Button */}
            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setIsOpen(!isOpen)}
                className={clsx(
                    "w-full flex items-center justify-between px-4 py-3 rounded-xl border transition-all duration-300 group",
                    isOpen
                        ? "bg-slate-900 border-cyan-500 shadow-[0_0_20px_rgba(34,211,238,0.15)]"
                        : "bg-slate-900/50 border-slate-700 hover:border-cyan-500/50"
                )}
            >
                <div className="flex items-center gap-3">
                    <div className={clsx(
                        "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                        isOpen ? "bg-cyan-500/20 text-cyan-400" : "bg-slate-800 text-slate-400 group-hover:text-cyan-400"
                    )}>
                        <Zap className="w-4 h-4" />
                    </div>
                    <div className="text-left">
                        <div className="text-xs text-slate-500 uppercase tracking-wider font-semibold">{label}</div>
                        <div className="text-white font-medium truncate max-w-[150px]">{displayValue}</div>
                    </div>
                </div>
                <ChevronDown className={clsx("w-5 h-5 text-slate-500 transition-transform", isOpen && "rotate-180 text-cyan-400")} />
            </motion.button>

            {/* Dropdown / Modal (Portaled) */}
            {mounted && createPortal(dropdownContent, document.body)}
        </div>
    );
}
