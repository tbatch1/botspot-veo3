'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Cpu, CheckCircle, AlertTriangle, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { useStore } from '@/lib/store';

export default function LiveLog() {
    const { project, isLoading, error } = useStore();
    const scrollRef = useRef<HTMLDivElement>(null);
    const [logs, setLogs] = useState<string[]>([]);

    // Use real logs from backend if available
    const displayLogs = project?.logs && project.logs.length > 0 ? project.logs : logs;

    // Simulate connection logs only if no project yet
    useEffect(() => {
        if (isLoading && !project) {
            setLogs([
                `[${new Date().toLocaleTimeString()}] Establishing Neural Uplink...`,
                `[${new Date().toLocaleTimeString()}] Handshaking with GPT-5.2 (OpenAI)...`
            ]);
        }
    }, [isLoading, project]);


    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs, project?.status, isLoading]);

    if (!project && !isLoading) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-4xl mx-auto mt-8 bg-black/80 border border-slate-800 rounded-xl overflow-hidden font-mono text-xs shadow-2xl"
        >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
                <div className="flex items-center gap-2 text-slate-400">
                    <Terminal className="w-4 h-4" />
                    <span>NEURAL_LOG_STREAM</span>
                </div>
                <div className="flex items-center gap-2">
                    {isLoading && <Loader2 className="w-3 h-3 animate-spin text-cyan-500" />}
                    <div className={clsx("w-2 h-2 rounded-full", isLoading ? "bg-cyan-500 animate-pulse" : "bg-slate-600")} />
                </div>
            </div>

            {/* Log Content */}
            <div
                ref={scrollRef}
                className="h-48 overflow-y-auto p-4 space-y-1 text-slate-300"
            >
                {displayLogs.map((log, i) => (
                    <div key={i} className="flex gap-2">
                        <span className="text-slate-600">{'>'}</span>
                        <span className={clsx(
                            log.includes("[STRATEGY]") ? "text-cyan-400 font-bold" :
                                log.includes("[FLUX PRO]") ? "text-purple-400" :
                                    log.includes("[SUCCESS]") ? "text-green-400" :
                                        log.includes("[ERROR]") ? "text-red-400" :
                                            "text-slate-300"
                        )}>
                            {log}
                        </span>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex gap-2 animate-pulse text-cyan-500/50">
                        <span className="text-slate-600">{'>'}</span>
                        <span>Processing...</span>
                    </div>
                )}
            </div>
        </motion.div>
    );
}
