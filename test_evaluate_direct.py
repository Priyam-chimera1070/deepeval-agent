"""
Direct evaluation test — no server needed.
Runs the full evaluate logic step by step with real tracebacks.
Best tool for debugging errors.
Run: .\\venv\\Scripts\\activate.ps1; py test_evaluate_direct.py
"""
from dotenv import load_dotenv
load_dotenv(override=True)

from app.evaluation.metric_predictor import build_guidelines_metrics
from app.evaluation.deepeval_runner import run_deepeval_metrics
from app.evaluation.result_formatter import format_run_result, format_error_run, format_final_response
from app.evaluation.guidelines import get_guidelines
from app.llm.llm_client import judge_output, get_deepeval_llm
import json

AGENT_NAME = "RAG Agent"
RUNS = [
    {
        "run_id": "run-001",
        "user_query": "Summarize the clinical trial results for Drug X",
        "input": "Summarize clinical trial results for Drug X for Medical Affairs",
        "output": """Key Insights: Drug X showed 45% reduction in primary endpoint.
Section 1: Overview - Drug X Phase 3 trial enrolled 1200 patients.
Section 2: Efficacy - Primary endpoint met with p<0.001.
Section 3: Safety - Well tolerated, 12% adverse events.
Section 4: Medical Affairs CCG - Full 3-column format: Indication | Evidence | Recommendation.
Section 5: Development Summary - Condensed pipeline status.
Section 6: Development CCG - Condensed format for pipeline team.
Section 7: Confidence - HIGH confidence based on Phase 3 data. MEDIUM for subgroup analysis. LOW for long-term outcomes.
Filters confirmed: Indication=Oncology, Phase=3, Role=Medical Affairs, Region=US, Year=2024."""
    }
]

print("=== Direct Evaluation Test (Multi-Run, Guidelines Mode) ===\n")

guidelines = get_guidelines(AGENT_NAME)
if not guidelines:
    print(f"ERROR: Guidelines not found for agent: {AGENT_NAME}!")
    exit(1)

deepeval_llm = get_deepeval_llm()
metrics = build_guidelines_metrics(guidelines, deepeval_llm)
print("Metrics built: GuidelinesAdherence + AnswerRelevancy\n")

run_results = []

for idx, run in enumerate(RUNS, start=1):
    run_id = run.get("run_id") or f"run-{idx:03d}"
    print(f"--- Run: {run_id} ---")

    try:
        print("Running DeepEval metrics...")
        deepeval_scores, deepeval_errors = run_deepeval_metrics(
            user_query=run["user_query"],
            actual_output=run["output"],
            metrics=metrics,
        )
        print(f"DeepEval scores: {deepeval_scores}")
        if deepeval_errors:
            print(f"DeepEval errors: {deepeval_errors}")

        print("Running judge...")
        judge_result = judge_output(
            user_query=run["user_query"],
            component_name=AGENT_NAME,
            actual_output=run["output"],
            guidelines=guidelines,
        )
        print(f"Judge score: {judge_result['score']} | Confidence: {judge_result['confidence']}")

        result = format_run_result(
            run_id=run_id,
            user_query=run["user_query"],
            deepeval_metrics=deepeval_scores,
            metric_errors=deepeval_errors,
            judge_score=judge_result["score"],
            judge_confidence=judge_result["confidence"],
            judge_reasoning=judge_result["reasoning"],
            judge_strengths=judge_result["strengths"],
            judge_issues=judge_result["issues"],
            judge_suggestions=judge_result["suggestions"],
        )
        print(f"\nResult:\n{json.dumps(result, indent=2)}\n")
        run_results.append(result)

    except Exception as e:
        print(f"RUN FAILED: {e}")
        run_results.append(format_error_run(run_id, run["user_query"], str(e)))

final = format_final_response("direct-test", AGENT_NAME, run_results)
print(f"Average Score: {final['average_score']}% | Status: {final['average_status']}")
print(f"Successful: {final['successful_runs']}/{final['total_runs']} | Failed: {final['failed_runs']}")
print("\n=== Direct Evaluation Test COMPLETE ===")
