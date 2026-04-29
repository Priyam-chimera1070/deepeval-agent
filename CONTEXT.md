# RAG Agent Evaluation Service — Complete Project Context

## What this project is
A backend-only evaluation microservice that receives RAG Agent outputs, evaluates them using guidelines-based approach with DeepEval metrics and an LLM judge, and returns structured JSON results. No UI, no frontend — backend only.

## Team Structure & Responsibilities
This is a team project. There are 3 roles:

- **My role (this service)**: Evaluation backend only — receiving RAG Agent outputs, running guidelines-based LLM evaluation, returning structured results
- **Pipeline team**: Builds the multi-agent runtime, saves logs/traces to S3, retrieves them, and calls my POST /evaluate API. They also integrate my API into CI/CD.
- **UI team**: Builds the dashboard and frontend to visualize the evaluation results my API returns

I do NOT touch the pipeline or the UI. My contract with both teams:
- Input: JSON payload sent by pipeline team to POST /evaluate
- Output: Structured JSON evaluation results

## Original Requirement (what this was built for)
Build an intelligent evaluation API service that:
- Receives RAG Agent outputs from the pipeline team
- Uses guidelines-based evaluation approach
- Runs DeepEval GuidelinesAdherence + AnswerRelevancy metrics
- Uses LLM judge to evaluate against predefined guidelines
- Returns actionable quality results automatically
- Works in automated CI/CD pipeline

## LLM
- Model: Claude (agent name: testing125) via Cortex platform
- Platform: Cortex (internal company AI platform at cortex.lilly.com)
- Auth: Cookie-based for local dev (CORTEX_COOKIE in .env)
- One single LLM instance used for everything — no multiple models
- Confirmed working: temperature=0.7, max_tokens=4096, multimodal=False, auth_mode=cookie

## Tech Stack
- FastAPI — API layer
- DeepEval 3.9.7 — evaluation metrics (GuidelinesAdherence GEval + AnswerRelevancy)
- LangChain — only used for the Cortex wrapper (cortex_llm.py)
- Pydantic 2.13.1 — request/response validation
- httpx — HTTP calls to Cortex platform
- Python 3.12
- uvicorn 0.44.0 — ASGI server

## Project Structure
```
DeepEval_Agent/
├── app/
│   ├── main.py                  # FastAPI app entry point, CORS, includes router
│   ├── api/
│   │   ├── schemas.py           # Pydantic request/response models (simplified)
│   │   └── routes.py            # POST /evaluate — guidelines-only evaluation logic
│   ├── core/
│   │   ├── config.py            # All env vars via pydantic-settings (settings object)
│   │   └── logger.py            # Session logger — one log file per server session
│   ├── llm/
│   │   ├── cortex_llm.py        # Cortex platform LangChain wrapper (CortexAgentChatModel)
│   │   ├── deepeval_wrapper.py  # Bridges Cortex LLM → DeepEval interface (CortexDeepEvalLLM)
│   │   └── llm_client.py        # Singletons + Judge (guidelines-based only)
│   └── evaluation/
│       ├── guidelines.py        # RAG Agent guidelines registry
│       ├── metric_predictor.py  # Builds guidelines metrics (GuidelinesAdherence + AnswerRelevancy)
│       ├── deepeval_runner.py   # Builds LLMTestCase + runs DeepEval metrics
│       └── result_formatter.py  # PASS/WARN/FAIL scoring + final JSON shape
├── logs/                        # Auto-created — one log file per server session
├── .env                         # CORTEX_COOKIE and CORTEX_AGENT_NAME (fill in)
├── .env.example                 # Template
├── requirements.txt
├── run.py                       # Start server: py run.py
├── test_api.py                  # Full API test: health + RAG Agent evaluation tests
├── test_llm.py                  # Direct LLM connection test (no server needed)
└── test_evaluate_direct.py      # Runs full evaluate logic directly (no server, shows tracebacks)
```

## Evaluation Approach — Guidelines Mode Only

The service now uses **only guidelines-based evaluation**:

1. Receives RAG Agent output
2. Loads predefined guidelines from registry
3. Builds fixed metrics: GuidelinesAdherence (GEval) + AnswerRelevancy
4. Runs DeepEval metrics (2 LLM calls)
5. LLM judge evaluates actual output against guidelines (1 LLM call)
6. Returns PASS/WARN/FAIL with scores and actionable feedback

**Total LLM calls: 3 per component** (faster and more precise than previous dual-mode approach)

## RAG Agent Guidelines

The guidelines cover 6 key requirements:
1. **Structure & Completeness** — all 7 sections in order, Key Insights first, min 4 max 8 cards per section
2. **Role Specificity** — strict Medical Affairs vs Development separation
3. **Content Accuracy & Grounding** — no fabrication, sources cited per card
4. **CCG Alignment** — MA full 3-column in Section 4, Dev condensed in Section 6
5. **Confidence & Transparency** — Section 7 must have HIGH/MEDIUM/LOW with rationale
6. **Filter Confirmation** — all 5 filters confirmed before output

## LLM Layer Detail
- cortex_llm.py → CortexAgentChatModel (LangChain BaseChatModel)
  - Fetches agent config from Cortex on init (_fetch_and_apply_config)
  - Supports cookie / MSAL / AWS SigV4 auth modes
  - Cookie auth: calls POST /model/ask/{agent_name} with httpx
  - Has fallback across model_versions if primary fails
- deepeval_wrapper.py → CortexDeepEvalLLM (DeepEval DeepEvalBaseLLM)
  - Thin wrapper so DeepEval metrics can use the same Cortex LLM
- llm_client.py
  - get_llm() → singleton CortexAgentChatModel
  - get_deepeval_llm() → singleton CortexDeepEvalLLM
  - judge_output() → evaluates actual output against guidelines

## Scoring Logic
- overall_score per component = mean(GuidelinesAdherence score + AnswerRelevancy score + judge_score)
- pipeline_score = mean(all component overall_scores)
- PASS: overall_score >= 0.85
- WARN: overall_score >= 0.70
- FAIL: overall_score < 0.70
- Thresholds configurable via PASS_THRESHOLD and WARN_THRESHOLD in .env

## API Endpoints
- POST /evaluate — main evaluation endpoint
- GET /health — returns {"status": "ok"}
- FastAPI docs available at http://localhost:8000/docs when server is running

## Payload Schema

### Request (simplified)
```json
{
  "query_id": "Q123",              
  "timestamp": "ISO_TIMESTAMP",   
  "user_query": "user question",  
  "components": [
    {
      "name": "RAG Agent",        
      "input": "...",              
      "output": "..."             
    }
  ]
}
```

Field notes:
- query_id — optional, auto-generated as "auto-{uuid}" if missing
- user_query — required
- components — array of RAG Agent outputs to evaluate

### Response (simplified)
```json
{
  "query_id": "Q123",
  "pipeline_score": 0.87,
  "pipeline_status": "PASS",
  "timestamp": "...",
  "results": [
    {
      "component_name": "RAG Agent",
      "metrics": {"guidelinesadherence": 0.91, "answerrelevancymetric": 0.88},
      "judge_score": 0.88,
      "judge_confidence": 0.92,
      "judge_reasoning": "...",
      "judge_strengths": ["..."],
      "judge_issues": ["..."],
      "judge_suggestions": ["..."],
      "overall_score": 0.895,
      "status": "PASS"
    }
  ]
}
```

Response field notes:
- metrics — always contains guidelinesadherence + answerrelevancymetric
- judge_confidence — how confident the judge is in its evaluation
- judge_suggestions — actionable fixes for each issue found

## Metrics Used

**Fixed metrics for all evaluations:**
- **GuidelinesAdherence** — GEval with RAG Agent guidelines as criteria (primary metric)
- **AnswerRelevancy** — output directly answers the user query

## Logging
- logs/ folder at project root — auto-created
- app/core/logger.py — get_session_logger() singleton
- One log file per server session: logs/evaluation_session_{timestamp}.log
- All POST /evaluate calls during a session append to the same file
- Logs every step: request received, component details, each step output, final result

## .env Required Values
```
CORTEX_COOKIE=<your_cookie_from_cortex.lilly.com>
CORTEX_AGENT_NAME=<your_claude_agent_name>   # currently: testing125
CORTEX_API_BASE=https://cortex.lilly.com
CORTEX_OPENAI_BASE=https://gateway.apim.lilly.com/cortex/cortex-openai
USE_AWS_AUTH=false
PASS_THRESHOLD=0.85
WARN_THRESHOLD=0.70
```

## Venv & Dependencies
- venv exists at DeepEval_Agent/venv/ — already created and all packages installed
- Activate in PowerShell: .\venv\Scripts\activate.ps1
- PowerShell does NOT support && — use ; instead
- Key installed versions: deepeval==3.9.7, fastapi==0.135.3, langchain==1.2.15, uvicorn==0.44.0, pydantic==2.13.1, httpx==0.28.1, msal==1.30.0, boto3

## Running the Service
```powershell
# Terminal 1 — start server
.\venv\Scripts\activate.ps1; py run.py

# Terminal 2 — run tests
.\venv\Scripts\activate.ps1; py test_api.py

# Test LLM connection only (no server needed)
.\venv\Scripts\activate.ps1; py test_llm.py

# Test full evaluate logic directly with real tracebacks (no server needed)
.\venv\Scripts\activate.ps1; py test_evaluate_direct.py
```

## Key Decisions Made
- **Simplified to guidelines-only approach** — removed standard mode, metric prediction, expected output generation
- **Fixed metrics** — always GuidelinesAdherence + AnswerRelevancy
- **Faster evaluation** — 3 LLM calls per component (down from 4-7)
- **Single agent focus** — optimized for RAG Agent evaluation only
- query_id is optional — auto-generated as "auto-{uuid}" if not provided
- Single LLM instance shared via singleton pattern in llm_client.py
- LangChain is only present because cortex_llm.py depends on it
- GEval metrics require evaluation_params in deepeval 3.9.7+
- Session logger singleton — one log file per server start, all requests in same file
- judge_suggestions added — actionable fixes per issue found
- judge_confidence added — transparency on how reliable the evaluation is

## Known Issues Fixed
- GEval.__init__() missing evaluation_params — deepeval 3.9.7 made it required. Fixed in metric_predictor.py
- FastAPI 500 with no traceback — use test_evaluate_direct.py to debug outside FastAPI
- Cookie expiry — if you get HTTP 302 errors, update CORTEX_COOKIE in .env
- JSON decode error in FastAPI docs — caused by pasting multiline strings with unescaped control characters. Use test_api.py with Python triple-quoted strings instead
- PowerShell does not support && — use ; instead

## Things to Watch During Testing
- Cookie expiry: CortexAgentChatModel fetches agent config on LLM singleton init — will throw 302 immediately if cookie is stale
- GEval metric names come from their name= constructor arg, standard metrics use class name lowercased
- test_evaluate_direct.py is the best debugging tool — shows real tracebacks step by step
- When sending large payloads via FastAPI /docs, avoid actual newlines inside string fields — use test_api.py instead

## Changes from Previous Version
- **Removed**: Standard mode, metric predictor/selector, expected output generator (Role A), all standard DeepEval metrics except AnswerRelevancy
- **Simplified**: Request schema (removed type, category, context, agent_prompt fields), response schema (removed category, evaluation_mode, expected_output fields)
- **Faster**: 3 LLM calls per component instead of 4-7
- **Focused**: Single agent (RAG Agent) with guidelines-based evaluation only
