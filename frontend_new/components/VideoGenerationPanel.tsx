'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Loader2, Video, Download, Mic2, RefreshCcw, Music2, Volume2 } from 'lucide-react';
import { api, Script, ScriptLine, ElevenLabsLibraryVoice, UnifiedVoice } from '@/lib/api';

interface Scene {
    id: number;
    visual_prompt: string;
    motion_prompt: string;
    duration: number;
    image_path?: string;
    video_path?: string;
}

interface VideoGenerationPanelProps {
    scenes: Scene[];
    status: string;
    finalVideoPath?: string;
    playerMode?: string;
    onApproveFinal: () => void;
    script: Script;
    onUpdateScript: (script: Script) => void;
    onRemixVoiceover: (
        script: Script,
        options?: {
            regenerate_all?: boolean;
            include_sfx?: boolean;
            include_bgm?: boolean;
            bgm_prompt?: string;
            speaker_voice_map?: Record<string, string>;
        }
    ) => Promise<void>;
    isVisible: boolean;
}

export default function VideoGenerationPanel({
    scenes,
    status,
    finalVideoPath,
    playerMode = 'auto',
    onApproveFinal,
    script,
    onUpdateScript,
    onRemixVoiceover,
    isVisible
}: VideoGenerationPanelProps) {
    if (!isVisible) return null;

    const directFinalVideoUrl = finalVideoPath ? api.getAssetUrl(finalVideoPath) : undefined;
    const [finalVideoObjectUrl, setFinalVideoObjectUrl] = useState<string | null>(null);
    const [finalVideoFallbackTried, setFinalVideoFallbackTried] = useState(false);
    const finalVideoSrc = finalVideoObjectUrl || directFinalVideoUrl;

    const normalizedPlayerMode = String(playerMode || 'auto').toLowerCase();

    const tryFinalVideoBlobFallback = async (opts?: { force?: boolean }) => {
        const force = Boolean(opts?.force);
        if (!finalVideoPath) return;
        if (!force && finalVideoFallbackTried) return;
        setFinalVideoFallbackTried(true);

        try {
            const url = api.getAssetUrl(finalVideoPath);
            const resp = await fetch(url, { method: 'GET' });
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const blob = await resp.blob();
            const objectUrl = URL.createObjectURL(blob);
            setFinalVideoObjectUrl((prev) => {
                if (prev) URL.revokeObjectURL(prev);
                return objectUrl;
            });
        } catch (e) {
            console.error('Final video blob fallback failed', e);
        }
    };

    useEffect(() => {
        setFinalVideoFallbackTried(false);
        if (finalVideoObjectUrl) {
            URL.revokeObjectURL(finalVideoObjectUrl);
            setFinalVideoObjectUrl(null);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [finalVideoPath]);

    useEffect(() => {
        return () => {
            if (finalVideoObjectUrl) URL.revokeObjectURL(finalVideoObjectUrl);
        };
    }, [finalVideoObjectUrl]);

    useEffect(() => {
        if (normalizedPlayerMode === 'blob') {
            tryFinalVideoBlobFallback({ force: true });
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [normalizedPlayerMode, finalVideoPath]);

    const [voices, setVoices] = useState<UnifiedVoice[]>([]);
    const [voicesError, setVoicesError] = useState<string | null>(null);
    const [showLibrary, setShowLibrary] = useState(false);
    const [libraryQuery, setLibraryQuery] = useState('');
    const [libraryAccent, setLibraryAccent] = useState('');
    const [libraryGender, setLibraryGender] = useState('');
    const [libraryItems, setLibraryItems] = useState<ElevenLabsLibraryVoice[]>([]);
    const [libraryLoading, setLibraryLoading] = useState(false);
    const [libraryError, setLibraryError] = useState<string | null>(null);
    const [libraryAuditionText, setLibraryAuditionText] = useState('');
    const [libraryAuditions, setLibraryAuditions] = useState<Record<string, string>>({});
    const [editedLines, setEditedLines] = useState<ScriptLine[]>(script?.lines || []);
    const [autoCastOpen, setAutoCastOpen] = useState(false);
    const [autoCastBusy, setAutoCastBusy] = useState(false);
    const [autoCastError, setAutoCastError] = useState<string | null>(null);
    const [autoCastPrefs, setAutoCastPrefs] = useState<Record<string, { accent: string; gender: string; search: string }>>({});
    const [regenerateAll, setRegenerateAll] = useState(true);
    const [includeBgm, setIncludeBgm] = useState(false);
    const [includeSfx, setIncludeSfx] = useState(false);
    const [bgmPrompt, setBgmPrompt] = useState<string>('Bright, sunny indie-pop (guitar, handclaps), ~105 BPM');

    useEffect(() => {
        setEditedLines(script?.lines || []);
        if (!libraryAuditionText) {
            const first = (script?.lines || [])[0]?.text;
            if (first) setLibraryAuditionText(first);
        }
    }, [script?.lines]);

    const speakers = useMemo(() => {
        const list = (editedLines || []).map((l) => String(l.speaker || '').trim()).filter(Boolean);
        return Array.from(new Set(list));
    }, [editedLines]);

    useEffect(() => {
        let mounted = true;
        api.listVoices({ limit: 600 })
            .then((items) => {
                if (!mounted) return;
                setVoices(items);
                setVoicesError(null);
            })
            .catch((err) => {
                if (!mounted) return;
                const msg = err?.response?.data?.detail || err?.message || 'Failed to load voices';
                setVoicesError(msg);
            });
        return () => {
            mounted = false;
        };
    }, []);

    const refreshVoices = async () => {
        try {
            const items = await api.listVoices({ limit: 600 });
            setVoices(items);
            setVoicesError(null);
        } catch (err: any) {
            const msg = err?.response?.data?.detail || err?.message || 'Failed to load voices';
            setVoicesError(msg);
        }
    };

    const guessGender = (speakerName: string) => {
        const s = String(speakerName || '').trim().toLowerCase();
        if (!s) return '';
        if (s.includes('narrator') || s.includes('voiceover') || s === 'vo') return '';
        const female = new Set(['maya', 'ria', 'sarah', 'emma', 'olivia', 'ava', 'mia', 'lily', 'zoe', 'chloe', 'isabella']);
        const male = new Set(['ethan', 'nate', 'daniel', 'mike', 'john', 'alex', 'liam', 'noah', 'jack', 'ben', 'chris']);
        if (female.has(s)) return 'female';
        if (male.has(s)) return 'male';
        return '';
    };

    const autoCast = async () => {
        setAutoCastBusy(true);
        setAutoCastError(null);
        try {
            const nextLines = [...editedLines];

            for (const speaker of speakers) {
                const pref = autoCastPrefs[speaker] || { accent: '', gender: '', search: '' };
                const desiredGender = pref.gender || guessGender(speaker);
                const desiredAccent = pref.accent || '';
                const desiredSearch = pref.search || (speaker.toLowerCase().includes('narrator') ? 'narrator' : '');

                const trySearch = async (featured: boolean) => {
                    return api.searchElevenlabsVoiceLibrary({
                        search: desiredSearch || undefined,
                        accent: desiredAccent || undefined,
                        gender: desiredGender || undefined,
                        featured,
                        page: 1,
                        page_size: 24,
                    });
                };

                let results = await trySearch(true);
                if (!results.voices?.length) results = await trySearch(false);

                const pick = (results.voices || []).find((v) => !!v.preview_url) || (results.voices || [])[0];
                if (!pick) continue;

                const newName = `${speaker} - ${pick.name}`.slice(0, 40);
                const added = await api.addElevenlabsVoiceFromLibrary({
                    public_owner_id: pick.public_owner_id,
                    voice_id: pick.voice_id,
                    new_name: newName,
                });

                for (let i = 0; i < nextLines.length; i++) {
                    if (String(nextLines[i].speaker || '').trim() === speaker) {
                        nextLines[i] = { ...nextLines[i], voice_id: added.voice_id };
                    }
                }
            }

            setEditedLines(nextLines);
            setRegenerateAll(true);
            await refreshVoices();
        } catch (err: any) {
            const msg = err?.response?.data?.detail || err?.message || 'Auto-cast failed';
            setAutoCastError(msg);
        } finally {
            setAutoCastBusy(false);
        }
    };

    const searchLibrary = async (page = 1) => {
        setLibraryLoading(true);
        setLibraryError(null);
        try {
            const res = await api.searchElevenlabsVoiceLibrary({
                search: libraryQuery || undefined,
                accent: libraryAccent || undefined,
                gender: libraryGender || undefined,
                page,
                page_size: 24,
            });
            setLibraryItems(res.voices || []);
        } catch (err: any) {
            const msg = err?.response?.data?.detail || err?.message || 'Failed to load Voice Library';
            setLibraryError(msg);
        } finally {
            setLibraryLoading(false);
        }
    };

    const voiceOptions = useMemo(() => {
        return voices
            .filter((v) => v?.voice_id && v?.name)
            .map((v) => ({
                value: v.voice_id,
                label: v.name,
                meta: [
                    v.provider ? String(v.provider).toUpperCase() : '',
                    v.labels?.gender,
                    (v.labels as any)?.locale || (v.labels as any)?.language,
                    v.category,
                ]
                    .filter(Boolean)
                    .join(' - '),
                preview_url: v.preview_url,
            }));
    }, [voices]);

    const parseTimeRange = (value: string) => {
        const raw = String(value || '').replace(/s/g, '');
        const parts = raw.split('-').map((p) => p.trim());
        const start = parts[0] ? Number(parts[0]) : 0;
        const end = parts[1] ? Number(parts[1]) : undefined;
        return { start: Number.isFinite(start) ? start : 0, end: Number.isFinite(end as any) ? (end as number) : undefined };
    };

    const setLineTime = (idx: number, start: number, end?: number) => {
        const next = [...editedLines];
        const s = Math.max(0, Number(start) || 0);
        const e = end !== undefined ? Math.max(s + 0.1, Number(end) || s + 0.1) : undefined;
        next[idx] = { ...next[idx], time_range: e !== undefined ? `${s.toFixed(1)}-${e.toFixed(1)}s` : `${s.toFixed(1)}s` };
        setEditedLines(next);
    };

    const setLineVoice = (idx: number, voiceId: string) => {
        const next = [...editedLines];
        next[idx] = { ...next[idx], voice_id: voiceId || undefined };
        setEditedLines(next);
        setRegenerateAll(true);
    };

    const auditionLine = async (idx: number) => {
        const line = editedLines[idx];
        const voiceId = String(line?.voice_id || '').trim();
        const text = String(line?.text || '').trim();
        if (!voiceId || !text) return;
        try {
            const res = await api.ttsPreview({ voice_id: voiceId, text });
            const url = api.getAssetUrl(res.audio_path);
            setLibraryAuditions((prev) => ({ ...prev, [`line:${idx}`]: url }));
        } catch (err: any) {
            // Keep it silent; user can see if preview fails via missing audio.
            console.error('Audition failed', err);
        }
    };

    const nudgeLine = (idx: number, deltaSeconds: number) => {
        const { start, end } = parseTimeRange(editedLines[idx]?.time_range || '');
        const nextStart = Math.max(0, start + deltaSeconds);
        const nextEnd = end !== undefined ? Math.max(nextStart + 0.1, end + deltaSeconds) : undefined;
        setLineTime(idx, nextStart, nextEnd);
    };

    const completedVideos = scenes.filter(s => s.video_path).length;
    const totalScenes = scenes.length;
    const progress = (completedVideos / totalScenes) * 100;
    const isGenerating = status === 'generating_videos';
    const isComplete = status === 'videos_complete';
    const isAssembling = status === 'assembling' || status === 'remixing_audio';
    const isFinalComplete = status === 'completed';
    const canRemix = isFinalComplete || isComplete;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="w-full max-w-6xl mx-auto p-6 bg-gradient-to-br from-slate-900/90 to-slate-800/90 backdrop-blur-xl border border-emerald-500/30 rounded-lg shadow-2xl"
        >
            {/* Header */}
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-700/50">
                <Video className="w-6 h-6 text-emerald-400" />
                <h2 className="text-2xl font-bold text-white">
                    {status === 'remixing_audio' ? 'Remixing Audio' : isFinalComplete ? 'Final Video' : 'Video Generation'}
                </h2>
                {(isGenerating || isAssembling) && (
                    <Loader2 className="w-5 h-5 text-emerald-400 animate-spin ml-2" />
                )}
                <span className="ml-auto px-3 py-1 bg-emerald-500/20 text-emerald-400 text-sm rounded-full border border-emerald-500/30">
                    {isFinalComplete ? 'Complete' : 'Approval Gate 3'}
                </span>
            </div>

            {/* Progress Bar */}
            {!isFinalComplete && (
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-slate-400">
                            {isGenerating ? 'Animating videos...' : isAssembling ? 'Assembling final video...' : 'All clips generated'}
                        </span>
                        {!isAssembling && (
                            <span className="text-sm font-bold text-emerald-400">
                                {completedVideos} / {totalScenes}
                            </span>
                        )}
                    </div>
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                        <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: isAssembling ? '100%' : `${progress}%` }}
                            transition={{ duration: 0.5, ease: 'easeOut' }}
                            className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500"
                        />
                    </div>
                </div>
            )}

            {/* Final Video Player */}
            {isFinalComplete && finalVideoPath && (
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="mb-6"
                >
                    <div className="relative aspect-video bg-black rounded-lg overflow-hidden border-2 border-emerald-500/50 shadow-2xl">
                        <video
                            controls
                            autoPlay
                            loop
                            className="w-full h-full"
                            src={finalVideoSrc || undefined}
                            onError={normalizedPlayerMode === 'direct' ? undefined : () => tryFinalVideoBlobFallback()}
                        >
                            Your browser does not support the video tag.
                        </video>
                    </div>

                    {/* Download Button */}
                    <div className="mt-4 flex justify-center">
                        <a
                            href={api.getAssetUrl(finalVideoPath)}
                            download
                            className="flex items-center gap-2 px-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-white font-bold rounded-lg shadow-lg transition-colors"
                        >
                            <Download className="w-5 h-5" />
                            Download Final Video
                        </a>
                    </div>
                </motion.div>
            )}

            {/* Video Clips Grid */}
            {!isFinalComplete && (
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
                                    {scene.video_path ? (
                                        <>
                                            <video
                                                src={api.getAssetUrl(scene.video_path)}
                                                className="w-full h-full object-cover"
                                                muted
                                                loop
                                                onMouseEnter={(e) => e.currentTarget.play()}
                                                onMouseLeave={(e) => e.currentTarget.pause()}
                                            />
                                            <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-1 bg-emerald-500/90 rounded text-xs font-bold text-white">
                                                <CheckCircle2 className="w-3 h-3" />
                                                Complete
                                            </div>
                                        </>
                                    ) : (
                                        <div className="w-full h-full flex flex-col items-center justify-center">
                                            {scene.image_path ? (
                                                <>
                                                    <img
                                                        src={api.getAssetUrl(scene.image_path)}
                                                        alt={`Scene ${scene.id}`}
                                                        className="w-full h-full object-cover opacity-50"
                                                    />
                                                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/50">
                                                        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mb-2" />
                                                        <span className="text-xs text-slate-300">Animating...</span>
                                                    </div>
                                                </>
                                            ) : (
                                                <span className="text-xs text-slate-500">Waiting...</span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Scene Info */}
                                <div className="mt-2 px-2">
                                    <div className="flex items-center justify-between mb-1">
                                        <span className="text-xs font-bold text-emerald-400">Scene {scene.id}</span>
                                        <span className="text-xs text-slate-500">{scene.duration}s</span>
                                    </div>
                                    <p className="text-xs text-slate-400 line-clamp-2">{scene.motion_prompt}</p>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Approve Assembly Button - Only show when videos complete */}
            {isComplete && !isAssembling && !isFinalComplete && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center justify-center pt-6 border-t border-slate-700/50"
                >
                    <button
                        onClick={onApproveFinal}
                        className="group flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white font-bold rounded-lg shadow-lg hover:shadow-emerald-500/50 transition-all"
                    >
                        <CheckCircle2 className="w-5 h-5 group-hover:scale-110 transition-transform" />
                        <span>Approve Videos & Assemble Final</span>
                    </button>
                </motion.div>
            )}

            {/* Info Notices */}
            {isComplete && !isFinalComplete && (
                <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-center">
                    <p className="text-sm text-emerald-300">
                        Clicking approve will combine all clips with audio into the final commercial (~15 seconds)
                    </p>
                </div>
            )}

            {isFinalComplete && (
                <div className="mt-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-center">
                    <p className="text-sm text-emerald-300">
                        Your commercial is ready! Preview above or download to share.
                    </p>
                </div>
            )}

            {/* Audio Remix (VO timing + voice casting) */}
            {canRemix && (
                <div className="mt-6 pt-6 border-t border-slate-700/50">
                    <div className="flex items-center gap-2 mb-4 text-cyan-300">
                        <Mic2 className="w-5 h-5" />
                        <h3 className="font-semibold">Voiceover Remix</h3>
                        <button
                            type="button"
                            onClick={() => {
                                setShowLibrary(true);
                                searchLibrary(1);
                            }}
                            className="ml-auto px-3 py-1.5 rounded bg-slate-800 text-slate-200 hover:bg-slate-700 text-sm"
                        >
                            Browse Voice Library
                        </button>
                        <button
                            type="button"
                            onClick={() => setAutoCastOpen((v) => !v)}
                            className="px-3 py-1.5 rounded bg-slate-800 text-slate-200 hover:bg-slate-700 text-sm"
                        >
                            Auto-cast
                        </button>
                    </div>

                    {voicesError && (
                        <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded text-sm text-red-200">
                            {voicesError}
                        </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                        <label className="flex items-center gap-2 text-sm text-slate-300">
                            <input type="checkbox" checked={regenerateAll} onChange={(e) => setRegenerateAll(e.target.checked)} />
                            Regenerate all VO
                        </label>
                        <label className="flex items-center gap-2 text-sm text-slate-300">
                            <input type="checkbox" checked={includeBgm} onChange={(e) => setIncludeBgm(e.target.checked)} />
                            <Music2 className="w-4 h-4" /> Add music
                        </label>
                        <label className="flex items-center gap-2 text-sm text-slate-300">
                            <input type="checkbox" checked={includeSfx} onChange={(e) => setIncludeSfx(e.target.checked)} />
                            <Volume2 className="w-4 h-4" /> Add SFX
                        </label>
                    </div>

                    {includeBgm && (
                        <div className="mb-4">
                            <label className="block text-xs text-slate-400 mb-1">Music prompt</label>
                            <input
                                value={bgmPrompt}
                                onChange={(e) => setBgmPrompt(e.target.value)}
                                className="w-full px-3 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                placeholder="e.g. bright indie-pop, 105 BPM, guitar + handclaps"
                            />
                        </div>
                    )}

                    {autoCastOpen && (
                        <div className="mb-4 p-3 rounded-lg bg-slate-950/40 border border-slate-800/60">
                            <div className="flex items-center justify-between gap-3">
                                <div>
                                    <div className="text-slate-100 font-semibold text-sm">Auto-cast from Voice Library</div>
                                    <div className="text-xs text-slate-400">Picks voices by accent/gender, adds them to your account, and assigns them to speakers.</div>
                                </div>
                                <button
                                    type="button"
                                    onClick={autoCast}
                                    disabled={autoCastBusy || speakers.length === 0}
                                    className="px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm disabled:opacity-60"
                                >
                                    {autoCastBusy ? 'Casting…' : 'Auto-cast now'}
                                </button>
                            </div>
                            {autoCastError && <div className="mt-2 text-sm text-red-300">{autoCastError}</div>}

                            <div className="mt-3 grid grid-cols-1 md:grid-cols-3 gap-3">
                                {speakers.map((speaker) => {
                                    const pref = autoCastPrefs[speaker] || { accent: '', gender: '', search: '' };
                                    return (
                                        <div key={speaker} className="p-2 rounded bg-slate-950/40 border border-slate-800/60">
                                            <div className="text-xs text-cyan-300 font-mono mb-2">{speaker}</div>
                                            <label className="block text-xs text-slate-400 mb-1">Accent</label>
                                            <input
                                                value={pref.accent}
                                                onChange={(e) =>
                                                    setAutoCastPrefs((prev) => ({ ...prev, [speaker]: { ...pref, accent: e.target.value } }))
                                                }
                                                className="w-full px-2 py-1.5 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                                placeholder="e.g. american, british, irish"
                                            />
                                            <label className="block text-xs text-slate-400 mb-1 mt-2">Gender</label>
                                            <select
                                                value={pref.gender}
                                                onChange={(e) =>
                                                    setAutoCastPrefs((prev) => ({ ...prev, [speaker]: { ...pref, gender: e.target.value } }))
                                                }
                                                className="w-full px-2 py-1.5 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                            >
                                                <option value="">Auto</option>
                                                <option value="male">Male</option>
                                                <option value="female">Female</option>
                                            </select>
                                            <label className="block text-xs text-slate-400 mb-1 mt-2">Search hint</label>
                                            <input
                                                value={pref.search}
                                                onChange={(e) =>
                                                    setAutoCastPrefs((prev) => ({ ...prev, [speaker]: { ...pref, search: e.target.value } }))
                                                }
                                                className="w-full px-2 py-1.5 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                                placeholder="e.g. narrator, upbeat, sarcastic"
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    <div className="space-y-3 max-h-[360px] overflow-auto pr-1">
                        {editedLines.map((line, idx) => {
                            const t = parseTimeRange(line.time_range);
                            const selectedVoice = line.voice_id || '';
                            return (
                                <div key={idx} className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/60">
                                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 mb-2">
                                        <div className="text-xs text-slate-400">
                                            <span className="font-mono text-cyan-300">{line.speaker}</span>
                                            <span className="ml-2">{line.time_range}</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <button
                                                type="button"
                                                onClick={() => nudgeLine(idx, -0.2)}
                                                className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-200 hover:bg-slate-700"
                                            >
                                                -0.2s
                                            </button>
                                            <button
                                                type="button"
                                                onClick={() => nudgeLine(idx, 0.2)}
                                                className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-200 hover:bg-slate-700"
                                            >
                                                +0.2s
                                            </button>
                                            {line.voice_id && (
                                                <button
                                                    type="button"
                                                    onClick={() => auditionLine(idx)}
                                                    className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-200 hover:bg-slate-700"
                                                >
                                                    Audition
                                                </button>
                                            )}
                                        </div>
                                    </div>

                                    <p className="text-sm text-slate-200 mb-3">{line.text}</p>

                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                        <div>
                                            <label className="block text-xs text-slate-400 mb-1">Voice</label>
                                            <select
                                                value={selectedVoice}
                                                onChange={(e) => setLineVoice(idx, e.target.value)}
                                                className="w-full px-2 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                            >
                                                <option value="">Auto (speaker mapping)</option>
                                                {voiceOptions.map((v) => (
                                                    <option key={v.value} value={v.value}>
                                                        {v.label}{v.meta ? ` — ${v.meta}` : ''}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="block text-xs text-slate-400 mb-1">Start (s)</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={t.start}
                                                onChange={(e) => setLineTime(idx, Number(e.target.value), t.end)}
                                                className="w-full px-2 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-xs text-slate-400 mb-1">End (s)</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={t.end ?? ''}
                                                onChange={(e) => setLineTime(idx, t.start, e.target.value === '' ? undefined : Number(e.target.value))}
                                                className="w-full px-2 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                                placeholder="(optional)"
                                            />
                                        </div>
                                    </div>

                                    {libraryAuditions[`line:${idx}`] && (
                                        <div className="mt-2">
                                            <audio controls src={libraryAuditions[`line:${idx}`]} className="w-full h-8 opacity-80" />
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    <div className="mt-4 flex items-center justify-end gap-3">
                        <button
                            type="button"
                            onClick={() => {
                                setEditedLines(script?.lines || []);
                                setRegenerateAll(false);
                            }}
                            className="px-4 py-2 rounded bg-slate-800 text-slate-200 hover:bg-slate-700 text-sm"
                        >
                            Reset
                        </button>
                        <button
                            type="button"
                            onClick={async () => {
                                const nextScript: Script = { ...script, lines: editedLines };
                                onUpdateScript(nextScript);
                                await onRemixVoiceover(nextScript, {
                                    regenerate_all: regenerateAll,
                                    include_bgm: includeBgm,
                                    include_sfx: includeSfx,
                                    bgm_prompt: includeBgm ? bgmPrompt : undefined,
                                });
                            }}
                            className="flex items-center gap-2 px-5 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm"
                        >
                            <RefreshCcw className="w-4 h-4" />
                            Remix Audio & Re-Render
                        </button>
                    </div>
                </div>
            )}

            {/* Voice Library Modal */}
            {showLibrary && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
                    <div className="w-full max-w-4xl rounded-xl bg-slate-900 border border-slate-700 shadow-2xl overflow-hidden">
                        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700/60">
                            <div>
                                <h4 className="text-white font-semibold">ElevenLabs Voice Library</h4>
                                <p className="text-xs text-slate-400">Search accents/tones and add to your account</p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setShowLibrary(false)}
                                className="px-3 py-1.5 rounded bg-slate-800 text-slate-200 hover:bg-slate-700 text-sm"
                            >
                                Close
                            </button>
                        </div>

                        <div className="px-5 py-4 border-b border-slate-800/60 grid grid-cols-1 md:grid-cols-3 gap-3">
                            <div>
                                <label className="block text-xs text-slate-400 mb-1">Search</label>
                                <input
                                    value={libraryQuery}
                                    onChange={(e) => setLibraryQuery(e.target.value)}
                                    className="w-full px-3 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                    placeholder="e.g. Irish, British, upbeat, sarcastic"
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-slate-400 mb-1">Accent</label>
                                <input
                                    value={libraryAccent}
                                    onChange={(e) => setLibraryAccent(e.target.value)}
                                    className="w-full px-3 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                    placeholder="e.g. american, british, australian"
                                />
                            </div>
                            <div>
                                <label className="block text-xs text-slate-400 mb-1">Gender</label>
                                <select
                                    value={libraryGender}
                                    onChange={(e) => setLibraryGender(e.target.value)}
                                    className="w-full px-3 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                >
                                    <option value="">Any</option>
                                    <option value="male">Male</option>
                                    <option value="female">Female</option>
                                </select>
                            </div>
                            <div className="md:col-span-3 flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => searchLibrary(1)}
                                    disabled={libraryLoading}
                                    className="px-4 py-2 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm disabled:opacity-60"
                                >
                                    {libraryLoading ? 'Searching…' : 'Search'}
                                </button>
                                {libraryError && <span className="text-sm text-red-300">{libraryError}</span>}
                            </div>
                            <div className="md:col-span-3">
                                <label className="block text-xs text-slate-400 mb-1">Audition text (optional)</label>
                                <input
                                    value={libraryAuditionText}
                                    onChange={(e) => setLibraryAuditionText(e.target.value)}
                                    className="w-full px-3 py-2 rounded bg-slate-950/60 border border-slate-700 text-slate-200 text-sm"
                                    placeholder="Type a line to audition voices with"
                                />
                            </div>
                        </div>

                        <div className="p-5 max-h-[70vh] overflow-auto">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {libraryItems.map((v) => (
                                    <div key={`${v.public_owner_id}:${v.voice_id}`} className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/60">
                                        <div className="flex items-start justify-between gap-3">
                                            <div>
                                                <div className="text-slate-100 font-semibold">{v.name}</div>
                                                <div className="text-xs text-slate-400 mt-0.5">
                                                    {[v.accent, v.gender, v.age, v.category].filter(Boolean).join(' • ')}
                                                </div>
                                                {v.descriptive && <div className="text-xs text-slate-300 mt-2">{v.descriptive}</div>}
                                            </div>
                                            <button
                                                type="button"
                                                onClick={async () => {
                                                    const newName = `${v.name} (${v.accent || 'voice'})`;
                                                    await api.addElevenlabsVoiceFromLibrary({
                                                        public_owner_id: v.public_owner_id,
                                                        voice_id: v.voice_id,
                                                        new_name: newName.slice(0, 40),
                                                    });
                                                    await refreshVoices();
                                                }}
                                                className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-sm whitespace-nowrap"
                                            >
                                                Add
                                            </button>
                                            <button
                                                type="button"
                                                onClick={async () => {
                                                    const text = (libraryAuditionText || '').trim() || 'Okay. Press play.';
                                                    const res = await api.ttsPreview({ voice_id: v.voice_id, text });
                                                    const url = api.getAssetUrl(res.audio_path);
                                                    setLibraryAuditions((prev) => ({ ...prev, [`lib:${v.voice_id}`]: url }));
                                                }}
                                                className="px-3 py-1.5 rounded bg-slate-800 text-slate-200 hover:bg-slate-700 text-sm whitespace-nowrap"
                                            >
                                                Audition
                                            </button>
                                        </div>
                                        {v.preview_url && (
                                            <div className="mt-2">
                                                <audio controls src={v.preview_url} className="w-full h-8 opacity-80" />
                                            </div>
                                        )}
                                        {libraryAuditions[`lib:${v.voice_id}`] && (
                                            <div className="mt-2">
                                                <audio controls src={libraryAuditions[`lib:${v.voice_id}`]} className="w-full h-8 opacity-90" />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                            {!libraryLoading && libraryItems.length === 0 && (
                                <div className="text-slate-400 text-sm">No results. Try a broader search (e.g. “British”, “Irish”, “Spanish”).</div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </motion.div>
    );
}
