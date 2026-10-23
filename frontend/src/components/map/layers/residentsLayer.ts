/**
 * Resident markers colored by status (green Safe, amber Needs help, red Critical,
 * gray-violet No reply), white outline; no-reply markers grow with each escalation level.
 * TODO(P1, §9.1 SHOULD): animate the no-reply pulse.
 * Adds the layers on the first call and updates their data after that.
 *
 * Implements: PLAN.md §9.1 (3D incident map). Owner: P1 (Frontend and UX).
 */
import type { FeatureCollection } from 'geojson';
import type { GeoJSONSource, Map } from 'maplibre-gl';
import type { DashboardCase } from '../../../api/types';
import { CATEGORY, categoryOf } from '../../status';

export const RESIDENTS_LAYER = 'residents';

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
      },
    })),
  };
  const source = map.getSource<GeoJSONSource>('residents');
  if (source) {
    source.setData(collection);
  } else {
    map.addSource('residents', { type: 'geojson', data: collection });
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
