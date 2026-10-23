/**
 * Approved volunteer routes, one line per run (geometry from CalculateRoutes), white outline.
 * Also used by the flat map on the volunteer route sheet.
 *
 * Implements: PLAN.md §9.1 (3D incident map). Owner: P1 (Frontend and UX).
 */
import type { Map } from 'maplibre-gl';
import type { Run } from '../../../api/types';

export function addRoutesLayer(map: Map, data: Run[]): void {
  // TODO(P1, §9.1)
}
