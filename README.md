# StillHere

**StillHere** is a 3D emergency response command center that keeps electricity-dependent residents safe during a California power shutoff (PG&E PSPS). Amazon Bedrock writes check-in texts, reads replies, explains priorities, escalates residents who go silent and plans volunteer routes; a county coordinator approves every dispatch. Built on AWS for SpartHill Hacks 2026 (AWS Track).

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
│   ├── video_script.md       5-minute video script (§14)
│   ├── sources.md            cited stats for the persona (§18)
│   └── submission.md         video link, contacts, final R1–R18 tick (§1.1)
├── data/                     synthetic demo data, seeded by POST /demo/reset
│   ├── residents.json        ~40 residents incl. the 5 hero residents (§3)
│   ├── outage_zone.geojson   PSPS polygon over East San Jose
│   ├── resources.json        resource centers and pharmacy
│   ├── volunteers.json       3 volunteers with vehicles
│   └── test_replies.json     20 labeled replies (eval + phone quick replies)
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
│   ├── tests/                pytest unit tests + AI eval script
│   ├── pytest.ini
│   ├── requirements.txt      Lambda dependencies
│   └── requirements-dev.txt  + pytest, httpx, uvicorn (local only)
├── frontend/                 React + Vite + TypeScript + Tailwind + MapLibre
│   └── src/
│       ├── main.tsx          providers + routes (/, /phone, /run/:runId)
│       ├── api/types.ts      shared contract: TypeScript mirror of schemas.py
│       ├── pages/            CommandCenter, Phone, RunSheet
│       └── components/
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
| `backend/tests/test_triage.py`, `test_geo.py`, `test_health.py`, `backend/requirements*.txt`, `infra/`, `amplify.yml`, `.env.example` | P2, Backend and infra |
| `backend/app/bedrock.py`, `agent.py`, `tools.py`, `prompts/`, `backend/tests/eval_replies.py`, `test_bedrock.py` | P3, AI |
| `data/`, `docs/` | P4, Story, data and video |

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
npm run dev                       # http://localhost:5173  (/3d-test = throwaway 3D map test)
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

Frontend: Amplify Hosting builds `frontend/` with [`amplify.yml`](amplify.yml). Connect the repo as a monorepo with root `frontend`, set `VITE_API_URL`, `VITE_LOCATION_API_KEY` and `VITE_LOCATION_REGION`, and add the SPA rewrite (`</^[^.]+$|\.(?!(css|gif|ico|jpg|js|mjs|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>` → `/index.html`, 200) so `/phone` and `/run/:runId` deep links work.
