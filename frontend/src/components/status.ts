/**
 * How a case looks everywhere (map markers, queue cards, counters): its display
 * category, color and labels. Colors from §9: green Safe, amber Needs help,
 * red Critical, gray-violet No reply.
 *
 * Implements: PLAN.md §9.1. Owner: P1 (Frontend and UX).
 */
import type { Band, Case, Device, EventType, Language, Resident } from '../api/types';

export type Category = 'critical' | 'needs_help' | 'no_reply' | 'safe' | 'not_contacted';

export function categoryOf(c: Pick<Case, 'status' | 'band'>): Category {
  switch (c.status) {
    case 'ok':
    case 'resolved':
      return 'safe';
    case 'not_contacted':
      return 'not_contacted';
    case 'awaiting_reply':
    case 'escalated':
    case 'silent':
      return 'no_reply';
    default: // needs_help, dispatched
      return c.band === 'Critical' ? 'critical' : 'needs_help';
  }
}

export const CATEGORY: Record<Category, { label: string; color: string }> = {
  critical: { label: 'Critical', color: '#dc2626' },
  needs_help: { label: 'Needs help', color: '#f59e0b' },
  no_reply: { label: 'No reply', color: '#8b7fa8' },
  safe: { label: 'Safe', color: '#16a34a' },
  not_contacted: { label: 'Not contacted', color: '#a8a29e' },
};

export const BAND_CLASS: Record<Band, string> = {
  Critical: 'bg-red-600 text-white',
  High: 'bg-amber-500 text-white',
  Watch: 'bg-yellow-100 text-yellow-900',
  OK: 'bg-green-100 text-green-900',
};

export const DEVICE_LABEL: Record<Device, string> = {
  oxygen: 'Oxygen',
  dialysis: 'Dialysis',
  insulin: 'Insulin',
  power_wheelchair: 'Power chair',
  other: 'Other device',
};

export const LANGUAGE_LABEL: Record<Language, string> = { en: 'EN', es: 'ES', vi: 'VI' };

export const STATUS_LABEL: Record<Case['status'], string> = {
  not_contacted: 'Not contacted',
  awaiting_reply: 'Awaiting reply',
  ok: 'OK',
  needs_help: 'Needs help',
  escalated: 'Escalated',
  silent: 'Silent',
  dispatched: 'Dispatched',
  resolved: 'Resolved',
};

/** Timeline marker colors per event type. */
export const EVENT_COLOR: Record<EventType, string> = {
  outage_started: '#1c1917',
  checkins_sent: '#4f46e5',
  reply: '#16a34a',
  escalation: '#8b7fa8',
  band_change: '#f59e0b',
  plan_drafted: '#2563eb',
  plan_approved: '#2563eb',
  stop_done: '#0d9488',
};

/** "6:45 PM" in San Jose time. */
export function clockTime(ts: string): string {
  return new Date(ts).toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'America/Los_Angeles',
  });
}

/** Given name. Vietnamese names put it last (Trần Văn Minh -> Minh). */
export function givenName(resident: Pick<Resident, 'name' | 'language'>): string {
  const parts = resident.name.split(' ');
  return resident.language === 'vi' ? parts[parts.length - 1] : parts[0];
}
