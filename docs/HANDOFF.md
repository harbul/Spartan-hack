# StillHere handoff: start here

> What is done, everything that remains, and where each role starts. Written 2026-10-23 at `main` @ `75da2f9`.
> Detailed status lives in [PROGRESS.md](PROGRESS.md); the plan is [PLAN.md](PLAN.md). Update PROGRESS.md (not this file) as work lands.

## 1. Where we are

**The whole MUST golden path and most of the SHOULD tier are built and tested offline. Nothing has run on AWS yet, and AWS credentials are the only blocker for the next gate.**

Offline means 117 backend tests pass, `npm run build` passes, and the live UI was driven in a browser against the real API, with in-memory tables and stand-ins for Bedrock and Amazon Location.

| Gate (PLAN.md §13) | Status |
|---|---|
| H0–H1 Deployed URL returns a Bedrock reply; 3D path chosen | Code done. **Needs AWS** (deploy) |
| H1–H4 Each part works alone | Met offline. Needs AWS check |
| H4–H6 Replies flow into the queue and onto the map | Met offline. Needs AWS check |
| H6–H7 Plan renders | Met offline. Needs AWS check (agent on real Bedrock, real routes) |
| **H7–H8 Golden path green on the deployed URL + safety video** | **Next. Blocked on AWS** |
| H8–H12 SHOULD tier | Mostly built: 3D map, fly-to, pulsing markers, About panel, Guardrails, review flag. Remaining in §5 below |

The golden path in the app:
1. `/`: Reset demo, then **1. Load outage zone**, then **2. Send check-ins**.
2. `/phone`: send the 4 hero quick replies, then **Others reply**.
3. `/`: **+3 h** (Lupe and 3 others escalate to L3), then **3. Plan dispatch**, then **4. Approve plan**.
4. Open a route sheet from the Plan tab and **Mark done**.

## 2. Start here (about 15 minutes)

1. Clone, then copy `.env.example` to `.env`. Without AWS, set `VITE_USE_MOCK=true` so the screens run on mock data.
2. Backend and frontend: follow [README → Run it locally](../README.md#run-it-locally).
   - Backend: `pip install -r requirements-dev.txt`, then `uvicorn app.main:app --reload --port 8000`, then `pytest`.
   - Frontend: `npm ci`, then `npm run dev`.
3. Pages:
   - `/`: command center.
   - `/phone`: resident phone simulator.
   - `/run/:runId`: volunteer route sheet (linked from the Plan tab).
   - `/3d-test`: throwaway 3D test page.
4. Read [PLAN.md](PLAN.md) §3 (demo story), §8 (API contract) and §13 (timeline), and the [PROGRESS.md](PROGRESS.md) "Current status".

## 3. Team rules (they kept `main` working so far)

- **Update [PROGRESS.md](PROGRESS.md) in the same PR as the work.** Never delete log entries; correct them with a new one.
- **Contract changes go in both files:** `backend/app/schemas.py` and `frontend/src/api/types.ts`.
- **Before every push or merge, run both checks:** `pytest` in `backend/` **and** `npm run build` in `frontend/`. The PR #5 merge broke `main` because only the backend tests were run.
- **Merge conflicts: combine both sides, don't pick one.** Then run both checks.
- P2 owns merges to `main`, and `main` must always deploy.

## 4. Critical path: the AWS gate (do this first, in order)

Owner: **P2**, with **P3** on steps 2, 6 and 7 and **P4** on step 8. **Every AWS service, permission, quota and value is listed in [AWS_SETUP.md](AWS_SETUP.md)**; work through it for steps 1–5. Commands are in [README → Deploy](../README.md#deploy).

1. **Credentials:** `aws configure`; region `us-west-2` unless the event says otherwise (record it in PROGRESS.md).
2. **Bedrock model access:** request a fast and a strong Claude model in the console, then list the inference profile IDs (`aws bedrock list-inference-profiles`).
3. **Deploy:** in `infra/`, run `sam build && sam deploy --guided`. Stack `stillhere`; enter the two model IDs. The stack also creates the map key and both guardrails.
4. **Map key:** `aws location describe-key --key-name stillhere-maps --query Key --output text`. Put it in `.env` and in Amplify.
5. **Amplify app:** connect the repo as a monorepo with root `frontend` (`amplify.yml`). Set `VITE_API_URL`, `VITE_LOCATION_API_KEY` and `VITE_LOCATION_REGION`, add the SPA rewrite rule from the README, and leave `VITE_USE_MOCK` unset.
6. **Smoke test** ([README → Deploy](../README.md#deploy)): hello-bedrock, reset, outages (40 affected), check-ins, inbound, clock, `/plans` (**time it: under ~20 s**), approve, run.
7. **AI eval:** `python tests/eval_replies.py` in `backend/` must reach **18/20 with no privacy hits**. Fix the prompts in `backend/app/prompts/` until it does.
8. **Gate:** 3 clean runs of the golden path on the deployed URL, then **record the safety video** (PLAN.md §14).

## 5. Remaining work by role

Each item: the first step and where to work. "Done" means it works on the deployed URL and PROGRESS.md is ticked.

### P2 · Backend and infra
- [ ] **The AWS gate (§4 above).** First step: credentials and `sam deploy`.
- [ ] **Lock down public surfaces** once the Amplify URL exists:
  - CORS in `backend/app/main.py` and `infra/template.yaml` (`AllowOrigins`).
  - The map key's `AllowReferers` (`infra/template.yaml`, TODOs there).
- [ ] **If the deployed map is blank** with a MIME-type error on `maplibre-gl-worker-*.mjs`, add a `Content-Type: text/javascript` header for `*.mjs` in Amplify.
- [ ] **Decide the `/demo/reset` response** (it returns `null` today) with P1.
- [ ] **Confirm the PROPOSED contract shapes** with P1 and P3 (list in [PROGRESS.md → Open questions](PROGRESS.md#open-questions)).
- [ ] **Remove 2 stale TODO comments:** `frontend/src/main.tsx` (polling is done in `api/client.ts`) and `infra/template.yaml` near `CodeUri` (seed data ships via the `backend/data` symlink).

### P3 · AI
- [ ] **Run the eval on real Bedrock** (`backend/tests/eval_replies.py`) and tune `backend/app/prompts/*.md` until it reaches 18/20 with no privacy hits.
- [ ] **Time the Job 5 agent** (`POST /plans`). If it gets near 20 s, look at PII masking first: `mask_pii()` makes one ApplyGuardrail call per Bedrock call in `backend/app/bedrock.py` (`_record_trace`). Mask after the turn, or mask only the newest message.
- [ ] **Fallback model retry** (`converse()` TODO, PLAN.md §16): retry once on `BEDROCK_FALLBACK_MODEL_ID` when the model is denied or throttled.
- [ ] **Spanish and Vietnamese end to end** on real Bedrock: the check-in, the reply assessment, and the escalation texts to the emergency contacts.
- [ ] **Photo replies** once P4 adds the 2 photos: Job 2 with the image; the eval uses them automatically.
- [ ] **Guardrails on the deploy:** check that the advice guardrail blocks "how much extra insulin should I take?" (tr-14) and that traces show "Guardrail: blocked". This is the video's Guardrail shot.

### P1 · Frontend and UX
- [ ] **Design polish plus loading, empty and error states** (`frontend/src/pages/CommandCenter.tsx`, `components/panels/*`, `index.css` TODO for the design tokens).
- [ ] **Backup-hours countdown in the triage queue cards** (`components/panels/TriageQueue.tsx`). `/dashboard` already sends `backup_hours_left`; today only the Resident panel shows it.
- [ ] **Agent step-by-step in the AI Trace tab** (`components/panels/TraceDrawer.tsx` TODO): show each Job 5 turn's tool calls, inputs and results.
- [ ] **Check with the map key:** satellite and hybrid styles, 3D building heights (if they all look the same, drop the buildings and keep the terrain), and the pulse on a full-size screen.
- [ ] **After the gate:** delete `frontend/src/api/mock.ts` and the `VITE_USE_MOCK` paths in `api/client.ts`, plus the `/3d-test` page (`pages/Map3DTest.tsx` and its route).

### P4 · Story, data and video
- [ ] **Verify every source** in `docs/sources.md`:
  - Fill "Accessed".
  - Read the Santa Clara County number off the HHS emPOWER map.
  - Find one confirmed outage-related harm. The 2019 El Dorado County case is **not** usable: the autopsy ruled out the outage.
  - Then flip `verified: true` in `frontend/src/components/panels/AboutPanel.tsx`.
- [ ] **Make the 2 reply photos:** `data/photos/minh_gauge.jpg` (oxygen tank gauge, about 3 h left) and `data/photos/wheelchair_battery.jpg` (battery warning), each under 1 MB.
- [ ] **Recording machine:** screen recorder ready (for example OBS). **Test 3D with pulsing markers there.** If it stutters, record in 2D or at 1× terrain.
- [ ] **Safety video at H7–H8** (one clean take of the golden path).
- [ ] **Finalize `docs/video_script.md`**. The architecture shot is `docs/architecture.svg`; open it in a browser to export a PNG.
- [ ] **Fill `docs/submission.md`:** upload place, format, event channel, team contacts, deployed URL, video link.

## 6. Timeline from here (PLAN.md §13)

| Phase | What has to happen |
|---|---|
| H7–H8 | AWS gate (§4): 3 clean runs on the deployed URL, safety video |
| H8–H12 | Finish SHOULD: polish and states, queue countdown, trace step detail, photos, ES/VI check, Guardrail shot |
| H12–H14 | Stretch (PLAN.md §11) only if the golden path is green; otherwise harden |
| H14–H15 | **Code freeze:** 3 clean runs from reset in a row, blocker fixes only |
| H15–H17 | Record, voiceover, edit, captions (video at 5:00 or less) |
| H17–H18 | Watch it cold with the score sheet and tick R1–R18 in `docs/submission.md`; **submit by 9:30 AM** (hard deadline 10:30 AM Saturday) |

## 7. Decisions still open

Full list with context in [PROGRESS.md → Open questions](PROGRESS.md#open-questions). The ones that block work:
- Exact H0 time, AWS region, and the submission details (upload place, format, event channel).
- PROPOSED contract shapes (P1, P2, P3).
- Photos committed as binaries? (P4, P3)
- Amplify connects `main` only, or this branch too? (P2)
- `/demo/reset` response (P1, P2)
- Agent timing vs PII masking (P3), and 3D on the recording machine (P1, P4).

## 8. Where things live

| Area | Files |
|---|---|
| API routes | `backend/app/main.py` (every PLAN.md §8 route, plus the 1-minute schedule handler) |
| Bedrock Jobs 1–4, Guardrails, traces | `backend/app/bedrock.py`, prompts in `backend/app/prompts/` |
| Job 5 dispatch agent | `backend/app/agent.py` (loop and greedy fallback), `backend/app/tools.py` (tools, plan rules) |
| Scoring and silence ladder | `backend/app/triage.py`, `backend/app/escalation.py` |
| Routes and maps | `backend/app/location.py` (Amazon Location plus a straight-line fallback) |
| Storage | `backend/app/store.py` (DynamoDB, S3), seed data in `data/` |
| Infra | `infra/template.yaml` (Lambda, API, tables, bucket, map key, guardrails, schedule), `amplify.yml` |
| Command center | `frontend/src/pages/CommandCenter.tsx`, `components/map/*`, `components/panels/*`, `components/timeline/*` |
| Phone and route sheet | `frontend/src/pages/Phone.tsx`, `frontend/src/pages/RunSheet.tsx` |
| API client and mock | `frontend/src/api/client.ts`, `frontend/src/api/mock.ts` |
| Tests | `backend/tests/` (`test_flow.py` runs the whole golden path offline), `backend/tests/eval_replies.py` (AI eval, needs AWS) |

**Known risks** (PLAN.md §16; PROGRESS.md has detail):
- The agent must finish under the 30 s API limit. It falls back to a greedy plan at 20 s, and the plan summary says so.
- 3D performance on the recording machine.
- Bedrock throttling when "Others reply" sends 32 replies at once. Lower its parallelism in `Phone.tsx` if needed.
