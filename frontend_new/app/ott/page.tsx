'use client';

import React from 'react';
import OTTWorkflowCanvas from '@/components/OTTWorkflowCanvas';
import TerminalLog from '@/components/TerminalLog';
import { motion } from 'framer-motion';

export default function OTTPage() {
    return (
        <div className="flex h-screen w-screen bg-[#020617] bg-[url('/grid.svg')] bg-fixed overflow-hidden">



            {/* CENTER PANE: The n8n Workflow Canvas (80%) */}
            <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="flex-1 h-full relative z-0 overflow-hidden"
            >
                <div className="h-full w-full overflow-y-auto">
                    {/* Integrated Node Graph */}
                    <OTTWorkflowCanvas />

                    {/* Helper text for editing */}
                    <div className="absolute bottom-8 left-0 right-0 text-center pointer-events-none">
                        <span className="px-4 py-2 bg-slate-900/80 rounded-full text-slate-500 text-xs shadow-lg backdrop-blur border border-slate-800">
                            Neural Pipeline Active • Select nodes to inspect
                        </span>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
