'use client';

import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal } from 'lucide-react';
import clsx from 'clsx';
import { useStore } from '@/lib/store';

export default function TerminalLog() {
    const { project, isLoading } = useStore();
    const scrollRef = useRef<HTMLDivElement>(null);
    const [logs, setLogs] = useState<string[]>([]);

    // Use real logs from backend if available
    const displayLogs = project?.logs && project.logs.length > 0 ? project.logs : logs;

    // Inject system error if present
    const finalLogs = useStore((state) => state.error)
        ? [...displayLogs, `[SYSTEM ERROR] ${useStore.getState().error}`]
        : displayLogs;

    // Simulate "Boot Sequence" only if no project yet
    useEffect(() => {
        if (isLoading && !project) {
            setLogs([
                `[SYSTEM] Initializing Neural Uplink...`,
                `[SYSTEM] Handshaking with Claude Opus (Strategist)...`,
                `[SYSTEM] Allocating Flux 1.1 Pro VRAM...`,
                `[SYSTEM] Establishing Secure Link to Gemini Vision...`
            ]);
        }
    }, [isLoading, project]);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [finalLogs, isLoading]);

    return (
        <div className="flex flex-col h-full bg-black/90 backdrop-blur-xl border-r border-slate-800/50 overflow-hidden font-mono text-[10px] sm:text-xs">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 bg-slate-900/50 border-b border-slate-800/50">
                <div className="flex items-center gap-2 text-cyan-400/80">
                    <Terminal className="w-3 h-3" />
                    <span className="tracking-widest uppercase">Live_Intelligence</span>
                </div>
                <div className="flex items-center gap-2">
                    {isLoading ? (
                        <span className="flex items-center gap-1 text-cyan-500 animate-pulse">
                            <span className="w-1.5 h-1.5 bg-cyan-500 rounded-full" />
                            PROCESSING
                        </span>
                    ) : (
                        <span className="flex items-center gap-1 text-slate-600">
                            <span className="w-1.5 h-1.5 bg-slate-600 rounded-full" />
                            IDLE
                        </span>
                    )}
                </div>
            </div>

            {/* Log Stream */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-3 space-y-1.5"
                style={{ scrollBehavior: 'smooth' }}
            >
                {/* CRT Scanline Overlay */}
                <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%] opacity-20" />

                <AnimatePresence initial={false}>
                    {finalLogs.map((log: string, i: number) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="flex gap-2"
                        >
                            <span className="text-slate-700 shrink-0">{new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
                            <span className="text-slate-600 shrink-0">{'>'}</span>
                            <span className={clsx(
                                "break-all",
                                log.includes("[STRATEGY]") ? "text-cyan-400 font-bold" :
                                    log.includes("[FLUX PRO]") ? "text-purple-400" :
                                        log.includes("[SUCCESS]") ? "text-emerald-400" :
                                            log.includes("[ERROR]") ? "text-red-500 font-bold" :
                                                log.includes("[CRITIC]") ? "text-amber-400" :
                                                    log.includes("FAIL") ? "text-red-400" :
                                                        "text-slate-300"
                            )}>
                                {log}
                            </span>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="flex gap-2 text-cyan-500/50 animate-pulse"
                    >
                        <span className="text-slate-600">{'>'}</span>
                        <span className="flex items-center gap-1">
                            Thinking <span className="animate-bounce">_</span>
                        </span>
                    </motion.div>
                )}
            </div>

            {/* Status Footer */}
            <div className="px-3 py-1.5 bg-slate-900/30 border-t border-slate-800/50 flex justify-between text-[9px] text-slate-500">
                <span>MEM: 24GB VRAM ALLOCATED</span>
                <span>LATENCY: 42ms</span>
            </div>
        </div>
    );
}
