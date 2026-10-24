/**
 * Resident details (beside the map, and on the Residents tab): profile, medical dependency, last contact, backup left,
 * AI assessment (labeled AI-estimated urgency), message thread with translations, suggested action.
 *
 * Data: /dashboard cases, GET /residents/{id}/messages.
 * Implements: PLAN.md §9.1 right. Owner: P1 (Frontend and UX).
 */
import type { DashboardCase, Message } from '../../api/types';
import BedrockBadge from '../BedrockBadge';
import Icon from '../Icon';
import { BAND_CLASS, CATEGORY, DEVICE_LABEL, STATUS_LABEL, categoryOf, clockTime, givenName } from '../status';

const NEED_LABEL: Record<string, string> = {
  cooling_for_medication: 'Cooling for medicine',
  power_for_device: 'Power for a device',
  transport: 'Transport',
  medication_resupply: 'Medicine resupply',
  welfare_check: 'Welfare check',
  other: 'Other / unknown',
};

interface Props {
  dcase: DashboardCase | undefined;
  messages: Message[];
}

export default function ResidentPanel({ dcase, messages }: Props) {
  if (!dcase) {
    return <p className="p-4 text-sm text-stone-500">Select a resident on the map or in the queue.</p>;
  }
  const { resident, assessment } = dcase;
  const category = CATEGORY[categoryOf(dcase)];
  const lastContact = dcase.last_inbound_at ?? dcase.last_outbound_at;

  return (
    <div className="space-y-4 p-4 text-sm">
      <section>
        <div className="flex items-center gap-2">
          <h2 className="text-lg font-semibold">{resident.name}</h2>
          <span className="text-stone-500">{resident.age}</span>
          <span className={`ml-auto rounded px-1.5 text-xs font-semibold ${BAND_CLASS[dcase.band]}`}>
            {dcase.band} {Math.round(dcase.priority)}
          </span>
        </div>
        <p className="text-stone-600">{resident.address}</p>
        <p className="mt-1 flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full" style={{ background: category.color }} />
          {STATUS_LABEL[dcase.status]}
          {dcase.escalation_level > 0 && <span className="text-stone-500">· escalation L{dcase.escalation_level}</span>}
        </p>
      </section>

      <dl className="grid grid-cols-2 gap-x-3 gap-y-1">
        <dt className="text-stone-500">Depends on</dt>
        <dd>{resident.devices.map((d) => DEVICE_LABEL[d]).join(', ')}</dd>
        <dt className="text-stone-500">Backup left (est.)</dt>
        <dd className={dcase.backup_hours_left !== null && dcase.backup_hours_left < 4 ? 'font-semibold text-red-600' : ''}>
          {dcase.backup_hours_left === null ? 'unknown' : `${dcase.backup_hours_left} h`}
        </dd>
        <dt className="text-stone-500">Lives alone</dt>
        <dd>{resident.lives_alone ? 'Yes' : 'No'}</dd>
        <dt className="text-stone-500">Last contact</dt>
        <dd>{lastContact ? clockTime(lastContact) : 'none'}</dd>
        <dt className="text-stone-500">Emergency contact</dt>
        <dd>
          {resident.emergency_contact.name} ({resident.emergency_contact.relation})
        </dd>
      </dl>

      {(assessment || dcase.rationale) && (
        <section className="rounded-lg border border-stone-200 bg-white p-3">
          <div className="mb-1 flex items-center gap-2">
            <h3 className="font-semibold">AI-estimated urgency</h3>
            <BedrockBadge />
          </div>
          <p className="mb-2 text-xs text-stone-500">An estimate to help prioritize, not a confirmed medical emergency.</p>
          {dcase.rationale && <p className="mb-2">{dcase.rationale}</p>}
          {assessment && (
            <dl className="grid grid-cols-2 gap-x-3 gap-y-1">
              <dt className="text-stone-500">Needs</dt>
              <dd>{assessment.needs.map((n) => NEED_LABEL[n] ?? n).join(', ') || 'none'}</dd>
              <dt className="text-stone-500">Supply left</dt>
              <dd>{assessment.supply_hours_left === null ? 'not stated' : `${assessment.supply_hours_left} h`}</dd>
              <dt className="text-stone-500">Distress</dt>
              <dd>{assessment.distress_level} / 3</dd>
              <dt className="text-stone-500">Confidence</dt>
              <dd>{Math.round(assessment.confidence * 100)}%</dd>
            </dl>
          )}
          {dcase.needs_review && (
            <p className="mt-2 rounded bg-orange-100 px-2 py-1 text-xs font-semibold text-orange-800">
              Needs human review: low confidence
            </p>
          )}
        </section>
      )}

      <section>
        <h3 className="mb-2 font-semibold">Messages</h3>
        {messages.length === 0 && <p className="text-stone-500">No messages yet.</p>}
        <ul className="space-y-2">
          {messages.map((m) => (
            <li key={m.ts + m.direction} className={m.direction === 'out' ? 'pr-8' : 'pl-8'}>
              <div className={`rounded-lg px-3 py-2 ${m.direction === 'out' ? 'bg-indigo-50' : 'bg-white ring-1 ring-stone-200'}`}>
                <p>{m.text}</p>
                {m.translation_en && <p className="mt-1 text-xs italic text-stone-500">{m.translation_en}</p>}
                {m.image_key && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-stone-500">
                    <Icon name="camera" className="h-3.5 w-3.5" /> photo attached
                  </p>
                )}
              </div>
              <div className="mt-0.5 flex items-center gap-1 text-xs text-stone-500">
                {m.direction === 'out' ? 'County' : givenName(resident)} · {clockTime(m.ts)}
                {m.direction === 'out' && <BedrockBadge />}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
