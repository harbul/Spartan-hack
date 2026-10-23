/**
 * Right panel, Plan tab: draft dispatch plan per volunteer with the agent's one-line reasons
 * (Amazon Bedrock badge) and the Approve button.
 *
 * Data: /dashboard plan, POST /plans, POST /plans/{id}/approve.
 * Implements: PLAN.md §4 Job 5, §9.1 right. Owner: P1 (Frontend and UX).
 */
export default function PlanPanel() {
  // TODO(P1, H6-H7): render dashboard.plan runs and stops, Approve button.
  return (
    <p className="p-4 text-sm text-stone-500">
      No plan yet. "Plan dispatch" asks the Amazon Bedrock agent for a draft; nothing is dispatched until you approve it.
    </p>
  );
}
