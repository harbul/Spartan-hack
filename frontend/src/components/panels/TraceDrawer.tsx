/**
 * Right panel, AI Trace tab: live list of Bedrock calls; each shows the masked prompt,
 * tool calls step by step, JSON output, latency, tokens and guardrail action.
 *
 * Data: GET /traces?limit=50.
 * Implements: PLAN.md §4, §9.1 right. Owner: P1 (Frontend and UX).
 */
export default function TraceDrawer() {
  // TODO(P1, H4-H6): list GET /traces; H8-H12: step-by-step detail per call.
  return (
    <p className="p-4 text-sm text-stone-500">
      No Bedrock calls yet. Every check-in, reply assessment and plan will appear here with its prompt,
      output, latency and tokens.
    </p>
  );
}
