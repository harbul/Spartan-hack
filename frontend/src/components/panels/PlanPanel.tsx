/**
 * Dispatch plan tab: draft dispatch plan per volunteer with the agent's one-line reasons
 * (Amazon Bedrock badge) and the Approve button.
 *
 * Data: /dashboard plan, POST /plans, POST /plans/{id}/approve.
 * Implements: PLAN.md §4 Job 5, §9.1 right. Owner: P1 (Frontend and UX).
 */
import type { DashboardCase, Plan, Stop, Volunteer } from '../../api/types';
import BedrockBadge from '../BedrockBadge';
import Icon from '../Icon';
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
      <div className="flex flex-col items-center gap-3 p-12 text-center text-sm text-stone-500">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-stone-200/70 text-stone-600">
          <Icon name="route" className="h-6 w-6" />
        </span>
        <p className="max-w-sm">
          No plan yet. "Plan dispatch" in the bar below asks the Amazon Bedrock agent for a draft; nothing is
          dispatched until you approve it.
        </p>
      </div>
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

      <div className="grid items-start gap-4 xl:grid-cols-2">
        {plan.runs.map((run, i) => (
          <section key={run.run_id} className="rounded-lg border border-stone-200 bg-white">
            <header className="flex items-center gap-2 border-b border-stone-200 px-3 py-2">
              <span className="h-3 w-3 rounded-full" style={{ background: ROUTE_COLORS[i % ROUTE_COLORS.length] }} />
              <span className="font-medium">{names.get(run.volunteer) ?? run.volunteer}</span>
              <span className="text-xs text-stone-500">
                {run.vehicle.replace('_', ' ')} · {run.stops.length} stops
                {run.duration_min !== null && ` · ~${Math.round(run.duration_min)} min drive`}
              </span>
              {plan.status === 'approved' && (
                <a
                  href={`/run/${run.run_id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="ml-auto flex items-center gap-1 text-xs text-indigo-700 underline"
                >
                  Route sheet <Icon name="external" className="h-3 w-3" />
                </a>
              )}
            </header>
            <ol className="divide-y divide-stone-100">
              {run.stops.map((stop, n) => {
                const c = byId.get(stop.resident_id);
                return (
                  <li key={stop.resident_id} className="px-3 py-2">
                    <button
                      onClick={() => onSelect(stop.resident_id)}
                      title="Show on map"
                      className="flex w-full items-center gap-2 rounded text-left hover:text-indigo-700"
                    >
                      <span className="w-4 text-xs text-stone-500">{n + 1}.</span>
                      <span className="font-medium">{c?.resident.name ?? stop.resident_id}</span>
                      <span className="rounded bg-stone-200 px-1.5 text-xs font-semibold">{ACTION_LABEL[stop.action]}</span>
                      {c && (
                        <span className={`ml-auto rounded px-1.5 text-xs font-semibold ${BAND_CLASS[c.band]}`}>
                          {c.band} · {STATUS_LABEL[c.status]}
                        </span>
                      )}
                    </button>
                    <p className="ml-6 mt-0.5 text-xs text-stone-700">{stop.reason}</p>
                    {stop.items.length > 0 && <p className="ml-6 text-xs text-stone-500">Bring: {stop.items.join(', ')}</p>}
                  </li>
                );
              })}
            </ol>
          </section>
        ))}
      </div>

      {plan.uncovered.length > 0 && (
        <section className="rounded-lg border border-red-200 bg-red-50 p-3">
          <h3 className="font-semibold text-red-800">Not covered: next wave ({plan.uncovered.length})</h3>
          <p className="text-xs text-red-800">
            {plan.uncovered.map((id) => byId.get(id)?.resident.name ?? id).join(', ')}
          </p>
        </section>
      )}

      {plan.status === 'draft' && (
        <button
          onClick={onApprove}
          disabled={busy}
          className="h-11 w-full rounded-lg bg-stone-900 font-medium text-white transition-colors duration-150 hover:bg-stone-700 disabled:opacity-50"
        >
          Approve plan and dispatch volunteers
        </button>
      )}
    </div>
  );
}
