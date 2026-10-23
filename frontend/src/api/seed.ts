/**
 * The seed data in /data, typed with the shared contract. Used by the phone
 * simulator (resident picker, quick replies) and by the mock dashboard.
 *
 * Implements: PLAN.md §9.2 (quick replies from data/test_replies.json). Owner: P1 (Frontend and UX).
 */
import residentsJson from '../../../data/residents.json';
import resourcesJson from '../../../data/resources.json';
import testRepliesJson from '../../../data/test_replies.json';
import volunteersJson from '../../../data/volunteers.json';
import zoneJson from '../../../data/outage_zone.geojson?raw';
import type { AssessmentStatus, Band, GeoJSONGeometry, Language, Need, Resident, Resource, Volunteer } from './types';

/** One labeled reply from data/test_replies.json. */
export interface TestReply {
  reply_id: string;
  resident_id: string;
  language: Language;
  text: string;
  image: string | null; // path under data/
  expected: {
    status: AssessmentStatus;
    needs: Need[];
    supply_hours_left: number | null;
    needs_transport: boolean;
    distress_level: number;
    band: Band;
  };
  note: string;
}

export const residents = residentsJson.residents as Resident[];
export const resources = resourcesJson.resources as Resource[];
export const volunteers = volunteersJson.volunteers as Volunteer[];
export const testReplies = testRepliesJson.replies as TestReply[];
export const zonePolygon = JSON.parse(zoneJson).features[0].geometry as GeoJSONGeometry;
