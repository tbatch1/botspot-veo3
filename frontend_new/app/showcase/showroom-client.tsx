'use client';

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';

type ManifestItem = {
    id?: string;
    key?: string;
    created_at?: string;
    name: string;
    url: string;
    category: string;
    video: string;
    plan?: string | null;
    project_id?: string | null;
    signature?: string | null;
};

type ShowcaseManifest = {
    generated_at: string;
    narrator_voice_id?: string;
    items: ManifestItem[];
    errors?: { key: string; name: string; error: string }[];
    notes?: string[];
};

const DEFAULT_API_URL = 'http://localhost:4000/api';
const DEFAULT_SOURCE = 'showroom';

function getApiUrl() {
    const raw = process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;
    return raw.replace(/\/+$/, '');
}

function getItemKey(item: ManifestItem): string {
    return String(item.id || item.key || item.video || item.name || '');
}

function loadFavs(key: string): Record<string, boolean> {
    try {
        const raw = localStorage.getItem(key);
        if (!raw) return {};
        const parsed = JSON.parse(raw);
        return parsed && typeof parsed === 'object' ? parsed : {};
    } catch {
        return {};
    }
}

function saveFavs(key: string, favs: Record<string, boolean>) {
    try {
        localStorage.setItem(key, JSON.stringify(favs));
    } catch {
        // ignore
    }
}

export default function ShowroomClient() {
    const searchParams = useSearchParams();
    const source = (searchParams.get('pack') || DEFAULT_SOURCE).trim() || DEFAULT_SOURCE;
    const isShowroom = source === 'showroom';

    const apiUrl = useMemo(() => getApiUrl(), []);
    const manifestUrl = isShowroom
        ? `${apiUrl}/showroom/manifest`
        : `${apiUrl}/assets/${encodeURIComponent(source)}/showcase_manifest.json`;

    const [manifest, setManifest] = useState<ShowcaseManifest | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshIndex, setRefreshIndex] = useState(0);
    const [importing, setImporting] = useState(false);
    const [favs, setFavs] = useState<Record<string, boolean>>({});

    const favKey = `showcase_favs:${source}`;

    useEffect(() => {
        setFavs(loadFavs(favKey));
    }, [favKey]);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setError(null);

        fetch(manifestUrl, { cache: 'no-store' })
            .then(async (r) => {
                if (!r.ok) throw new Error(`Failed to load manifest (${r.status})`);
                return (await r.json()) as ShowcaseManifest;
            })
            .then((data) => {
                if (cancelled) return;
                setManifest(data);
            })
            .catch((e: unknown) => {
                if (cancelled) return;
                setError(e instanceof Error ? e.message : String(e));
            })
            .finally(() => {
                if (cancelled) return;
                setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, [manifestUrl, refreshIndex]);

    const items = manifest?.items || [];
    const favoriteItems = items.filter((i) => favs[getItemKey(i)]);

    function toggleFav(itemKey: string) {
        setFavs((prev) => {
            const next = { ...prev, [itemKey]: !prev[itemKey] };
            saveFavs(favKey, next);
            return next;
        });
    }

    async function deleteFromShowroom(item: ManifestItem) {
        if (!isShowroom) return;
        const itemId = String(item.id || '');
        if (!itemId) return;

        const ok = window.confirm('Delete this video from the showroom?');
        if (!ok) return;

        try {
            const r = await fetch(`${apiUrl}/showroom/item/${encodeURIComponent(itemId)}`, {
                method: 'DELETE',
            });
            if (!r.ok) {
                const msg = await r.text();
                throw new Error(msg || `Delete failed (${r.status})`);
            }

            const itemKey = getItemKey(item);
            setManifest((prev) => {
                if (!prev) return prev;
                return { ...prev, items: (prev.items || []).filter((it) => getItemKey(it) !== itemKey) };
            });
            setFavs((prev) => {
                const next = { ...prev };
                delete next[itemKey];
                saveFavs(favKey, next);
                return next;
            });
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : String(e));
        }
    }

    async function restoreShowcasePack() {
        if (!isShowroom) return;
        const ok = window.confirm(
            'Restore the showroom to the best 15s showcase pack (cached VO + music + endcards)? This clears the current list (keeps files on disk).'
        );
        if (!ok) return;
        setImporting(true);
        setError(null);
        try {
            const r = await fetch(`${apiUrl}/showroom/restore_best_15s?pack=showcase_pack_edge&delete_files=false`, {
                method: 'POST',
            });
            if (!r.ok) {
                const msg = await r.text();
                throw new Error(msg || `Restore failed (${r.status})`);
            }
            setRefreshIndex((i) => i + 1);
        } catch (e: unknown) {
            setError(e instanceof Error ? e.message : String(e));
        } finally {
            setImporting(false);
        }
    }

    return (
        <div className="min-h-screen w-full bg-[#020617] bg-[url('/grid.svg')] bg-fixed text-slate-100">
            <div className="max-w-6xl mx-auto px-6 py-10">
                <div className="flex items-start justify-between gap-6">
                    <div>
                        <h1 className="text-2xl font-semibold">Showroom</h1>
                        <p className="text-slate-400 text-sm mt-2">
                            Source: <span className="text-slate-200 font-mono">{source}</span>
                        </p>
                        <p className="text-slate-500 text-xs mt-1">
                            Manifest: <span className="font-mono">{manifestUrl}</span>
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link
                            href="/ott"
                            className="px-3 py-2 rounded-lg bg-slate-900/70 text-slate-200 text-sm border border-slate-800 hover:border-slate-600"
                        >
                            Back to Studio
                        </Link>
                        <button
                            onClick={() => setRefreshIndex((i) => i + 1)}
                            className="px-3 py-2 rounded-lg bg-slate-900/70 text-slate-200 text-sm border border-slate-800 hover:border-slate-600"
                        >
                            Refresh
                        </button>
                    </div>
                </div>


                {loading && <div className="mt-10 text-slate-400">Loading…</div>}
                {error && (
                    <div className="mt-10 rounded-lg border border-red-900/50 bg-red-950/20 p-4 text-red-200">
                        {error}
                    </div>
                )}


                {!loading && !error && !items.length && (
                    <div className="mt-10 text-slate-400 text-sm">No items yet.</div>
                )}

                {!!favoriteItems.length && (
                    <div className="mt-10">
                        <h2 className="text-lg font-semibold">Favorites</h2>
                        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                            {favoriteItems.map((item) => {
                                const itemKey = getItemKey(item);
                                return (
                                    <FavoriteCard
                                        key={itemKey}
                                        itemKey={itemKey}
                                        item={item}
                                        apiUrl={apiUrl}
                                        source={source}
                                        onToggleFav={() => toggleFav(itemKey)}
                                        onDelete={isShowroom ? () => deleteFromShowroom(item) : undefined}
                                        fav
                                    />
                                );
                            })}
                        </div>
                    </div>
                )}

                {!!items.length && (
                    <div className="mt-10">
                        <h2 className="text-lg font-semibold">All Ads</h2>
                        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
                            {items.map((item) => {
                                const itemKey = getItemKey(item);
                                return (
                                    <FavoriteCard
                                        key={itemKey}
                                        itemKey={itemKey}
                                        item={item}
                                        apiUrl={apiUrl}
                                        source={source}
                                        onToggleFav={() => toggleFav(itemKey)}
                                        onDelete={isShowroom ? () => deleteFromShowroom(item) : undefined}
                                        fav={!!favs[itemKey]}
                                    />
                                );
                            })}
                        </div>
                    </div>
                )}

                {!!manifest?.errors?.length && (
                    <div className="mt-10 rounded-xl border border-yellow-900/50 bg-yellow-950/20 p-4">
                        <div className="font-semibold text-yellow-100">Errors</div>
                        <div className="mt-2 text-yellow-100/90 text-sm space-y-1">
                            {manifest.errors.map((e) => (
                                <div key={e.key}>
                                    {e.name}: <span className="font-mono text-xs">{e.error}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

function FavoriteCard({
    item,
    itemKey,
    apiUrl,
    source,
    fav,
    onToggleFav,
    onDelete,
}: {
    item: ManifestItem;
    itemKey: string;
    apiUrl: string;
    source: string;
    fav: boolean;
    onToggleFav: () => void;
    onDelete?: () => void;
}) {
    const videoUrl = `${apiUrl}/assets/${encodeURIComponent(source)}/${encodeURIComponent(item.video)}`;
    const planUrl = item.plan ? `${apiUrl}/assets/${encodeURIComponent(item.plan)}` : null;

    return (
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden">
            <div className="p-4 flex items-start justify-between gap-4">
                <div>
                    <div className="font-semibold">{item.name}</div>
                    <div className="text-slate-400 text-sm">{item.category}</div>
                    <div className="text-slate-500 text-xs mt-1 font-mono">{item.url}</div>
                    {item.created_at && <div className="text-slate-600 text-xs mt-1 font-mono">{item.created_at}</div>}
                </div>
                <div className="flex items-center gap-2">
                    {onDelete && <KebabMenu itemKey={itemKey} onDelete={onDelete} />}
                    <button
                        onClick={onToggleFav}
                        className={`px-3 py-2 rounded-lg text-sm border ${
                            fav
                                ? 'bg-emerald-900/30 border-emerald-700 text-emerald-100'
                                : 'bg-slate-900/50 border-slate-700 text-slate-200 hover:border-slate-500'
                        }`}
                    >
                        {fav ? 'Favorited' : 'Favorite'}
                    </button>
                </div>
            </div>

            <div className="bg-black">
                <video className="w-full h-auto" controls preload="metadata" src={videoUrl} />
            </div>

            <div className="p-4 flex flex-wrap gap-2">
                <a
                    href={videoUrl}
                    download
                    className="px-3 py-2 rounded-lg bg-slate-900/60 text-slate-200 text-sm border border-slate-800 hover:border-slate-600"
                >
                    Download MP4
                </a>
                {planUrl && (
                    <a
                        href={planUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-2 rounded-lg bg-slate-900/60 text-slate-200 text-sm border border-slate-800 hover:border-slate-600"
                    >
                        Open Plan JSON
                    </a>
                )}
            </div>
        </div>
    );
}

function KebabMenu({ itemKey, onDelete }: { itemKey: string; onDelete: () => void }) {
    const [open, setOpen] = useState(false);
    const rootRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (!open) return;

        function onDocClick(e: MouseEvent) {
            const root = rootRef.current;
            if (!root) return;
            if (e.target instanceof Node && root.contains(e.target)) return;
            setOpen(false);
        }

        function onKeyDown(e: KeyboardEvent) {
            if (e.key === 'Escape') setOpen(false);
        }

        document.addEventListener('mousedown', onDocClick);
        document.addEventListener('keydown', onKeyDown);
        return () => {
            document.removeEventListener('mousedown', onDocClick);
            document.removeEventListener('keydown', onKeyDown);
        };
    }, [open]);

    return (
        <div ref={rootRef} className="relative">
            <button
                type="button"
                aria-label="More options"
                aria-expanded={open}
                onClick={() => setOpen((v) => !v)}
                className="cursor-pointer select-none px-2 py-2 rounded-lg bg-slate-900/50 border border-slate-700 text-slate-200 hover:border-slate-500 flex items-center justify-center"
            >
                ⋮
            </button>
            {open && (
                <div className="absolute right-0 mt-2 w-44 rounded-xl border border-slate-800 bg-slate-950/95 shadow-xl overflow-hidden z-10">
                    <button
                        type="button"
                        className="w-full text-left px-3 py-2 text-sm text-red-200 hover:bg-red-950/40"
                        onClick={() => {
                            setOpen(false);
                            onDelete();
                        }}
                    >
                        Delete
                        <span className="block text-xs text-red-200/70 font-mono mt-1">{itemKey.slice(0, 8)}</span>
                    </button>
                </div>
            )}
        </div>
    );
}
