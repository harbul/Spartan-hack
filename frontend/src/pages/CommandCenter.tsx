/**
 * Command center (/): the coordinator's four-area screen, like FireTrace.
 *   Top bar     logo, incident name, area, outage window, Reset demo, About
 *   Left        panels/Overview + panels/TriageQueue
 *   Center      map/IncidentMap (3D)
 *   Right       tabs: panels/ResidentPanel, panels/TraceDrawer, panels/PlanPanel
 *   Bottom      action bar (Send check-ins -> Plan dispatch -> Approve) above timeline/Timeline
 * The top bar and action bar live in this page until they need their own file.
 *
 * Data: GET /dashboard every 3 s (api/client useDashboard; MOCK until H4-H6).
 * Implements: PLAN.md §9.1. Owner: P1 (Frontend and UX).
 */
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { apiGet, useDashboard } from '../api/client';
import BedrockBadge from '../components/BedrockBadge';
import IncidentMap from '../components/map/IncidentMap';
import Overview from '../components/panels/Overview';
import PlanPanel from '../components/panels/PlanPanel';
import ResidentPanel from '../components/panels/ResidentPanel';
import TraceDrawer from '../components/panels/TraceDrawer';
import TriageQueue from '../components/panels/TriageQueue';
import { clockTime } from '../components/status';
import Timeline from '../components/timeline/Timeline';

type Tab = 'resident' | 'trace' | 'plan';
const TABS: { id: Tab; label: string }[] = [
  { id: 'resident', label: 'Resident' },
  { id: 'trace', label: 'AI Trace' },
  { id: 'plan', label: 'Plan' },
];

export default function CommandCenter() {
  const { data, advance, reset, messages } = useDashboard();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('resident');
  const selected = data.cases.find((c) => c.resident_id === selectedId);

  const select = (residentId: string) => {
    setSelectedId(residentId);
    setTab('resident');
  };

  return (
    <main className="flex h-screen flex-col bg-[#f7f4ee] text-stone-800">
      <header className="flex items-center gap-4 border-b border-stone-300 px-4 py-2">
        <span className="text-lg font-semibold">StillHere</span>
        <span className="font-medium">{data.outage?.name}</span>
        <span className="text-sm text-stone-500">
          East San Jose foothills
          {data.outage && ` · power off ${clockTime(data.outage.starts_at)} to ~${clockTime(data.outage.est_restore_at)}`}
        </span>
        <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">Demo data · mock</span>
        <button onClick={reset} className="ml-auto rounded border border-stone-400 px-3 py-1 text-sm">
          Reset demo
        </button>
        <button className="rounded px-2 py-1 text-sm text-stone-600" title="About StillHere (H8-H12)" disabled>
          About
        </button>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[340px_1fr_380px]">
        <aside className="flex min-h-0 flex-col border-r border-stone-300">
          <Overview dashboard={data} />
          <TriageQueue cases={data.cases} selectedId={selectedId} onSelect={select} />
        </aside>

        <section className="relative min-h-0">
          <IncidentMap dashboard={data} selectedId={selectedId} onSelect={select} />
          <HelloBedrockCard />
        </section>

        <aside className="flex min-h-0 flex-col border-l border-stone-300">
          <nav className="flex border-b border-stone-300">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex-1 py-2 text-sm ${tab === t.id ? 'border-b-2 border-stone-800 font-semibold' : 'text-stone-500'}`}
              >
                {t.label}
              </button>
            ))}
          </nav>
          <div className="min-h-0 flex-1 overflow-y-auto">
            {tab === 'resident' && (
              <ResidentPanel dcase={selected} messages={selectedId ? messages(selectedId) : []} />
            )}
            {tab === 'trace' && <TraceDrawer />}
            {tab === 'plan' && <PlanPanel />}
          </div>
        </aside>
      </div>

      {/* TODO(P1, H4-H7): wire to POST /outages/{id}/checkins, /plans, /plans/{id}/approve. */}
      <div className="flex items-center gap-2 border-t border-stone-300 px-4 py-2 text-sm">
        {['Send check-ins', 'Plan dispatch', 'Approve plan'].map((label, i) => (
          <button key={label} disabled className="rounded bg-stone-800 px-3 py-1 text-white opacity-40">
            {i + 1}. {label}
          </button>
        ))}
        <span className="text-xs text-stone-500">Actions call the API from H4-H6; the timeline drives the mock for now.</span>
      </div>
      <Timeline dashboard={data} onAdvance={advance} />
    </main>
  );
}

// --- Skeleton / debug (H0-H1 gate): delete with GET /hello-bedrock once the §8 routes exist.

interface HelloBedrock {
  reply: string;
  model_id: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
}

function HelloBedrockCard() {
  // Each fetch is a real (billed) Bedrock call, so never refetch on its own.
  const hello = useQuery({
    queryKey: ['hello-bedrock'],
    queryFn: () => apiGet<HelloBedrock>('/hello-bedrock'),
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: Infinity,
  });

  return (
    <section className="absolute bottom-3 left-3 w-80 rounded-lg border border-stone-300 bg-[#faf7f0]/95 p-3 text-sm shadow">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-stone-500">Bedrock check</h2>
        <BedrockBadge />
      </div>
      {hello.isPending && <p>Amazon Bedrock is writing a hello…</p>}
      {hello.isError && <p className="text-red-700">Failed: {hello.error.message}</p>}
      {hello.isSuccess && (
        <>
          <p>{hello.data.reply}</p>
          <p className="mt-1 text-xs text-stone-500">
            {hello.data.model_id} · {hello.data.latency_ms} ms · {hello.data.input_tokens} in /{' '}
            {hello.data.output_tokens} out tokens
          </p>
        </>
      )}
      <button
        className="mt-1 text-xs text-indigo-700 underline disabled:opacity-50"
        onClick={() => hello.refetch()}
        disabled={hello.isFetching}
      >
        Call again
      </button>
    </section>
  );
}
