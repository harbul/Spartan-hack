/**
 * MOCK (H1-H4): a /dashboard response built from the seed data, so the screens
 * can be built before the API exists. It follows the demo story over virtual time:
 *   +5 min   check-ins sent to all 40 residents
 *   replies  the 20 labeled test replies, then most others reply "1"
 *   silence  Lupe and three others never reply and climb the §5 ladder
 *            (L1 30 min, L2 60, L3 90; halved for oxygen and dialysis)
 * Priorities and "why" texts are placeholders, not the §5 score or Bedrock.
 * Delete when /dashboard is wired (H4-H6).
 *
 * Owner: P1 (Frontend and UX).
 */
import { residents, resources, testReplies, volunteers, zonePolygon, type TestReply } from './seed';
import { givenName } from '../components/status';
import type { Assessment, Band, Case, DashboardCase, DashboardResponse, Event, Message, Resident } from './types';

const START = '2026-10-24T01:00:00Z'; // 6 PM PDT, Friday Oct 23
const OUTAGE_HOURS = 14;
const CHECKINS_AT = 5;
const OUTAGE_ID = 'out-mock';
const SILENT = new Set(['res-005', 'res-025', 'res-036', 'res-039']);
const REPLY_AT = [22, 12, 26, 9, 31, 18, 7, 15, 35, 11, 20, 8, 28, 40, 10, 24, 33, 45, 17, 14];

const HERO_WHY: Record<string, string> = {
  'res-001': 'Oxygen tank has ~3 h left but power is out for 14 h, he lives alone, and he wrote that he feels short of breath.',
  'res-002': 'Her insulin needs cooling and the fridge has stopped; backup lasts ~12 h against a 14 h outage.',
  'res-003': "Power chair at 20% and he can't get out if it dies; he lives alone and needs a ride.",
  'res-004': 'Generator running and she says all is well; her backup covers the outage.',
  'res-005': 'No reply after a re-ping and a message to her daughter; oxygen, lives alone, age 89.',
};
const PRIORITY: Record<Band, number> = { Critical: 92, High: 68, Watch: 42, OK: 9 };

const at = (minutes: number) => new Date(Date.parse(START) + minutes * 60_000).toISOString();
const byResident = new Map(testReplies.map((r, i) => [r.resident_id, { reply: r, minute: REPLY_AT[i] }]));
const halved = (r: Resident) => r.devices.some((d) => d === 'oxygen' || d === 'dialysis');

function okReplyMinute(index: number) {
  return 8 + ((index * 7) % 48);
}

function assessmentFrom(reply: TestReply): Assessment {
  const e = reply.expected;
  const confidence = e.status === 'unclear' ? 0.4 : 0.9;
  return {
    status: e.status,
    needs: e.needs,
    supply_hours_left: e.supply_hours_left,
    needs_transport: e.needs_transport,
    distress_level: e.distress_level,
    detected_language: reply.language,
    english_translation: reply.language === 'en' ? reply.text : '(translation appears when Bedrock reads the reply)',
    key_quote: reply.text,
    confidence,
    reasoning: '(mock)',
  };
}

function caseAt(resident: Resident, index: number, minute: number): Case {
  const base: Case = {
    outage_id: OUTAGE_ID,
    resident_id: resident.resident_id,
    status: 'not_contacted',
    priority: 0,
    band: 'OK',
    score_breakdown: null,
    rationale: null,
    assessment: null,
    escalation_level: 0,
    last_outbound_at: null,
    last_inbound_at: null,
    needs_review: false,
  };
  if (minute < CHECKINS_AT) return base;
  base.status = 'awaiting_reply';
  base.band = 'Watch';
  base.priority = PRIORITY.Watch;
  base.last_outbound_at = at(CHECKINS_AT);

  const labeled = byResident.get(resident.resident_id);
  const replyMinute = SILENT.has(resident.resident_id) ? null : (labeled?.minute ?? okReplyMinute(index));
  if (replyMinute !== null && minute >= replyMinute) {
    const assessment = labeled ? assessmentFrom(labeled.reply) : null;
    const band = labeled?.reply.expected.band ?? 'OK';
    const status = labeled?.reply.expected.status ?? 'ok';
    return {
      ...base,
      status: status === 'unclear' ? 'awaiting_reply' : status,
      band,
      priority: PRIORITY[band],
      assessment,
      rationale: HERO_WHY[resident.resident_id] ?? (labeled ? `Reply: "${labeled.reply.text}"` : 'Replied 1: OK'),
      last_inbound_at: at(replyMinute),
      needs_review: (assessment?.confidence ?? 1) < 0.6,
    };
  }

  // Silence ladder (§5)
  const silentFor = minute - CHECKINS_AT;
  const factor = halved(resident) ? 0.5 : 1;
  const level = ([3, 2, 1] as const).find((l) => silentFor >= l * 30 * factor) ?? 0;
  const status = level === 3 ? 'silent' : level === 2 ? 'escalated' : 'awaiting_reply';
  const band: Band = level === 3 ? (halved(resident) ? 'Critical' : 'High') : level === 2 ? 'High' : 'Watch';
  return {
    ...base,
    status,
    band,
    priority: PRIORITY[band] + level * 3,
    escalation_level: level,
    rationale: level ? (HERO_WHY[resident.resident_id] ?? `No reply for ${silentFor} min (escalation L${level}).`) : null,
  };
}

function eventsUntil(minute: number): Event[] {
  const events: Event[] = [
    { outage_id: OUTAGE_ID, ts: at(0), type: 'outage_started', label: 'Outage started: 40 registered residents affected', resident_id: null, from_status: null, to_status: null },
    { outage_id: OUTAGE_ID, ts: at(CHECKINS_AT), type: 'checkins_sent', label: 'Check-ins sent to 40 residents', resident_id: null, from_status: null, to_status: null },
  ];
  testReplies.forEach((reply, i) => {
    const name = residents.find((r) => r.resident_id === reply.resident_id)!.name;
    events.push({ outage_id: OUTAGE_ID, ts: at(REPLY_AT[i]), type: 'reply', label: `${name} replied`, resident_id: reply.resident_id, from_status: 'awaiting_reply', to_status: null });
  });
  for (const id of SILENT) {
    const resident = residents.find((r) => r.resident_id === id)!;
    const factor = halved(resident) ? 0.5 : 1;
    for (const level of [1, 2, 3]) {
      const what = ['', 're-ping sent', 'emergency contact messaged', 'door-knock added'][level];
      events.push({ outage_id: OUTAGE_ID, ts: at(CHECKINS_AT + level * 30 * factor), type: 'escalation', label: `${resident.name}: L${level} ${what}`, resident_id: id, from_status: null, to_status: null });
    }
  }
  return events.filter((e) => e.ts <= at(minute)).sort((a, b) => a.ts.localeCompare(b.ts));
}

export function mockDashboard(minute: number): DashboardResponse {
  const cases: DashboardCase[] = residents.map((resident, i) => {
    const c = caseAt(resident, i, minute);
    const hours = (c.assessment?.supply_hours_left ?? resident.baseline_backup_hours) - minute / 60;
    return { ...c, resident, backup_hours_left: Math.max(0, Math.round(hours * 10) / 10) };
  });
  const count = (fn: (c: Case) => boolean) => cases.filter(fn).length;
  return {
    now: at(minute),
    outage: {
      outage_id: OUTAGE_ID,
      name: 'East San Jose PSPS',
      polygon: zonePolygon,
      starts_at: START,
      est_restore_at: at(OUTAGE_HOURS * 60),
      affected_ids: residents.map((r) => r.resident_id),
      status: 'active',
    },
    counts: {
      safe: count((c) => c.status === 'ok' || c.status === 'resolved'),
      needs_help: count((c) => (c.status === 'needs_help' || c.status === 'dispatched') && c.band !== 'Critical'),
      critical: count((c) => (c.status === 'needs_help' || c.status === 'dispatched') && c.band === 'Critical'),
      no_reply: count((c) => ['awaiting_reply', 'escalated', 'silent'].includes(c.status)),
    },
    cases,
    events: eventsUntil(minute),
    plan: null,
    resources,
    volunteers,
  };
}

export function mockMessages(residentId: string, minute: number): Message[] {
  const resident = residents.find((r) => r.resident_id === residentId);
  if (!resident || minute < CHECKINS_AT) return [];
  const what = resident.devices.every((d) => d === 'insulin') ? 'medicine' : 'equipment';
  const messages: Message[] = [
    {
      resident_id: residentId,
      ts: at(CHECKINS_AT),
      direction: 'out',
      channel: 'sms',
      text: `Hi ${givenName(resident)}, this is Santa Clara County. Power in your area goes off at 6 PM until about 8 AM. How many hours can your ${what} last without power? Reply 1 if you're OK, 2 if you need help. Reply STOP to opt out.`,
      translation_en: null,
      image_key: null,
      trace_id: null,
    },
  ];
  const c = caseAt(resident, residents.indexOf(resident), minute);
  if (c.last_inbound_at) {
    const reply = byResident.get(residentId)?.reply;
    messages.push({
      resident_id: residentId,
      ts: c.last_inbound_at,
      direction: 'in',
      channel: 'sms',
      text: reply?.text ?? '1',
      translation_en: null,
      image_key: reply?.image ?? null,
      trace_id: null,
    });
  }
  return messages;
}
