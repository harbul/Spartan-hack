/**
 * Key events list beside the timeline track (outage start, check-ins, replies, escalations, plan, stops).
 *
 * Data: /dashboard events.
 * Implements: PLAN.md §5 incident timeline. Owner: P1 (Frontend and UX).
 */
import type { Event } from '../../api/types';
import { EVENT_COLOR, clockTime } from '../status';

export default function KeyEvents({ events }: { events: Event[] }) {
  const newestFirst = [...events].reverse();
  return (
    <ol className="h-full space-y-1 overflow-y-auto text-xs">
      {newestFirst.map((e) => (
        <li key={e.ts + e.label} className="flex gap-2">
          <span className="w-14 shrink-0 tabular-nums text-stone-500">{clockTime(e.ts)}</span>
          <span className="mt-1 h-2 w-2 shrink-0 rounded-full" style={{ background: EVENT_COLOR[e.type] }} />
          <span>{e.label}</span>
        </li>
      ))}
      {events.length === 0 && <li className="text-stone-500">No events yet.</li>}
    </ol>
  );
}
