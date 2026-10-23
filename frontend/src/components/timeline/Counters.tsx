/**
 * Live counters above the timeline track: Safe, Needs help, Critical, No reply.
 *
 * Data: /dashboard counts.
 * Implements: PLAN.md §5 incident timeline. Owner: P1 (Frontend and UX).
 */
import type { Counts } from '../../api/types';
import { CATEGORY } from '../status';

export default function Counters({ counts }: { counts: Counts }) {
  const items = [
    { ...CATEGORY.safe, value: counts.safe },
    { ...CATEGORY.needs_help, value: counts.needs_help },
    { ...CATEGORY.critical, value: counts.critical },
    { ...CATEGORY.no_reply, value: counts.no_reply },
  ];
  return (
    <div className="flex gap-4 text-sm">
      {items.map((item) => (
        <span key={item.label} className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: item.color }} />
          <span className="font-semibold tabular-nums">{item.value}</span>
          <span className="text-stone-500">{item.label}</span>
        </span>
      ))}
    </div>
  );
}
