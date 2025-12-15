'use client';

import { useStore } from '@/lib/store';
import BriefInput from '@/components/BriefInput';
import StoryboardBotspot from '@/components/StoryboardBotspot';
import { api } from '@/lib/api';

export default function BotspotPage() {
    const { project } = useStore();

    return (
        <div className="min-h-screen">
            {!project ? (
                <BriefInput />
            ) : (
                <div className="space-y-12 pb-20">
                    <StoryboardBotspot />

                    {project.status === 'completed' && project.final_video_path && (
                        <div className="max-w-4xl mx-auto mt-12 animate-in zoom-in duration-500">
                            <h2 className="text-3xl font-bold text-center mb-6 bg-gradient-to-r from-green-400 to-emerald-600 bg-clip-text text-transparent">Final Production</h2>
                            <div className="aspect-video rounded-2xl overflow-hidden shadow-2xl shadow-green-900/20 border border-slate-800">
                                <video
                                    controls
                                    className="w-full h-full"
                                    src={api.getAssetUrl(project.final_video_path)}
                                />
                            </div>
                            <div className="flex justify-center mt-6">
                                <a
                                    href={api.getAssetUrl(project.final_video_path)}
                                    download
                                    className="text-slate-400 hover:text-white transition-colors underline"
                                >
                                    Download Video
                                </a>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
