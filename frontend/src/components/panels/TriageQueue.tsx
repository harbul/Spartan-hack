/**
 * Searchable, sortable triage queue. One card per case: name, device icons, language badge,
 * status chip, score and band, the AI "why" (Amazon Bedrock badge), "Needs review" flag.
 * Clicking a card flies the map to the home.
 *
 * Data: /dashboard cases.
 * Implements: PLAN.md §9.1 left. Owner: P1 (Frontend and UX).
 */
import { useState } from 'react';
import type { DashboardCase } from '../../api/types';
import BedrockBadge from '../BedrockBadge';
import { BAND_CLASS, CATEGORY, DEVICE_LABEL, LANGUAGE_LABEL, STATUS_LABEL, categoryOf } from '../status';

type Sort = 'priority' | 'name' | 'silence';

const SORTS: Record<Sort, (a: DashboardCase, b: DashboardCase) => number> = {
  priority: (a, b) => b.priority - a.priority,
  name: (a, b) => a.resident.name.localeCompare(b.resident.name),
  silence: (a, b) => b.escalation_level - a.escalation_level || b.priority - a.priority,
};

interface Props {
  cases: DashboardCase[];
  selectedId: string | null;
  onSelect: (residentId: string) => void;
}

export default function TriageQueue({ cases, selectedId, onSelect }: Props) {
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<Sort>('priority');
  const q = query.trim().toLowerCase();
  const shown = cases
    .filter((c) => !q || `${c.resident.name} ${c.resident.address}`.toLowerCase().includes(q))
    .sort(SORTS[sort]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex gap-2 border-b border-stone-300 p-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search name or street"
          className="min-w-0 flex-1 rounded border border-stone-300 bg-white px-2 py-1 text-sm"
        />
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as Sort)}
          className="rounded border border-stone-300 bg-white px-1 text-sm"
          aria-label="Sort"
        >
          <option value="priority">Priority</option>
          <option value="silence">Silence</option>
          <option value="name">Name</option>
        </select>
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto">
        {shown.map((c) => {
          const category = CATEGORY[categoryOf(c)];
          return (
            <li key={c.resident_id}>
              <button
                onClick={() => onSelect(c.resident_id)}
                className={`w-full border-b border-stone-200 px-3 py-2 text-left hover:bg-white ${
                  c.resident_id === selectedId ? 'bg-white' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: category.color }} />
                  <span className="truncate font-medium">{c.resident.name}</span>
                  <span className="rounded bg-stone-200 px-1 text-[10px] font-semibold">
                    {LANGUAGE_LABEL[c.resident.language]}
                  </span>
                  <span className={`ml-auto rounded px-1.5 text-xs font-semibold ${BAND_CLASS[c.band]}`}>
                    {c.band} {Math.round(c.priority)}
                  </span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-1 text-[11px] text-stone-600">
                  {c.resident.devices.map((d) => (
                    <span key={d} className="rounded border border-stone-300 px-1">
                      {DEVICE_LABEL[d]}
                    </span>
                  ))}
                  <span>· {STATUS_LABEL[c.status]}</span>
                  {c.needs_review && (
                    <span className="rounded bg-orange-100 px-1 font-semibold text-orange-800">Needs review</span>
                  )}
                </div>
                {c.rationale && (
                  <div className="mt-1 flex items-start gap-1.5 text-xs text-stone-700">
                    <BedrockBadge />
                    <span className="line-clamp-2">{c.rationale}</span>
                  </div>
                )}
              </button>
            </li>
          );
        })}
        {shown.length === 0 && <li className="p-3 text-sm text-stone-500">No residents match.</li>}
      </ul>
    </div>
  );
}
