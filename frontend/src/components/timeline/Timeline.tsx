/**
 * Incident timeline (the crisis clock): play/pause at 1x/4x/16x, jump +30 min/+1 h/+3 h
 * (each calls POST /clock/advance), event markers on the track. Forward only in the MUST tier.
 * Playing moves `speed` virtual minutes per real second (16x shows 3 h in about 11 s).
 *
 * Data: /dashboard (now, events), POST /clock/advance.
 * Implements: PLAN.md §5 incident timeline, §9.1 bottom. Owner: P1 (Frontend and UX).
 */
import { useEffect, useState } from 'react';
import type { DashboardResponse } from '../../api/types';
import { EVENT_COLOR, clockTime } from '../status';
import Counters from './Counters';
import KeyEvents from './KeyEvents';

const SPEEDS = [1, 4, 16];
const JUMPS = [
  { label: '+30 min', minutes: 30 },
  { label: '+1 h', minutes: 60 },
  { label: '+3 h', minutes: 180 },
];

interface Props {
  dashboard: DashboardResponse;
  onAdvance: (minutes: number) => void;
}

export default function Timeline({ dashboard, onAdvance }: Props) {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(4);
  const { outage, now, events, counts } = dashboard;

  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(() => onAdvance(speed), 1000);
    return () => clearInterval(timer);
  }, [playing, speed, onAdvance]);

  if (!outage) return null;
  const start = Date.parse(outage.starts_at);
  const span = Date.parse(outage.est_restore_at) - start;
  const position = (ts: string) => `${Math.min(100, Math.max(0, ((Date.parse(ts) - start) / span) * 100))}%`;
  const elapsedMin = Math.round((Date.parse(now) - start) / 60_000);

  return (
    <section className="grid grid-cols-[1fr_300px] gap-4 border-t border-stone-300 bg-[#faf7f0] px-4 py-3">
      <div className="space-y-2">
        <div className="flex items-center gap-4">
          <Counters counts={counts} />
          <span className="ml-auto text-sm tabular-nums">
            <span className="font-semibold">{clockTime(now)}</span>
            <span className="text-stone-500">
              {' '}
              · {Math.floor(elapsedMin / 60)} h {elapsedMin % 60} min into the outage
            </span>
          </span>
        </div>

        <div className="relative h-8">
          <div className="absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded bg-stone-200" />
          <div className="absolute left-0 top-1/2 h-1 -translate-y-1/2 rounded bg-stone-500" style={{ width: position(now) }} />
          {events.map((e) => (
            <span
              key={e.ts + e.label}
              title={`${clockTime(e.ts)} ${e.label}`}
              className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white"
              style={{ left: position(e.ts), background: EVENT_COLOR[e.type] }}
            />
          ))}
          <span
            className="absolute top-0 h-8 w-0.5 -translate-x-1/2 bg-red-600"
            style={{ left: position(now) }}
            aria-label="now"
          />
        </div>
        <div className="flex justify-between text-[11px] text-stone-500">
          <span>{clockTime(outage.starts_at)} power off</span>
          <span>{clockTime(outage.est_restore_at)} est. restore</span>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <button onClick={() => setPlaying((p) => !p)} className="w-20 rounded bg-stone-800 px-3 py-1 text-white">
            {playing ? 'Pause' : 'Play'}
          </button>
          {SPEEDS.map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`rounded px-2 py-1 ${s === speed ? 'bg-stone-300 font-semibold' : 'bg-stone-100'}`}
            >
              {s}×
            </button>
          ))}
          <span className="mx-2 h-5 w-px bg-stone-300" />
          {JUMPS.map((j) => (
            <button key={j.label} onClick={() => onAdvance(j.minutes)} className="rounded bg-stone-100 px-2 py-1">
              {j.label}
            </button>
          ))}
        </div>
      </div>
      <div className="h-36">
        <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-stone-500">Key events</h3>
        <KeyEvents events={events} />
      </div>
    </section>
  );
}
