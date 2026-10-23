# StillHere progress log

> Where the project stands right now, so nobody has to read the whole git history. The plan ([PLAN.md](PLAN.md)) is the source of truth; this file tracks progress against it.
>
> **Update this file at the end of every phase, in the same commit as the work.**
>
> Rules:
> - Update it at the end of every phase or task, in the same commit or PR as the work. Never in a separate "update progress" PR later.
> - Keep entries short and factual: bullets, not paragraphs. Link to PRs and files instead of repeating their contents.
> - Never delete old log entries. Correct mistakes with a new entry.
> - Any Claude session working on this repo reads `docs/PROGRESS.md` (and `PLAN.md`) before starting, and updates it before finishing.
> - If a decision changes the plan, update `PLAN.md` in the same commit and record it in the Decisions log.

---

## Current status

- **Current phase:** H4–H6 (replies flow into the queue and onto the map), built offline while H0–H1 waits on AWS credentials
- **Last updated:** 2026-10-23 04:46 UTC · Claude session
- **Overall health:** 🟡 code through H4–H6 is done and tested without AWS (80 tests, plus the live UI against the real API with in-memory tables and stand-in Bedrock jobs). Nothing has run on real Bedrock or DynamoDB yet (no credentials)
- **Gates:**
  - H0–H1 "Deployed URL returns a Bedrock reply; 3D path chosen" · ⬜ not met (no AWS credentials). 3D path chosen provisionally (Amazon `Terrain3D`)
  - H1–H4 "Each part works alone" · 🟡 met with stubs and mocks; real-AWS check pending
  - H4–H6 "Replies flow into the queue and onto the map" · 🟡 met offline: reset → zone → 40 check-ins → 4 phone replies → +3 h ends with Minh Critical, Rosa/Harold High, Denise OK, Lupe silent L3. Real-AWS check pending (README smoke test)

### Done vs remaining (snapshot)

| Area | Done (merged to `main`) | Remaining |
|---|---|---|
| **AWS** | SAM template (Lambda, HTTP API, 8 tables, bucket, map key, scoped Bedrock IAM, 1-minute schedule), `amplify.yml`, deploy + smoke-test steps in README | Credentials, Bedrock model access, first `sam deploy`, Amplify app, then run the smoke test and `eval_replies.py` |
| **P2 Backend** | `/health`, `/hello-bedrock` (debug), `/demo/reset`, `/outages`, `/outages/{id}/checkins`, `/inbound` (+ photo to S3), `/clock/advance`, `/dashboard`, `/residents/{id}/messages`, `/traces`; `store.py`, `geo.py`, `triage.py`, `escalation.py`, scheduled check | `/plans`, approve, stop done, `/runs/{id}`, `location.py` (H6–H7); CORS lock-down |
| **P3 AI** | `converse()` + trace rows, Jobs 1–4 with prompts, privacy by construction for every SMS, eval script (Job 2 + triage, privacy check) | Run the eval on real Bedrock (18/20), Job 5 agent + tools (H6–H7), Guardrails + name/address masking, fallback model |
| **P1 Frontend** | Command center on the live API (polling, action bar steps 1–2, busy/error states), timeline, phone simulator on `/inbound`, AI Trace list, flat map; mock behind `VITE_USE_MOCK`; `/3d-test` | Plan tab + Approve, routes layer, volunteer view (`/run/:runId`) (H6–H7); 3D, fly-to, pulsing markers, trace detail, About panel (H8–H12); delete the mock (H7–H8) |
| **P4 Story/data** | 40 residents, zone, resources, volunteers, 20 labeled replies; drafts of `sources.md` and `video_script.md` | Verify every source and fill the emPOWER number + a confirmed harm case; 2 reply photos; architecture diagram (H6–H7); safety video (H8) |

---

## Phase checklist

Phases and gates from [PLAN.md §13](PLAN.md#13-timeline-18-build-hours). H0 is when hacking starts.

| Phase | Gate | Status | Finished |
|---|---|---|---|
| Pre-event setup | §18 checklist done (see Open questions) | ⚠️ superseded: hacking started with items still open | |
| H0–H1 | Deployed URL returns a Bedrock reply; 3D path chosen (Amazon or fallback) | 🔄 in progress: code done, deploy blocked on credentials | |
| H1–H4 | Each part works alone | 🔄 in progress: code done and tested offline; real-AWS check blocked on credentials | |
| H4–H6 | Replies flow into the queue and onto the map | 🔄 in progress: code done and tested offline; real-AWS check blocked on credentials | |
| H6–H7 | Plan renders | ⬜ not started | |
| H7–H8 | Golden path green, or cut (safety video recorded) | ⬜ not started | |
| H8–H12 | SHOULD tier done | ⬜ not started | |
| H12–H14 | Green or harden | ⬜ not started | |
| H14–H15 | Code freeze: 3 clean runs in a row | ⬜ not started | |
| H15–H17 | Final cut | ⬜ not started | |
| H17–H18 | Submitted | ⬜ not started | |

Status key: ⬜ not started · 🔄 in progress · ✅ done · ⚠️ cut or blocked

---

## Scope tracker

From [PLAN.md §11](PLAN.md#11-scope-tiers). Tick items as they are finished.

### MUST: the golden path, green by H8

- [ ] Seed data, plus a Reset demo button (done on the live API; real-AWS check pending)
- [ ] Outage zone → affected residents on a **flat (2D) satellite map**, markers colored by status (done on the live API; satellite imagery needs the key)
- [ ] Job 1: check-ins sent (shown in the phone simulator) (done; real-Bedrock check pending)
- [ ] Job 2: text replies → assessment → Job 3: score and "why" in the queue (done; real-Bedrock check and eval pending)
- [ ] Timeline bar (forward only: play and jump buttons, counters, event markers) plus escalation L1 to L3 (Job 4) (done; real-Bedrock check pending)
- [ ] Job 5: agent plan → routes on the map → Approve → volunteer view
- [ ] AI Trace drawer (list done; step-by-step detail in H8–H12)
- [ ] Deployed: Amplify URL plus the SAM stack (template ready; blocked on credentials)

### SHOULD: H8 to H12

- [ ] 3D terrain and buildings, tilted camera, 2D/3D toggle
- [ ] Click a marker or card → camera flies to the home → Resident panel opens
- [ ] Backup-hours countdown per resident, pulsing no-reply markers, Key events list
- [ ] Photo replies (multimodal)
- [ ] Spanish and Vietnamese end to end
- [ ] Guardrails (denied topic plus PII masking in traces)
- [ ] "Needs human review" path for low confidence
- [ ] Design polish, plus loading, empty and error states
- [ ] About panel with sourced stats

### STRETCH: only if the golden path is green at H12

- [ ] Drag the timeline back to replay earlier states (rebuilt from `events`)
- [ ] Small charts under the timeline (cases by band over time, replies over time)
- [ ] Animated route drawing and a moving volunteer dot after approval
- [ ] Knowledge Base grounded tips
- [ ] One-click SITREP for the county Emergency Operations Center (EOC)
- [ ] Natural-language questions for the coordinator
- [ ] Amazon Connect voice line

### Requirements R1–R18

From [PLAN.md §1.1](PLAN.md#11-requirements-compliance-checklist). Tick when the build meets it; the final tick against the video happens in [submission.md](submission.md).

- [ ] R1 Gate: the app uses Amazon Bedrock doing real work
- [ ] R2 A specific persona who depends on a critical service
- [ ] R3 A real continuity problem during a crisis
- [ ] R4 The "so what" is clear and drove the build
- [ ] R5 An AI application, not just an app written with AI
- [ ] R6 Built on AWS, in the provided AWS account
- [ ] R7 A working application that solves the need end to end
- [ ] R8 Bedrock is integral, not bolted on, and shown working
- [ ] R9 The team understands what it built
- [ ] R10 Polish: looks like something a real person would trust
- [ ] R11 Above and beyond: ambition or real-world impact
- [ ] R12 Video is 5 minutes or less
- [ ] R13 Video shows the architecture
- [ ] R14 Video describes the application, persona and need
- [ ] R15 Video shows Bedrock in use
- [ ] R16 Submitted by 10:30 AM Saturday
- [ ] R17 A way for judges to reach the team through the event channel
- [ ] R18 Nothing depends on explaining later

---

## Phase log

Newest entry on top. Template:

```
### <date> · <phase> · <short title>
**By:** <P1–P4 or Claude session> · **Branch/PR:** <link>
**Done:**
- ...
**Not done / cut:**
- ...
**Decisions made:** (anything that differs from PLAN.md, and why)
- ...
**Blockers / risks:**
- ...
**Next steps:** (who does what next)
- ...
```

### 2026-10-23 · H4–H6 · "Others reply" button
**By:** Claude session · **Branch/PR:** `feat/others-reply`
**Done:**
- [`Phone.tsx`](../frontend/src/pages/Phone.tsx): "Others reply" button sends the 32 non-hero replies (tr-05 to tr-20 plus `data/crowd_replies.json`) through `/inbound`, 6 at a time, with progress ("Amazon Bedrock is reading replies… n/32"). Disabled in mock mode (the mock already includes them). Text only: the tr-18 photo file doesn't exist yet.
- [`test_flow.py`](../backend/tests/test_flow.py): new golden-path test with the crowd: after +3 h exactly res-005, res-025, res-036, res-039 are silent, 12 escalation drafts (not ~108), 36 replies. The 4-hero test is unchanged.
- [`video_script.md`](video_script.md): "most of the neighborhood answers too" beat and the button in the demo take.
- Checks: `pytest` 83 passed, `npm run build` ok. In Chromium on the live API (in-memory tables, stand-in jobs): check-ins → Others reply (32/32) → 4 hero replies → +3 h gave 21 Safe, 11 Needs help, 4 Critical, 4 No reply, Lupe first in the queue.
**Not done / cut:**
- Not run on real Bedrock: 32 replies run Jobs 2 and 3 (~64 calls); time it at H0 and lower the parallelism if Bedrock throttles.
**Next steps:**
- H6–H7: Job 5 plan, routes, Approve, volunteer view.

### 2026-10-23 · H4–H6 · Real zone, stable bands, crowd replies
**By:** Claude session · **Branch/PR:** `data/demo-seed`
**Done:**
- [`outage_zone.geojson`](../data/outage_zone.geojson): real hand-drawn polygon (was the placeholder), from the valley edge east into the foothills. All 40 residents are ≥ 238 m inside; resources and volunteer starts ≥ 303 m outside.
- Band stability: the 6 test replies whose score sat exactly on a cut-off (tr-01, 05, 11, 16, 17 at 30/60/80; tr-18 at 30) now keep their band when Job 2 rates distress one notch higher or lower. Done through resident profiles only (5 now live alone; Patricia Johnson backup 12 h and not alone); reply texts and labels unchanged.
- [`crowd_replies.json`](../data/crowd_replies.json): 16 simple OK replies (EN/ES/VI) for the background residents with no test reply. Silent residents are now exactly res-005 (Lupe), res-025, res-036, res-039, matching the mock.
- `api/seed.ts` exports `crowdReplies`; `api/mock.ts` derives its silent set and crowd texts from the data instead of hard-coding them.
- `test_seed_data.py`: volunteer starts are outside the zone; crowd replies are valid and leave only the 4 silent residents; the golden-path stops (10 High/Critical replies + 4 door-knocks = 14) fit 3 volunteers × 6.
- PLAN.md §3, §10, §17 and the README folder map mention the crowd step.
**Not done / cut:**
- No "Others reply" button yet. `/inbound` now exists on main, so the button (phone simulator) can post tr-05 to tr-20 and every crowd reply through it before the clock moves. That brings the golden path from 36 silent residents to 4.
- The 2 photos and `docs/sources.md` are still open.
**Decisions made:**
- See the Decisions log entries for crowd replies and band stability.
**Next steps:**
- P1: the "Others reply" button. P2: extend `test_flow.py` to send the crowd and expect 4 silent. P4: photos, sources.

### 2026-10-23 · H1–H4 · Parallel data set dropped; silence-load check
**By:** Claude session · **Branch/PR:** `data/demo-seed`
**Done:**
- A second, parallel fill of `data/` (44 residents, a new zone polygon) was merged with main and dropped in favour of main's data, which `test_seed_data.py` and `api/mock.ts` already depend on. The new zone polygon was dropped too: it left res-014 outside the zone and put crc-1, crc-2, vol-2 and vol-3 inside it.
- Ticked the §18 rules question in PLAN.md (matches the Decisions log).
- Checked the escalation load on main's data: see the Silence flood open question.
**Not done / cut:**
- No data changes.
**Blockers / risks:**
- Silence flood (Open questions). Insulin "hours left" is medically soft (unopened insulin keeps at room temperature for weeks; heat is the real risk); P4 to check against the FDA source when filling `docs/sources.md`.
**Next steps:**
- All: pick a silence-flood option before P2 builds escalation and P3 tunes the planner.

### 2026-10-23 · H4–H6 · Replies flow into the queue and onto the map (offline)
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah) · Plan: supply-hours fallback and Rosa's margin decided by the team before starting
**Done:**
- P2: [`triage.py`](../backend/app/triage.py) §5 score with the supply-hours fallback; [`escalation.py`](../backend/app/escalation.py) virtual clock, L1–L3 ladder (parallel, steps stamped when they fell due), rescoring with band-change events; routes `/outages/{id}/checkins`, `/inbound` (photo to S3), `/clock/advance`, `/dashboard` (`outage_id` optional), `/residents/{id}/messages`, `/traces`; the 1-minute schedule is back on and routed by `main.handler`.
- P3: Job 3 `explain_priority()` and Job 4 `draft_escalation()` with prompts; L1/L2 SMS never see device words (tested for all 40 residents); [`eval_replies.py`](../backend/tests/eval_replies.py) runs Job 2 + triage on the 20 replies and the privacy check.
- P1: [`api/client.ts`](../frontend/src/api/client.ts) on the live API (3 s polling, actions one at a time with named busy text), action bar steps 1–2, phone simulator posts to `/inbound`, AI Trace list; mock kept behind `VITE_USE_MOCK=true`.
- P4: Rosa lives alone (High at 65–70); drafts of [`sources.md`](sources.md) (from web search, to verify) and [`video_script.md`](video_script.md).
- Checks: `pytest` 80 passed (incl. [`test_flow.py`](../backend/tests/test_flow.py): reset → outage → check-ins → 4 hero replies → +3 h → dashboard), `compileall`, `cfn-lint`, `npm run build`. In Chromium, the live UI against the real API (in-memory tables, stand-in jobs) ran the whole path: 1 safe, 2 needs help, 1 critical, 36 no reply; mock mode unchanged.
**Not done / cut:**
- Nothing ran on real Bedrock/DynamoDB/S3 (no credentials); eval not run.
- `sources.md`: emPOWER county number and a confirmed harm case still missing; the 2 photos still missing.
**Decisions made:**
- See the Decisions log entries dated 2026-10-23 (H4–H6).
**Blockers / risks:**
- Credentials → model access → deploy, as before.
- **36 silent residents:** in the golden path only the 4 heroes reply, so the other 36 also climb to L3. That is ~108 Job 4 calls and ~36 Job 3 calls on the first +3 h, and 36 door-knocks on the map. See Open questions.
- Concurrent escalation checks (the schedule and `/clock/advance` at the same moment) could draft a level twice; rare, harmless for the demo.
**Next steps:**
- Team: decide the "36 silent residents" question; P4 verify sources, make the 2 photos.
- When credentials arrive: README smoke test, then `python tests/eval_replies.py` (fix prompts until 18/20).
- H6–H7: P2 `location.py` + `/plans` + approve + stop done + `/runs/{id}`; P3 Job 5 agent + tools (+ greedy fallback); P1 Plan tab, routes layer, volunteer view; P4 architecture diagram.

### 2026-10-23 · H1–H4 · Each part works alone (offline)
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah), merged via [neels22/Spartan-hack#2](https://github.com/neels22/Spartan-hack/pull/2)
**Done:**
- P4: [`residents.json`](../data/residents.json) 40 residents (15 EN, 13 ES, 12 VI; all device types; all inside the zone), [`resources.json`](../data/resources.json) 2 CRCs + pharmacy just outside the zone, [`volunteers.json`](../data/volunteers.json) 3 volunteers, [`test_replies.json`](../data/test_replies.json) 20 labeled replies with expected bands from §5. Checked by [`test_seed_data.py`](../backend/tests/test_seed_data.py).
- P2: [`store.py`](../backend/app/store.py) for every §7 table (Decimal in/out, per-thread boto3), reseed from `data/`; [`geo.py`](../backend/app/geo.py) point-in-polygon + nearest resource; `POST /demo/reset`, `POST /outages` (affected residents, cases, `outage_started` event); shared 503/502 error handlers.
- P3: trace row per Bedrock call (masked phones); Job 1 `write_checkin()` / `write_checkins()` (10 threads); Job 2 `assess_reply()` with photo and the forced `record_assessment` tool (built from `schemas.Assessment`); prompts in `checkin.md` and `assess.md`; EN/ES/VI privacy word check in `eval_replies.py`.
- P1: four-area command center, timeline (play 1×/4×/16×, jumps, markers, Key events, counters), phone simulator (quick replies, photo resize under 1 MB), all on [`api/mock.ts`](../frontend/src/api/mock.ts) through `useDashboard()` in [`api/client.ts`](../frontend/src/api/client.ts).
- Checks: `pytest` 31 passed (5 skipped stubs for later phases), `compileall` ok, `sam build` ok with `data/` and prompts in the package, `npm run build` ok, both pages exercised in Chromium.
**Not done / cut:**
- Nothing ran against real AWS (no credentials): reset/outages on DynamoDB, Jobs 1–2 on Bedrock.
- The 2 photo files for tr-02 and tr-18 (`data/photos/`) don't exist yet.
- Out of scope for H1–H4 and left as TODOs: `/checkins` and `/inbound` routes, triage, escalation, `/dashboard`, traces list, eval run.
**Decisions made:**
- See the Decisions log entries dated 2026-10-23 (H1–H4).
**Blockers / risks:**
- Same as H0–H1: credentials → model access → deploy. Then run the H1–H4 smoke test below.
- Rosa's expected band (High) is exactly 60; it needs the model to rate her distress at 1 or more.
**Next steps:**
- When credentials arrive: deploy, `curl -X POST <ApiUrl>/demo/reset`, `POST /outages` with the zone (expect 40 affected), then run Jobs 1–2 once by hand (README) and look at the `traces` table.
- H4–H6: P2 `/inbound`, `/clock/advance`, triage (with the supply fallback below), escalation, `/dashboard`; P3 Jobs 3–4 + eval run; P1 swap `useDashboard()` to the API; P4 the 2 photos, sources, script draft.

### 2026-10-23 · H0–H1 · Walking skeleton (code done, deploy blocked)
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah), merged via [neels22/Spartan-hack#4](https://github.com/neels22/Spartan-hack/pull/4)
**Done:**
- P3: `converse()` in [`bedrock.py`](../backend/app/bedrock.py): Converse API, model IDs from env at call time, returns text, `model_id`, `latency_ms`, tokens, `stop_reason` and the raw response. TODOs where tracing (§4), Guardrails (§4 Job 6) and the fallback model (§16) plug in.
- P2: `GET /health` and skeleton `GET /hello-bedrock` in [`main.py`](../backend/app/main.py); clear 503 when model IDs are unset, 502 with the AWS error code otherwise. CORS for local runs.
- P2: [`template.yaml`](../infra/template.yaml): Bedrock `InvokeModel` scoped to the configured IDs, browser map API key (`AWS::Location::APIKey`, Maps only), 1-minute schedule commented out. [`amplify.yml`](../amplify.yml) for the monorepo build.
- P1: [`IncidentMap`](../frontend/src/components/map/IncidentMap.tsx) shows the Amazon Location Hybrid style over East San Jose; [`CommandCenter`](../frontend/src/pages/CommandCenter.tsx) shows the `/hello-bedrock` reply with an "Amazon Bedrock" badge. Throwaway 3D test at `/3d-test` ([`Map3DTest.tsx`](../frontend/src/pages/Map3DTest.tsx)).
- P4: the 5 hero residents in [`residents.json`](../data/residents.json), all inside the zone polygon and valid against `schemas.Resident`. README "Run it locally" and "Deploy" have the real commands.
- Checks: `pytest` 4 passed (8 skipped stubs), `compileall` ok, `cfn-lint` ok, `sam build` ok (43 MB, no dev deps), Mangum handler answers HTTP API v2 events, `npm run build` ok. Locally `/health` works and `/hello-bedrock` reaches Bedrock and fails only on credentials (`UnrecognizedClientException`).
**Not done / cut:**
- Not deployed and no real Bedrock reply yet: no AWS credentials, no model access.
- Map with satellite imagery not seen yet: no Location API key (the SAM stack creates one).
- Mapbox fallback not built (needs a new dependency); only needed if both Amazon options fail.
**Decisions made:**
- See the Decisions log entries dated 2026-10-23 (H0–H1).
**Blockers / risks:**
- Gate needs: AWS credentials → Bedrock model access → `sam deploy` → map key into `.env`/Amplify. Commands in [README.md](../README.md#deploy).
- Building heights: the extrusion uses the `height` tile property with a 6 m default; check on `/3d-test` once the key exists.
**Next steps:**
- Team: run the README Deploy steps, then curl `<ApiUrl>/hello-bedrock` and open `/` and `/3d-test` locally; mark this phase ✅ here.
- H1–H4 (after the gate): P2 tables + `/demo/reset` (decide how `data/` reaches the Lambda), `/outages`; P3 Jobs 1–2 + trace rows in `converse()`; P1 four-area layout on mock JSON; P4 the other ~35 residents, resources, volunteers, 20 test replies.

### 2026-10-23 · Pre-event setup · Repo folder structure
**By:** Claude session · **Branch/PR:** [`claude/peaceful-carson-mu16gc`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/peaceful-carson-mu16gc)
**Done:**
- Folder structure and stubs from PLAN.md §10; every file has a header (what, plan section, owner). See the folder map in [README.md](../README.md).
- Shared contracts: [`backend/app/schemas.py`](../backend/app/schemas.py) and [`frontend/src/api/types.ts`](../frontend/src/api/types.ts) (§7 records, §8 API shapes).
- Prompt specs for Jobs 1–5 in [`backend/app/prompts/`](../backend/app/prompts/).
- One example record per data file in [`data/`](../data/) (Rosa Delgado from §3; 555 numbers; placeholder East San Jose polygon).
- Minimal configs: `requirements.txt`, `pytest.ini`, Vite + React + TS + Tailwind 4, SAM skeleton ([`infra/template.yaml`](../infra/template.yaml)), [`.env.example`](../.env.example).
- Updated the PLAN.md §10 tree to show the added files (`.env.example`, `PROGRESS.md`, `schemas.py`, `pytest.ini`, `api/types.ts`, `map/layers/`).
- Checks: `compileall` ok, `pytest` runs (8 skipped), all JSON/GeoJSON parse, `npm run build` ok, `cfn-lint` ok on the SAM template.
**Not done / cut:**
- No feature logic: §18 rules question is open, so every function is a signature with a TODO.
- `docs/architecture.png` not added (P4 makes it later; no binaries now).
**Decisions made:**
- See the Decisions log entries dated 2026-10-23.
**Blockers / risks:**
- §18 rules question decides whether anything beyond docs, data and design may be written before H0.
- Shapes marked PROPOSED in the contracts need a 10-minute P1/P2/P3 review at H0.
- Amplify needs a SPA rewrite rule (`/<*>` → `/index.html`) so `/phone` and `/run/:runId` deep links work.
**Next steps:**
- All: answer the Open questions below, confirm PROPOSED shapes.
- P4: fill `data/` (40 residents, 20 test replies, real zone polygon), `docs/sources.md`.
- P2 at H0: deploy the SAM skeleton; P3 at H0: request Bedrock model access, hello `converse()`.
- P1 at H0: test 3D terrain with the Amazon Location style on a throwaway page.

---

## Decisions log

Decisions that change or clarify the plan. If one changes the plan, `PLAN.md` is updated too.

| Date | Decision | Reason | Who |
|---|---|---|---|
| 2026-10-23 | Added `backend/app/schemas.py` and `frontend/src/api/types.ts` as the only shared-contract files | One place per side for the §7/§8 shapes, so P1/P2/P3 don't drift | Claude session (requested by team) |
| 2026-10-23 | Bedrock Jobs 1–4 are functions in `bedrock.py`; Job 5 in `agent.py`; all tool specs (incl. Job 2 `record_assessment`) in `tools.py` | §10 has no separate jobs file; keeps all P3 code in P3's three files | Claude session |
| 2026-10-23 | Prompt files hold a spec (purpose, inputs, output, rules) above a `## Prompt` heading; `load_prompt()` sends only the text under that heading | Spec and prompt stay side by side without sending the spec to the model | Claude session |
| 2026-10-23 | Each `data/*.json` is an object with a `_meta` block (about, plan, owner) and one list key (`residents`, `resources`, ...); the GeoJSON keeps this info in feature `properties` | JSON has no comments; every file still says what it is and who owns it. Loaders skip `_meta` | Claude session |
| 2026-10-23 | Map layers live in `frontend/src/components/map/layers/` (one file per layer) | §10 lists the layers under `map/`; one file each avoids conflicts | Claude session |
| 2026-10-23 | One Lambda for HTTP and the 1-minute schedule; `main.handler` will route scheduled events to the escalation check (TODO in `main.py`) | Matches §6 diagram (EventBridge → same Lambda) | Claude session |
| 2026-10-23 | Added `backend/app/__init__.py` and `backend/pytest.ini` (beyond §10) | Makes `app` a regular package for the Lambda handler path, and lets `pytest` import it from `backend/` | Claude session |
| 2026-10-23 | `samconfig.toml` is gitignored | `sam deploy --guided` saves parameter values there, incl. the optional Location key | Claude session |
| 2026-10-23 | Vite reads env from the repo-root `.env` (`envDir: '..'`) | One `.env.example` for the whole team | Claude session |
| 2026-10-23 | `/dashboard` cases embed the resident (`DashboardCase.resident`) | §8 has no residents list, but the map needs names and locations. PROPOSED; confirm at H0 | Claude session |
| 2026-10-23 | Hacking has started; code is allowed (closes the §18 rules question) | Answered by the team at H0 | Team |
| 2026-10-23 | **3D path: Amazon Location `terrain=Terrain3D` (§6 option 1), provisional.** Fallback 1 (open Terrain Tiles, Terrarium) works today | In us-west-2 the Satellite, Hybrid and Standard style descriptors accept `terrain=Terrain3D` and add a `raster-dem` source (`terrainSource`) plus a `terrain` block. No style ships 3D buildings, so we extrude the `buildings` tile layer ourselves. Tiles need the key, so the visual check waits for it. Fallback 1 is proven in Chromium: East San Jose foothills render in 3D (sampled ~590 m vs ~25 m downtown) | Claude session |
| 2026-10-23 | Model IDs in use: **none yet**. `BEDROCK_FAST_MODEL_ID` / `BEDROCK_STRONG_MODEL_ID` stay empty until access is granted; set them in `.env` and as SAM parameters | Bedrock access not granted at H0 | Team |
| 2026-10-23 | `converse()` returns a `ConverseResult` (text, model_id, latency_ms, tokens, stop_reason, raw) instead of the raw response | Callers get the numbers the trace row needs; tool-use callers still have `raw` | Claude session |
| 2026-10-23 | `backend/requirements-dev.txt` (pytest, httpx, uvicorn); local server is `uvicorn app.main:app` (closes the dev-deps question) | Keeps test tools out of the Lambda zip; `sam local` needs Docker | Claude session |
| 2026-10-23 | Bedrock IAM: `InvokeModel` on the configured profile and model ARNs, plus foundation models only when called through those profiles (`bedrock:InferenceProfileArn`) | Least privilege without hard-coding IDs | Claude session |
| 2026-10-23 | The SAM stack creates the browser map key (`<stack>-maps`, Maps only, no expiry) | No key at H0; one deploy gives us one. The key is public in the bundle; referer restriction is a TODO | Claude session |
| 2026-10-23 | 1-minute EventBridge schedule commented out until `main.handler` routes scheduled events (H4–H6) | It would fail every minute until then | Claude session |
| 2026-10-23 | `amplify.yml` at the repo root (monorepo, `appRoot: frontend`, Node 22) | Amplify needs it to build a subfolder app; Vite 8 needs Node 20.19+ | Claude session |
| 2026-10-23 | `IncidentMap` uses the Hybrid style (satellite + street labels) | Plan allows satellite or hybrid; labels help the coordinator | Claude session |
| 2026-10-23 | `components/map/maplibre.ts` sets the MapLibre worker URL; `amazonStyle.ts` builds the style URLs | MapLibre v6 finds its worker at runtime and Vite doesn't copy it (map failed with "Worker failed to load") | Claude session |
| 2026-10-23 | `/hello-bedrock` and its response type stay out of the shared contracts | Debug route for the gate only; deleted when §8 routes land | Claude session |
| 2026-10-23 | Seed data reaches the Lambda through a symlink `backend/data -> ../data` (closes the seed-data question) | `sam build` copies the files; no extra deploy step. Deploy from macOS/Linux/WSL (Windows git may check out the link as a text file); locally `store.py` also falls back to the repo-root `data/` | Claude session |
| 2026-10-23 | DynamoDB tables are named `<stack>-<table>` (e.g. `stillhere-cases`) | Matches `.env.example`, so local runs hit the deployed tables with stack name `stillhere` | Claude session |
| 2026-10-23 | All 40 demo residents are inside the zone; Harold lives alone | §3 says ~40 residents in the zone; living alone keeps Harold's reply in High with modest distress (§3 doesn't say) | Claude session |
| 2026-10-23 | Test-reply bands assume **`time_pressure` uses `supply_hours_left`, else `baseline_backup_hours`** (PROPOSED for triage.py) | Without the fallback, Rosa and Harold score Watch (below the agent's 60 cut-off) and Lupe never reaches Critical, which breaks the §3 story | Claude session |
| 2026-10-23 | Job 1 sends the model only first name, language, "medicine"/"equipment" and local times, never the devices | Privacy by construction (§4 Job 1 rule); a test checks every resident's request for device words | Claude session |
| 2026-10-23 | Jobs return `JobResult(output, trace_id)` | Callers need the trace id for `Message.trace_id` / `Plan.trace_id` | Claude session |
| 2026-10-23 | Trace masking covers phone numbers only until Guardrails (§4 Job 6, SHOULD tier) | Names and addresses need ApplyGuardrail; demo data is fictional meanwhile | Claude session |
| 2026-10-23 | Frontend API client added: `api/client.ts` (fetch helpers, `useDashboard()`), `api/seed.ts`, `api/mock.ts` (closes the API-client question) | One hook to switch from mock to `/dashboard` in H4–H6 without touching the screens | Claude session |
| 2026-10-23 | `BedrockBadge.tsx` and `status.ts` live in `components/`; top bar and action bar stay in `CommandCenter.tsx` (closes the shared-UI question) | The badge and colors are used by several panels; the bars by one page | Claude session |
| 2026-10-23 | Vite may read `../data` (`server.fs.allow`) and the app imports the seed JSON | §9.2 says quick replies come from `data/test_replies.json`; one source of truth | Claude session |
| 2026-10-23 | **Triage uses `supply_hours_left`, else `baseline_backup_hours`**, both counted down to virtual now (closes the supply-fallback question) | Team decision before H4–H6; keeps the §3 story (Rosa, Harold High; Lupe Critical) | Team |
| 2026-10-23 | Rosa lives alone (closes the "Rosa on the line" question) | Team asked for margin; lowering her backup hours can't change her score (12 h is already under the 14 h outage), living alone does: 65 at distress 0, 70 at 1 | Team + Claude session |
| 2026-10-23 | A reply with status `unclear` sets the case to `needs_help` with review, not back to awaiting | Someone answered, so a person should look; escalating them as silent would be wrong | Claude session |
| 2026-10-23 | Escalation steps are stamped at the moment they fell due (check-in + timer), and never reset `last_outbound_at` | A +3 h jump still lays the timeline out correctly; silence and the ladder both count from the check-in | Claude session |
| 2026-10-23 | Job 3 runs on band changes, on every reply, and once when a case first escalates; not at check-in | Bounds Bedrock calls (40 saved at check-in) while every escalated case still gets a "why" | Claude session |
| 2026-10-23 | `explain_priority()` also takes the resident | The breakdown only has points; the "why" needs the device and living alone (dashboard only, so naming the device is fine) | Claude session |
| 2026-10-23 | `GET /dashboard` takes `outage_id` optionally, defaulting to the active outage | The frontend doesn't need to remember the outage id; backward compatible with §8 | Claude session |
| 2026-10-23 | Events table sort key is `sk = "<ts>#<write order>"` | Many events share a virtual timestamp; `ts` alone overwrote rows | Claude session |
| 2026-10-23 | The 1-minute schedule sends `{"stillhere": "escalation_check"}`; `main.handler` routes it | Simple, explicit routing; the schedule is back on | Claude session |
| 2026-10-23 | `VITE_USE_MOCK=true` keeps the screens on the mock until the AWS gate; delete the mock in H7–H8 | The team can keep building screens offline | Claude session |
| 2026-10-23 | Display categories: ok/resolved = Safe; awaiting_reply/escalated/silent = No reply; needs_help/dispatched = Critical if band Critical, else Needs help | One rule (`categoryOf`) for markers, cards and counters; `/dashboard` counts should use the same rule | Claude session |
| 2026-10-23 | **Silence flood fixed with crowd replies** (option a): after the 4 hero replies, the other 16 test replies and 16 simple OK replies (`data/crowd_replies.json`) arrive; only 4 residents stay silent | Without it, 36 residents go silent at +3 h, swamping the plan (18 stops) and hiding Lupe. Keeps 40 households on the map. Closes the Silence flood question | Team (chosen), Claude session |
| 2026-10-23 | Test-reply bands must hold with distress ±1 (no score on a 30/60/80 cut-off) | Job 2 distress is a judgment call; a one-notch miss shouldn't flip a band in the eval or on camera. Rosa now lives alone (70, was 60). Closes the Rosa question | Claude session |

---

## Open questions

Waiting on the team or organizers. When answered, remove it here and record the answer in the Decisions log.

From [PLAN.md §18](PLAN.md#18-pre-event-checklist-and-open-questions):

- [ ] **Event schedule:** hacking has started; record the exact H0 clock time so H0 to H18 maps to the clock.
- [ ] **AWS account:** credentials not here yet. Region assumed `us-west-2` (in `.env.example` and the README); confirm. Bedrock model access for one fast and one strong Claude model, and their inference profile IDs.
- [ ] **Amazon Location:** style and 3D terrain are confirmed at the style level in us-west-2 (see Decisions). Still open: a visual check on `/3d-test` with the key, and `OptimizeWaypoints` (H6–H7). Mapbox token only if both Amazon options fail.
- [ ] **Persona sources** for `docs/sources.md`: HHS emPOWER (Santa Clara County), PG&E PSPS history, FDA insulin storage guidance, one documented outage-related harm.
- [ ] **Assets:** wireframes of the four-area command center, the phone simulator and the volunteer view; a draft of the architecture diagram.
- [ ] **Accounts:** an Amplify app connected to this repo; a screen recorder ready (for example OBS).
- [ ] **Submission:** where the video is uploaded, the accepted format, and the event channel for judge questions. Record answers in `docs/submission.md`.

From the repo setup (2026-10-23):

- [ ] **PROPOSED shapes** in `schemas.py` / `types.ts`: `ScoreBreakdown` field names, `Escalation`, `ToolCall`, `DashboardCase.resident`, `Outage.status`, `Stop.action` values, `Volunteer.capacity` meaning, `Resource.offers`. P1, P2, P3 confirm at H0.
- [ ] **Test reply photos:** `test_replies.json` points tr-02 to `data/photos/minh_gauge.jpg` and tr-18 to `data/photos/wheelchair_battery.jpg`. Someone takes or makes the 2 photos (under 1 MB each); OK to commit them as binaries? (P4, P3)
- [ ] **Lockfile:** `frontend/package-lock.json` is committed so all four laptops and Amplify install the same versions. Keep it? (P1, P2)

From H0–H1 (2026-10-23):

- [ ] **Amplify branch for the gate:** Amplify deploys `main` (§6). Connect this branch too for the gate check, or merge first? (P2)
- [ ] **Lock down public surfaces:** CORS (`*` in FastAPI and the HTTP API) and the map key's allowed referers should name the Amplify URL and localhost once the Amplify URL exists. (P2)
- [ ] **3D buildings height:** the extrusion reads the `height` property of the `buildings` tile layer, with 6 m if it's missing. Check on `/3d-test` with the key. If all buildings look the same height, drop buildings and keep terrain. (P1)
- [ ] **Sources to verify:** open every link in `docs/sources.md`, read the Santa Clara County emPOWER number off the live map, and find a confirmed outage-related harm (the 2019 El Dorado County case was ruled not outage-caused). (P4)
- [ ] **`/demo/reset` response:** returns `null` (§8 says n/a). Fine for the Reset button? (P1, P2)
- [ ] **Worker file type on Amplify:** the MapLibre worker ships as `assets/maplibre-gl-worker-*.mjs`. If the deployed map is blank with a MIME-type error, add a `Content-Type: text/javascript` custom header for `*.mjs`. (P1, P2)
