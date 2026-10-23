/**
 * MapLibre GL setup shared by every map: CSS and the web worker.
 * MapLibre v6 finds its worker next to its own module at runtime, which Vite
 * doesn't copy (dev or build), so we hand it the bundled worker URL.
 * Import maplibregl from here, not from 'maplibre-gl'.
 *
 * Owner: P1 (Frontend and UX).
 */
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import 'maplibre-gl/dist/maplibre-gl.css';

maplibregl.setWorkerUrl(workerUrl);

export { maplibregl };
