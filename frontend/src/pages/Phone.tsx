/**
 * Resident phone simulator (/phone): phone frame, resident picker, SMS thread,
 * text box, photo attach (resized under 1 MB), and quick replies from
 * data/test_replies.json. Posts to the same /inbound webhook real SMS would use.
 *
 * Data: GET /residents/{id}/messages, POST /inbound.
 * Implements: PLAN.md §9.2, §6 (SMS channel). Owner: P1 (Frontend and UX).
 */
export default function Phone() {
  // TODO(P1, §9.2)
  return <main className="p-4">Resident phone simulator</main>;
}
