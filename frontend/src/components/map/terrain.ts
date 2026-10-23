/**
 * 3D for the incident map: terrain, building extrusions and the tilted camera.
 * The approach chosen on /3d-test (PROGRESS.md Decisions, §6):
 *   with a Location key   Amazon style with terrain=Terrain3D (adds `terrainSource`), plus our building extrusions
 *   fallback / no key     open Terrain Tiles (AWS Open Data, Terrarium) as `terrainSource`; no key also adds a hillshade
 * The overlay layers (zone, routes, markers) are plain GeoJSON and drape over the terrain.
 *
 * Implements: PLAN.md §6 (3D map), §9.1 SHOULD (3D terrain and buildings, 2D/3D toggle). Owner: P1 (Frontend and UX).
 */
import type { Map, RasterDEMSourceSpecification } from 'maplibre-gl';

export const TERRAIN_SOURCE = 'terrainSource';
const BUILDINGS_LAYER = '3d-buildings';
const HILLSHADE_LAYER = 'hillshade';

export const OPEN_TERRAIN: RasterDEMSourceSpecification = {
  type: 'raster-dem',
  tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
  encoding: 'terrarium',
  tileSize: 256,
  maxzoom: 15,
  attribution: 'Terrain Tiles: Mapzen, AWS Open Data',
};

/** Tilted toward the foothills (they rise to the east of the zone). */
export const CAMERA_3D = { pitch: 60, bearing: 60 };
export const CAMERA_2D = { pitch: 0, bearing: 0 };

export type Exaggeration = 1 | 2 | 3;

/** Turn terrain (and buildings, when the Amazon tiles have them) on or off. Safe to call repeatedly. */
export function setTerrain3D(map: Map, on: boolean, exaggeration: Exaggeration, { hillshade }: { hillshade: boolean }): void {
  if (!map.getSource(TERRAIN_SOURCE)) map.addSource(TERRAIN_SOURCE, OPEN_TERRAIN);
  map.setTerrain(on ? { source: TERRAIN_SOURCE, exaggeration } : null);

  const firstOverlay = ['zone-fill', 'routes-casing', 'residents-selected'].find((id) => map.getLayer(id));
  if (hillshade && !map.getLayer(HILLSHADE_LAYER)) {
    map.addLayer({ id: HILLSHADE_LAYER, type: 'hillshade', source: TERRAIN_SOURCE }, firstOverlay);
  }
  if (map.getLayer(HILLSHADE_LAYER)) map.setLayoutProperty(HILLSHADE_LAYER, 'visibility', on ? 'visible' : 'none');

  if (map.getSource('aws') && !map.getLayer(BUILDINGS_LAYER)) {
    map.addLayer(
      {
        id: BUILDINGS_LAYER,
        type: 'fill-extrusion',
        source: 'aws',
        'source-layer': 'buildings',
        minzoom: 14,
        filter: ['==', ['get', 'kind'], 'building'],
        paint: {
          'fill-extrusion-color': '#d9d4c7',
          'fill-extrusion-height': ['coalesce', ['get', 'height'], 6], // PROGRESS.md: check heights with the key
          'fill-extrusion-base': ['coalesce', ['get', 'min_height'], 0],
          'fill-extrusion-opacity': 0.85,
        },
      },
      firstOverlay,
    );
  }
  if (map.getLayer(BUILDINGS_LAYER)) map.setLayoutProperty(BUILDINGS_LAYER, 'visibility', on ? 'visible' : 'none');
}
