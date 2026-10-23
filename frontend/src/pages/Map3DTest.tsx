/**
 * THROWAWAY (H0-H1): 3D map test at /3d-test. Decides the 3D approach (PLAN.md §6).
 * Delete this file and its route in main.tsx once IncidentMap gets 3D (H8-H12).
 *
 * Options, in the §6 order:
 *   amazon        Amazon Location Satellite style with terrain=Terrain3D, plus building extrusions
 *   open-terrain  Amazon Satellite style + open Terrain Tiles (AWS Open Data, Terrarium encoding)
 *   (Mapbox, the last fallback, needs a new dependency; only add it if both fail.)
 * Without a Location key, both run as terrain-only (hillshade, no imagery) to test the 3D part.
 *
 * Owner: P1 (Frontend and UX).
 */
import type { ErrorEvent, StyleSpecification } from 'maplibre-gl';
import { useEffect, useRef, useState } from 'react';
import {
  EAST_SAN_JOSE,
  amazonStyleUrl,
  hasLocationKey,
  withLocationKey,
} from '../components/map/amazonStyle';
import { maplibregl } from '../components/map/maplibre';

type Option = 'amazon' | 'open-terrain';

const OPEN_TERRAIN = {
  type: 'raster-dem' as const,
  tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
  encoding: 'terrarium' as const,
  tileSize: 256,
  maxzoom: 15,
  attribution: 'Terrain Tiles: Mapzen, AWS Open Data',
};

const NO_KEY_STYLE: StyleSpecification = {
  version: 8,
  sources: { terrainSource: OPEN_TERRAIN },
  layers: [{ id: 'bg', type: 'background', paint: { 'background-color': '#e7e2d6' } }],
};

/** Alum Rock foothills (should be a few hundred meters) and downtown San Jose (near sea level). */
const PROBES: [string, [number, number]][] = [
  ['foothills', [-121.775, 37.39]],
  ['downtown', [-121.886, 37.336]],
];

export default function Map3DTest() {
  const container = useRef<HTMLDivElement>(null);
  const [option, setOption] = useState<Option>('amazon');
  const [log, setLog] = useState<string[]>([]);

  useEffect(() => {
    if (!container.current) return;
    const lines: string[] = [];
    const say = (line: string) => {
      lines.push(line);
      setLog([...lines]);
    };
    say(hasLocationKey ? `option: ${option}` : `option: ${option} (no key: terrain only)`);

    const style = !hasLocationKey
      ? NO_KEY_STYLE
      : option === 'amazon'
        ? amazonStyleUrl('Satellite', { terrain3d: true })
        : amazonStyleUrl('Satellite');
    const map = new maplibregl.Map({
      container: container.current,
      style,
      transformRequest: withLocationKey,
      ...EAST_SAN_JOSE,
      pitch: 65,
      bearing: 70, // look east, toward the foothills
      maxPitch: 85,
    });
    map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), 'top-right');

    map.on('load', () => {
      if (!map.getSource('terrainSource')) map.addSource('terrainSource', OPEN_TERRAIN);
      map.setTerrain({ source: 'terrainSource', exaggeration: 2 });
      if (!hasLocationKey) {
        map.addLayer({ id: 'hillshade', type: 'hillshade', source: 'terrainSource' });
      }
      if (map.getSource('aws')) {
        map.addLayer({
          id: '3d-buildings',
          type: 'fill-extrusion',
          source: 'aws',
          'source-layer': 'buildings',
          minzoom: 14,
          filter: ['==', ['get', 'kind'], 'building'],
          paint: {
            'fill-extrusion-color': '#d9d4c7',
            'fill-extrusion-height': ['coalesce', ['get', 'height'], 6],
            'fill-extrusion-base': ['coalesce', ['get', 'min_height'], 0],
            'fill-extrusion-opacity': 0.85,
          },
        });
        say('3D buildings layer added (zoom in past 14 to see it)');
      } else {
        say('no `aws` vector source, so no 3D buildings');
      }
      const terrain = map.getTerrain();
      say(terrain ? `terrain on: ${terrain.source}, ${terrain.exaggeration}x` : 'terrain OFF');
    });
    map.once('idle', () => {
      for (const [name, lngLat] of PROBES) {
        const meters = map.queryTerrainElevation(lngLat);
        say(`elevation ${name}: ${meters === null ? 'n/a' : `${Math.round(meters)} m (incl. 2x)`}`);
      }
    });
    map.on('error', (event: ErrorEvent) => say(`error: ${event.error?.message ?? 'unknown'}`));
    return () => map.remove();
  }, [option]);

  return (
    <main className="relative h-screen w-screen">
      <div ref={container} className="h-full w-full" />
      <section className="absolute left-4 top-4 w-80 rounded-lg bg-[#faf7f0]/95 p-3 text-sm shadow">
        <h1 className="mb-2 font-semibold">3D map test (throwaway, §6)</h1>
        <div className="mb-2 flex gap-2">
          {(['amazon', 'open-terrain'] as const).map((value) => (
            <button
              key={value}
              onClick={() => setOption(value)}
              className={`rounded px-2 py-1 ${option === value ? 'bg-stone-800 text-white' : 'bg-stone-200'}`}
            >
              {value}
            </button>
          ))}
        </div>
        <ul id="log" className="space-y-0.5 font-mono text-xs">
          {log.map((line, i) => (
            <li key={i}>{line}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
