'use client';

import React from 'react';
import { VideoSequencer } from '../../components/VideoSequencer';
import type { Sequence } from '../../types/sequence';

export default function SequencerPage() {
  const userId = 'demo-user'; // In production, get this from auth

  const handleSequenceCreated = (sequence: Sequence) => {
    console.log('New sequence created:', sequence);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Video Sequencer
          </h1>
          <p className="text-lg text-gray-600">
            Create multi-scene videos with Google Veo 3.1 and seamless continuity
          </p>
        </div>

        <VideoSequencer
          userId={userId}
          onSequenceCreated={handleSequenceCreated}
        />
      </div>
    </div>
  );
}
