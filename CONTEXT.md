# RAG / DxSynthesizer Agent Evaluation Service

Backend-only FastAPI microservice (v3.0.0) that evaluates **batches of runs** from a single agent against a per-agent guidelines spec, using DeepEval metrics + a Cortex LLM judge. Pipeline team posts to `POST /evaluate`; UI team consumes the JSON response. No frontend in this repo.

## Tech stack
- **FastAPI** + **uvicorn** — API + ASGI server
- **DeepEval 3.9.7** — `GuidelinesAdherence` (GEval) + `AnswerRelevancyMetric`
- **LangChain** — only used by the Cortex wrapper (`cortex_llm.py`)
- **Pydantic 2** — request/response validation
- **httpx** — Cortex platform calls
- **Python 3.12**, venv at `venv/`

## LLM
- Single Cortex agent (e.g. Claude `testing125`) reached via `cortex.lilly.com`
- Auth modes: cookie (dev), MSAL (Azure AD), AWS SigV4 — auto-selected from env
- One singleton instance shared everywhere via `llm_client.get_llm()` / `get_deepeval_llm()`

## Project structure
```
DeepEval_Agent/
├── app/
│   ├── main.py                       # FastAPI app, CORS, /health, mounts router
│   ├── api/
│   │   ├── routes.py                 # POST /evaluate — async batch w/ Semaphore(MAX_PARALLEL_RUNS=10)
│   │   └── schemas.py                # EvaluationRequest{agent_name?, evaluation_id?, runs[]}, RunPayload, RunResult, EvaluationResponse
│   ├── core/
│   │   ├── config.py                 # pydantic-settings (Cortex URLs, pass/warn thresholds)
│   │   └── logger.py                 # Singleton session logger → logs/evaluation_session_{ts}.log
│   ├── llm/
│   │   ├── cortex_llm.py             # CortexAgentChatModel (LangChain BaseChatModel) — agent config fetch, model_versions fallback, cookie/MSAL/AWS, tools + structured output
│   │   ├── deepeval_wrapper.py       # CortexDeepEvalLLM — thin DeepEvalBaseLLM adapter
│   │   └── llm_client.py             # Singletons + judge_output() (3-attempt retry, robust JSON parsing, humanized errors)
│   └── evaluation/
│       ├── guidelines.py             # AGENT_GUIDELINES dict — keys: "rag agent", "dxsynthesizer"
│       ├── metric_predictor.py       # build_guidelines_metrics() → fixed [GuidelinesAdherence GEval, AnswerRelevancyMetric] (threshold=0.5)
│       ├── deepeval_runner.py        # run_deepeval_metrics() — per-metric 3-attempt retry, transient/fatal classification, humanized errors → (scores, errors)
│       └── result_formatter.py       # format_run_result / format_error_run / format_final_response — converts to percentages, assigns PASS/WARN/FAIL/ERROR
├── logs/                             # Auto-created, one file per server session
├── .env                              # CORTEX_COOKIE, CORTEX_AGENT_NAME, etc.
├── requirements.txt
├── run.py                            # uvicorn entry point
├── sample_payload.json               # RAG Agent example (5 runs)
├── sample_payload_dxsynth.json       # DxSynthesizer example (50 runs)
├── test_api.py                       # Hits live server with 1-run + 2-run payloads
├── test_evaluate_direct.py           # Runs evaluate logic in-process (real tracebacks)
└── test_llm.py                       # Cortex LLM connectivity check
```

## Evaluation flow (per request)
1. Resolve `agent_name` (defaults to `"RAG Agent"`); load guidelines from registry once.
2. Build metrics once: `[GEval(GuidelinesAdherence, threshold=0.5), AnswerRelevancyMetric]`.
3. Process up to `MAX_PARALLEL_RUNS=10` runs concurrently (asyncio + semaphore; sync DeepEval calls offloaded via `asyncio.to_thread`):
   - Run DeepEval metrics → 2 LLM calls (with 3-attempt retry on transient failures)
   - Run `judge_output()` → 1 LLM call (with 3-attempt retry, robust JSON parse fallback)
   - Format result; status from `overall_score` (% scale)
4. Aggregate: `average_score` is mean of `overall_score` across **successful** runs only.

**~3 LLM calls per run.**

## Status thresholds (config: `pass_threshold=0.85`, `warn_threshold=0.70`)
- `PASS`  ≥ 85
- `WARN`  ≥ 70
- `FAIL`  < 70
- `ERROR` — run crashed entirely

## Request schema (`POST /evaluate`)
```json
{
  "agent_name": "RAG Agent",                        // optional; default "RAG Agent"
  "evaluation_id": "eval-xyz",                      // optional; auto-generated as eval-{8hex}
  "timestamp": "2026-04-28T10:30:00Z",              // optional
  "runs": [
    {
      "run_id": "run-001",                          // optional; auto-generated as run-{idx:03d}
      "timestamp": "2026-04-28T10:15:22Z",          // optional
      "user_query": "Summarize Drug X trial results",
      "input": "Summarize for Medical Affairs",
      "output": "Key Insights: ...\nSection 1: ..."
    }
  ]
}
```

## Response schema
```json
{
  "evaluation_id": "eval-xyz",
  "agent_name": "RAG Agent",
  "timestamp": "...",
  "total_runs": 5,
  "successful_runs": 4,
  "failed_runs": 1,
  "average_score": 87.4,
  "average_status": "PASS",
  "runs": [
    {
      "run_id": "run-001",
      "timestamp": "...",
      "user_query": "...",
      "metrics": { "guidelinesadherence": 91.0, "answerrelevancymetric": 88.0 },   // percentages, null if metric failed
      "metric_errors": { "answerrelevancymetric": "The evaluator LLM call timed out..." },  // only present per failed metric
      "judge_score": 88.0,
      "judge_confidence": 92.0,
      "judge_reasoning": "...",
      "judge_strengths": ["..."],
      "judge_issues": ["..."],
      "judge_suggestions": ["..."],
      "judge_error": null,                          // human-readable if judge failed
      "overall_score": 89.0,
      "status": "PASS",
      "error": null                                 // only set if entire run failed (status="ERROR")
    }
  ]
}
```

**Important:** all scores in the response are **percentages (0–100)**, even though internal thresholds in `config.py` are stored as 0–1.

## Agents in the registry
- `"rag agent"` — 6-rule spec (structure, role specificity, grounding, CCG alignment, confidence, filter confirmation)
- `"dxsynthesizer"` — strict 9-section congress-brief spec with hard-fail rules, citation discipline, role-aware track ordering

Look up via `get_guidelines(agent_name)` (case-insensitive). Adding a new agent = add an entry to `AGENT_GUIDELINES` in `app/evaluation/guidelines.py`.

## Error handling
Every failure path produces a humanized message (cookie expired, JSON parse failure, 429/5xx, timeouts, network errors). Three layers:
- **Per metric** — `deepeval_runner._humanize_metric_error()`
- **Per judge call** — `llm_client._humanize_llm_error()`
- **Per run** — `routes._humanize_run_error()`

## Logging
- `app/core/logger.py` installs a singleton root logger at startup (`get_session_logger()` is called from `main.py`).
- One file per server session: `logs/evaluation_session_YYYYMMDD_HHMMSS.log`
- All module loggers (`app.*`, `deepeval`, `httpx`) flow into the same file.

## .env
```
CORTEX_COOKIE=<paste fresh cookie from cortex.lilly.com>
CORTEX_AGENT_NAME=testing125
CORTEX_API_BASE=https://cortex.lilly.com
CORTEX_OPENAI_BASE=https://gateway.apim.lilly.com/cortex/cortex-openai
USE_AWS_AUTH=false
PASS_THRESHOLD=0.85
WARN_THRESHOLD=0.70
```

## Running
PowerShell does **not** support `&&` — use `;`.
```powershell
# Start server (terminal 1)
.\venv\Scripts\activate.ps1; py run.py

# API tests against running server (terminal 2)
.\venv\Scripts\activate.ps1; py test_api.py

# Direct evaluation (no server, full tracebacks — best debug tool)
.\venv\Scripts\activate.ps1; py test_evaluate_direct.py

# LLM connectivity only
.\venv\Scripts\activate.ps1; py test_llm.py
```

Server listens on `http://localhost:8000`. Swagger UI at `/docs`. Raw OpenAPI at `/openapi.json` (no static yaml/json file on disk — generated at runtime by FastAPI).

## Endpoints
- `POST /evaluate` — main evaluation endpoint
- `GET /health` — `{"status": "ok"}`

## Common gotchas
- **Cookie expiry** — `CortexAgentChatModel` fetches agent config on singleton init; HTTP 302 means refresh `CORTEX_COOKIE`.
- **GEval requires `evaluation_params`** in DeepEval ≥ 3.9.7 (already set).
- **Don't paste multiline strings into Swagger UI** — control characters break JSON parsing. Use `test_api.py` with triple-quoted strings instead.
- **Concurrency** — `MAX_PARALLEL_RUNS=10`. Lower if you see Cortex 429s; raise cautiously.
