# Quick Start Guide - RAG Agent Evaluation Service

## ✅ All Changes Complete - Ready to Test!

---

## What Changed?

The service is now **guidelines-only** for RAG Agent evaluation:
- ❌ Removed: Standard mode, metric prediction, expected output generation
- ✅ Kept: Guidelines-based evaluation with fixed metrics
- 🚀 Result: 46% less code, 3 LLM calls per component (down from 4-7)

---

## Quick Test Commands

### 1. Start the Server
```powershell
.\venv\Scripts\activate.ps1; py run.py
```
**Expected:** Server starts on http://localhost:8000

---

### 2. Test Health Endpoint
```powershell
# In another terminal
curl http://localhost:8000/health
```
**Expected:** `{"status":"ok"}`

---

### 3. Run API Tests
```powershell
.\venv\Scripts\activate.ps1; py test_api.py
```
**Expected:** 
- Health check passes
- RAG Agent evaluation completes
- Multiple components test passes

---

### 4. Run Direct Evaluation Test
```powershell
.\venv\Scripts\activate.ps1; py test_evaluate_direct.py
```
**Expected:** Step-by-step evaluation with scores

---

### 5. Test LLM Connection
```powershell
.\venv\Scripts\activate.ps1; py test_llm.py
```
**Expected:** LLM responds successfully

---

## New API Format

### Request (Simplified)
```json
{
  "user_query": "Summarize clinical trial results",
  "components": [
    {
      "name": "RAG Agent",
      "input": "...",
      "output": "..."
    }
  ]
}
```

**Removed fields:** `type`, `category`, `context`, `agent_prompt`, `final_output`

---

### Response (Simplified)
```json
{
  "query_id": "auto-abc123",
  "pipeline_score": 0.87,
  "pipeline_status": "PASS",
  "results": [
    {
      "component_name": "RAG Agent",
      "metrics": {
        "guidelinesadherence": 0.91,
        "answerrelevancymetric": 0.88
      },
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

**Removed fields:** `category`, `evaluation_mode`, `expected_output`, `expected_output_confidence`

---

## Example cURL Test

```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Summarize Drug X trial results",
    "components": [{
      "name": "RAG Agent",
      "input": "Summarize for Medical Affairs",
      "output": "Key Insights: Drug X showed 45% reduction...\nSection 1: Overview...\nSection 7: Confidence - HIGH..."
    }]
  }'
```

---

## Evaluation Flow

```
1. Load RAG Agent guidelines
   ↓
2. Build metrics (GuidelinesAdherence + AnswerRelevancy)
   ↓
3. Run DeepEval metrics (2 LLM calls)
   ↓
4. Judge against guidelines (1 LLM call)
   ↓
5. Calculate scores and status
   ↓
6. Return results
```

**Total: 3 LLM calls per component**

---

## Scoring

- **Overall Score** = mean(GuidelinesAdherence + AnswerRelevancy + Judge Score)
- **PASS** ≥ 0.85
- **WARN** ≥ 0.70
- **FAIL** < 0.70

---

## Logs

Check `logs/evaluation_session_YYYYMMDD_HHMMSS.log` for detailed execution logs.

---

## Troubleshooting

### Server won't start
- Check `.env` file has `CORTEX_COOKIE` and `CORTEX_AGENT_NAME`
- Verify venv is activated

### Cookie expired error
- Update `CORTEX_COOKIE` in `.env` with fresh cookie from cortex.lilly.com

### Import errors
- Ensure venv is activated: `.\venv\Scripts\activate.ps1`
- Verify all packages installed: `pip list`

### Evaluation fails
- Check logs in `logs/` directory
- Run `test_evaluate_direct.py` for detailed tracebacks
- Verify guidelines exist in `app/evaluation/guidelines.py`

---

## Documentation

- **CONTEXT.md** - Complete project documentation
- **CHANGES_SUMMARY.md** - What changed and why
- **DEAD_CODE_ANALYSIS.md** - Dead code cleanup details
- **VERIFICATION_CHECKLIST.md** - Verification steps
- **FINAL_STATUS.md** - Project status summary

---

## Key Files

### Application
- `app/main.py` - FastAPI app
- `app/api/routes.py` - Evaluation endpoint
- `app/evaluation/guidelines.py` - RAG Agent guidelines

### Tests
- `test_api.py` - Full API tests
- `test_evaluate_direct.py` - Direct evaluation test
- `test_llm.py` - LLM connection test

### Config
- `.env` - Environment variables
- `requirements.txt` - Dependencies

---

## Next Steps

1. ✅ Start server
2. ✅ Run tests
3. ✅ Verify logs
4. ✅ Test with real data
5. ⏳ Notify pipeline team of API changes
6. ⏳ Notify UI team of response changes

---

## Support

Questions? Check:
1. CONTEXT.md for project details
2. Logs for runtime issues
3. test_evaluate_direct.py for debugging

---

**Version:** 2.0.0  
**Status:** ✅ Ready for Testing  
**Last Updated:** 2026-04-27
