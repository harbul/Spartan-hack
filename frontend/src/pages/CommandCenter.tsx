/**
 * Command center (/): the coordinator's screen, split into four tabs so each view does
 * one job. The tab lives in the URL (?tab=), so Back and shared links work.
 *   Incident map   map/IncidentMap (3D); picking a home opens panels/ResidentPanel beside it
 *   Residents      panels/Overview + panels/TriageQueue, with panels/ResidentPanel for the pick
 *   Dispatch plan  panels/PlanPanel
 *   AI activity    timeline/KeyEvents + panels/TraceDrawer (every Amazon Bedrock call)
 * Always on screen: Sidebar (tabs, phone simulator, About, Reset demo), the header
 * (tab title, incident name, area, outage window) and the bottom console: the action bar
 * (Load zone -> Send check-ins -> Plan dispatch -> Approve) above timeline/Timeline.
 * Every tab stays mounted, so the map keeps its camera (and flies to a resident picked
 * elsewhere) and the queue keeps its search. The action bar lives in this page until it
 * needs its own file.
 *
 * Data: GET /dashboard every 3 s (api/client useDashboard; VITE_USE_MOCK=true for the mock).
 * Implements: PLAN.md §9.1. Owner: P1 (Frontend and UX).
 */
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { USE_MOCK, apiGet, useDashboard, useMessages, useTraces } from '../api/client';
import BedrockBadge from '../components/BedrockBadge';
import Icon, { type IconName } from '../components/Icon';
import IncidentMap from '../components/map/IncidentMap';
import AboutPanel from '../components/panels/AboutPanel';
import Overview from '../components/panels/Overview';
import PlanPanel from '../components/panels/PlanPanel';
import ResidentPanel from '../components/panels/ResidentPanel';
import TraceDrawer from '../components/panels/TraceDrawer';
import TriageQueue from '../components/panels/TriageQueue';
import Sidebar, { type SidebarTab } from '../components/Sidebar';
import { clockTime } from '../components/status';
import KeyEvents from '../components/timeline/KeyEvents';
import Timeline from '../components/timeline/Timeline';

type Tab = 'map' | 'residents' | 'plan' | 'activity';
const TABS: { id: Tab; label: string; icon: IconName; hint: string }[] = [
  { id: 'map', label: 'Incident map', icon: 'map', hint: 'Every registered home in the outage zone. Pick one to see who lives there.' },
  { id: 'residents', label: 'Residents', icon: 'users', hint: 'The triage queue, highest priority first. Pick a resident for their replies and the AI assessment.' },
  { id: 'plan', label: 'Dispatch plan', icon: 'route', hint: 'Volunteer routes drafted by the AI planner. Nothing is dispatched until you approve.' },
  { id: 'activity', label: 'AI activity', icon: 'activity', hint: 'Key incident events, and every Amazon Bedrock call with its prompt and output.' },
];
const isTab = (value: string | null): value is Tab => TABS.some((t) => t.id === value);
const hrefFor = (tab: Tab) => (tab === 'map' ? '/' : `/?tab=${tab}`);

interface Step {
  label: string;
  onClick: () => void;
  enabled: boolean;
  done: boolean;
}

export default function CommandCenter() {
  const { data, error, busy, advance, reset, loadZone, sendCheckins, planDispatch, approvePlan } = useDashboard();
  const [params, setParams] = useSearchParams();
  const tabParam = params.get('tab');
  const tab: Tab = isTab(tabParam) ? tabParam : 'map';
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [aboutOpen, setAboutOpen] = useState(false);
  const messages = useMessages(selectedId, data);
  const traces = useTraces();

  if (!data) {
    return (
      <main className="flex h-screen items-center justify-center gap-2 text-stone-600">
        {error ? (
          <ApiError error={error} />
        ) : (
          <>
            <Icon name="loader" className="h-5 w-5 animate-spin text-indigo-600" /> Loading the command center…
          </>
        )}
      </main>
    );
  }
  const setTab = (next: Tab) => setParams(next === 'map' ? {} : { tab: next });
  const selected = data.cases.find((c) => c.resident_id === selectedId);
  const toContact = data.cases.filter((c) => c.status === 'not_contacted').length;
  const open = data.cases.filter((c) => ['needs_help', 'escalated', 'silent'].includes(c.status)).length;
  const draft = data.plan?.status === 'draft';
  const showPlan = (action: () => void) => () => {
    action();
    setTab('plan');
  };
  const steps: Step[] = [
    { label: 'Load outage zone', onClick: loadZone, enabled: !data.outage, done: !!data.outage },
    {
      label: `Send check-ins${toContact ? ` (${toContact})` : ''}`,
      onClick: sendCheckins,
      enabled: toContact > 0,
      done: !!data.outage && toContact === 0,
    },
    { label: 'Plan dispatch', onClick: showPlan(planDispatch), enabled: open > 0 && !draft, done: !!data.plan },
    { label: 'Approve plan', onClick: showPlan(approvePlan), enabled: draft, done: data.plan?.status === 'approved' },
  ];

  // The map and the queue keep you where you are; a plan stop shows the home on the map.
  const select = (residentId: string) => setSelectedId(residentId);
  const showOnMap = (residentId: string) => {
    setSelectedId(residentId);
    setTab('map');
  };

  const critical = data.counts.critical;
  const badges: Partial<Record<Tab, SidebarTab['badge']>> = {
    residents: critical > 0 ? { text: `${critical}`, label: `${critical} Critical`, className: 'bg-red-600 text-white' } : undefined,
    plan: draft
      ? { text: 'Draft', label: 'waiting for approval', className: 'bg-amber-100 text-amber-900' }
      : data.plan?.status === 'approved'
        ? { text: 'Live', label: 'approved', className: 'bg-green-100 text-green-900' }
        : undefined,
    activity:
      traces.length > 0
        ? { text: `${traces.length}`, label: `${traces.length} Amazon Bedrock calls`, className: 'bg-indigo-100 text-indigo-800' }
        : undefined,
  };
  const current = TABS.find((t) => t.id === tab)!;

  return (
    <div className="flex h-screen text-stone-800">
      <Sidebar
        tabs={TABS.map((t) => ({ id: t.id, label: t.label, icon: t.icon, href: hrefFor(t.id), badge: badges[t.id] }))}
        active={tab}
        resetDisabled={!!busy}
        onAbout={() => setAboutOpen(true)}
        onReset={reset}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex flex-wrap items-center gap-x-6 gap-y-2 border-b border-stone-200 bg-panel px-5 py-3">
          <div className="min-w-0">
            <h1 className="text-lg font-semibold leading-tight">{current.label}</h1>
            <p className="text-sm text-stone-500">{current.hint}</p>
          </div>
          <div className="ml-auto text-sm lg:text-right">
            <p className="flex items-center gap-2 font-medium lg:justify-end">
              {data.outage?.name ?? 'No outage loaded'}
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-900">
                Demo data{USE_MOCK && ' · mock'}
              </span>
            </p>
            <p className="text-stone-500">
              East San Jose foothills
              {data.outage && ` · power off ${clockTime(data.outage.starts_at)} to ~${clockTime(data.outage.est_restore_at)}`}
            </p>
          </div>
        </header>
        {error && <ApiError error={error} />}

        <main id="main" className="relative min-h-0 flex-1">
          {/* Hidden with visibility, not display: the map keeps its size and camera between tabs. */}
          <section aria-label="Incident map" inert={tab !== 'map'} className={`absolute inset-0 flex ${tab === 'map' ? '' : 'invisible'}`}>
            <div className="relative min-w-0 flex-1">
              <IncidentMap dashboard={data} selectedId={selectedId} onSelect={select} />
            </div>
            {selected && (
              <aside
                aria-label="Selected resident"
                className="absolute inset-x-0 bottom-0 z-10 flex max-h-[60%] flex-col border-t border-stone-200 bg-panel shadow-lg md:static md:max-h-none md:w-[380px] md:border-l md:border-t-0 md:shadow-none"
              >
                <div className="flex items-center justify-between border-b border-stone-200 py-1 pl-4 pr-2">
                  <h2 className="text-xs font-semibold uppercase tracking-wide text-stone-500">Selected resident</h2>
                  <button
                    onClick={() => setSelectedId(null)}
                    aria-label="Close resident details"
                    className="flex h-10 w-10 items-center justify-center rounded-lg text-stone-500 hover:bg-stone-200/60 hover:text-stone-900"
                  >
                    <Icon name="x" className="h-5 w-5" />
                  </button>
                </div>
                <div className="min-h-0 flex-1 overflow-y-auto">
                  <ResidentPanel dcase={selected} messages={messages} />
                </div>
              </aside>
            )}
          </section>

          <section aria-label="Residents" hidden={tab !== 'residents'} className="absolute inset-0 flex flex-col md:flex-row">
            <div className="flex h-1/2 min-h-0 flex-col border-b border-stone-200 bg-panel md:h-auto md:w-[380px] md:border-b-0 md:border-r">
              <Overview dashboard={data} />
              <TriageQueue cases={data.cases} selectedId={selectedId} onSelect={select} />
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto">
              {selected ? (
                <div className="mx-auto max-w-3xl">
                  <div className="flex justify-end px-4 pt-4">
                    <button
                      onClick={() => showOnMap(selected.resident_id)}
                      className="flex h-10 items-center gap-2 rounded-lg border border-stone-300 bg-white px-3 text-sm font-medium hover:bg-stone-100"
                    >
                      <Icon name="pin" /> Show on map
                    </button>
                  </div>
                  <ResidentPanel dcase={selected} messages={messages} />
                </div>
              ) : (
                <EmptyState icon="users">
                  Pick a resident in the queue to see their replies, the AI assessment and the suggested action.
                </EmptyState>
              )}
            </div>
          </section>

          <section aria-label="Dispatch plan" hidden={tab !== 'plan'} className="absolute inset-0 overflow-y-auto">
            <div className="mx-auto max-w-5xl">
              <PlanPanel
                plan={data.plan}
                cases={data.cases}
                volunteers={data.volunteers}
                busy={!!busy}
                onApprove={approvePlan}
                onSelect={showOnMap}
              />
            </div>
          </section>

          <section aria-label="AI activity" hidden={tab !== 'activity'} className="absolute inset-0 flex flex-col overflow-y-auto lg:flex-row lg:overflow-hidden">
            <div className="flex min-h-48 flex-col border-b border-stone-200 bg-panel lg:w-80 lg:border-b-0 lg:border-r">
              <h2 className="px-4 pb-2 pt-4 text-xs font-semibold uppercase tracking-wide text-stone-500">Key events</h2>
              <div className="min-h-0 flex-1 px-4 pb-4">
                <KeyEvents events={data.events} />
              </div>
            </div>
            <div className="min-w-0 flex-1 lg:overflow-y-auto">
              <div className="p-4">
                <HelloBedrockCard />
              </div>
              <h2 className="px-4 pb-2 text-xs font-semibold uppercase tracking-wide text-stone-500">Amazon Bedrock calls</h2>
              <TraceDrawer traces={traces} />
            </div>
          </section>
        </main>

        <footer className="border-t border-stone-200 bg-panel px-4 py-3">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <WorkflowSteps steps={steps} busy={!!busy} />
            <p aria-live="polite" className="flex items-center gap-2 text-xs text-stone-600">
              {busy && (
                <>
                  <Icon name="loader" className="h-4 w-4 animate-spin text-indigo-600" />
                  <BedrockBadge /> {busy}
                </>
              )}
            </p>
          </div>
          <Timeline dashboard={data} onAdvance={advance} />
        </footer>
      </div>

      {aboutOpen && <AboutPanel onClose={() => setAboutOpen(false)} />}
    </div>
  );
}

/** The action bar: the next step is the dark button, finished steps get a check. */
function WorkflowSteps({ steps, busy }: { steps: Step[]; busy: boolean }) {
  const next = steps.findIndex((s) => s.enabled);
  return (
    <ol aria-label="Incident workflow" className="flex flex-wrap items-center gap-2">
      {steps.map((step, i) => {
        const finished = step.done && !step.enabled;
        const style =
          i === next
            ? 'bg-stone-900 text-white hover:bg-stone-700'
            : step.enabled
              ? 'border border-stone-300 bg-white text-stone-800 hover:bg-stone-100'
              : 'text-stone-500';
        return (
          <li key={i} className="flex items-center gap-2">
            {i > 0 && <span className="hidden h-px w-3 bg-stone-300 sm:block" />}
            <button
              onClick={step.onClick}
              disabled={!step.enabled || busy}
              className={`flex h-10 items-center gap-2 rounded-lg px-3 text-sm font-medium transition-colors duration-150 disabled:opacity-60 ${style}`}
            >
              <span
                className={`flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-semibold ${
                  i === next ? 'bg-white text-stone-900' : finished ? 'bg-green-600 text-white' : 'bg-stone-200 text-stone-700'
                }`}
              >
                {finished ? <Icon name="check" className="h-3 w-3" /> : i + 1}
              </span>
              {step.label}
              {finished && <span className="sr-only">(done)</span>}
            </button>
          </li>
        );
      })}
    </ol>
  );
}

function EmptyState({ icon, children }: { icon: IconName; children: ReactNode }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-3 p-8 text-center text-sm text-stone-500">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-stone-200/70 text-stone-600">
        <Icon name={icon} className="h-6 w-6" />
      </span>
      <p className="max-w-sm">{children}</p>
    </div>
  );
}

function ApiError({ error }: { error: Error }) {
  return (
    <p role="alert" className="border-b border-red-200 bg-red-50 px-4 py-1.5 text-sm text-red-800">
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
    <section className="rounded-lg border border-stone-200 bg-white p-3 text-sm">
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
