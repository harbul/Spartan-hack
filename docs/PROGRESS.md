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

- **Current phase:** H8–H12 (SHOULD tier) in progress, built offline. AWS credentials are here (Workshop Studio, `us-east-1` only); the H7–H8 gate now waits on the deploy, and the event account can't create IAM roles (see the AWS entry in the Phase log)
- **Handoff:** new to the project or picking up a role? Start at **[HANDOFF.md](HANDOFF.md)**: status, the AWS critical path, and remaining work by role
- **Last updated:** 2026-10-23 21:35 UTC · Claude session
- **Overall health:** 🟡 MUST golden path and most of SHOULD are code-complete and tested without AWS (117 tests, `npm run build`, live UI against the real API with in-memory tables and stand-in Bedrock and Location). Credentials are here and pre-flighted: Bedrock (Haiku 4.5, Sonnet 4.6) and Amazon Location answer in `us-east-1`. Nothing is deployed yet: the account can't create IAM roles, so the Lambda needs a role from the organizers (`FunctionRoleArn`) or we run the backend locally (`DeployApi=false`), [AWS_SETUP.md §2](AWS_SETUP.md#2-deploy-the-stack)
- **Gates:**
  - H0–H1 "Deployed URL returns a Bedrock reply; 3D path chosen" · ⬜ not met: Bedrock answers in the event account, but nothing is deployed (the account can't create IAM roles; [AWS_SETUP.md §2](AWS_SETUP.md#2-deploy-the-stack)). 3D path chosen provisionally (Amazon `Terrain3D`, confirmed in `us-east-1`)
  - H1–H4 "Each part works alone" · 🟡 met with stubs and mocks; real-AWS check pending
  - H4–H6 "Replies flow into the queue and onto the map" · 🟡 met offline: reset → zone → 40 check-ins → 4 phone replies → +3 h ends with Minh Critical, Rosa/Harold High, Denise OK, Lupe silent L3. Real-AWS check pending (README smoke test)
  - H6–H7 "Plan renders" · 🟡 met offline: + Others reply → +3 h → plan (13 stops, 3 volunteers, routes on the map) → approve → route sheet → mark done. Real-AWS check pending (agent on real Bedrock, routes on real Amazon Location)

### Done vs remaining (snapshot)

| Area | Done (merged to `main`) | Remaining |
|---|---|---|
| **AWS** | SAM template (Lambda, HTTP API, 8 tables, bucket, map key, 2 guardrails, scoped Bedrock + Location + Guardrail IAM, 1-minute schedule), `amplify.yml`, deploy + smoke-test steps in README Organizers' answer on IAM (mode A/B/C), first `sam deploy` in `us-east-1`, Amplify app (modes A/B), README smoke test (incl. `/plans`), `eval_replies.py`, 3 clean runs (HANDOFF.md §4). Credentials and model access: done |
| **P2 Backend** | Every §8 route; `store`, `geo`, `triage`, `escalation`, `location` (+ straight-line fallback), scheduled check; reply screening never blocks a reply | Real-AWS check; lock CORS and map-key referers; `/demo/reset` response; confirm PROPOSED shapes; 2 stale TODO comments |
| **P3 AI** | `converse()` + traces, Jobs 1–5 with prompts (Job 5 agent with rules in code + greedy fallback), privacy by construction, Guardrails (advice on SMS + reply screening, PII masking in traces), eval script | Eval on real Bedrock (18/20); time the agent (< ~20 s; PII masking latency); fallback model retry; ES/VI end to end; photo replies once photos exist; Guardrail shot |
| **P1 Frontend** | Command center on the live API (action bar 1–4, Plan tab, routes), 3D map (terrain, toggles, fly-to), pulsing no-reply markers, About panel, timeline, phone simulator (+ Others reply), route sheet, AI Trace list (+ guardrail result); mock behind `VITE_USE_MOCK` | Polish + loading/empty/error states; backup-hours countdown in queue cards; agent step detail in AI Trace; check satellite/buildings/pulse with the key; delete mock and `/3d-test` after the gate |
| **P4 Story/data** | 40 residents, real zone, resources, volunteers, 20 labeled + 16 crowd replies; `architecture.svg`; drafts of `sources.md` and `video_script.md` | Verify sources (emPOWER number, a confirmed harm case) then flip `verified` in the About panel; 2 reply photos; recorder + 3D check on the recording machine; safety video (H7–H8); final script; `submission.md` |

---

## Phase checklist

Phases and gates from [PLAN.md §13](PLAN.md#13-timeline-18-build-hours). H0 is when hacking starts.

| Phase | Gate | Status | Finished |
|---|---|---|---|
| Pre-event setup | §18 checklist done (see Open questions) | ⚠️ superseded: hacking started with items still open | |
| H0–H1 | Deployed URL returns a Bedrock reply; 3D path chosen (Amazon or fallback) | 🔄 in progress: code done, Bedrock answers; deploy waits on the IAM answer (or `DeployApi=false`) | |
| H1–H4 | Each part works alone | 🔄 in progress: code done and tested offline; real-AWS check waits on the deploy | |
| H4–H6 | Replies flow into the queue and onto the map | 🔄 in progress: code done and tested offline; real-AWS check waits on the deploy | |
| H6–H7 | Plan renders | 🔄 in progress: code done and tested offline; real-AWS check waits on the deploy | |
| H7–H8 | Golden path green, or cut (safety video recorded) | ⬜ not started | |
| H8–H12 | SHOULD tier done | 🔄 in progress: 3D map, fly-to, pulse, About panel and Guardrails code done offline | |
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
- [ ] Job 5: agent plan → routes on the map → Approve → volunteer view (done; real Bedrock + Location check pending)
- [ ] AI Trace drawer (list done; step-by-step detail in H8–H12)
- [ ] Deployed: Amplify URL plus the SAM stack (template ready with three deploy modes; waits on the organizers' IAM answer)

### SHOULD: H8 to H12

- [ ] 3D terrain and buildings, tilted camera, 2D/3D toggle (done on open terrain; Amazon satellite + buildings need the key)
- [x] Click a marker or card → camera flies to the home → Resident panel opens
- [ ] Backup-hours countdown per resident, pulsing no-reply markers, Key events list (pulse added; check it on a full-size screen)
- [ ] Photo replies (multimodal)
- [ ] Spanish and Vietnamese end to end
- [ ] Guardrails (denied topic plus PII masking in traces) (code, tests and SAM resources done; needs the deploy)
- [ ] "Needs human review" path for low confidence
- [ ] Design polish, plus loading, empty and error states
- [ ] About panel with sourced stats (done; stats tagged "to verify" until `sources.md` is checked)

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

### 2026-10-23 · H0–H1 · Event AWS account pre-flight, `us-east-1`, deploy modes
**By:** Claude session · **Branch/PR:** [`claude/zealous-keller-yvesgv`](https://github.com/neels22/Spartan-hack/tree/claude/zealous-keller-yvesgv)
**Done:**
- Pre-flight with the event credentials (read-only, plus about 10 one-line Bedrock calls and 3 Location calls; nothing created). Results in [AWS_SETUP.md → What we found](AWS_SETUP.md#what-we-found-in-the-event-account-2026-10-23):
  - Workshop Studio account: `WSParticipantRole` = `PowerUserAccess` + `ws-default-policy`. Temporary credentials.
  - Only `us-east-1` (every other region is denied).
  - **No IAM role creation;** `iam:PassRole` only on `WSParticipantRole`, which Lambda can't assume. The default `sam deploy` would fail on the Lambda and Scheduler roles.
  - Everything else the stack uses is allowed in `us-east-1`. Bedrock quotas: 10,000 requests per minute per model, ApplyGuardrail 100 per second.
- Bedrock models tested with Converse in `us-east-1`:
  - Fast `us.anthropic.claude-haiku-4-5-20251001-v1:0` and strong `us.anthropic.claude-sonnet-4-6` answer, including forced tool choice with `temperature`.
  - Fallback `us.anthropic.claude-sonnet-4-5-20250929-v1:0` answers.
  - Haiku 5.5 is denied (marketplace). Sonnet 5.5 rejects forced tool choice and `temperature`; Sonnet 5 rejects `temperature`.
- Amazon Location in `us-east-1`: the Hybrid style descriptor with `terrain=Terrain3D` returns `terrainSource`; `CalculateRoutes` and `OptimizeWaypoints` return results with IAM credentials.
- `infra/template.yaml`, three deploy modes:
  - default: unchanged behavior;
  - `FunctionRoleArn`: an existing role for the Lambda and the schedule, no IAM roles created;
  - `DeployApi=false`: tables, bucket, guardrails and map key only.

  Model parameters now default to the tested IDs. The 1-minute schedule is an explicit `AWS::Scheduler::Schedule` + `SchedulerRole` (was a SAM `ScheduleV2` event), because SAM drops its own scheduler role when `RoleArn` is an `Fn::If`.
- Region `us-east-1` and the tested model IDs in `.env.example`; frontend map region default `us-east-1` (`amazonStyle.ts`). AWS_SETUP.md rewritten with the findings and the modes; README and HANDOFF.md §4 point to them. PLAN.md §16: new risk row.
- Checks:
  - `cfn-lint` and `sam validate --lint` pass, and `sam build` passes (43 MB).
  - The SAM transform was run for each mode, to check what each creates and that no reference dangles. Default: 19 resources, roles `ApiFunctionRole` and `SchedulerRole`. `FunctionRoleArn`: 17 resources, no roles. `DeployApi=false`: 12 resources, no roles.
  - `pytest` and `npm run build` pass.
**Not done / cut:**
- Not deployed: needs the organizers' answer, or the team's go-ahead for `DeployApi=false`.
- Photo input on Sonnet 4.6 not tested.
**Decisions made:** see the Decisions log (region, model IDs, deploy modes, explicit schedule).
**Blockers / risks:**
- IAM: mode C has no public API URL (record the demo locally), and the backend must be restarted when the temporary credentials expire. The "deployed URL" part of the H0–H1 and H7–H8 gates needs mode A or B.
**Next steps:**
- P2: ask the organizers for IAM role creation or a Lambda role (exact ask in [AWS_SETUP.md §2, mode B](AWS_SETUP.md#2-deploy-the-stack)). Meanwhile deploy mode C and run the README smoke test locally.
- P3: `eval_replies.py` on real Bedrock with the tested models.

### 2026-10-23 · Handoff · AWS setup checklist
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah)
**Done:**
- [AWS_SETUP.md](AWS_SETUP.md): every AWS service, permission, quota and value the code needs, from `infra/template.yaml`, the boto3 calls, the env vars, `amplify.yml` and the map code. Pre-flight (services allowed, region, deployer permissions, tools), Bedrock (model access, profile IDs, quotas vs the code's parallelism), Location, what `sam deploy` creates, Amplify, where each value goes, cost, and what is not used.
- Linked from HANDOFF.md §4 and README → Deploy. Two open questions added (services allowed in the event account; which repo Amplify connects).
**Decisions made:**
- Documented as-is: `LocationApiKey` (SAM parameter, `LOCATION_API_KEY`) is passed to the Lambda but not read; routes use the Lambda role. `BedrockFallbackModelId` is granted in IAM but unused until P3 adds the retry. No code or template change.
**Next steps:**
- P2: work through AWS_SETUP.md when credentials arrive, pre-flight first; P3 requests Bedrock model access as early as possible.

### 2026-10-23 · Handoff · Project handed to the team
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah)
**Done:**
- [HANDOFF.md](HANDOFF.md): where we are, a 15-minute start, team rules (run `pytest` **and** `npm run build` before every merge), the AWS critical path in order, remaining work by role P1–P4 with first steps and files, the timeline to submission, open decisions and a file map.
- Refreshed this file's Current status, Done vs remaining and Open questions (closed "Assets", merged "Persona sources" into "Sources to verify").
**Next steps:**
- P2 (+P3, P4): the AWS gate, HANDOFF.md §4. Everyone else: their role's list in HANDOFF.md §5; all of it can start offline.

### 2026-10-23 · H8–H12 · Review of PR #12 and two fixes
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah)
**Done:**
- Reviewed PR #12 (3D map, fly-to, pulse, About panel, Guardrails) on a copy of `main`: `pytest` 116 passed, type-check, `vite build`, `cfn-lint` ok, no log entries lost. Design is sound.
- [`residentsLayer.ts`](../frontend/src/components/map/layers/residentsLayer.ts): the pulse changed a paint property on every frame, even with nothing pulsing, so MapLibre redrew the 3D terrain nonstop. Now it idles when no marker pulses and updates at most 20 times a second. Headless (software rendering) 3D with no pulsing went from 2 to 28 fps.
- [`main.py`](../backend/app/main.py): `screen_reply()` (advice guardrail) ran before Job 2 without a guard, so a guardrail error would have failed every reply and lost the message. It now logs and continues unscreened; new test in `test_flow.py`.
- Checks: `pytest` 117 passed, `npm run build` ok.
**Blockers / risks:**
- 3D with pulsing markers is still very slow under software rendering (about 1 fps headless). Real GPUs should be fine, but test the recording machine before H15; if 3D stutters, record in 2D or at 1× terrain (§16).
- PII masking makes one ApplyGuardrail call per Bedrock call, including each Job 5 agent turn. See Open questions.

### 2026-10-23 · H8–H12 · 3D map, fly-to, pulse, About panel, Guardrails (offline)
**By:** Claude session · **Branch/PR:** `feat/should-tier`
**Done:**
- P1: [`IncidentMap`](../frontend/src/components/map/IncidentMap.tsx) is 3D by default (pitch 60°, looking east at the foothills) with 2D/3D, terrain 1×/2×/3×, Satellite/Hybrid (with a key) and fullscreen. [`terrain.ts`](../frontend/src/components/map/terrain.ts) holds the /3d-test approach: Amazon `Terrain3D` with a key, open Terrain Tiles otherwise (+ hillshade with no key), building extrusions when the Amazon tiles have them. Selecting a resident (marker, queue card, plan stop) flies the camera to the home once per selection.
- P1: no-reply markers pulse, harder with each escalation level ([`residentsLayer.ts`](../frontend/src/components/map/layers/residentsLayer.ts)).
- P1: [`AboutPanel`](../frontend/src/components/panels/AboutPanel.tsx): what StillHere does, "AI reads and explains, rules rank, humans decide", the AWS services, and the `sources.md` stats, each tagged "to verify" until it has an Accessed date.
- P3: Guardrails (§4 Job 6) in [`bedrock.py`](../backend/app/bedrock.py): the advice guardrail runs on Jobs 1 and 4 (SMS only) with fixed EN/ES/VI fallback texts if it blocks a draft; `screen_reply()` checks every inbound reply (ApplyGuardrail) and sends medical-advice questions (e.g. tr-14 "how much extra insulin") to human review while Job 2 still assesses them; `mask_pii()` uses the PII guardrail for names and addresses in traces, phones by pattern as before. Trace rows carry `guardrail_action`; the AI Trace list shows "Guardrail: blocked/passed". Everything is skipped while the guardrail IDs are unset.
- P2: [`template.yaml`](../infra/template.yaml): `AdviceGuardrail` (denied topic MedicalAdvice) and `PiiGuardrail` (NAME/ADDRESS/PHONE anonymized), their IDs into the Lambda env and stack outputs, `bedrock:ApplyGuardrail` on both. `.env.example` has the PII guardrail vars.
- Checks: `pytest` 116 passed (new: guardrail config, intervention → trace, safe fallbacks keep the privacy rule, screening, PII masking + fallback), `compileall`, `cfn-lint`, `npm run build`. In Chromium (production build against the offline API): 3D terrain with zone, markers and routes draped on it; 2D toggle; queue click flies to Lupe and opens her panel; About panel.
**Not done / cut:**
- Not seen with the Amazon key: satellite imagery, `Terrain3D`, building heights. Guardrails not run on real Bedrock (does the denied topic catch tr-14? does PII masking keep traces readable?).
- The pulse could only be checked at low resolution in the narrow preview pane; check it on a full-size screen.
- Photo replies, ES/VI end to end and "needs review" polish need real Bedrock or the photos; design polish not started.
- `/3d-test` kept for the building-height check with the key; delete after.
**Decisions made:**
- See the Decisions log entries for two guardrails, the `guardrail` trace job, and 3D by default.
**Blockers / risks:**
- A hidden or background browser tab pauses MapLibre (no `requestAnimationFrame`): the map stays blank until the tab is visible. Record the video with the tab in front.
**Next steps:**
- At H0: deploy (creates both guardrails), then send tr-14 from the phone and check the Trace drawer shows "Guardrail: blocked"; open `/` with the key to check satellite + 3D.
- P1: design polish and the trace step detail. P4: verify sources, then set `verified: true` per stat in `AboutPanel.tsx`.

### 2026-10-23 · H6–H7 · Merge fix: PR #5 with #8 and #9
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah)
**Done:**
- The merge of PR #5 with #8 (crowd replies) and #9 ("Others reply" button) took only PR #5's side of each conflict. That left `main` failing `npm run build` (`Phone.tsx` kept #9's `sendOthers` but lost its constants), dropped three log entries below, and dropped #9's video-script beat.
- `Phone.tsx`: #9's data-driven "Others reply" button restored (sends tr-05 to tr-20 and `data/crowd_replies.json`; exactly res-005, res-025, res-036, res-039 stay silent). PR #5's hard-coded 3-resident button removed.
- `test_flow.py`: the plan test derives the silent set from the data (4), like the button. README and video script follow the merged button.
- Restored the three log entries below (never delete log entries).
- **Bug found by the merged data:** the planner only had to cover priority ≥ 60, so res-039 (insulin, 25 h backup, not alone: Watch 50 even when silent) got no door-knock. §5 says every L3 silent case gets one. Now `tools.must_cover()` = priority ≥ 60 **or** silent, used by `submit_plan`, the greedy planner, the mock plan and the planner prompt; new test.
- Checks: `pytest` 107 passed, `npm run build` ok.
**Next steps:**
- Same as the H6–H7 entry: real-AWS checks when credentials arrive.

### 2026-10-23 · H6–H7 · Plan renders (offline)
**By:** Claude session · **Branch/PR:** [`claude/focused-einstein-cqibah`](https://github.com/harbul/Spartan-hack/compare/main...neels22:Spartan-hack:claude/focused-einstein-cqibah) · Plan: capacity handling and the diagram format decided by the team before starting
**Done:**
- P2: [`location.py`](../backend/app/location.py) OptimizeWaypoints + CalculateRoutes with a straight-line fallback; IAM for both; `POST /plans`, `/plans/{id}/approve`, `/runs/{id}/stops/{rid}/done`, `GET /runs/{id}` (+ volunteer and stop details); `/dashboard` returns the latest plan.
- P3: Job 5 [`agent.py`](../backend/app/agent.py) Converse tool-use loop (12 turns, 20 s budget) with [`tools.py`](../backend/app/tools.py): five tools, `submit_plan` checks every §4 rule in code and returns problems to the agent, greedy fallback planner; `planner.md` prompt.
- P1: Plan tab (runs, stops, reasons, next wave, Approve), routes on the map (dashed draft, solid approved), action bar steps 3–4, volunteer route sheet `/run/:runId`, "Others reply (demo)" on the phone simulator; the mock plans, approves and serves a route sheet too.
- P4: [`architecture.svg`](architecture.svg) for the video; README smoke test and video script extended.
- Checks: `pytest` 103 passed (new: location, tools, agent, plan flow), `compileall`, `cfn-lint`, `sam build`, `npm run build`. In Chromium against the real API (in-memory tables, greedy planner standing in for Bedrock, Location unavailable): heroes + Others reply (33) → +3 h → plan 13 stops / 3 volunteers → approve → route sheet → mark done; and in mock mode.
**Not done / cut:**
- Nothing on real AWS yet: the agent's real behavior and timing, real road routes.
- Trace drawer shows each agent turn and its tool names; tool outputs per step stay for H8–H12.
**Decisions made:**
- See the Decisions log entries dated 2026-10-23 (H6–H7).
**Blockers / risks:**
- Credentials, as before. First real `/plans` call is the riskiest step: agent time vs the 30 s API limit (falls back to greedy at 20 s, visible in the summary).
**Next steps:**
- When credentials arrive: README smoke test end to end, `eval_replies.py`, then three clean browser runs on the deployed URL (H7–H8 gate) and record the safety video.
- H7–H8: delete the mock once the gate is met; P4 verify sources, make the 2 photos.

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
| 2026-10-23 | Closed "Assets" (the UI is built and `architecture.svg` exists, so wireframes are no longer needed) and merged "Persona sources" into "Sources to verify" | Keep Open questions to what still blocks work | Claude session |
| 2026-10-23 | Handoff to the team: [HANDOFF.md](HANDOFF.md) holds status, the AWS critical path and remaining work by role; PROGRESS.md stays the detailed tracker | One place for a teammate to start | Team |
| 2026-10-23 | **Capacity (closes "36 silent residents"):** "Others reply" on the phone simulator (#9's data-driven version) sends the other test replies and the crowd replies through the real `/inbound` (Lupe, res-025, res-036, res-039 stay silent); plans list what can't fit as `Plan.uncovered` ("next wave") | 3 volunteers × 6 stops = 18; without it ~40 cases were ≥ 60. Simulated residents, real processing | Team |
| 2026-10-23 | A plan must cover every case with priority ≥ 60 **and every silent (L3) case**, whatever its priority | §5: L3 is "automatically added as a door-knock stop in the next plan"; res-039 scores Watch while silent | Claude session |
| 2026-10-23 | `submit_plan` enforces the §4 rules in code (6 stops, Critical first, seats for rides, real open cases, no uncovered case while room is left) and returns problems to the agent | The agent decides who and why; the code guarantees the rules | Claude session |
| 2026-10-23 | Agent: 12 turns and a 20 s budget, then the greedy planner; the summary says why. A missing model ID still raises (503) | Stays under the 30 s API limit; a setup error is never hidden behind a fallback | Claude session |
| 2026-10-23 | `optimize_run` takes `volunteer_id` + `resident_ids` (not raw coordinates) and its Location results are cached for `submit_plan` | Easier for the model to call correctly; no double Location calls | Claude session |
| 2026-10-23 | Location failures fall back to nearest-neighbour order and straight lines at 30 km/h, noted in the plan summary and the Plan tab | §16; the demo keeps working and nobody mistakes a straight line for a road | Claude session |
| 2026-10-23 | Contract: `Stop.action` = cooler / battery / door_knock / ride (no longer PROPOSED); `Plan.uncovered`; `RunResponse.volunteer` + `stops_detail` | Next wave visible; the route sheet needs one call | Claude session |
| 2026-10-23 | Architecture diagram is `docs/architecture.svg` (replaces the planned `.png`) | Team choice: text-based, versioned, readable at 1080p | Team |
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
| 2026-10-23 | **Two guardrails:** advice (denied topic) on SMS jobs and reply screening; PII (anonymize) only for trace rows via ApplyGuardrail | One guardrail with PII filters on the SMS jobs would also mask the resident's own name ("Hi {NAME}") | Claude session |
| 2026-10-23 | A reply asking for medical advice is screened, flagged for human review, and still assessed by Job 2 | Blocking Job 2's input would leave the case with no assessment; the app never answers residents anyway | Claude session |
| 2026-10-23 | `BedrockJob` gains `"guardrail"` (schemas.py + types.ts) | Reply screening is a Bedrock call with its own trace row in the AI Trace drawer | Claude session |
| 2026-10-23 | The incident map opens in 3D (pitch 60°, bearing 60°) | The foothills are the visual of the video; 2D stays one click away | Claude session |
| 2026-10-23 | **Region `us-east-1`** (closes the "AWS account" region question) | The event's Workshop Studio policy denies every other region; `.env.example`, the frontend map default, README and AWS_SETUP.md now use it | Claude session (event account) |
| 2026-10-23 | **Model IDs:** fast `us.anthropic.claude-haiku-4-5-20251001-v1:0`, strong `us.anthropic.claude-sonnet-4-6`, fallback `us.anthropic.claude-sonnet-4-5-20250929-v1:0`; defaults in `.env.example` and the SAM parameters (replaces "none yet") | Tested with Converse in the event account. Haiku 5.5 is denied (marketplace); Sonnet 5.5 rejects forced tool choice and `temperature`, which Job 2 and `converse()` use | Claude session |
| 2026-10-23 | **Three deploy modes in `infra/template.yaml`:** default (creates roles), `FunctionRoleArn` (existing role, no roles created), `DeployApi=false` (tables, bucket, guardrails, map key; backend runs locally) (closes "Services allowed in the event account") | The event account can't create IAM roles (`PowerUserAccess`; `iam:PassRole` only on `WSParticipantRole`); one template still covers every answer from the organizers | Claude session |
| 2026-10-23 | The 1-minute schedule is an explicit `AWS::Scheduler::Schedule` with its own `SchedulerRole` (no longer a SAM `ScheduleV2` event) | With `RoleArn` as an `Fn::If`, SAM creates no scheduler role at all, which would break the default mode; explicit resources can follow the mode | Claude session |
| 2026-10-23 | Amazon Location `Terrain3D` path confirmed in `us-east-1` too (style descriptor returns `terrainSource`) | Region moved; the 3D decision above was checked in `us-west-2` | Claude session |

---

## Open questions

Waiting on the team or organizers. When answered, remove it here and record the answer in the Decisions log.

From [PLAN.md §18](PLAN.md#18-pre-event-checklist-and-open-questions):

- [ ] **Event schedule:** hacking has started; record the exact H0 clock time so H0 to H18 maps to the clock.
- [ ] **IAM in the event account:** it can't create roles, so the Lambda can't be deployed as is. Ask the organizers to allow role creation (mode A) or to provide a Lambda role (mode B; exact ask in [AWS_SETUP.md §2](AWS_SETUP.md#2-deploy-the-stack)). Until then, mode C (`DeployApi=false`, backend run locally). (P2)
- [ ] **Amazon Location:** style and 3D terrain are confirmed at the style level in us-west-2 and `us-east-1`, and `OptimizeWaypoints`/`CalculateRoutes` answer in `us-east-1` (a straight-line fallback stays). Still open: a visual check with the key, and real routes on the deploy. Mapbox token only if both Amazon options fail.
- [ ] **Accounts:** an Amplify app connected to this repo; a screen recorder ready (for example OBS).
- [ ] **Which repo Amplify connects:** the team repo `harbul/Spartan-hack` or the fork? It deploys `main` on every push. (P2)
- [ ] **Submission:** where the video is uploaded, the accepted format, and the event channel for judge questions. Record answers in `docs/submission.md`.

From the repo setup (2026-10-23):

- [ ] **PROPOSED shapes** in `schemas.py` / `types.ts`: `ScoreBreakdown` field names, `Escalation`, `ToolCall`, `DashboardCase.resident`, `Outage.status`, `Volunteer.capacity` meaning (now used as ride seats), `Resource.offers`. P1, P2, P3 confirm. (`Stop.action` confirmed in H6–H7.)
- [ ] **Test reply photos:** `test_replies.json` points tr-02 to `data/photos/minh_gauge.jpg` and tr-18 to `data/photos/wheelchair_battery.jpg`. Someone takes or makes the 2 photos (under 1 MB each); OK to commit them as binaries? (P4, P3)
- [ ] **Lockfile:** `frontend/package-lock.json` is committed so all four laptops and Amplify install the same versions. Keep it? (P1, P2)

From H0–H1 (2026-10-23):

- [ ] **Amplify branch for the gate:** Amplify deploys `main` (§6). Connect this branch too for the gate check, or merge first? (P2)
- [ ] **Lock down public surfaces:** CORS (`*` in FastAPI and the HTTP API) and the map key's allowed referers should name the Amplify URL and localhost once the Amplify URL exists. (P2)
- [ ] **3D buildings height:** the extrusion reads the `height` property of the `buildings` tile layer, with 6 m if it's missing. Check on `/3d-test` with the key. If all buildings look the same height, drop buildings and keep terrain. (P1)
- [ ] **Sources to verify:** open every link in `docs/sources.md`, read the Santa Clara County emPOWER number off the live map, and find a confirmed outage-related harm (the 2019 El Dorado County case was ruled not outage-caused). (P4)
- [ ] **`/demo/reset` response:** returns `null` (§8 says n/a). Fine for the Reset button? (P1, P2)
- [ ] **PII masking vs the agent's 20 s budget:** `mask_pii()` calls ApplyGuardrail inside every `converse()`, so each Job 5 turn waits for one more round trip, and long agent transcripts may exceed ApplyGuardrail's text limit (it then masks phones only). Time `/plans` at H0; if it nears 20 s, mask after the turn returns or mask only the newest message. (P3)
- [ ] **3D on the recording machine:** check 3D with pulsing markers stays smooth on the machine that records the video; otherwise record in 2D or at 1× terrain. (P1, P4)
- [ ] **Worker file type on Amplify:** the MapLibre worker ships as `assets/maplibre-gl-worker-*.mjs`. If the deployed map is blank with a MIME-type error, add a `Content-Type: text/javascript` custom header for `*.mjs`. (P1, P2)
