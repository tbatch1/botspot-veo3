'use client';

import React, { useState } from 'react';
import type { Sequence } from '../../types/sequence';

interface ExportPanelProps {
  sequence: Sequence;
  onExport: () => Promise<void>;
  className?: string;
}

export function ExportPanel({ sequence, onExport, className = '' }: ExportPanelProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const completedScenes = sequence.scenes.filter((s) => s.status === 'completed');
  const totalScenes = sequence.scenes.length;
  const isReadyToExport = completedScenes.length === totalScenes && totalScenes > 0;
  const isExported = sequence.status === 'exported' && sequence.export?.finalVideoUrl;

  const handleExport = async () => {
    setIsExporting(true);
    setExportError(null);

    try {
      await onExport();
    } catch (error: any) {
      setExportError(error.message || 'Export failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
  };

  const downloadVideo = () => {
    if (sequence.export?.finalVideoUrl) {
      const link = document.createElement('a');
      link.href = sequence.export.finalVideoUrl;
      link.download = `${sequence.title.replace(/\s+/g, '-')}-combined.mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Export Final Video</h3>

        {/* Export Status */}
        {!isExported && (
          <div className="mb-6">
            <div className="flex items-start gap-3 mb-4">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isReadyToExport ? 'bg-green-100' : 'bg-yellow-100'}`}>
                {isReadyToExport ? (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-green-600">
                    <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z" />
                  </svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-yellow-600">
                    <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z" />
                    <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z" />
                  </svg>
                )}
              </div>
              <div className="flex-1">
                <p className={`font-medium ${isReadyToExport ? 'text-green-900' : 'text-yellow-900'}`}>
                  {isReadyToExport ? 'Ready to export' : 'Not ready yet'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {isReadyToExport
                    ? 'All scenes are completed and ready to be combined'
                    : `${completedScenes.length} of ${totalScenes} scenes completed`}
                </p>
              </div>
            </div>

            {/* Progress Bar */}
            {!isReadyToExport && totalScenes > 0 && (
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(completedScenes.length / totalScenes) * 100}%` }}
                />
              </div>
            )}

            {/* Export Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Total Scenes</p>
                <p className="text-xl font-bold text-gray-900">{totalScenes}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Total Duration</p>
                <p className="text-xl font-bold text-gray-900">{formatDuration(sequence.totalDuration)}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Total Cost</p>
                <p className="text-xl font-bold text-gray-900">
                  ${(sequence.totalCost.actual || sequence.totalCost.estimated).toFixed(4)}
                </p>
              </div>
            </div>

            {/* Export Error */}
            {exportError && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm font-medium text-red-800 mb-1">Export Failed</p>
                <p className="text-xs text-red-700">{exportError}</p>
              </div>
            )}

            {/* Export Button */}
            <button
              onClick={handleExport}
              disabled={!isReadyToExport || isExporting || sequence.status === 'exporting'}
              className="w-full px-4 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isExporting || sequence.status === 'exporting' ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Exporting... (This may take a few minutes)</span>
                </>
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z" />
                    <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z" />
                  </svg>
                  <span>Export Final Video</span>
                </>
              )}
            </button>

            <p className="text-xs text-gray-500 text-center mt-2">
              FFmpeg will combine all scenes into a single video file
            </p>
          </div>
        )}

        {/* Export Success */}
        {isExported && sequence.export && (
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="text-green-600">
                  <path d="M10.97 4.97a.75.75 0 0 1 1.07 1.05l-3.99 4.99a.75.75 0 0 1-1.08.02L4.324 8.384a.75.75 0 1 1 1.06-1.06l2.094 2.093 3.473-4.425a.267.267 0 0 1 .02-.022z" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="font-medium text-green-900">Export Complete!</p>
                <p className="text-sm text-green-700 mt-1">
                  Your video has been successfully combined and exported
                </p>
                <p className="text-xs text-green-600 mt-2">
                  Exported on {new Date(sequence.export.exportedAt).toLocaleString()}
                </p>
              </div>
            </div>

            {/* Video Preview */}
            <div className="rounded-lg overflow-hidden border border-gray-200">
              <video
                src={sequence.export.finalVideoUrl}
                controls
                className="w-full"
                style={{ maxHeight: '400px' }}
              />
            </div>

            {/* Export Info */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Final Duration</p>
                <p className="text-lg font-bold text-gray-900">
                  {formatDuration(sequence.export.combinedDuration)}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Total Scenes</p>
                <p className="text-lg font-bold text-gray-900">{totalScenes}</p>
              </div>
            </div>

            {/* Download Button */}
            <button
              onClick={downloadVideo}
              className="w-full px-4 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
            >
              <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z" />
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z" />
              </svg>
              <span>Download Video</span>
            </button>

            {/* Re-export Button */}
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="w-full px-4 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Re-export Video
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
