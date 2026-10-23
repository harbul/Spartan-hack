/**
 * The incident map: MapLibre GL with the Amazon Location satellite/hybrid style,
 * 3D terrain and buildings, tilted toward the East San Jose foothills.
 * Controls: 2D/3D toggle, terrain exaggeration (1x/2x/3x), satellite/hybrid, fullscreen.
 * Clicking a marker flies the camera to the home and selects the resident.
 * Draws the layers in ./layers. Every layer is plain GeoJSON, so the base map
 * can switch to a fallback (§6) without touching them.
 *
 * MUST tier (now): flat map, zone, resident and resource markers, click to select.
 * Without a Location key it draws the same layers on a plain background.
 * TODO(P1, §6, §9.1 SHOULD): 3D (approach chosen on /3d-test), fly-to, routes layer.
 *
 * Data: /dashboard (outage, cases, resources, volunteers, plan).
 * Implements: PLAN.md §6 (3D map), §9.1 center. Owner: P1 (Frontend and UX).
 */
import type { LngLatBoundsLike, Map, StyleSpecification } from 'maplibre-gl';
import { useEffect, useRef, useState } from 'react';
import type { DashboardResponse } from '../../api/types';
import { EAST_SAN_JOSE, amazonStyleUrl, hasLocationKey, withLocationKey } from './amazonStyle';
import { addResidentsLayer, RESIDENTS_LAYER } from './layers/residentsLayer';
import { addResourcesLayer } from './layers/resourcesLayer';
import { addZoneLayer } from './layers/zoneLayer';
import { maplibregl } from './maplibre';

const PLAIN_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#e7e2d6' } }],
};

interface Props {
  dashboard: DashboardResponse;
  selectedId: string | null;
  onSelect: (residentId: string) => void;
}

export default function IncidentMap({ dashboard, selectedId, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<Map | null>(null);
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    if (!container.current) return;
    const instance = new maplibregl.Map({
      container: container.current,
      style: hasLocationKey ? amazonStyleUrl('Hybrid') : PLAIN_STYLE,
      transformRequest: withLocationKey,
      ...EAST_SAN_JOSE,
    });
    instance.addControl(new maplibregl.NavigationControl(), 'top-right');
    instance.on('click', RESIDENTS_LAYER, (e) => {
      const id = e.features?.[0]?.properties?.id;
      if (typeof id === 'string') onSelectRef.current(id);
    });
    instance.on('mouseenter', RESIDENTS_LAYER, () => (instance.getCanvas().style.cursor = 'pointer'));
    instance.on('mouseleave', RESIDENTS_LAYER, () => (instance.getCanvas().style.cursor = ''));
    instance.on('load', () => setMap(instance));
    return () => {
      setMap(null);
      instance.remove();
    };
  }, []);

  // Fit the outage zone once per outage, when the map is ready.
  const outage = dashboard.outage;
  const outageId = outage?.outage_id;
  useEffect(() => {
    if (!map || !outage) return;
    const ring = (outage.polygon.coordinates as [number, number][][])[0];
    const lngs = ring.map((p) => p[0]);
    const lats = ring.map((p) => p[1]);
    const bounds: LngLatBoundsLike = [
      [Math.min(...lngs), Math.min(...lats)],
      [Math.max(...lngs), Math.max(...lats)],
    ];
    map.fitBounds(bounds, { padding: 40, duration: 0 });
  }, [map, outageId]); // only when the outage changes, not on every poll

  useEffect(() => {
    if (!map) return;
    if (dashboard.outage) addZoneLayer(map, dashboard.outage);
    addResourcesLayer(map, dashboard);
    addResidentsLayer(map, dashboard.cases, selectedId);
  }, [map, dashboard, selectedId]);

  return (
    <div className="relative h-full w-full">
      <div ref={container} className="h-full w-full" />
      {!hasLocationKey && (
        <p className="absolute right-12 top-2 rounded bg-white/80 px-2 py-1 text-xs text-stone-600">
          No VITE_LOCATION_API_KEY: plain background instead of satellite
        </p>
      )}
    </div>
  );
}
