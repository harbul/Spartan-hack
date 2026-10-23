# StillHere

**StillHere** is a 3D emergency response command center that keeps electricity-dependent residents safe during a California power shutoff (PG&E PSPS). Amazon Bedrock writes check-in texts, reads replies, explains priorities, escalates residents who go silent and plans volunteer routes; a county coordinator approves every dispatch. Built on AWS for SpartHill Hacks 2026 (AWS Track).

- **New to the project? Start at [docs/HANDOFF.md](docs/HANDOFF.md)**: status, the AWS critical path, and remaining work by role.
- **Build plan (source of truth):** [docs/PLAN.md](docs/PLAN.md)
- **Progress log (where we are now):** [docs/PROGRESS.md](docs/PROGRESS.md). Read both before starting work; update PROGRESS.md in the same commit as your work.

## Folder map

```
Spartan-hack/
├── .env.example              every env var, one line each (copy to .env)
├── amplify.yml               Amplify Hosting build for frontend/
├── docs/
│   ├── PLAN.md               the build plan
│   ├── PROGRESS.md           phase status, scope tracker, decisions, open questions
│   ├── HANDOFF.md            start here: status, critical path, remaining work by role
│   ├── architecture.svg      architecture diagram for the video (§6)
│   ├── video_script.md       5-minute video script (§14)
│   ├── sources.md            cited stats for the persona (§18)
│   └── submission.md         video link, contacts, final R1–R18 tick (§1.1)
├── data/                     synthetic demo data, seeded by POST /demo/reset
│   ├── residents.json        40 residents incl. the 5 hero residents (§3)
│   ├── outage_zone.geojson   PSPS polygon over East San Jose
│   ├── resources.json        resource centers and pharmacy
│   ├── volunteers.json       3 volunteers with vehicles
│   ├── test_replies.json     20 labeled replies (eval + phone quick replies)
│   └── crowd_replies.json    16 simple OK replies; everyone else stays silent (4 residents)
├── backend/                  Python 3.12, FastAPI on Lambda
│   ├── app/
│   │   ├── main.py           API routes (§8) + Lambda handler
│   │   ├── schemas.py        shared contract: Pydantic models (§7, §8)
│   │   ├── store.py          DynamoDB access
│   │   ├── triage.py         deterministic score + bands (§5)
│   │   ├── escalation.py     silence ladder + virtual clock (§5)
│   │   ├── geo.py            point-in-polygon, nearest resource
│   │   ├── location.py       Amazon Location routes client
│   │   ├── bedrock.py        converse() wrapper, tracing, Guardrails, Jobs 1–4
│   │   ├── agent.py          Job 5 dispatch planner (tool-use loop)
│   │   ├── tools.py          tool schemas + implementations
│   │   └── prompts/          one prompt spec per Bedrock job
│   ├── data -> ../data       symlink so `sam build` ships the seed data to the Lambda
│   ├── tests/                pytest unit tests (conftest.py: fake DynamoDB) + AI eval script
│   ├── pytest.ini
│   ├── requirements.txt      Lambda dependencies
│   └── requirements-dev.txt  + pytest, httpx, uvicorn (local only)
├── frontend/                 React + Vite + TypeScript + Tailwind + MapLibre
│   └── src/
│       ├── main.tsx          providers + routes (/, /phone, /run/:runId)
│       ├── api/types.ts      shared contract: TypeScript mirror of schemas.py
│       ├── api/client.ts     fetch helpers + useDashboard() (mock until H4–H6)
│       ├── api/seed.ts       data/*.json, typed (phone quick replies, mock)
│       ├── api/mock.ts       MOCK dashboard following the demo story (delete in H4–H6)
│       ├── pages/            CommandCenter, Phone, RunSheet
│       └── components/
│           ├── status.ts     status colors and labels; BedrockBadge.tsx
│           ├── map/          IncidentMap + layers/ (zone, residents, routes, resources)
│           ├── timeline/     Timeline, KeyEvents, Counters
│           └── panels/       Overview, TriageQueue, ResidentPanel, TraceDrawer, PlanPanel
└── infra/
    └── template.yaml         SAM: Lambda, HTTP API, tables, bucket, schedule, IAM
```

## Who owns what

| Folder or file | Owner |
|---|---|
| `frontend/` (incl. `src/api/types.ts`) | P1, Frontend and UX |
| `backend/app/main.py`, `schemas.py`, `store.py`, `triage.py`, `escalation.py`, `geo.py`, `location.py` | P2, Backend and infra |
| `backend/tests/test_triage.py`, `test_geo.py`, `test_health.py`, `test_store.py`, `conftest.py`, `backend/requirements*.txt`, `infra/`, `amplify.yml`, `.env.example` | P2, Backend and infra |
| `backend/app/bedrock.py`, `agent.py`, `tools.py`, `prompts/`, `backend/tests/eval_replies.py`, `test_bedrock.py` | P3, AI |
| `data/`, `docs/`, `backend/tests/test_seed_data.py` | P4, Story, data and video |

The shared contracts (`backend/app/schemas.py` and `frontend/src/api/types.ts`) are agreed by P1, P2 and P3: change both in the same PR. P2 owns merges to `main`, and `main` must always deploy (§12).

## Run it locally

Needs Python 3.12, Node 22, and (for AWS) the AWS CLI and SAM CLI with credentials for the team account.

```bash
# One-time: environment (repo root)
cp .env.example .env              # fill in model IDs, API URL, map key (see Deploy below)

# Backend (from backend/)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt          # app deps + pytest, httpx, uvicorn
set -a && source ../.env && set +a           # AWS creds come from your AWS profile / env
uvicorn app.main:app --reload --port 8000
curl localhost:8000/health                   # {"ok":true}
curl localhost:8000/hello-bedrock            # real Bedrock reply (503 if model IDs unset)

# Tests (from backend/)
pytest                            # unit tests (Bedrock is stubbed)
python tests/eval_replies.py      # AI eval against data/test_replies.json (calls Bedrock; from H4)

# Frontend (from frontend/)
npm install
npm run dev                       # http://localhost:5173  (/phone simulator, /3d-test throwaway 3D test)
npm run build                     # type-check + production build
```

## Deploy

```bash
# Backend (from infra/): Lambda + HTTP API + tables + browser map key
sam build
sam deploy --guided               # stack name: stillhere, region: us-west-2,
                                  # BedrockFastModelId / BedrockStrongModelId = inference profile IDs,
                                  # "ApiFunction has no authentication. Is this okay?" -> y
                                  # (answers are saved to infra/samconfig.toml, gitignored)
# Later deploys: sam build && sam deploy

# Values for .env and Amplify, from the stack outputs
aws cloudformation describe-stacks --stack-name stillhere \
  --query "Stacks[0].Outputs" --output table          # ApiUrl -> VITE_API_URL
aws location describe-key --key-name stillhere-maps \
  --query Key --output text                           # -> VITE_LOCATION_API_KEY
```

Smoke test after a deploy (`API=<ApiUrl>`; run the Python from `backend/` with `.env` loaded):

```bash
curl $API/hello-bedrock                                   # H0-H1 gate: a real Bedrock reply
curl -X POST $API/demo/reset                              # reseeds 40 residents
python3 -c 'import json; g=json.load(open("../data/outage_zone.geojson"))["features"][0]["geometry"]; print(json.dumps({"name":"East San Jose PSPS","polygon":g,"starts_at":"2026-10-24T01:00:00Z","est_restore_at":"2026-10-24T15:00:00Z"}))' \
  | curl -X POST $API/outages -H 'content-type: application/json' -d @-   # expect 40 affected

# Jobs 1 and 2 by hand (writes rows to the stillhere-traces table)
python - <<'PY'
from app import bedrock, store
from app.schemas import Outage, Resident
minh = Resident.model_validate(store.load_seed("residents")[0])
outage = Outage(outage_id="smoke", name="smoke", polygon={}, starts_at="2026-10-24T01:00:00Z",
                est_restore_at="2026-10-24T15:00:00Z", affected_ids=[], status="active")
sms = bedrock.write_checkin(minh, outage)
print(sms.output)
print(bedrock.assess_reply(minh, sms.output, "Bình oxy còn khoảng 3 tiếng. Tôi hơi khó thở.").output)
PY
```

The H4–H6 golden path through the API, then the AI eval (from `backend/`, needs AWS):

```bash
OUTAGE=<outage_id from POST /outages>
curl -X POST $API/outages/$OUTAGE/checkins               # {"sent": 40}: Job 1 for everyone
curl -X POST $API/inbound -H 'content-type: application/json' \
  -d '{"phone":"+14085550102","text":"tengo 3 plumas, el refri ya no enfría"}'   # Rosa: Jobs 2 + 3, High
curl -X POST $API/clock/advance -H 'content-type: application/json' -d '{"minutes":180}'  # Job 4 escalations
curl $API/dashboard                                       # counts, cases, events at virtual now
python tests/eval_replies.py                              # needs 18/20 and no privacy hits
```

H6–H7, the dispatch plan (after most residents have replied, see "Others reply" below):

```bash
curl -X POST $API/plans -H 'content-type: application/json' -d "{\"outage_id\":\"$OUTAGE\"}"  # Job 5 agent; under ~20 s
PLAN=<plan_id>; RUN=<a run_id from the plan>
curl -X POST $API/plans/$PLAN/approve                     # cases become dispatched
curl $API/runs/$RUN                                       # the volunteer's route sheet
curl -X POST $API/runs/$RUN/stops/res-005/done            # Lupe's door-knock done
```

The AI Trace tab should show one Job 5 row per agent turn. If the plan summary says "Fallback plan" or "straight lines", the agent or Amazon Location did not finish; the log says why.

Or run it in the browser: `/` → Reset demo → 1. Load outage zone → 2. Send check-ins; on `/phone` send the 4 hero quick replies, then **Others reply** (the other test replies and `data/crowd_replies.json` go through the real `/inbound`; Lupe and 3 more stay silent); back on `/`, +3 h → 3. Plan dispatch → 4. Approve plan → open a route sheet from the Plan tab and mark a stop done. Set `VITE_USE_MOCK=true` to work on the screens without an API.

Frontend: Amplify Hosting builds `frontend/` with [`amplify.yml`](amplify.yml). Connect the repo as a monorepo with root `frontend`, set `VITE_API_URL`, `VITE_LOCATION_API_KEY` and `VITE_LOCATION_REGION`, and add the SPA rewrite (`</^[^.]+$|\.(?!(css|gif|ico|jpg|js|mjs|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>` → `/index.html`, 200) so `/phone` and `/run/:runId` deep links work.
