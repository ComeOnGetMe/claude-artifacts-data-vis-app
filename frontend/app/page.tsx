import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <div className="border-b p-4">
        <h1 className="text-2xl font-bold">
          Interactive Data Viz Orchestrator
        </h1>
      </div>
      <Chat />
    </main>
  );
}

