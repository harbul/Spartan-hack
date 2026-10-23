# AWS setup checklist

> Every AWS thing StillHere needs, taken from the code (`infra/template.yaml`, the boto3 calls in `backend/app/`, the env vars, `amplify.yml`, the frontend map).
> Work through it top to bottom when credentials arrive. Owner: **P2** (P3 on Bedrock). It covers steps 1–5 of [HANDOFF.md §4](HANDOFF.md#4-critical-path-the-aws-gate-do-this-first-in-order).
> Most of it is created by one `sam deploy`. By hand you do only: model access, Amplify, and copying a few values.

## 0. Pre-flight (do before anything else)

- [ ] **Services allowed in the event account (R6).** Event accounts are often restricted. Confirm we can use all of these, or find out which are blocked: **Amazon Bedrock (incl. Guardrails), Amazon Location Service, Lambda, API Gateway, DynamoDB, S3, EventBridge Scheduler, CloudFormation, IAM role creation, AWS Amplify**.
- [ ] **Region: `us-west-2`** unless the event says otherwise. Everything must be in one region. If it changes, update `AWS_REGION` and `VITE_LOCATION_REGION`, and record it in PROGRESS.md.
- [ ] **Deployer permissions:** the person running `sam deploy` needs:
  - CloudFormation;
  - IAM (create roles for the Lambda and the Scheduler; `CAPABILITY_IAM`);
  - Lambda, API Gateway v2 (HTTP API), DynamoDB, S3, EventBridge Scheduler and CloudWatch Logs;
  - Bedrock `CreateGuardrail`;
  - Location `CreateKey`.

  `sam deploy --guided` also creates its own artifact bucket (stack `aws-sam-cli-managed-default`).
- [ ] **Local tools:** AWS CLI v2, SAM CLI, Python 3.12 on PATH (`sam build` runs without a container), Node 22. Docker is not needed.
- [ ] `aws configure`, then check it with `aws sts get-caller-identity` (it should print the event account).

## 1. Amazon Bedrock (the critical one; ask for access first, it can be slow)

- [ ] **Model access** (console → Amazon Bedrock → Model access). Request two Anthropic Claude models; the first Anthropic request needs the one-time use-case form.

  | Role | Used by | Must support |
  |---|---|---|
  | **Fast** (Haiku tier) | Job 1 check-ins, Job 3 the "why", Job 4 escalations | Converse API |
  | **Strong** (Sonnet tier) | Job 2 reply reading, Job 5 dispatch agent | Converse API, **tool use** (forced tool choice, multi-turn), **image input** (photo replies) |

- [ ] **Find the inference profile IDs** (use these, not the plain model IDs):
  `aws bedrock list-inference-profiles --region us-west-2 --query "inferenceProfileSummaries[].inferenceProfileId"`
  You want the two `us.anthropic.…` IDs for the models you were granted.
- [ ] **Check they answer** before deploying:
  `aws bedrock-runtime converse --region us-west-2 --model-id <ID> --messages '[{"role":"user","content":[{"text":"hi"}]}]'`
- [ ] **Quotas** (Service Quotas → Amazon Bedrock): on-demand requests and tokens per minute for both models, and ApplyGuardrail throughput. Peak load comes from the code's parallelism:
  - check-ins: 10 parallel fast-model calls;
  - "Others reply": 6 parallel × (strong + fast + 2 ApplyGuardrail);
  - escalations: 8 parallel;
  - plus one PII ApplyGuardrail on every model call.

  If calls throttle, request an increase or lower `OTHERS_PARALLEL` in `frontend/src/pages/Phone.tsx`.
- Nothing to create by hand for **Guardrails**: the stack creates `stillhere-advice` (denied topic "MedicalAdvice": SMS jobs and reply screening) and `stillhere-pii` (anonymizes names, addresses, phones in traces). Both are used at version DRAFT, and the Lambda gets their IDs automatically.
- Optional: `BedrockFallbackModelId` (another Claude tier or Amazon Nova, PLAN.md §16). The template already grants access to it, but **the code doesn't use it yet** (P3 TODO in `converse()`).

What the code calls: `bedrock-runtime:Converse` (IAM `bedrock:InvokeModel`, scoped to exactly the configured profiles and the models behind them) and `bedrock:ApplyGuardrail` (on the two guardrails).

### Amazon Location Service (nothing to request; the stack sets it up)

- **Maps (browser):** the API key `stillhere-maps` (`geo-maps:*`, this region). The browser loads Hybrid/Satellite styles with `terrain=Terrain3D` from `maps.geo.us-west-2.amazonaws.com/v2`. The key ships in the bundle, so it is public: lock its `AllowReferers` later (§3).
- **Routes (backend):** `geo-routes:OptimizeWaypoints` and `CalculateRoutes` (Car), through the **Lambda role**, no key. If either fails, `backend/app/location.py` falls back to straight lines, so a routes problem never blocks the plan.
- **Not AWS-account:** without a key, the map uses open terrain tiles from the public AWS Open Data bucket `elevation-tiles-prod`; no setup.

## 2. Deploy the stack (creates almost everything)

- [ ] From `infra/`: `sam build && sam deploy --guided` ([README → Deploy](../README.md#deploy)).
  - Stack name `stillhere`, region `us-west-2`.
  - `BedrockFastModelId` and `BedrockStrongModelId`: the two profile IDs.
  - Leave `BedrockFallbackModelId`, `BedrockGuardrailId` and **`LocationApiKey` empty**. The code doesn't read `LocationApiKey`; routes use the Lambda's IAM role.
  - Answer `y` to "ApiFunction has no authentication".

  What it creates:

  | Resource | Detail |
  |---|---|
  | Lambda `ApiFunction` | Python 3.12, 1024 MB, 30 s; FastAPI + Mangum; seed data and prompts in the package |
  | API Gateway HTTP API | `ANY /{proxy+}`, CORS `*` (lock to the Amplify URL later) |
  | DynamoDB ×8, on-demand | `stillhere-residents`, `-outages`, `-cases`, `-messages`, `-plans`, `-traces`, `-events` (key `outage_id` + `sk`), `-config` |
  | S3 | private reply-photos bucket |
  | EventBridge Scheduler | `rate(1 minute)`, Input `{"stillhere":"escalation_check"}` (silence check) |
  | Location API key | `stillhere-maps`: `geo-maps:*` on this region's provider, no expiry (browser map) |
  | Bedrock Guardrails | `stillhere-advice`, `stillhere-pii` |
  | IAM | Lambda role: the 8 tables, the bucket, Bedrock (the configured models), ApplyGuardrail (2 guardrails), `geo-routes:OptimizeWaypoints`/`CalculateRoutes`. Plus the Scheduler role |
  | CloudWatch Logs | automatic, `/aws/lambda/stillhere-ApiFunction-…` |

- [ ] **Read the outputs:** `aws cloudformation describe-stacks --stack-name stillhere --query "Stacks[0].Outputs" --output table`
- [ ] **Map key value:** `aws location describe-key --key-name stillhere-maps --query Key --output text`
- [ ] **First check:** `curl <ApiUrl>/health` returns `{"ok":true}`, and `curl <ApiUrl>/hello-bedrock` returns a real reply with the model ID.

## 3. Amplify Hosting (frontend; console, not in the template)

- [ ] **New app**, then connect the GitHub repo. Open question: the team repo `harbul/Spartan-hack` or the fork? Amplify deploys `main` on every push.
  - Tick **monorepo**, app root **`frontend`** (the build is in `amplify.yml`, Node 22).
- [ ] **Environment variables:**
  - `VITE_API_URL` = the `ApiUrl` output
  - `VITE_LOCATION_API_KEY` = the map key
  - `VITE_LOCATION_REGION` = `us-west-2`
  - leave `VITE_USE_MOCK` unset
- [ ] **Rewrite (SPA)**, so `/phone` and `/run/…` deep links work:
  source `</^[^.]+$|\.(?!(css|gif|ico|jpg|js|mjs|png|txt|svg|woff|woff2|ttf|map|json|webp)$)([^.]+$)/>`, target `/index.html`, type `200 (Rewrite)`.
- [ ] **If the map is blank** with a MIME-type error on `maplibre-gl-worker-*.mjs`, add a custom header `Content-Type: text/javascript` for `*.mjs`.
- [ ] **After the first deploy:** restrict CORS (`backend/app/main.py`, `infra/template.yaml` `AllowOrigins`) and the map key's `AllowReferers` to the Amplify URL (template TODOs), then redeploy.

## 4. Values to copy (where each one goes)

| Value | From | Into |
|---|---|---|
| Fast and strong profile IDs | `list-inference-profiles` | SAM parameters; `.env` `BEDROCK_FAST_MODEL_ID`, `BEDROCK_STRONG_MODEL_ID` |
| `ApiUrl` | stack output | Amplify `VITE_API_URL`; `.env` `VITE_API_URL` (local frontend against the deploy) |
| Map key | `describe-key stillhere-maps` | Amplify and `.env` `VITE_LOCATION_API_KEY` |
| `AdviceGuardrailId`, `PiiGuardrailId` | stack outputs | `.env` `BEDROCK_GUARDRAIL_ID`, `BEDROCK_PII_GUARDRAIL_ID` (local only; the Lambda has them) |
| `PhotosBucketName` | stack output | `.env` `PHOTOS_BUCKET` (local only) |
| Region | your choice | `.env` `AWS_REGION`, `VITE_LOCATION_REGION`, Amplify |

The table names in `.env.example` (`stillhere-…`) already match the stack. For local runs against the deploy, your own credentials need the same permissions as the Lambda role (DynamoDB, S3, Bedrock, ApplyGuardrail, `geo-routes`).

## 5. Then: the smoke test and the gate

Continue with [HANDOFF.md §4](HANDOFF.md#4-critical-path-the-aws-gate-do-this-first-in-order), steps 6–8:
1. The README smoke test, including `/plans` (time it, under ~20 s).
2. `python tests/eval_replies.py` at 18/20.
3. 3 clean runs on the Amplify URL, then the safety video.

## Cost (small)

Everything is on-demand or pay-per-use; there are no always-on servers. One full golden-path run is roughly:
- **About 150 model calls:** 40 check-ins, about 36 reply assessments and 36 "why"s, about 12 escalation drafts, 5–12 agent turns.
- **About 190 ApplyGuardrail calls.**
- **A few hundred** DynamoDB, Location and Lambda requests.

Bedrock tokens are the main cost. Set a billing alarm if the event account allows it.

## Not used (so you can skip it)

- `LocationApiKey` SAM parameter: not read by the code. Routes use the Lambda role.
- `BedrockFallbackModelId`: granted in IAM, but used only once P3 adds the retry.
- `VITE_MAPBOX_TOKEN`: only if Amazon Location maps fail (PLAN.md §6 fallback). Not wired.
- Amazon Connect, End User Messaging (real SMS), Bedrock Knowledge Bases: production-path or STRETCH ideas, not in the code.
