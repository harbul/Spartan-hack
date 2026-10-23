/**
 * Resident markers colored by status (green Safe, amber Needs help, red Critical,
 * gray-violet No reply), white outline; no-reply markers pulse harder with silence.
 *
 * Implements: PLAN.md §9.1 (3D incident map). Owner: P1 (Frontend and UX).
 */
import type { Map } from 'maplibre-gl';
import type { DashboardCase } from '../../../api/types';

export function addResidentsLayer(map: Map, data: DashboardCase[]): void {
  // TODO(P1, §9.1)
}
