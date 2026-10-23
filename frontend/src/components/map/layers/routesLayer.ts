/**
 * Volunteer routes, one line per run (geometry from CalculateRoutes), white outline.
 * Dashed while the plan is a draft, solid once approved.
 * Also used by the flat map on the volunteer route sheet.
 * Adds the layers on the first call and updates their data after that.
 *
 * Implements: PLAN.md §9.1 (3D incident map), §9.3. Owner: P1 (Frontend and UX).
 */
import type { FeatureCollection } from 'geojson';
import type { GeoJSONSource, Map } from 'maplibre-gl';
import type { Plan } from '../../../api/types';

/** One color per volunteer (by position in the plan); the Plan tab and route sheet use the same. */
export const ROUTE_COLORS = ['#2563eb', '#db2777', '#0d9488', '#7c3aed', '#ea580c'];

export function addRoutesLayer(map: Map, plan: Plan | null, beforeId?: string): void {
  const collection: FeatureCollection = {
    type: 'FeatureCollection',
    features: (plan?.runs ?? [])
      .filter((run) => run.geometry)
      .map((run, i) => ({
        type: 'Feature',
        geometry: run.geometry as unknown as FeatureCollection['features'][number]['geometry'],
        properties: { run_id: run.run_id, color: ROUTE_COLORS[i % ROUTE_COLORS.length] },
      })),
  };
  const source = map.getSource<GeoJSONSource>('routes');
  if (source) {
    source.setData(collection);
  } else {
    const before = beforeId && map.getLayer(beforeId) ? beforeId : undefined;
    map.addSource('routes', { type: 'geojson', data: collection });
    map.addLayer(
      { id: 'routes-casing', type: 'line', source: 'routes', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#ffffff', 'line-width': 7 } },
      before,
    );
    map.addLayer(
      { id: 'routes-line', type: 'line', source: 'routes', layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': ['get', 'color'], 'line-width': 4 } },
      before,
    );
  }
  map.setPaintProperty('routes-line', 'line-dasharray', plan?.status === 'approved' ? [1, 0] : [2, 1.5]);
}
