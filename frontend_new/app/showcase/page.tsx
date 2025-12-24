import { Suspense } from 'react';
import ShowroomClient from './showroom-client';

export default function ShowcasePage() {
    return (
        <Suspense fallback={<div className="min-h-screen bg-[#020617] text-slate-400 p-6">Loading…</div>}>
            <ShowroomClient />
        </Suspense>
    );
}
