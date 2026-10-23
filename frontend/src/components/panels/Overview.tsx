/**
 * Left incident overview header: counters for affected, Critical, no reply, pending visits.
 *
 * Data: /dashboard counts, cases, plan.
 * Implements: PLAN.md §9.1 left. Owner: P1 (Frontend and UX).
 */
import type { DashboardResponse } from '../../api/types';

export default function Overview({ dashboard }: { dashboard: DashboardResponse }) {
  const done = new Set(dashboard.cases.filter((c) => c.status === 'resolved').map((c) => c.resident_id));
  const pendingVisits =
    dashboard.plan?.status === 'approved'
      ? dashboard.plan.runs.flatMap((r) => r.stops).filter((s) => !done.has(s.resident_id)).length
      : 0;
  const tiles = [
    { label: 'Affected', value: dashboard.cases.length, className: 'text-stone-800' },
    { label: 'Critical', value: dashboard.counts.critical, className: 'text-red-600' },
    { label: 'No reply', value: dashboard.counts.no_reply, className: 'text-[#8b7fa8]' },
    { label: 'Pending visits', value: pendingVisits, className: 'text-stone-800' },
  ];
  return (
    <div className="grid grid-cols-4 gap-2 border-b border-stone-300 p-3">
      {tiles.map((t) => (
        <div key={t.label}>
          <div className={`text-2xl font-semibold ${t.className}`}>{t.value}</div>
          <div className="text-[11px] uppercase tracking-wide text-stone-500">{t.label}</div>
        </div>
      ))}
    </div>
  );
}
