/**
 * Outage zone layer: translucent red fill with a dashed edge.
 * Adds the layer on the first call and updates its data after that.
 *
 * Implements: PLAN.md §9.1 (3D incident map). Owner: P1 (Frontend and UX).
 */
import type { Feature } from 'geojson';
import type { GeoJSONSource, Map } from 'maplibre-gl';
import type { Outage } from '../../../api/types';

export function addZoneLayer(map: Map, data: Outage): void {
  const feature = { type: 'Feature', geometry: data.polygon, properties: {} } as Feature;
  const source = map.getSource<GeoJSONSource>('zone');
  if (source) {
    source.setData(feature);
    return;
  }
  map.addSource('zone', { type: 'geojson', data: feature });
  map.addLayer({
    id: 'zone-fill',
    type: 'fill',
    source: 'zone',
    paint: { 'fill-color': '#dc2626', 'fill-opacity': 0.12 },
  });
  map.addLayer({
    id: 'zone-edge',
    type: 'line',
    source: 'zone',
    paint: { 'line-color': '#dc2626', 'line-width': 2, 'line-dasharray': [3, 2] },
  });
}
