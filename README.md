# StillHere

**StillHere** is a 3D emergency response command center that keeps electricity-dependent residents safe during a California power shutoff (PG&E PSPS). Amazon Bedrock writes check-in texts, reads replies, explains priorities, escalates residents who go silent and plans volunteer routes; a county coordinator approves every dispatch. Built on AWS for SpartHill Hacks 2026 (AWS Track).

- **Build plan (source of truth):** [docs/PLAN.md](docs/PLAN.md)
- **Progress log (where we are now):** [docs/PROGRESS.md](docs/PROGRESS.md). Read both before starting work; update PROGRESS.md in the same commit as your work.

## Folder map

```
Spartan-hack/
├── .env.example              every env var, one line each (copy to .env)
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
│   └── requirements.txt
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
| `backend/tests/test_triage.py`, `test_geo.py`, `backend/requirements.txt`, `infra/`, `.env.example` | P2, Backend and infra |
| `backend/app/bedrock.py`, `agent.py`, `tools.py`, `prompts/`, `backend/tests/eval_replies.py` | P3, AI |
| `data/`, `docs/` | P4, Story, data and video |

The shared contracts (`backend/app/schemas.py` and `frontend/src/api/types.ts`) are agreed by P1, P2 and P3: change both in the same PR. P2 owns merges to `main`, and `main` must always deploy (§12).

## Run it locally

Placeholder commands until the code exists.

```bash
# One-time: environment
cp .env.example .env              # fill in model IDs, keys, table names

# Backend (from backend/)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
set -a && source ../.env && set +a
sam local start-api -t ../infra/template.yaml   # or uvicorn, see docs/PROGRESS.md open questions

# Tests (from backend/)
pytest                            # unit tests
python tests/eval_replies.py      # AI eval against data/test_replies.json (calls Bedrock)

# Frontend (from frontend/)
npm install
npm run dev                       # http://localhost:5173
npm run build                     # type-check + production build

# Deploy (from infra/)
sam build && sam deploy --guided
```
