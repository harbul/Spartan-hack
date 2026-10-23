/**
 * Right panel, Plan tab: draft dispatch plan per volunteer with the agent's one-line reasons
 * (Amazon Bedrock badge) and the Approve button.
 *
 * Data: /dashboard plan, POST /plans, POST /plans/{id}/approve.
 * Implements: PLAN.md §4 Job 5, §9.1 right. Owner: P1 (Frontend and UX).
 */
import type { DashboardCase, Plan, Stop, Volunteer } from '../../api/types';
import BedrockBadge from '../BedrockBadge';
import { ROUTE_COLORS } from '../map/layers/routesLayer';
import { BAND_CLASS, STATUS_LABEL } from '../status';

export const ACTION_LABEL: Record<Stop['action'], string> = {
  cooler: 'Cooler',
  battery: 'Battery',
  door_knock: 'Door-knock',
  ride: 'Ride',
};

interface Props {
  plan: Plan | null;
  cases: DashboardCase[];
  volunteers: Volunteer[];
  busy: boolean;
  onApprove: () => void;
  onSelect: (residentId: string) => void;
}

export default function PlanPanel({ plan, cases, volunteers, busy, onApprove, onSelect }: Props) {
  if (!plan) {
    return (
      <p className="p-4 text-sm text-stone-500">
        No plan yet. "Plan dispatch" asks the Amazon Bedrock agent for a draft; nothing is dispatched until you approve it.
      </p>
    );
  }
  const byId = new Map(cases.map((c) => [c.resident_id, c]));
  const names = new Map(volunteers.map((v) => [v.volunteer_id, v.name]));
  const fallback = plan.summary.includes('Fallback plan') || plan.summary.includes('straight lines');

  return (
    <div className="space-y-4 p-4 text-sm">
      <section>
        <div className="mb-1 flex items-center gap-2">
          <h2 className="font-semibold">{plan.status === 'draft' ? 'Draft plan' : 'Approved plan'}</h2>
          <BedrockBadge />
        </div>
        <p>{plan.summary}</p>
        {fallback && (
          <p className="mt-1 rounded bg-amber-50 px-2 py-1 text-xs text-amber-900">
            Part of this plan was made without the AI planner or Amazon Location; check it before approving.
          </p>
        )}
      </section>

      {plan.runs.map((run, i) => (
        <section key={run.run_id} className="rounded border border-stone-300 bg-white">
          <header className="flex items-center gap-2 border-b border-stone-200 px-3 py-2">
            <span className="h-3 w-3 rounded-full" style={{ background: ROUTE_COLORS[i % ROUTE_COLORS.length] }} />
            <span className="font-medium">{names.get(run.volunteer) ?? run.volunteer}</span>
            <span className="text-xs text-stone-500">
              {run.vehicle.replace('_', ' ')} · {run.stops.length} stops
              {run.duration_min !== null && ` · ~${Math.round(run.duration_min)} min drive`}
            </span>
            {plan.status === 'approved' && (
              <a href={`/run/${run.run_id}`} target="_blank" rel="noreferrer" className="ml-auto text-xs text-indigo-700 underline">
                Route sheet
              </a>
            )}
          </header>
          <ol className="divide-y divide-stone-100">
            {run.stops.map((stop, n) => {
              const c = byId.get(stop.resident_id);
              return (
                <li key={stop.resident_id} className="px-3 py-2">
                  <button onClick={() => onSelect(stop.resident_id)} className="flex w-full items-center gap-2 text-left">
                    <span className="w-4 text-xs text-stone-500">{n + 1}.</span>
                    <span className="font-medium">{c?.resident.name ?? stop.resident_id}</span>
                    <span className="rounded bg-stone-200 px-1.5 text-[11px] font-semibold">{ACTION_LABEL[stop.action]}</span>
                    {c && (
                      <span className={`ml-auto rounded px-1.5 text-[11px] font-semibold ${BAND_CLASS[c.band]}`}>
                        {c.band} · {STATUS_LABEL[c.status]}
                      </span>
                    )}
                  </button>
                  <p className="ml-6 mt-0.5 text-xs text-stone-700">{stop.reason}</p>
                  {stop.items.length > 0 && <p className="ml-6 text-[11px] text-stone-500">Bring: {stop.items.join(', ')}</p>}
                </li>
              );
            })}
          </ol>
        </section>
      ))}

      {plan.uncovered.length > 0 && (
        <section className="rounded border border-red-200 bg-red-50 p-3">
          <h3 className="font-semibold text-red-800">Not covered: next wave ({plan.uncovered.length})</h3>
          <p className="text-xs text-red-800">
            {plan.uncovered.map((id) => byId.get(id)?.resident.name ?? id).join(', ')}
          </p>
        </section>
      )}

      {plan.status === 'draft' && (
        <button onClick={onApprove} disabled={busy} className="w-full rounded bg-stone-800 py-2 font-medium text-white disabled:opacity-40">
          Approve plan and dispatch volunteers
        </button>
      )}
    </div>
  );
}
