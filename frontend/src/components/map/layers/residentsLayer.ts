/**
 * Resident markers colored by status (green Safe, amber Needs help, red Critical,
 * gray-violet No reply), white outline; no-reply markers grow with each escalation level.
 * No-reply markers also pulse, harder at each escalation level (§9.1: silence is the signal);
 * startPulse() runs the animation.
 * Adds the layers on the first call and updates their data after that.
 *
 * Implements: PLAN.md §9.1 (3D incident map). Owner: P1 (Frontend and UX).
 */
import type { FeatureCollection } from 'geojson';
import type { GeoJSONSource, Map } from 'maplibre-gl';
import type { DashboardCase } from '../../../api/types';
import { CATEGORY, categoryOf } from '../../status';

export const RESIDENTS_LAYER = 'residents';
const PULSE_LAYER = 'residents-pulse';
const PULSE_MS = 1600;

export function addResidentsLayer(map: Map, data: DashboardCase[], selectedId: string | null = null): void {
  const collection: FeatureCollection = {
    type: 'FeatureCollection',
    features: data.map((c) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [c.resident.lng, c.resident.lat] },
      properties: {
        id: c.resident_id,
        color: CATEGORY[categoryOf(c)].color,
        radius: 7 + c.escalation_level * 1.5,
        pulse: categoryOf(c) === 'no_reply' ? 1 + c.escalation_level : 0, // 0 = no pulse
      },
    })),
  };
  const source = map.getSource<GeoJSONSource>('residents');
  if (source) {
    source.setData(collection);
  } else {
    map.addSource('residents', { type: 'geojson', data: collection });
    map.addLayer({
      id: PULSE_LAYER,
      type: 'circle',
      source: 'residents',
      filter: ['>', ['get', 'pulse'], 0],
      paint: { 'circle-radius': ['get', 'radius'], 'circle-color': CATEGORY.no_reply.color, 'circle-opacity': 0 },
    });
    map.addLayer({
      id: 'residents-selected',
      type: 'circle',
      source: 'residents',
      paint: { 'circle-radius': 14, 'circle-color': '#1c1917', 'circle-opacity': 0.25 },
    });
    map.addLayer({
      id: RESIDENTS_LAYER,
      type: 'circle',
      source: 'residents',
      paint: {
        'circle-radius': ['get', 'radius'],
        'circle-color': ['get', 'color'],
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 2,
      },
    });
  }
  map.setFilter('residents-selected', ['==', ['get', 'id'], selectedId ?? '']);
}

/** Animate the no-reply rings: each one grows and fades every PULSE_MS. Returns a stop function. */
export function startPulse(map: Map): () => void {
  let frame = 0;
  const step = (time: number) => {
    if (map.getLayer(PULSE_LAYER)) {
      const phase = (time % PULSE_MS) / PULSE_MS;
      // ring grows 5 px per step of pulse (awaiting reply 5 px ... L3 20 px), fading out as it grows
      map.setPaintProperty(PULSE_LAYER, 'circle-radius', ['+', ['get', 'radius'], ['*', phase * 5, ['get', 'pulse']]]);
      map.setPaintProperty(PULSE_LAYER, 'circle-opacity', 0.55 * (1 - phase));
    }
    frame = requestAnimationFrame(step);
  };
  frame = requestAnimationFrame(step);
  return () => cancelAnimationFrame(frame);
}
