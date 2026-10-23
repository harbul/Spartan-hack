/**
 * Shared contract: TypeScript types for the records (§7) and API shapes (§8).
 *
 * Mirror of backend/app/schemas.py. Change both in the same PR.
 * Shapes the plan does not spell out are marked PROPOSED; confirm them at H0
 * (see docs/PROGRESS.md, Open questions).
 *
 * Implements: PLAN.md §4 (Job 2 assessment), §5, §7, §8.
 * Owner: P1 (Frontend and UX), kept in sync with P2.
 */

// --- Enums (§3, §4, §5, §7) --------------------------------------------------

export type Language = 'en' | 'es' | 'vi';
export type Device = 'oxygen' | 'dialysis' | 'insulin' | 'power_wheelchair' | 'other';
export type CaseStatus =
  | 'not_contacted'
  | 'awaiting_reply'
  | 'ok'
  | 'needs_help'
  | 'escalated'
  | 'silent'
  | 'dispatched'
  | 'resolved';
export type Band = 'Critical' | 'High' | 'Watch' | 'OK';
export type AssessmentStatus = 'ok' | 'needs_help' | 'unclear';
export type Need =
  | 'cooling_for_medication'
  | 'power_for_device'
  | 'transport'
  | 'medication_resupply'
  | 'welfare_check'
  | 'other';
export type EscalationLevel = 0 | 1 | 2 | 3;
export type Direction = 'out' | 'in';
export type Channel = 'sms' | 'contact' | 'door';
export type PlanStatus = 'draft' | 'approved';
export type EventType =
  | 'outage_started'
  | 'checkins_sent'
  | 'reply'
  | 'escalation'
  | 'band_change'
  | 'plan_drafted'
  | 'plan_approved'
  | 'stop_done';
export type ResourceType = 'resource_center' | 'pharmacy';
export type StopAction = 'cooler' | 'battery' | 'door_knock' | 'ride';
export type BedrockJob = 'checkin' | 'assess' | 'explain' | 'escalate' | 'planner' | 'guardrail'; // guardrail: reply screening (Job 6)

/** ISO 8601 string in UTC (virtual time where noted). */
export type Timestamp = string;

export interface LatLng {
  lat: number;
  lng: number;
}

/** GeoJSON geometry, kept loose so the map can hand it straight to MapLibre. */
export type GeoJSONGeometry = { type: string; coordinates: unknown };

// --- Records (§7) -------------------------------------------------------------

export interface EmergencyContact {
  name: string;
  relation: string;
  phone: string;
  language: Language;
}

export interface Resident {
  resident_id: string;
  name: string;
  age: number;
  phone: string;
  address: string;
  lat: number;
  lng: number;
  language: Language;
  devices: Device[];
  baseline_backup_hours: number;
  lives_alone: boolean;
  emergency_contact: EmergencyContact;
  notes: string;
}

export interface Outage {
  outage_id: string;
  name: string;
  polygon: GeoJSONGeometry;
  starts_at: Timestamp;
  est_restore_at: Timestamp;
  affected_ids: string[];
  status: string; // PROPOSED values: 'active' | 'restored'
}

/** Job 2 forced tool call `record_assessment` (§4). */
export interface Assessment {
  status: AssessmentStatus;
  needs: Need[];
  supply_hours_left: number | null;
  needs_transport: boolean;
  distress_level: number; // 0-3
  detected_language: string;
  english_translation: string;
  key_quote: string; // verbatim, original language
  confidence: number; // 0-1; below 0.6 sets Case.needs_review
  reasoning: string;
}

/** Deterministic triage score parts (§5). PROPOSED field names. */
export interface ScoreBreakdown {
  device_weight: number;
  time_pressure: number;
  alone: number;
  silence: number;
  distress: number;
  transport: number;
  status_ok_multiplier: number;
  total: number;
}

export interface Case {
  outage_id: string;
  resident_id: string;
  status: CaseStatus;
  priority: number;
  band: Band;
  score_breakdown: ScoreBreakdown | null;
  rationale: string | null; // Job 3 one-line "why"
  assessment: Assessment | null;
  escalation_level: EscalationLevel;
  last_outbound_at: Timestamp | null;
  last_inbound_at: Timestamp | null;
  needs_review: boolean;
}

export interface Message {
  resident_id: string;
  ts: Timestamp;
  direction: Direction;
  channel: Channel;
  text: string;
  translation_en: string | null;
  image_key: string | null;
  trace_id: string | null;
}

export interface Stop {
  resident_id: string;
  action: StopAction;
  items: string[];
  reason: string;
  eta: Timestamp | null;
}

export interface Run {
  run_id: string;
  volunteer: string; // volunteer_id
  vehicle: string;
  stops: Stop[]; // in visit order
  geometry: GeoJSONGeometry | null; // LineString from CalculateRoutes
  duration_min: number | null;
}

export interface Plan {
  plan_id: string;
  outage_id: string;
  status: PlanStatus;
  runs: Run[];
  summary: string;
  trace_id: string | null;
  uncovered: string[]; // open cases with priority >= 60 that didn't fit: "next wave"
}

/** One tool call inside a trace. PROPOSED shape. */
export interface ToolCall {
  name: string;
  input: Record<string, unknown>;
  output: unknown;
}

export interface Trace {
  trace_id: string;
  ts: Timestamp;
  job: BedrockJob;
  model_id: string;
  input_masked: string;
  tool_calls: ToolCall[];
  output: unknown;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  guardrail_action: string | null;
}

export interface Event {
  outage_id: string;
  ts: Timestamp; // virtual time
  type: EventType;
  label: string;
  resident_id: string | null;
  from_status: CaseStatus | null;
  to_status: CaseStatus | null;
}

export interface Volunteer {
  volunteer_id: string;
  name: string;
  phone: string;
  vehicle: string;
  start: LatLng;
  capacity: number; // PROPOSED meaning: passenger seats for ride stops
}

export interface Resource {
  resource_id: string;
  name: string;
  type: ResourceType;
  address: string;
  lat: number;
  lng: number;
  offers: string[]; // PROPOSED
}

// --- API requests and responses (§8) ------------------------------------------

export interface CreateOutageRequest {
  name: string;
  polygon: GeoJSONGeometry;
  starts_at: Timestamp;
  est_restore_at: Timestamp;
}

export interface CreateOutageResponse {
  outage_id: string;
  affected: string[];
}

export interface CheckinsResponse {
  sent: number;
}

export interface InboundRequest {
  phone: string;
  text: string;
  image_b64?: string; // resized client-side to under 1 MB (§16)
}

export interface CaseResponse {
  case: Case;
}

export interface ClockAdvanceRequest {
  minutes: number;
}

/** One escalation step taken during /clock/advance. PROPOSED shape. */
export interface Escalation {
  resident_id: string;
  level: EscalationLevel;
  channel: Channel;
  text: string;
}

export interface ClockAdvanceResponse {
  now: Timestamp;
  escalations: Escalation[];
}

export interface CreatePlanRequest {
  outage_id: string;
}

export interface PlanResponse {
  plan: Plan;
}

export interface Counts {
  safe: number;
  needs_help: number;
  critical: number;
  no_reply: number;
}

/** A case as /dashboard returns it. PROPOSED: embeds the resident for map markers. */
export interface DashboardCase extends Case {
  resident: Resident;
  backup_hours_left: number | null; // at virtual now
}

export interface DashboardResponse {
  now: Timestamp;
  outage: Outage | null;
  counts: Counts;
  cases: DashboardCase[];
  events: Event[];
  plan: Plan | null;
  resources: Resource[];
  volunteers: Volunteer[];
}

export interface MessagesResponse {
  messages: Message[];
}

export interface TracesResponse {
  traces: Trace[];
}

export interface RunStopDetail {
  resident_id: string;
  name: string;
  address: string;
  lat: number;
  lng: number;
  status: CaseStatus;
}

export interface RunResponse {
  run: Run;
  volunteer: Volunteer | null;
  stops_detail: RunStopDetail[]; // same order as run.stops
}
