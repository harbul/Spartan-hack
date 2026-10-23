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
export default function IncidentMap() {
  // TODO(P1, §6, §9.1): MUST tier is a flat 2D satellite map; 3D is the SHOULD upgrade.
  return null;
}
