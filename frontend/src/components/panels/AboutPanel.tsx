/**
 * About StillHere (top bar "About"): what the app does, how decisions are made,
 * the AWS services, and the sourced stats behind the persona.
 * Every stat comes from docs/sources.md and stays tagged "to verify" until P4 opens
 * the link and fills in "Accessed" there; then set `verified` here.
 *
 * Implements: PLAN.md §9 SHOULD (About panel with sourced stats), §2, §18. Owner: P1 (Frontend and UX), stats by P4.
 */
import { useEffect } from 'react';
import BedrockBadge from '../BedrockBadge';

interface Stat {
  number: string;
  claim: string;
  source: string;
  url: string;
  verified: boolean; // flip to true once docs/sources.md has an "Accessed" date for it
}

const STATS: Stat[] = [
  {
    number: '~1.1 million',
    claim: 'PG&E customers lost power in the Oct 26, 2019 Public Safety Power Shutoff',
    source: 'KTVU',
    url: 'https://www.ktvu.com/news/1400-customers-still-without-electricity-from-recent-pge-planned-shutoffs',
    verified: false,
  },
  {
    number: '~55 hours',
    claim: 'average outage length in the Oct 26 and 29, 2019 shutoffs',
    source: 'PG&E post-event report to the CPUC',
    url: 'https://webproda.cpuc.ca.gov/-/media/cpuc-website/divisions/safety-and-enforcement-division/reports/psps-post-event-reports/2019/pge-psps-postevent-report-oct-2629-2019-amended.pdf',
    verified: false,
  },
  {
    number: '~3,900',
    claim: 'customers in those shutoffs were told only after the power was cut',
    source: 'PG&E post-event report to the CPUC',
    url: 'https://webproda.cpuc.ca.gov/-/media/cpuc-website/divisions/safety-and-enforcement-division/reports/psps-post-event-reports/2019/pge-psps-postevent-report-oct-2629-2019-amended.pdf',
    verified: false,
  },
  {
    number: 'Up to 28 days',
    claim: 'insulin vials or cartridges may stay unrefrigerated at 59–86 °F (labels vary); heat is the real risk',
    source: 'U.S. FDA',
    url: 'https://www.fda.gov/drugs/emergencypreparedness/ucm085213.htm',
    verified: false,
  },
];

const SERVICES = [
  ['Amazon Bedrock', 'writes check-ins, reads replies (text and photos), explains priorities, drafts escalations, plans routes'],
  ['Amazon Location Service', 'satellite and 3D map, route optimization for volunteers'],
  ['AWS Lambda + API Gateway', 'one FastAPI app for every action'],
  ['Amazon DynamoDB', 'residents, cases, messages, plans, traces, events'],
  ['Amazon EventBridge', 'checks for silence every minute'],
  ['Amazon S3 + AWS Amplify', 'reply photos; hosts this app'],
];

export default function AboutPanel({ onClose }: { onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-stone-900/40 p-6" onClick={onClose}>
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="about-title"
        onClick={(e) => e.stopPropagation()}
        className="max-h-full w-full max-w-2xl overflow-y-auto rounded-lg bg-[#faf7f0] p-6 text-sm text-stone-800 shadow-xl"
      >
        <header className="mb-3 flex items-start justify-between gap-4">
          <div>
            <h2 id="about-title" className="text-lg font-semibold">About StillHere</h2>
            <p className="text-stone-600">In a crisis, silence is the loudest signal.</p>
          </div>
          <button onClick={onClose} className="rounded border border-stone-300 px-2 py-0.5 text-stone-600" aria-label="Close">
            Close
          </button>
        </header>

        <p className="mb-3">
          When a Public Safety Power Shutoff cuts power, people whose medicine or equipment runs on electricity are at
          risk. StillHere helps a county medical-needs coordinator reach every registered resident in the outage zone,
          understand their replies in their own language, and notice who goes silent, then plans volunteer visits that a
          person approves.
        </p>
        <p className="mb-4 rounded border border-stone-200 bg-white px-3 py-2">
          <span className="font-semibold">AI reads and explains, rules rank, humans decide.</span> Amazon Bedrock turns
          messy replies into structured needs and writes every message; a fixed, explainable score sets the priority;
          nothing is dispatched until the coordinator clicks Approve. Urgency is always labeled AI-estimated, never a
          diagnosis.
        </p>

        <h3 className="mb-2 font-semibold">Why it matters</h3>
        <ul className="mb-4 space-y-2">
          {STATS.map((s) => (
            <li key={s.claim} className="flex gap-3">
              <span className="w-28 shrink-0 font-semibold">{s.number}</span>
              <span>
                {s.claim}.{' '}
                <a href={s.url} target="_blank" rel="noreferrer" className="text-indigo-700 underline">
                  {s.source}
                </a>
                {!s.verified && (
                  <span className="ml-1 rounded bg-amber-100 px-1 text-xs text-amber-900" title="Not yet checked against the source (docs/sources.md)">
                    to verify
                  </span>
                )}
              </span>
            </li>
          ))}
        </ul>

        <h3 className="mb-2 flex items-center gap-2 font-semibold">
          Built on AWS <BedrockBadge />
        </h3>
        <dl className="mb-4 grid grid-cols-[180px_1fr] gap-x-3 gap-y-1">
          {SERVICES.map(([name, what]) => (
            <div key={name} className="contents">
              <dt className="font-medium">{name}</dt>
              <dd className="text-stone-600">{what}</dd>
            </div>
          ))}
        </dl>

        <p className="text-xs text-stone-500">
          Demo data: every resident, address and phone number is fictional (555 numbers). Texts go to a phone simulator
          that calls the same webhook real SMS would; production would add real SMS, an Amazon Connect voice line for
          landlines, and the county's registry.
        </p>
      </section>
    </div>
  );
}
