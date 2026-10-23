/**
 * Command center (/): the coordinator's four-area screen, like FireTrace.
 *   Top bar     logo, incident name, area, outage window, Reset demo, About
 *   Left        panels/Overview + panels/TriageQueue
 *   Center      map/IncidentMap (3D)
 *   Right       tabs: panels/ResidentPanel, panels/TraceDrawer, panels/PlanPanel
 *   Bottom      action bar (Send check-ins -> Plan dispatch -> Approve) above timeline/Timeline
 * The top bar and action bar live in this page until they need their own file.
 *
 * Data: GET /dashboard every 3 s.
 * Implements: PLAN.md §9.1. Owner: P1 (Frontend and UX).
 */
export default function CommandCenter() {
  // TODO(P1, §9.1): compose the four areas.
  return <main className="p-4">StillHere command center</main>;
}
