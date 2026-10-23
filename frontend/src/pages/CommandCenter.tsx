/**
 * Command center (/): the coordinator's four-area screen, like FireTrace.
 *   Top bar     logo, incident name, area, outage window, Reset demo, About
 *   Left        panels/Overview + panels/TriageQueue
 *   Center      map/IncidentMap (3D)
 *   Right       tabs: panels/ResidentPanel, panels/TraceDrawer, panels/PlanPanel
 *   Bottom      action bar (Send check-ins -> Plan dispatch -> Approve) above timeline/Timeline
 * The top bar and action bar live in this page until they need their own file.
 *
 * Data: GET /dashboard every 3 s (api/client useDashboard; VITE_USE_MOCK=true for the mock).
 * Implements: PLAN.md §9.1. Owner: P1 (Frontend and UX).
 */
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { USE_MOCK, apiGet, useDashboard, useMessages, useTraces } from '../api/client';
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
  const { data, error, busy, advance, reset, loadZone, sendCheckins, planDispatch, approvePlan } = useDashboard();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('resident');
  const messages = useMessages(selectedId, data);
  const traces = useTraces();

  if (!data) {
    return (
      <main className="flex h-screen items-center justify-center bg-[#f7f4ee] text-stone-600">
        {error ? <ApiError error={error} /> : 'Loading the command center…'}
      </main>
    );
  }
  const selected = data.cases.find((c) => c.resident_id === selectedId);
  const toContact = data.cases.filter((c) => c.status === 'not_contacted').length;
  const open = data.cases.filter((c) => ['needs_help', 'escalated', 'silent'].includes(c.status)).length;
  const draft = data.plan?.status === 'draft';
  const showPlan = (action: () => void) => () => {
    action();
    setTab('plan');
  };
  const steps = [
    { label: 'Load outage zone', onClick: loadZone, enabled: !data.outage },
    { label: `Send check-ins${toContact ? ` (${toContact})` : ''}`, onClick: sendCheckins, enabled: toContact > 0 },
    { label: 'Plan dispatch', onClick: showPlan(planDispatch), enabled: open > 0 && !draft },
    { label: 'Approve plan', onClick: showPlan(approvePlan), enabled: draft },
  ];

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
        <span className="rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
          Demo data{USE_MOCK && ' · mock'}
        </span>
        <button onClick={reset} disabled={!!busy} className="ml-auto rounded border border-stone-400 px-3 py-1 text-sm">
          Reset demo
        </button>
        <button className="rounded px-2 py-1 text-sm text-stone-600" title="About StillHere (H8-H12)" disabled>
          About
        </button>
      </header>
      {error && <ApiError error={error} />}

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
            {tab === 'resident' && <ResidentPanel dcase={selected} messages={messages} />}
            {tab === 'trace' && <TraceDrawer traces={traces} />}
            {tab === 'plan' && (
              <PlanPanel
                plan={data.plan}
                cases={data.cases}
                volunteers={data.volunteers}
                busy={!!busy}
                onApprove={approvePlan}
                onSelect={select}
              />
            )}
          </div>
        </aside>
      </div>

      <div className="flex items-center gap-2 border-t border-stone-300 px-4 py-2 text-sm">
        {steps.map((step, i) => (
          <button
            key={step.label}
            onClick={step.onClick}
            disabled={!step.enabled || !!busy}
            className="rounded bg-stone-800 px-3 py-1 text-white disabled:opacity-40"
          >
            {i + 1}. {step.label}
          </button>
        ))}
        {busy && (
          <span className="flex items-center gap-2 text-xs text-stone-600">
            <BedrockBadge /> {busy}
          </span>
        )}
      </div>
      <Timeline dashboard={data} onAdvance={advance} />
    </main>
  );
}

function ApiError({ error }: { error: Error }) {
  return (
    <p className="border-b border-red-200 bg-red-50 px-4 py-1.5 text-sm text-red-800">
      API problem: {error.message}. Check VITE_API_URL, or set VITE_USE_MOCK=true to work offline.
    </p>
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
