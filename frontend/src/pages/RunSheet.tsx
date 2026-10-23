/**
 * Volunteer route sheet (/run/:runId): mobile layout, flat 2D map (no 3D on
 * phones), ordered stops with action, items, address and reason, "Mark done".
 *
 * Data: GET /runs/{run_id}, POST /runs/{run_id}/stops/{resident_id}/done.
 * Implements: PLAN.md §9.3. Owner: P1 (Frontend and UX).
 */
export default function RunSheet() {
  // TODO(P1, §9.3)
  return <main className="p-4">Volunteer route sheet</main>;
}
