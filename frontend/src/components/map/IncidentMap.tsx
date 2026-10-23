/**
 * The incident map: MapLibre GL with the Amazon Location satellite/hybrid style,
 * 3D terrain and buildings, tilted toward the East San Jose foothills.
 * Controls: 2D/3D toggle, terrain exaggeration (1x/2x/3x), satellite/hybrid, fullscreen.
 * Clicking a marker flies the camera to the home and selects the resident.
 * Draws the layers in ./layers. Every layer is plain GeoJSON, so the base map
 * can switch to a fallback (§6) without touching them.
 *
 * Data: /dashboard (outage, cases, resources, volunteers, plan).
 * Implements: PLAN.md §6 (3D map), §9.1 center. Owner: P1 (Frontend and UX).
 */
import { useEffect, useRef } from 'react';
import { EAST_SAN_JOSE, amazonStyleUrl, hasLocationKey, withLocationKey } from './amazonStyle';
import { maplibregl } from './maplibre';

export default function IncidentMap() {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!container.current || !hasLocationKey) return;
    const map = new maplibregl.Map({
      container: container.current,
      style: amazonStyleUrl('Hybrid'),
      transformRequest: withLocationKey,
      ...EAST_SAN_JOSE,
    });
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    // TODO(P1, §6, §9.1): layers, markers, fly-to; 3D (SHOULD tier) uses the approach chosen on /3d-test.
    return () => map.remove();
  }, []);

  if (!hasLocationKey) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-stone-200 text-sm text-stone-600">
        Map needs VITE_LOCATION_API_KEY (see .env.example)
      </div>
    );
  }
  return <div ref={container} className="h-full w-full" />;
}
