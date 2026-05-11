# Dev Guide

DeepEval_Agent is a single FastAPI microservice that evaluates batches of agent runs against per-agent guidelines using DeepEval metrics + a custom Cortex LLM judge. No frontend in this repo — only a JSON API consumed by the pipeline team and the UI team.

```
DeepEval_Agent/
├── app/
│   ├── main.py                       FastAPI entry, /health, mounts router
│   ├── api/
│   │   ├── routes.py                 POST /evaluate (async batch, semaphore=10)
│   │   └── schemas.py                EvaluationRequest, RunPayload, RunResult, EvaluationResponse
│   ├── core/
│   │   ├── config.py                 pydantic-settings — loads .env into `settings`
│   │   └── logger.py                 Singleton session logger
│   ├── llm/
│   │   ├── apim_auth.py              APIMTokenManager — OAuth2 client_credentials, cached + refreshed
│   │   ├── cortex_service.py         CortexAPIService — httpx + token, sync/async, retries, singleton
│   │   ├── cortex_llm.py             CortexAgentChatModel — slim LangChain BaseChatModel
│   │   ├── deepeval_wrapper.py       CortexDeepEvalLLM — DeepEval judge adapter
│   │   └── llm_client.py             Singletons + judge_output() (custom JSON judge)
│   └── evaluation/
│       ├── guidelines.py             AGENT_GUIDELINES registry
│       ├── metric_predictor.py       build_guidelines_metrics() → [GEval, AnswerRelevancyMetric]
│       ├── deepeval_runner.py        Per-metric retry, transient/fatal classification
│       └── result_formatter.py       Format runs, % conversion, PASS/WARN/FAIL/ERROR
├── logs/                             Auto-created, one file per server session
├── .env                              Local secrets (gitignored)
├── .env.example                      Template
├── requirements.txt                  Runtime deps
├── run.py                            uvicorn entry point
├── sample_payload.json               RAG Agent example
├── sample_payload_dxsynth.json       DxSynthesizer example
├── test_api.py                       Hits live server
├── test_evaluate_direct.py           Runs evaluation in-process (best debug tool)
└── test_llm.py                       Cortex LLM connectivity smoke test
```

**Layering rule (informal — no `import-linter` configured):**
`api/routes → evaluation/* → llm/llm_client → llm/deepeval_wrapper → llm/cortex_llm → llm/cortex_service → llm/apim_auth`. Lower layers must not import upper ones. `core/` is leaf — anything may import it.

---

## 1. Setup

```powershell
git clone <repo-url>
cd DeepEval_Agent

py -m venv venv
.\venv\Scripts\activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item .env.example .env
# then fill in APIM_* secrets (see table below)
```

Bash equivalent:

```bash
python -m venv venv
source venv/Scripts/activate    # Linux/Mac: venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### `.env` keys

| Key | Used by | When required |
|---|---|---|
| `APIM_TENANT_ID` | `apim_auth.py` | Always — Azure AD tenant GUID |
| `APIM_CLIENT_ID` | `apim_auth.py` | Always — service principal client ID |
| `APIM_CLIENT_SECRET` | `apim_auth.py` | Always — SP secret |
| `APIM_SCOPE` | `apim_auth.py` | Always — e.g. `api://Cortex.lilly.com/.default` |
| `APIM_TOKEN_URL` | `apim_auth.py` | Optional — defaults to `https://login.microsoftonline.com/{APIM_TENANT_ID}/oauth2/v2.0/token` |
| `CORTEX_AGENT_NAME` | `cortex_llm.py` | Always — Cortex deployment / agent ID (e.g. `dx-congress-agent1`) |
| `CORTEX_OPENAI_BASE` | `cortex_service.py` | Always — gateway URL (dev: `https://gateway.apim-dev.lilly.com/cortex/cortex-openai`) |
| `CORTEX_ENDPOINT_TEMPLATE` | `cortex_llm.py` | Path appended to base. Default: `chat/completions`. `{agent}` is substituted if present. |
| `CORTEX_AGENT_IN_BODY` / `CORTEX_AGENT_BODY_FIELD` | `cortex_llm.py` | If `true`, adds `{<field>: <agent>}` to JSON body. Default field: `model`. |
| `CORTEX_AGENT_IN_HEADER` / `CORTEX_AGENT_HEADER_NAME` | `cortex_llm.py` | If `true`, adds `<header>: <agent>` to request headers. |
| `CORTEX_SEND_API_VERSION` | `cortex_llm.py` | If `true`, appends `?api-version=...` query. Needed for Azure-OpenAI-shaped gateways. |
| `CORTEX_TEMPERATURE` / `CORTEX_MAX_TOKENS` | `cortex_llm.py` | Optional defaults (0.0 / 4096). |
| `PASS_THRESHOLD` / `WARN_THRESHOLD` | `result_formatter.py` | Optional (0.85 / 0.70 — 0–1 scale). |

---

## 2. Run the service

```powershell
.\venv\Scripts\activate.ps1
py run.py
# → http://localhost:8000/docs
```

Endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/evaluate` | Evaluate a batch of runs. Body = `EvaluationRequest`. |
| `GET` | `/health` | `{"status":"ok"}` |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/openapi.json` | OpenAPI schema (generated at runtime; not on disk) |

---

## 3. Test scripts

| File | What it does | When to use |
|---|---|---|
| [test_llm.py](test_llm.py) | Builds `CortexAgentChatModel`, sends one prompt | First step after changing `.env` or `cortex_*` files |
| [test_evaluate_direct.py](test_evaluate_direct.py) | Runs the full evaluate logic in-process (no HTTP) | Best debug tool — full Python tracebacks |
| [test_api.py](test_api.py) | POSTs payloads to a running server on `localhost:8000` | End-to-end check of the live API |

```powershell
.\venv\Scripts\activate.ps1; py test_llm.py
.\venv\Scripts\activate.ps1; py test_evaluate_direct.py
# In a second terminal (after `py run.py` is running):
.\venv\Scripts\activate.ps1; py test_api.py
```

PowerShell does **not** support `&&` — chain with `;`.

---

## 4. How a request flows

```
POST /evaluate  (api/routes.py)
   │
   ├─ Resolve agent guidelines      (evaluation/guidelines.py)
   ├─ Build metrics                 (evaluation/metric_predictor.py)
   ├─ For each run (parallel, semaphore=10, sync work via asyncio.to_thread):
   │     ├─ run_deepeval_metrics()  (evaluation/deepeval_runner.py)
   │     │     └─ DeepEval calls CortexDeepEvalLLM ───┐
   │     └─ judge_output()          (llm/llm_client.py)
   │           └─ CortexAgentChatModel.invoke(...)    │
   │                                                  ▼
   │                                      llm/cortex_llm.py
   │                                            │
   │                                            ▼
   │                                   llm/cortex_service.py  ── singleton
   │                                            │  (httpx + retry + 401-refresh)
   │                                            ▼
   │                                   llm/apim_auth.py       ── singleton
   │                                            │  (cached OAuth bearer)
   │                                            ▼
   │                                   Cortex APIM gateway
   │
   └─ Aggregate → EvaluationResponse  (evaluation/result_formatter.py)
```

**Per-run cost: ~3 LLM calls** (2 metrics + 1 judge).

---

## 5. Adding a new agent

1. Append to `AGENT_GUIDELINES` in [app/evaluation/guidelines.py](app/evaluation/guidelines.py):
   ```python
   AGENT_GUIDELINES["my new agent"] = """\
   1. Rule one ...
   2. Rule two ...
   """
   ```
2. Send `"agent_name": "my new agent"` in the request payload (case-insensitive lookup).
3. No code change needed in routes / metrics / formatter.

---

## 6. Working with `requirements.txt`

This project uses a single flat `requirements.txt` (no `pyproject.toml`, no monorepo):

```
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
langchain
langchain-core
httpx
deepeval
```

| Dep | Why |
|---|---|
| `fastapi`, `uvicorn[standard]` | API + ASGI server |
| `pydantic`, `pydantic-settings` | Request/response models + `.env` loading |
| `python-dotenv` | Loads `.env` for the test scripts |
| `langchain`, `langchain-core` | `BaseChatModel`, `HumanMessage`, `SystemMessage` (no `langchain-openai` — we removed it when ditching cookie/MSAL auth) |
| `httpx` | All Cortex + APIM token HTTP calls |
| `deepeval` | `GEval` + `AnswerRelevancyMetric` |

Adding a new dep: add the line, then `pip install -r requirements.txt`. Removed deps from the cookie/MSAL/AWS era: `msal`, `boto3`, `botocore`, `langchain-openai` — do not re-add unless you're reintroducing those auth modes.

---

## 7. Cortex auth (APIM OAuth2 client-credentials)

We do **not** use cookies, MSAL, or AWS SigV4 anymore. Single auth path:

1. [apim_auth.py](app/llm/apim_auth.py) `APIMTokenManager.get_access_token()`
   - POSTs `grant_type=client_credentials` to the MS v2 token endpoint
   - Caches the token; refreshes 60s before `expires_in`
   - Thread-safe (lock) — safe under the parallel-runs semaphore
2. [cortex_service.py](app/llm/cortex_service.py) `CortexAPIService`
   - Long-lived `httpx.Client` + `httpx.AsyncClient` (connection pooling)
   - Adds `Authorization: Bearer <token>` to every call
   - Retries on 5xx/429 with exponential backoff
   - On 401: invalidates the cached token, fetches a fresh one, retries
3. [cortex_llm.py](app/llm/cortex_llm.py) `CortexAgentChatModel`
   - Builds the OpenAI-style chat-completions payload
   - Uses the configurable endpoint shape from `.env` (so a gateway change = env tweak, not code change)

**Working dev shape (as of last test):**
```env
CORTEX_OPENAI_BASE=https://gateway.apim-dev.lilly.com/cortex/cortex-openai
CORTEX_ENDPOINT_TEMPLATE=chat/completions
CORTEX_AGENT_IN_BODY=true
CORTEX_AGENT_BODY_FIELD=model
CORTEX_AGENT_IN_HEADER=false
CORTEX_SEND_API_VERSION=false
```

---

## 8. Logging

`get_session_logger()` is called once in [app/main.py](app/main.py) at startup. It installs a singleton root logger that writes to `logs/evaluation_session_YYYYMMDD_HHMMSS.log`. Every module-level `logger = logging.getLogger(__name__)` in `app.*`, `deepeval`, and `httpx` flows into the same file.

Tail the latest log while debugging:

```powershell
Get-ChildItem logs\*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content -Wait -Tail 50
```

---

## 9. Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `RuntimeError: APIM token endpoint returned non-JSON response` | `APIM_TENANT_ID` is wrong/placeholder; MS returns a sign-in HTML page | Fix the tenant GUID in `.env` |
| `HTTP 403 — User (...) is not a member of the required groups or roles` | Service principal not authorized for this Cortex agent | Get your platform admin to add the SP's object ID to the right Cortex security group |
| `HTTP 404 — Resource: Model Config with id: model_config_name not found` | `model_config_name` is the literal placeholder. The agent ID isn't being sent where the gateway expects it. | Toggle `CORTEX_AGENT_IN_BODY` / `CORTEX_AGENT_IN_HEADER` / `CORTEX_ENDPOINT_TEMPLATE` until the gateway accepts. The standard OpenAI shape (`model` in body) works on dev. |
| `404 — {"detail":"Not Found"}` | Wrong URL path entirely | Check `CORTEX_OPENAI_BASE` + `CORTEX_ENDPOINT_TEMPLATE` |
| Swagger UI fails on multiline JSON | Control characters in pasted payloads break JSON parsing | Use `test_api.py` with triple-quoted strings, not the browser |
| `ModuleNotFoundError: app` | Running a script from outside the repo root | `cd` to the repo root before running `py test_*.py` |
| Stale `.env` values being picked up | Prior `python -m` session imported the module already | Restart the Python process; `load_dotenv(override=True)` is set in the test scripts but module-level singletons cache settings |
| `asyncio` "Event loop is closed" warnings on Windows | Known interaction between `httpx.AsyncClient` and `ProactorEventLoop` shutdown | Cosmetic — ignore unless it causes failures |
| Cortex 429s under load | Too many parallel runs | Lower `MAX_PARALLEL_RUNS` in [app/api/routes.py](app/api/routes.py) (default 10) |

---

## 10. Quick smoke test before pushing

```powershell
.\venv\Scripts\activate.ps1
py -c "import ast; [ast.parse(open(f).read()) for f in ('app/main.py','app/api/routes.py','app/llm/cortex_llm.py','app/llm/cortex_service.py','app/llm/apim_auth.py','app/llm/llm_client.py','app/evaluation/deepeval_runner.py','app/evaluation/result_formatter.py')]; print('AST OK')"
py test_llm.py
py test_evaluate_direct.py
```

If all three pass, the service is healthy end-to-end.
