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

- **Current phase:** H0–H1 (walking skeleton)
- **Last updated:** 2026-10-23 03:25 UTC · Claude session
- **Overall health:** 🟡 code for H0–H1 is done and checked locally; waiting on AWS credentials, Bedrock model access and a deploy
- **Next gate:** H0–H1, "Deployed URL returns a Bedrock reply; 3D path chosen (Amazon or fallback)" · ⬜ not met: nothing deployed yet (no AWS credentials). 3D path chosen provisionally (Amazon `Terrain3D`), visual check needs the map key

---

## Phase checklist

Phases and gates from [PLAN.md §13](PLAN.md#13-timeline-18-build-hours). H0 is when hacking starts.

| Phase | Gate | Status | Finished |
|---|---|---|---|
| Pre-event setup | §18 checklist done (see Open questions) | ⚠️ superseded: hacking started with items still open | |
| H0–H1 | Deployed URL returns a Bedrock reply; 3D path chosen (Amazon or fallback) | 🔄 in progress: code done, deploy blocked on credentials | |
| H1–H4 | Each part works alone | ⬜ not started | |
| H4–H6 | Replies flow into the queue and onto the map | ⬜ not started | |
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

- [ ] Seed data, plus a Reset demo button
- [ ] Outage zone → affected residents on a **flat (2D) satellite map**, markers colored by status
- [ ] Job 1: check-ins sent (shown in the phone simulator)
- [ ] Job 2: text replies → assessment → Job 3: score and "why" in the queue
- [ ] Timeline bar (forward only: play and jump buttons, counters, event markers) plus escalation L1 to L3 (Job 4)
- [ ] Job 5: agent plan → routes on the map → Approve → volunteer view
- [ ] AI Trace drawer
- [ ] Deployed: Amplify URL plus the SAM stack

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

### 2026-10-23 · H0–H1 · Walking skeleton (code done, deploy blocked)
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah)
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
- [ ] **Seed data in Lambda:** `/demo/reset` reseeds from `data/`, but the Lambda package is `backend/` only. Copy `data/` into the build, upload it to S3, or move `CodeUri` to the repo root? (P2)
- [ ] **Test reply photos:** where do the 2 eval photos live (suggest `data/photos/`) and are binary files OK in the repo? (P4, P3)
- [ ] **Frontend API client:** add `frontend/src/api/client.ts` (fetch wrapper + TanStack Query hooks) next to `types.ts`? Not added because it wasn't in the agreed additions. (P1)
- [ ] **Small shared UI pieces** from §9 with no file in §10: top bar, action bar, About panel, "Amazon Bedrock" badge. They start inside `CommandCenter.tsx`; split into `components/` when needed? (P1)
- [ ] **Lockfile:** `frontend/package-lock.json` is committed so all four laptops and Amplify install the same versions. Keep it? (P1, P2)

From H0–H1 (2026-10-23):

- [ ] **Amplify branch for the gate:** Amplify deploys `main` (§6). Connect this branch too for the gate check, or merge first? (P2)
- [ ] **Lock down public surfaces:** CORS (`*` in FastAPI and the HTTP API) and the map key's allowed referers should name the Amplify URL and localhost once the Amplify URL exists. (P2)
- [ ] **3D buildings height:** the extrusion reads the `height` property of the `buildings` tile layer, with 6 m if it's missing. Check on `/3d-test` with the key. If all buildings look the same height, drop buildings and keep terrain. (P1)
- [ ] **Worker file type on Amplify:** the MapLibre worker ships as `assets/maplibre-gl-worker-*.mjs`. If the deployed map is blank with a MIME-type error, add a `Content-Type: text/javascript` custom header for `*.mjs`. (P1, P2)
