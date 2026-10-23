/**
 * API client: fetch helpers for ${VITE_API_URL} and the dashboard hook the
 * command center uses.
 *
 * useDashboard() reads the MOCK for now (H1-H4). In H4-H6 it polls
 * GET /dashboard every 3 s, and advance() calls POST /clock/advance; the
 * screens don't change.
 *
 * Implements: PLAN.md §8 (API contract), §9 (TanStack Query, 3 s polling). Owner: P1 (Frontend and UX).
 */
import { useCallback, useMemo, useState } from 'react';
import { mockDashboard, mockMessages } from './mock';
import type { DashboardResponse, Message } from './types';

const API_URL = import.meta.env.VITE_API_URL;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, init);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail ?? `HTTP ${response.status}`);
  return body as T;
}

export const apiGet = <T>(path: string) => request<T>(path);

export const apiPost = <T>(path: string, body?: unknown) =>
  request<T>(path, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

const MAX_MINUTES = 14 * 60; // outage length in the mock

export interface DashboardState {
  data: DashboardResponse;
  advance: (minutes: number) => void;
  reset: () => void;
  messages: (residentId: string) => Message[];
}

export function useDashboard(): DashboardState {
  // TODO(P1, H4-H6): useQuery(['dashboard'], () => apiGet(`/dashboard?outage_id=...`),
  // { refetchInterval: 3000 }); advance -> apiPost('/clock/advance', { minutes }).
  const [minute, setMinute] = useState(0);
  const data = useMemo(() => mockDashboard(minute), [minute]);
  const advance = useCallback((minutes: number) => setMinute((m) => Math.min(m + minutes, MAX_MINUTES)), []);
  const reset = useCallback(() => setMinute(0), []);
  const messages = useCallback((residentId: string) => mockMessages(residentId, minute), [minute]);
  return { data, advance, reset, messages };
}
