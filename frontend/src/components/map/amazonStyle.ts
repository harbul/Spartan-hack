/**
 * Amazon Location Service (Maps API v2) base-map styles for MapLibre.
 * The key and region come from VITE_LOCATION_API_KEY / VITE_LOCATION_REGION.
 * `terrain=Terrain3D` adds a raster-dem source (`terrainSource`) and turns terrain on.
 *
 * Implements: PLAN.md §6 (3D map). Owner: P1 (Frontend and UX).
 */
import type { RequestTransformFunction } from 'maplibre-gl';

const KEY = import.meta.env.VITE_LOCATION_API_KEY ?? '';
const REGION = import.meta.env.VITE_LOCATION_REGION || 'us-west-2';

export const hasLocationKey = KEY.length > 0;

export type AmazonStyle = 'Satellite' | 'Hybrid';

/** Camera over the East San Jose foothills outage zone (data/outage_zone.geojson). */
export const EAST_SAN_JOSE = { center: [-121.805, 37.373] as [number, number], zoom: 12.5 };

export function amazonStyleUrl(style: AmazonStyle, { terrain3d = false } = {}): string {
  const params = new URLSearchParams({ key: KEY });
  if (terrain3d) params.set('terrain', 'Terrain3D');
  return `https://maps.geo.${REGION}.amazonaws.com/v2/styles/${style}/descriptor?${params}`;
}

/** Adds the key to every Amazon Location request (tiles, glyphs, sprites) that lacks one. */
export const withLocationKey: RequestTransformFunction = (url) => {
  if (!url.includes('.amazonaws.com/v2/') || url.includes('key=')) return { url };
  return { url: `${url}${url.includes('?') ? '&' : '?'}key=${encodeURIComponent(KEY)}` };
};
