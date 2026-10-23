/**
 * The incident map: MapLibre GL with the Amazon Location satellite/hybrid style,
 * 3D terrain and buildings, tilted toward the East San Jose foothills.
 * Controls: 2D/3D toggle, terrain exaggeration (1x/2x/3x), satellite/hybrid, fullscreen.
 * Selecting a resident (marker, queue card or plan stop) flies the camera to the home.
 * No-reply markers pulse, harder with each escalation level.
 * Draws the layers in ./layers. Every layer is plain GeoJSON, so the base map
 * can switch to a fallback (§6) without touching them.
 *
 * Without a Location key it draws the same layers on a plain background, with
 * open terrain and a hillshade in 3D (see terrain.ts).
 *
 * Data: /dashboard (outage, cases, resources, volunteers, plan).
 * Implements: PLAN.md §6 (3D map), §9.1 center. Owner: P1 (Frontend and UX).
 */
import type { LngLatBoundsLike, Map, StyleSpecification } from 'maplibre-gl';
import { useEffect, useRef, useState } from 'react';
import type { DashboardResponse } from '../../api/types';
import { EAST_SAN_JOSE, amazonStyleUrl, hasLocationKey, withLocationKey, type AmazonStyle } from './amazonStyle';
import { addResidentsLayer, RESIDENTS_LAYER, startPulse } from './layers/residentsLayer';
import { addResourcesLayer } from './layers/resourcesLayer';
import { addRoutesLayer } from './layers/routesLayer';
import { addZoneLayer } from './layers/zoneLayer';
import { maplibregl } from './maplibre';
import { CAMERA_2D, CAMERA_3D, setTerrain3D, type Exaggeration } from './terrain';

const PLAIN_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#e7e2d6' } }],
};
const FLY_ZOOM = 15.5;
const FIT_ZOOM_3D = 0.5;

const styleFor = (base: AmazonStyle) => (hasLocationKey ? amazonStyleUrl(base, { terrain3d: true }) : PLAIN_STYLE);

interface Props {
  dashboard: DashboardResponse;
  selectedId: string | null;
  onSelect: (residentId: string) => void;
}

export default function IncidentMap({ dashboard, selectedId, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<Map | null>(null);
  const [styleVersion, setStyleVersion] = useState(0); // bumps after every (re)loaded style, to re-add the layers
  const [is3D, setIs3D] = useState(true);
  const [exaggeration, setExaggeration] = useState<Exaggeration>(2);
  const [base, setBase] = useState<AmazonStyle>('Hybrid');
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    if (!container.current) return;
    const instance = new maplibregl.Map({
      container: container.current,
      style: styleFor('Hybrid'),
      transformRequest: withLocationKey,
      ...EAST_SAN_JOSE,
      ...CAMERA_3D,
      maxPitch: 80,
    });
    instance.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');
    instance.addControl(new maplibregl.FullscreenControl({ container: container.current.parentElement! }), 'top-right');
    instance.on('click', RESIDENTS_LAYER, (e) => {
      const id = e.features?.[0]?.properties?.id;
      if (typeof id === 'string') onSelectRef.current(id);
    });
    instance.on('mouseenter', RESIDENTS_LAYER, () => (instance.getCanvas().style.cursor = 'pointer'));
    instance.on('mouseleave', RESIDENTS_LAYER, () => (instance.getCanvas().style.cursor = ''));
    instance.on('style.load', () => setStyleVersion((v) => v + 1));
    instance.once('load', () => setMap(instance));
    const stopPulse = startPulse(instance);
    return () => {
      stopPulse();
      setMap(null);
      instance.remove();
    };
  }, []);

  // Satellite / Hybrid (only with a key): a new style drops our layers; style.load re-adds them.
  const firstBase = useRef(true);
  useEffect(() => {
    if (!map || !hasLocationKey) return;
    if (firstBase.current) {
      firstBase.current = false;
      return;
    }
    map.setStyle(styleFor(base));
  }, [map, base]);

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
    map.fitBounds(bounds, { padding: 40, duration: 0, ...(is3D ? CAMERA_3D : CAMERA_2D) });
    // Tilted, the far side of the zone looks small: zoom in a little past the plain fit.
    if (is3D) map.setZoom(map.getZoom() + FIT_ZOOM_3D);
  }, [map, outageId]); // only when the outage changes, not on every poll or toggle

  // Terrain on/off and exaggeration; the camera tilts with it.
  useEffect(() => {
    if (!map) return;
    setTerrain3D(map, is3D, exaggeration, { hillshade: !hasLocationKey });
  }, [map, styleVersion, is3D, exaggeration]);

  const firstToggle = useRef(true);
  useEffect(() => {
    if (!map) return;
    if (firstToggle.current) {
      firstToggle.current = false;
      return;
    }
    map.easeTo({ ...(is3D ? CAMERA_3D : CAMERA_2D), duration: 800 });
  }, [map, is3D]);

  useEffect(() => {
    if (!map) return;
    if (dashboard.outage) addZoneLayer(map, dashboard.outage);
    addResourcesLayer(map, dashboard);
    addResidentsLayer(map, dashboard.cases, selectedId);
    addRoutesLayer(map, dashboard.plan, 'residents-selected'); // under the markers
  }, [map, styleVersion, dashboard, selectedId]);

  // Fly to the selected home, once per selection (not on every 3 s poll).
  const flownTo = useRef<string | null>(null);
  useEffect(() => {
    if (!map || !selectedId || flownTo.current === selectedId) return;
    const resident = dashboard.cases.find((c) => c.resident_id === selectedId)?.resident;
    if (!resident) return;
    flownTo.current = selectedId;
    map.flyTo({
      center: [resident.lng, resident.lat],
      zoom: Math.max(map.getZoom(), FLY_ZOOM),
      pitch: is3D ? CAMERA_3D.pitch : 0,
      duration: 1600,
      essential: true,
    });
  }, [map, selectedId, dashboard.cases, is3D]);

  return (
    <div className="relative h-full w-full">
      <div ref={container} className="h-full w-full" />
      <div className="absolute left-2 top-2 flex flex-col gap-1 text-xs">
        <Segmented
          label="View"
          options={[
            ['2D', !is3D, () => setIs3D(false)],
            ['3D', is3D, () => setIs3D(true)],
          ]}
        />
        {is3D && (
          <Segmented
            label="Terrain"
            options={([1, 2, 3] as const).map((x) => [`${x}×`, exaggeration === x, () => setExaggeration(x)])}
          />
        )}
        {hasLocationKey && (
          <Segmented
            label="Map"
            options={(['Satellite', 'Hybrid'] as const).map((s) => [s, base === s, () => setBase(s)])}
          />
        )}
        {!hasLocationKey && (
          <p className="rounded bg-white/80 px-2 py-1 text-stone-600">No VITE_LOCATION_API_KEY: terrain shading, no satellite</p>
        )}
      </div>
    </div>
  );
}

function Segmented({ label, options }: { label: string; options: [string, boolean, () => void][] }) {
  return (
    <div className="flex items-center overflow-hidden rounded border border-stone-300 bg-white/90 shadow-sm" role="group" aria-label={label}>
      <span className="px-2 text-stone-500">{label}</span>
      {options.map(([text, active, onClick]) => (
        <button
          key={text}
          onClick={onClick}
          aria-pressed={active}
          className={`px-2 py-1 ${active ? 'bg-stone-800 text-white' : 'text-stone-700 hover:bg-stone-100'}`}
        >
          {text}
        </button>
      ))}
    </div>
  );
}
