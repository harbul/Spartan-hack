/**
 * Resource centers, the pharmacy and volunteer start points as distinct icons.
 *
 * Implements: PLAN.md §9.1 (3D incident map). Owner: P1 (Frontend and UX).
 */
import type { Map } from 'maplibre-gl';
import type { Resource, Volunteer } from '../../../api/types';

export function addResourcesLayer(map: Map, data: { resources: Resource[]; volunteers: Volunteer[] }): void {
  // TODO(P1, §9.1)
}
