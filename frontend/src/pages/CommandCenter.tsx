/**
 * Command center (/): the coordinator's four-area screen, like FireTrace.
 *   Top bar     logo, incident name, area, outage window, Reset demo, About
 *   Left        panels/Overview + panels/TriageQueue
 *   Center      map/IncidentMap (3D)
 *   Right       tabs: panels/ResidentPanel, panels/TraceDrawer, panels/PlanPanel
 *   Bottom      action bar (Send check-ins -> Plan dispatch -> Approve) above timeline/Timeline
 * The top bar and action bar live in this page until they need their own file.
 *
 * Data: GET /dashboard every 3 s.
 * Implements: PLAN.md §9.1. Owner: P1 (Frontend and UX).
 */
import { useQuery } from '@tanstack/react-query';
import IncidentMap from '../components/map/IncidentMap';

export default function CommandCenter() {
  // TODO(P1, §9.1): compose the four areas. For now: the map plus the H0-H1 Bedrock check.
  return (
    <main className="flex h-screen flex-col bg-[#f7f4ee] text-stone-800">
      <header className="flex items-center gap-3 border-b border-stone-300 px-4 py-2">
        <span className="font-semibold">StillHere</span>
        <span className="text-sm text-stone-500">East San Jose PSPS · Demo data</span>
      </header>
      <div className="relative flex-1">
        <IncidentMap />
        <HelloBedrockCard />
      </div>
    </main>
  );
}

/** "Amazon Bedrock" badge for every AI-produced element (§9). */
function BedrockBadge() {
  return (
    <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800">
      Amazon Bedrock
    </span>
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

async function fetchHelloBedrock(): Promise<HelloBedrock> {
  const response = await fetch(`${import.meta.env.VITE_API_URL}/hello-bedrock`);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail ?? `HTTP ${response.status}`);
  return body as HelloBedrock;
}

function HelloBedrockCard() {
  // Each fetch is a real (billed) Bedrock call, so never refetch on its own.
  const hello = useQuery({
    queryKey: ['hello-bedrock'],
    queryFn: fetchHelloBedrock,
    retry: false,
    refetchOnWindowFocus: false,
    staleTime: Infinity,
  });

  return (
    <section className="absolute bottom-4 left-4 w-96 rounded-lg border border-stone-300 bg-[#faf7f0]/95 p-4 shadow">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold">Walking skeleton: Bedrock check</h2>
        <BedrockBadge />
      </div>
      {hello.isPending && <p className="text-sm">Amazon Bedrock is writing a hello…</p>}
      {hello.isError && <p className="text-sm text-red-700">Failed: {hello.error.message}</p>}
      {hello.isSuccess && (
        <>
          <p className="mb-2">{hello.data.reply}</p>
          <p className="text-xs text-stone-500">
            {hello.data.model_id} · {hello.data.latency_ms} ms · {hello.data.input_tokens} in /{' '}
            {hello.data.output_tokens} out tokens
          </p>
        </>
      )}
      <button
        className="mt-2 text-xs text-indigo-700 underline disabled:opacity-50"
        onClick={() => hello.refetch()}
        disabled={hello.isFetching}
      >
        Call again
      </button>
    </section>
  );
}
