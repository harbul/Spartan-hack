/**
 * "Amazon Bedrock" badge on every AI-produced element (check-ins, translations,
 * the "why", escalations, plan reasons), so judges see Bedrock doing the work.
 *
 * Implements: PLAN.md §9 (make Bedrock visible everywhere). Owner: P1 (Frontend and UX).
 */
export default function BedrockBadge() {
  return (
    <span className="inline-flex shrink-0 items-center rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] font-medium text-indigo-800">
      Amazon Bedrock
    </span>
  );
}
