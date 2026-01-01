'use client';

import { useState } from 'react';
import Chat from '@/components/Chat';
import Preview from '@/components/Preview';
import type { QueryResult } from '@/lib/types';

export default function Home() {
  // Persist code and data across multiple submissions
  const [previewCode, setPreviewCode] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<QueryResult | null>(null);

  // Handle code updates - update whenever new code is provided
  // Code persists across submissions until new code arrives or manually cleared
  const handleCodeUpdate = (code: string | null) => {
    // Only update if code is provided (not null)
    // This allows code to persist when data arrives in a separate message
    if (code !== null) {
      setPreviewCode(code);
    }
  };

  // Handle data updates - update whenever new data is provided
  // Data persists across submissions until new data arrives or manually cleared
  const handleDataUpdate = (data: QueryResult | null) => {
    // Only update if data is provided (not null)
    // This allows data to persist when code arrives in a separate message
    if (data !== null) {
      setPreviewData(data);
    }
  };

  // Clear function for manual reset
  const handleClearPreview = () => {
    setPreviewCode(null);
    setPreviewData(null);
  };

  return (
    <main className="flex min-h-screen flex-col">
      <div className="border-b p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">
          Interactive Data Viz Orchestrator
        </h1>
        {(previewCode || previewData) && (
          <button
            onClick={handleClearPreview}
            className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Clear Preview
          </button>
        )}
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 border-r overflow-hidden">
          <Chat 
            onCodeUpdate={handleCodeUpdate}
            onDataUpdate={handleDataUpdate}
          />
        </div>
        <div className="flex-1 overflow-hidden">
          <Preview code={previewCode} data={previewData} />
        </div>
      </div>
    </main>
  );
}

