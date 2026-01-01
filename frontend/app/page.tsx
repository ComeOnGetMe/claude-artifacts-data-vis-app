'use client';

import { useState } from 'react';
import Chat from '@/components/Chat';
import Preview from '@/components/Preview';
import type { QueryResult } from '@/lib/types';

export default function Home() {
  const [previewCode, setPreviewCode] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<QueryResult | null>(null);

  return (
    <main className="flex min-h-screen flex-col">
      <div className="border-b p-4">
        <h1 className="text-2xl font-bold">
          Interactive Data Viz Orchestrator
        </h1>
      </div>
      <div className="flex flex-1 overflow-hidden">
        <div className="flex-1 border-r overflow-hidden">
          <Chat 
            onCodeUpdate={setPreviewCode}
            onDataUpdate={setPreviewData}
          />
        </div>
        <div className="flex-1 overflow-hidden">
          <Preview code={previewCode} data={previewData} />
        </div>
      </div>
    </main>
  );
}

