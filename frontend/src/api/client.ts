/**
 * API client: fetch helpers for ${VITE_API_URL} and the hooks the screens use.
 *
 * useDashboard() polls GET /dashboard every 3 s; its actions call the §8 routes.
 * With VITE_USE_MOCK=true it runs on api/mock.ts instead (offline work until the
 * AWS gate; delete the mock in H7-H8). Screens don't know which one they get.
 *
 * Implements: PLAN.md §8 (API contract), §9 (TanStack Query, 3 s polling). Owner: P1 (Frontend and UX).
 */
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo, useRef, useState } from 'react';
import { type MockPlanState, mockDashboard, mockMessages, mockRun } from './mock';
import { zonePolygon } from './seed';
import type {
  CaseResponse,
  CheckinsResponse,
  ClockAdvanceResponse,
  CreateOutageResponse,
  DashboardResponse,
  InboundRequest,
  Message,
  MessagesResponse,
  PlanResponse,
  RunResponse,
  Trace,
  TracesResponse,
} from './types';

const API_URL = import.meta.env.VITE_API_URL;
export const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';
const POLL_MS = 3000;
const OUTAGE_HOURS = 14;

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

export interface DashboardState {
  data: DashboardResponse | undefined;
  error: Error | null;
  /** What is running right now, named for the UI ("Amazon Bedrock is writing…"), or null. */
  busy: string | null;
  advance: (minutes: number) => void;
  reset: () => void;
  loadZone: () => void;
  sendCheckins: () => void;
  planDispatch: () => void;
  approvePlan: () => void;
}

const minutesSinceStart = (d: DashboardResponse | undefined) =>
  d?.outage ? Math.round((Date.parse(d.now) - Date.parse(d.outage.starts_at)) / 60_000) : 0;

function useLiveDashboard(): DashboardState {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => apiGet<DashboardResponse>('/dashboard'),
    refetchInterval: POLL_MS,
  });
  const [busy, setBusy] = useState<string | null>(null);
  const [actionError, setActionError] = useState<Error | null>(null);
  const inFlight = useRef(false);

  const run = useCallback(
    async (label: string, action: () => Promise<unknown>) => {
      if (inFlight.current) return; // e.g. timeline play ticks while Job 4 is still drafting
      inFlight.current = true;
      setBusy(label);
      setActionError(null);
      try {
        await action();
      } catch (err) {
        setActionError(err as Error);
      } finally {
        inFlight.current = false;
        setBusy(null);
        await queryClient.invalidateQueries();
      }
    },
    [queryClient],
  );

  const data = query.data;
  const outageId = data?.outage?.outage_id;
  const toContact = data?.cases.filter((c) => c.status === 'not_contacted').length ?? 0;
  return {
    data,
    error: actionError ?? query.error,
    busy,
    advance: useCallback(
      (minutes: number) =>
        void run(`Advancing the clock ${minutes} min; Amazon Bedrock drafts any escalations…`, () =>
          apiPost<ClockAdvanceResponse>('/clock/advance', { minutes }),
        ),
      [run],
    ),
    reset: () => void run('Resetting the demo…', () => apiPost('/demo/reset')),
    loadZone: () =>
      void run('Loading the outage zone…', () => {
        const start = data?.now ?? new Date().toISOString();
        const restore = new Date(Date.parse(start) + OUTAGE_HOURS * 3_600_000).toISOString();
        return apiPost<CreateOutageResponse>('/outages', {
          name: 'East San Jose PSPS',
          polygon: zonePolygon,
          starts_at: start,
          est_restore_at: restore,
        });
      }),
    sendCheckins: () =>
      void run(`Amazon Bedrock is writing ${toContact} check-ins…`, () =>
        apiPost<CheckinsResponse>(`/outages/${outageId}/checkins`),
      ),
    planDispatch: () =>
      void run('Amazon Bedrock is planning volunteer routes with Amazon Location…', () =>
        apiPost<PlanResponse>('/plans', { outage_id: outageId }),
      ),
    approvePlan: () =>
      void run('Approving the plan…', () => apiPost<PlanResponse>(`/plans/${data?.plan?.plan_id}/approve`)),
  };
}

function useMockDashboard(): DashboardState {
  const [minute, setMinute] = useState(0);
  const [plan, setPlan] = useState<MockPlanState | null>(null);
  const data = useMemo(() => mockDashboard(minute, plan), [minute, plan]);
  return {
    data,
    error: null,
    busy: null,
    advance: useCallback((minutes: number) => setMinute((m) => Math.min(m + minutes, OUTAGE_HOURS * 60)), []),
    reset: () => {
      setMinute(0);
      setPlan(null);
    },
    loadZone: () => {}, // the mock always has its outage
    sendCheckins: () => setMinute((m) => Math.max(m, 5)), // the mock sends them at +5 min
    planDispatch: () => setPlan({ status: 'draft', drafted_at: minute, done: [] }),
    approvePlan: () => setPlan((p) => p && { ...p, status: 'approved' }),
  };
}

export const useDashboard: () => DashboardState = USE_MOCK ? useMockDashboard : useLiveDashboard;

/** A resident's thread (GET /residents/{id}/messages), polled. The mock needs its dashboard's time. */
export function useMessages(residentId: string | null, dashboard?: DashboardResponse): Message[] {
  const query = useQuery({
    queryKey: ['messages', residentId],
    queryFn: () => apiGet<MessagesResponse>(`/residents/${residentId}/messages`),
    refetchInterval: POLL_MS,
    enabled: !USE_MOCK && residentId !== null,
  });
  if (!residentId) return [];
  if (USE_MOCK) return mockMessages(residentId, dashboard ? minutesSinceStart(dashboard) : 5);
  return query.data?.messages ?? [];
}

/** Newest Bedrock calls for the AI Trace tab (GET /traces), polled. */
export function useTraces(): Trace[] {
  const query = useQuery({
    queryKey: ['traces'],
    queryFn: () => apiGet<TracesResponse>('/traces?limit=50'),
    refetchInterval: POLL_MS,
    enabled: !USE_MOCK,
  });
  return query.data?.traces ?? [];
}

/** A volunteer's route sheet (GET /runs/{id}), polled. The mock serves an approved plan at +4 h. */
export function useRun(runId: string): { data: RunResponse | null | undefined; error: Error | null } {
  const query = useQuery({
    queryKey: ['run', runId],
    queryFn: () => apiGet<RunResponse>(`/runs/${runId}`),
    refetchInterval: POLL_MS,
    enabled: !USE_MOCK,
  });
  const mock = useMemo(
    () => (USE_MOCK ? mockRun(runId, mockDashboard(240, { status: 'approved', drafted_at: 240, done: [] })) : null),
    [runId],
  );
  return USE_MOCK ? { data: mock, error: null } : { data: query.data, error: query.error };
}

export const markStopDone = (runId: string, residentId: string) =>
  apiPost<CaseResponse>(`/runs/${runId}/stops/${residentId}/done`);

/** The phone simulator's send: the same /inbound webhook real SMS would call. */
export const sendInbound = (body: InboundRequest) => apiPost<CaseResponse>('/inbound', body);
