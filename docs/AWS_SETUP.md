# AWS setup checklist

> Every AWS thing StillHere needs, taken from the code (`infra/template.yaml`, the boto3 calls in `backend/app/`, the env vars, `amplify.yml`, the frontend map).
> Work through it top to bottom. Owner: **P2** (P3 on Bedrock). It covers steps 1–5 of [HANDOFF.md §4](HANDOFF.md#4-critical-path-the-aws-gate-do-this-first-in-order).
> Most of it is created by one `sam deploy`. By hand you do only: Amplify, and copying a few values.

## What we found in the event account (2026-10-23)

Checked with the event credentials, read-only plus a few tiny Bedrock and Location calls:

- **It is an AWS Workshop Studio account.** The credentials are temporary (they include a session token) and belong to the role `WSParticipantRole`, which has `PowerUserAccess` plus the event policy `ws-default-policy`.
- **Only `us-east-1`.** `ws-default-policy` denies every other region (Bedrock invocations are exempt, so cross-region inference profiles still work). Everything in this doc uses `us-east-1`.
- **No IAM role creation.** `PowerUserAccess` allows no IAM writes besides service-linked roles. `iam:PassRole` is allowed only on `WSParticipantRole`, and Lambda can't assume that role. The stack's default mode creates two roles (Lambda and Scheduler), so **it fails here**. See §2 for the other two modes.
- **Everything else is allowed in `us-east-1`:** Bedrock (incl. Guardrails), Amazon Location, Lambda, API Gateway, DynamoDB, S3, EventBridge Scheduler, CloudFormation, Amplify and CloudWatch Logs. Lambda has 110 unreserved concurrent executions.
- **Bedrock models are already enabled** for most Claude models; tested IDs are in §1. Haiku 5.5 is blocked by the event's marketplace settings.
- **Amazon Location works in `us-east-1`:** the Hybrid style with `terrain=Terrain3D`, `CalculateRoutes` and `OptimizeWaypoints`.

**Open with the organizers:** either allow IAM role creation, or provide a role for the Lambda (details in §2, mode B). Until then, use mode C.

## 0. Pre-flight (do before anything else)

- [x] **Services allowed in the event account (R6):** all of them in `us-east-1`, except IAM role creation (above).
- [x] **Region: `us-east-1`** (the only region the event allows). It is already set in `.env.example` (`AWS_REGION`, `VITE_LOCATION_REGION`) and is the frontend's default. Use it for `sam deploy` and Amplify too.
- [ ] **Credentials:** copy them from the Workshop Studio event page. They expire: when calls start failing with `ExpiredToken`, copy fresh ones.
  - Put them in your shell (`export AWS_ACCESS_KEY_ID=… AWS_SECRET_ACCESS_KEY=… AWS_SESSION_TOKEN=…`) or in `~/.aws/credentials`. **Never in the repo**, `.env` included.
  - Check: `aws sts get-caller-identity` prints `assumed-role/WSParticipantRole/Participant`.
- [ ] **Deployer permissions:** the person running `sam deploy` needs:
  - CloudFormation;
  - Lambda, API Gateway v2 (HTTP API), DynamoDB, S3, EventBridge Scheduler and CloudWatch Logs;
  - Bedrock `CreateGuardrail`;
  - Location `CreateKey`;
  - mode A only: IAM role creation (`CAPABILITY_IAM`); mode B only: `iam:PassRole` on the given role.

  `WSParticipantRole` has all of these except the IAM ones. `sam deploy --guided` also creates its own artifact bucket (stack `aws-sam-cli-managed-default`).
- [ ] **Local tools:** AWS CLI v2, SAM CLI, Python 3.12 on PATH (`sam build` runs without a container), Node 22. Docker is not needed. If you can't install the CLIs system-wide, `pip install awscli aws-sam-cli` in a venv works.

## 1. Amazon Bedrock

- [x] **Model access:** already enabled in the event account. Tested with Converse in `us-east-1`:

  | Role | Used by | Must support | Profile ID (tested) |
  |---|---|---|---|
  | **Fast** | Job 1 check-ins, Job 3 the "why", Job 4 escalations | Converse API | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
  | **Strong** | Job 2 reply reading, Job 5 dispatch agent | Converse API, **tool use** (forced tool choice, multi-turn), **image input** (photo replies), `temperature` | `us.anthropic.claude-sonnet-4-6` |
  | Fallback | Not used by the code yet (P3 TODO in `converse()`) | Same as strong | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (legacy) |

  These are the defaults of the SAM parameters and in `.env.example`. Sonnet 4.6 lists image input; a call with a photo hasn't been tested yet.

  **Don't use these without a code change:**
  - **Haiku 5.5** (`us.` and `global.`): `AccessDeniedException`, "private marketplace eligibility". The event hasn't enabled it.
  - **Sonnet 5.5:** rejects forced tool choice (`toolChoice: {"tool": …}`, used by Job 2's `record_assessment` in `backend/app/bedrock.py`) and `temperature` (sent on every `converse()` call).
  - **Sonnet 5:** rejects `temperature`.
  - **Claude 3 Haiku:** end of life.
- [ ] **Re-check a model answers** (for example after new credentials):
  `aws bedrock-runtime converse --region us-east-1 --model-id <ID> --messages '[{"role":"user","content":[{"text":"hi"}]}]'`
  List all profiles: `aws bedrock list-inference-profiles --region us-east-1 --query "inferenceProfileSummaries[].inferenceProfileId"`.
- [x] **Quotas** (Service Quotas → Amazon Bedrock, `us-east-1`):
  - Cross-region inference: 10,000 requests per minute for each model, and 5M (Haiku 4.5) or 6M (Sonnet 4.6) tokens per minute.
  - ApplyGuardrail: 100 requests per second.

  That is far above the code's peak:
  - check-ins: 10 parallel fast-model calls;
  - "Others reply": 6 parallel × (strong + fast + 2 ApplyGuardrail);
  - escalations: 8 parallel;
  - plus one PII ApplyGuardrail on every model call.

  If calls still throttle, lower `OTHERS_PARALLEL` in `frontend/src/pages/Phone.tsx`.
- Nothing to create by hand for **Guardrails**: the stack creates `stillhere-advice` (denied topic "MedicalAdvice": SMS jobs and reply screening) and `stillhere-pii` (anonymizes names, addresses, phones in traces). Both are used at version DRAFT, and the Lambda gets their IDs automatically.

What the code calls: `bedrock-runtime:Converse` (IAM `bedrock:InvokeModel`, scoped to exactly the configured profiles and the models behind them) and `bedrock:ApplyGuardrail` (on the two guardrails).

### Amazon Location Service (nothing to request; the stack sets it up)

- **Maps (browser):** the API key `stillhere-maps` (`geo-maps:*`, this region). The browser loads Hybrid/Satellite styles with `terrain=Terrain3D` from `maps.geo.us-east-1.amazonaws.com/v2`; in `us-east-1` the Hybrid descriptor returns the `terrainSource` (tested). The key ships in the bundle, so it is public: lock its `AllowReferers` later (§3).
- **Routes (backend):** `geo-routes:OptimizeWaypoints` and `CalculateRoutes` (Car), through the **Lambda role** (or your own credentials locally), no key. Both tested in `us-east-1`. If either fails, `backend/app/location.py` falls back to straight lines, so a routes problem never blocks the plan.
- **Not AWS-account:** without a key, the map uses open terrain tiles from the public AWS Open Data bucket `elevation-tiles-prod`; no setup.

## 2. Deploy the stack

From `infra/`: `sam build && sam deploy --guided` ([README → Deploy](../README.md#deploy)). Stack name `stillhere`, region `us-east-1`. The guided prompts ask for every parameter:
- `BedrockFastModelId`, `BedrockStrongModelId`, `BedrockFallbackModelId`: keep the defaults (the tested IDs in §1).
- Leave `BedrockGuardrailId` and **`LocationApiKey` empty**. The code doesn't read `LocationApiKey`; routes use the Lambda's IAM role.
- `FunctionRoleArn` and `DeployApi` pick the mode below.
- Answer `y` to "ApiFunction has no authentication" (modes A and B).

The answers are saved to `infra/samconfig.toml` (gitignored), so later deploys are `sam build && sam deploy`.

### Pick the mode

| Mode | When | Parameters | What you get |
|---|---|---|---|
| **A. Default** | The organizers allow IAM role creation | `FunctionRoleArn` empty, `DeployApi` `true` | Everything below; the stack creates the Lambda and Scheduler roles |
| **B. Given role** | The organizers provide a role for the Lambda | `FunctionRoleArn` = its ARN, `DeployApi` `true` | Everything below, with no IAM roles created |
| **C. No IAM** | Neither (works in the event account today) | `DeployApi` `false` | Tables, bucket, guardrails and map key only. No Lambda, API or schedule: you run the backend yourself (below) |

**Mode B: what to ask the organizers for.** One IAM role that:
- trusts `lambda.amazonaws.com` and `scheduler.amazonaws.com`;
- allows what `ApiFunction`'s `Policies` in `infra/template.yaml` allow:
  - CRUD on the `stillhere-*` DynamoDB tables;
  - the photos bucket;
  - `bedrock:InvokeModel` and `bedrock:ApplyGuardrail`;
  - `geo-routes:CalculateRoutes` and `geo-routes:OptimizeWaypoints`.

  SAM ignores those `Policies` when a role is given, so the role must carry them itself.
- allows CloudWatch Logs (`AWSLambdaBasicExecutionRole`) and `lambda:InvokeFunction` for the schedule;
- comes with `iam:PassRole` on it for `WSParticipantRole`.

If the role doesn't trust `scheduler.amazonaws.com`, only the 1-minute schedule fails. The demo doesn't need it, because **+3 h** (`POST /clock/advance`) runs the same check.

**Mode C: running the backend yourself.** After the deploy:
1. Copy the stack outputs into `.env` (§4): `BEDROCK_GUARDRAIL_ID`, `BEDROCK_PII_GUARDRAIL_ID`, `PHOTOS_BUCKET`, `VITE_LOCATION_API_KEY`. The table names and model IDs in `.env.example` already match.
2. Start the backend with the event credentials in your shell: `uvicorn app.main:app --port 8000` from `backend/` ([README → Run it locally](../README.md#run-it-locally)). `WSParticipantRole` already has every permission the Lambda role would have.
3. Start the frontend with `npm run dev`, with `VITE_API_URL=http://localhost:8000`.

Limits of mode C:
- There is no public API URL, so an Amplify page can't reach the backend. Record the demo from the laptop running both.
- When the credentials expire, restart `uvicorn` with fresh ones.
- There is no 1-minute schedule (use **+3 h**).

### What the stack creates

| Resource | Detail | Modes |
|---|---|---|
| Lambda `ApiFunction` | Python 3.12, 1024 MB, 30 s; FastAPI + Mangum; seed data and prompts in the package | A, B |
| API Gateway HTTP API | `ANY /{proxy+}`, CORS `*` (lock to the Amplify URL later) | A, B |
| EventBridge Scheduler | `rate(1 minute)`, Input `{"stillhere":"escalation_check"}` (silence check) | A, B |
| IAM | Lambda role: the 8 tables, the bucket, Bedrock (the configured models), ApplyGuardrail (2 guardrails), `geo-routes:OptimizeWaypoints`/`CalculateRoutes`. Plus the Scheduler role | A only |
| DynamoDB ×8, on-demand | `stillhere-residents`, `-outages`, `-cases`, `-messages`, `-plans`, `-traces`, `-events` (key `outage_id` + `sk`), `-config` | all |
| S3 | private reply-photos bucket | all |
| Location API key | `stillhere-maps`: `geo-maps:*` on this region's provider, no expiry (browser map) | all |
| Bedrock Guardrails | `stillhere-advice`, `stillhere-pii` | all |
| CloudWatch Logs | automatic, `/aws/lambda/stillhere-ApiFunction-…` | A, B |

- [ ] **Read the outputs:** `aws cloudformation describe-stacks --stack-name stillhere --query "Stacks[0].Outputs" --output table`
- [ ] **Map key value:** `aws location describe-key --key-name stillhere-maps --query Key --output text`
- [ ] **First check:** `curl <ApiUrl>/health` returns `{"ok":true}`, and `curl <ApiUrl>/hello-bedrock` returns a real reply with the model ID. In mode C, use `http://localhost:8000` instead of `<ApiUrl>`.

## 3. Amplify Hosting (frontend; console, not in the template; modes A and B)

- [ ] **New app** in `us-east-1`, then connect the GitHub repo. This needs someone with admin access on the repo, to authorize the Amplify GitHub App. Open question: the team repo `harbul/Spartan-hack` or the fork? Amplify deploys `main` on every push.
  - Tick **monorepo**, app root **`frontend`** (the build is in `amplify.yml`, Node 22).
- [ ] **Environment variables:**
  - `VITE_API_URL` = the `ApiUrl` output
  - `VITE_LOCATION_API_KEY` = the map key
  - `VITE_LOCATION_REGION` = `us-east-1`
  - leave `VITE_USE_MOCK` unset
- [ ] **Rewrite (SPA)**, so `/phone` and `/run/…` deep links work:
  source `</^[^.]+$|\.(?!(css|gif|ico|jpg|js|mjs|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>`, target `/index.html`, type `200 (Rewrite)`.
- [ ] **If the map is blank** with a MIME-type error on `maplibre-gl-worker-*.mjs`, add a custom header `Content-Type: text/javascript` for `*.mjs`.
- [ ] **After the first deploy:** restrict CORS (`backend/app/main.py`, `infra/template.yaml` `AllowOrigins`) and the map key's `AllowReferers` to the Amplify URL (template TODOs), then redeploy.

## 4. Values to copy (where each one goes)

| Value | From | Into |
|---|---|---|
| Fast, strong and fallback profile IDs | §1 (already the defaults) | SAM parameters; `.env` `BEDROCK_FAST_MODEL_ID`, `BEDROCK_STRONG_MODEL_ID`, `BEDROCK_FALLBACK_MODEL_ID` |
| `ApiUrl` (modes A, B) | stack output | Amplify `VITE_API_URL`; `.env` `VITE_API_URL` (local frontend against the deploy) |
| Map key | `describe-key stillhere-maps` | Amplify and `.env` `VITE_LOCATION_API_KEY` |
| `AdviceGuardrailId`, `PiiGuardrailId` | stack outputs | `.env` `BEDROCK_GUARDRAIL_ID`, `BEDROCK_PII_GUARDRAIL_ID` (local only; the Lambda has them) |
| `PhotosBucketName` | stack output | `.env` `PHOTOS_BUCKET` (local only) |
| Region | `us-east-1` (event rule) | `.env` `AWS_REGION`, `VITE_LOCATION_REGION`, Amplify (already the defaults) |

The table names in `.env.example` (`stillhere-…`) already match the stack. For local runs against the deploy, your own credentials need the same permissions as the Lambda role (DynamoDB, S3, Bedrock, ApplyGuardrail, `geo-routes`); `WSParticipantRole` has them. The backend reads `AWS_REGION`, not `AWS_DEFAULT_REGION`, so keep `AWS_REGION=us-east-1` in `.env`.

## 5. Then: the smoke test and the gate

Continue with [HANDOFF.md §4](HANDOFF.md#4-critical-path-the-aws-gate-do-this-first-in-order), steps 6–8:
1. The README smoke test, including `/plans` (time it, under ~20 s).
2. `python tests/eval_replies.py` at 18/20.
3. 3 clean runs on the Amplify URL (or locally in mode C), then the safety video.

## Cost (small)

Everything is on-demand or pay-per-use; there are no always-on servers. One full golden-path run is roughly:
- **About 150 model calls:** 40 check-ins, about 36 reply assessments and 36 "why"s, about 12 escalation drafts, 5–12 agent turns.
- **About 190 ApplyGuardrail calls.**
- **A few hundred** DynamoDB, Location and Lambda requests.

Bedrock tokens are the main cost. Set a billing alarm if the event account allows it.

## Not used (so you can skip it)

- `LocationApiKey` SAM parameter: not read by the code. Routes use the Lambda role.
- `BedrockFallbackModelId`: has a tested default and is granted in IAM, but used only once P3 adds the retry.
- `VITE_MAPBOX_TOKEN`: only if Amazon Location maps fail (PLAN.md §6 fallback). Not wired.
- Amazon Connect, End User Messaging (real SMS), Bedrock Knowledge Bases: production-path or STRETCH ideas, not in the code.
