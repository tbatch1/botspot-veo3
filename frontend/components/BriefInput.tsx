'use client';

import { useState } from 'react';
import { useStore } from '@/lib/store';
import { Sparkles, ArrowRight } from 'lucide-react';

export default function BriefInput() {
    const [input, setInput] = useState('');
    const { createPlan, isLoading } = useStore();

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim()) {
            createPlan(input);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8 text-center">
            <div className="space-y-4">
                <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
                    The AI Creative Director
                </h1>
                <p className="text-xl text-slate-400 max-w-2xl mx-auto">
                    Turn a product URL or description into a broadcast-ready video ad in minutes.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="w-full max-w-2xl relative">
                <div className="relative group">
                    <div className="absolute -inset-1 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Paste a product URL or describe your brand..."
                        className="relative w-full bg-slate-900/90 border border-slate-800 rounded-xl py-6 pl-6 pr-32 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 text-white placeholder:text-slate-500"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-500 text-white px-6 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isLoading ? (
                            <Sparkles className="w-5 h-5 animate-spin" />
                        ) : (
                            <>
                                Generate <ArrowRight className="w-4 h-4" />
                            </>
                        )}
                    </button>
                </div>
            </form>

            <div className="flex gap-4 text-sm text-slate-500">
                <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800">✨ Gemini 1.5 Flash</span>
                <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800">🎨 Imagen 3</span>
                <span className="px-3 py-1 rounded-full bg-slate-900 border border-slate-800">🎬 Runway Gen-3</span>
            </div>
        </div>
    );
}
