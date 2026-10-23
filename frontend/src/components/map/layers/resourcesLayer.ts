/**
 * Resource centers, the pharmacy and volunteer start points as distinct markers
 * (blue resource center, teal pharmacy, small dark volunteer).
 * Adds the layer on the first call and updates its data after that.
 *
 * Implements: PLAN.md §9.1 (3D incident map). Owner: P1 (Frontend and UX).
 */
import type { Feature, FeatureCollection } from 'geojson';
import type { GeoJSONSource, Map } from 'maplibre-gl';
import type { Resource, Volunteer } from '../../../api/types';

export const RESOURCE_COLORS = { resource_center: '#2563eb', pharmacy: '#0d9488', volunteer: '#1c1917' };

export function addResourcesLayer(map: Map, data: { resources: Resource[]; volunteers: Volunteer[] }): void {
  const point = (lng: number, lat: number, kind: keyof typeof RESOURCE_COLORS, name: string): Feature => ({
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [lng, lat] },
    properties: { kind, name, color: RESOURCE_COLORS[kind] },
  });
  const collection: FeatureCollection = {
    type: 'FeatureCollection',
    features: [
      ...data.resources.map((r) => point(r.lng, r.lat, r.type, r.name)),
      ...data.volunteers.map((v) => point(v.start.lng, v.start.lat, 'volunteer', v.name)),
    ],
  };
  const source = map.getSource<GeoJSONSource>('resources');
  if (source) {
    source.setData(collection);
    return;
  }
  map.addSource('resources', { type: 'geojson', data: collection });
  map.addLayer({
    id: 'resources',
    type: 'circle',
    source: 'resources',
    paint: {
      'circle-radius': ['match', ['get', 'kind'], 'volunteer', 5, 9],
      'circle-color': ['get', 'color'],
      'circle-stroke-color': '#ffffff',
      'circle-stroke-width': 3,
    },
  });
}
