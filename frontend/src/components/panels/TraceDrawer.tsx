/**
 * Right panel, AI Trace tab: live list of Bedrock calls; each shows the masked prompt,
 * tool calls step by step, JSON output, latency, tokens and guardrail action.
 *
 * Data: GET /traces?limit=50.
 * Implements: PLAN.md §4, §9.1 right. Owner: P1 (Frontend and UX).
 */
import { useState } from 'react';
import type { BedrockJob, Trace } from '../../api/types';
import BedrockBadge from '../BedrockBadge';
import { clockTime } from '../status';

const JOB_LABEL: Record<BedrockJob, string> = {
  checkin: 'Job 1 · Check-in writer',
  assess: 'Job 2 · Reply understanding',
  explain: 'Job 3 · Triage explainer',
  escalate: 'Job 4 · Escalation drafter',
  planner: 'Job 5 · Dispatch planner',
};

export default function TraceDrawer({ traces }: { traces: Trace[] }) {
  const [open, setOpen] = useState<string | null>(null);
  if (traces.length === 0) {
    return (
      <p className="p-4 text-sm text-stone-500">
        No Bedrock calls yet. Every check-in, reply assessment and plan will appear here with its prompt,
        output, latency and tokens.
      </p>
    );
  }
  // TODO(P1, H8-H12): step-by-step tool calls for the Job 5 agent, guardrail actions.
  return (
    <ul className="divide-y divide-stone-200 text-sm">
      {traces.map((t) => (
        <li key={t.trace_id}>
          <button onClick={() => setOpen(open === t.trace_id ? null : t.trace_id)} className="w-full px-3 py-2 text-left hover:bg-white">
            <div className="flex items-center gap-2">
              <BedrockBadge />
              <span className="font-medium">{JOB_LABEL[t.job]}</span>
              <span className="ml-auto text-xs text-stone-500">{clockTime(t.ts)}</span>
            </div>
            <div className="mt-0.5 text-xs text-stone-500">
              {t.model_id} · {t.latency_ms} ms · {t.input_tokens} in / {t.output_tokens} out tokens
              {t.tool_calls.length > 0 && ` · tool: ${t.tool_calls.map((c) => c.name).join(', ')}`}
            </div>
          </button>
          {open === t.trace_id && (
            <div className="space-y-2 bg-white px-3 pb-3 text-xs">
              <h4 className="font-semibold">Prompt (PII masked)</h4>
              <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-stone-100 p-2">{t.input_masked}</pre>
              <h4 className="font-semibold">Output</h4>
              <pre className="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-stone-100 p-2">
                {typeof t.output === 'string' ? t.output : JSON.stringify(t.output, null, 2)}
              </pre>
            </div>
          )}
        </li>
      ))}
    </ul>
  );
}
