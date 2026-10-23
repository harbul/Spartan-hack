/**
 * Volunteer route sheet (/run/:runId): mobile layout, flat 2D map (no 3D on
 * phones), ordered stops with action, items, address and reason, "Mark done".
 *
 * Data: GET /runs/{run_id}, POST /runs/{run_id}/stops/{resident_id}/done.
 * Implements: PLAN.md §9.3. Owner: P1 (Frontend and UX).
 */
import { useQueryClient } from '@tanstack/react-query';
import type { Map, StyleSpecification } from 'maplibre-gl';
import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { USE_MOCK, markStopDone, useRun } from '../api/client';
import type { RunResponse } from '../api/types';
import BedrockBadge from '../components/BedrockBadge';
import { EAST_SAN_JOSE, amazonStyleUrl, hasLocationKey, withLocationKey } from '../components/map/amazonStyle';
import { addRoutesLayer, ROUTE_COLORS } from '../components/map/layers/routesLayer';
import { maplibregl } from '../components/map/maplibre';
import { ACTION_LABEL } from '../components/panels/PlanPanel';

const PLAIN_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#e7e2d6' } }],
};

function RouteMap({ sheet }: { sheet: RunResponse }) {
  const container = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<Map | null>(null);

  useEffect(() => {
    if (!container.current) return;
    const instance = new maplibregl.Map({
      container: container.current,
      style: hasLocationKey ? amazonStyleUrl('Hybrid') : PLAIN_STYLE,
      transformRequest: withLocationKey,
      ...EAST_SAN_JOSE,
    });
    instance.on('load', () => setMap(instance));
    return () => {
      setMap(null);
      instance.remove();
    };
  }, []);

  useEffect(() => {
    if (!map) return;
    const plan = { runs: [sheet.run], status: 'approved' } as Parameters<typeof addRoutesLayer>[1];
    addRoutesLayer(map, plan);
    const markers = sheet.stops_detail.map((stop, i) => {
      const el = document.createElement('div');
      el.className = 'flex h-6 w-6 items-center justify-center rounded-full border-2 border-white text-xs font-bold text-white shadow';
      el.style.background = stop.status === 'resolved' ? '#16a34a' : ROUTE_COLORS[0];
      el.textContent = String(i + 1);
      return new maplibregl.Marker({ element: el }).setLngLat([stop.lng, stop.lat]).addTo(map);
    });
    const points = sheet.stops_detail.map((s) => [s.lng, s.lat] as [number, number]);
    if (sheet.volunteer) points.push([sheet.volunteer.start.lng, sheet.volunteer.start.lat]);
    if (points.length) {
      const lngs = points.map((p) => p[0]);
      const lats = points.map((p) => p[1]);
      map.fitBounds(
        [
          [Math.min(...lngs), Math.min(...lats)],
          [Math.max(...lngs), Math.max(...lats)],
        ],
        { padding: 40, duration: 0 },
      );
    }
    return () => markers.forEach((m) => m.remove());
  }, [map, sheet]);

  return <div ref={container} className="h-64 w-full" />;
}

export default function RunSheet() {
  const { runId = '' } = useParams();
  const { data: sheet, error } = useRun(runId);
  const queryClient = useQueryClient();
  const [mockDone, setMockDone] = useState<string[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  if (error) return <main className="p-4 text-sm text-red-700">Could not load this route: {error.message}</main>;
  if (sheet === undefined) return <main className="p-4 text-sm text-stone-500">Loading the route…</main>;
  if (sheet === null) return <main className="p-4 text-sm text-stone-500">No route {runId}.</main>;

  const done = async (residentId: string) => {
    if (USE_MOCK) return setMockDone((d) => [...d, residentId]);
    setSaving(residentId);
    setSaveError(null);
    try {
      await markStopDone(runId, residentId);
      await queryClient.invalidateQueries({ queryKey: ['run', runId] });
    } catch (err) {
      setSaveError((err as Error).message);
    } finally {
      setSaving(null);
    }
  };

  const view: RunResponse = {
    ...sheet,
    stops_detail: sheet.stops_detail.map((s) => (mockDone.includes(s.resident_id) ? { ...s, status: 'resolved' } : s)),
  };
  const remaining = view.stops_detail.filter((s) => s.status !== 'resolved').length;

  return (
    <main className="mx-auto min-h-screen max-w-md bg-[#f7f4ee] text-stone-800">
      <header className="px-4 pb-2 pt-4">
        <p className="text-xs uppercase tracking-wide text-stone-500">StillHere · volunteer route · Demo data</p>
        <h1 className="text-xl font-semibold">{view.volunteer?.name ?? view.run.volunteer}</h1>
        <p className="text-sm text-stone-600">
          {view.run.vehicle.replace('_', ' ')} · {view.run.stops.length} stops
          {view.run.duration_min !== null && ` · ~${Math.round(view.run.duration_min)} min drive`} · {remaining} left
        </p>
      </header>
      <RouteMap sheet={view} />
      {saveError && <p className="px-4 pt-2 text-sm text-red-700">{saveError}</p>}
      <ol className="space-y-2 p-4">
        {view.run.stops.map((stop, i) => {
          const detail = view.stops_detail[i];
          const isDone = detail.status === 'resolved';
          return (
            <li key={stop.resident_id} className={`rounded-lg border border-stone-300 bg-white p-3 ${isDone ? 'opacity-50' : ''}`}>
              <div className="flex items-center gap-2">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-stone-800 text-xs font-bold text-white">{i + 1}</span>
                <span className="font-semibold">{detail.name}</span>
                <span className="ml-auto rounded bg-stone-200 px-1.5 text-xs font-semibold">{ACTION_LABEL[stop.action]}</span>
              </div>
              <p className="mt-1 text-sm text-stone-600">{detail.address}</p>
              <p className="mt-1 flex items-start gap-1.5 text-sm">
                <BedrockBadge />
                <span>{stop.reason}</span>
              </p>
              {stop.items.length > 0 && <p className="mt-1 text-sm text-stone-600">Bring: {stop.items.join(', ')}</p>}
              <button
                onClick={() => done(stop.resident_id)}
                disabled={isDone || saving === stop.resident_id}
                className="mt-2 w-full rounded bg-green-700 py-2 font-medium text-white disabled:bg-stone-300"
              >
                {isDone ? 'Done' : saving === stop.resident_id ? 'Saving…' : 'Mark done'}
              </button>
            </li>
          );
        })}
      </ol>
    </main>
  );
}
