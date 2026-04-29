from typing import Optional
from app.core.config import settings


def determine_status(score_percent: float) -> str:
    """Status thresholds are stored as 0-1 in settings; convert to percentage for comparison."""
    if score_percent >= settings.pass_threshold * 100:
        return "PASS"
    if score_percent >= settings.warn_threshold * 100:
        return "WARN"
    return "FAIL"


def _to_percent(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    return round(float(value) * 100, 2)


def format_run_result(
    run_id: str,
    user_query: str,
    deepeval_metrics: dict,
    judge_score: float,
    judge_confidence: float,
    judge_reasoning: str,
    judge_strengths: list,
    judge_issues: list,
    judge_suggestions: list,
    timestamp: Optional[str] = None,
    metric_errors: Optional[dict] = None,
    judge_error: Optional[str] = None,
) -> dict:
    metrics_pct = {k: _to_percent(v) for k, v in deepeval_metrics.items()}
    judge_score_pct = _to_percent(judge_score) or 0.0

    all_scores = [v for v in metrics_pct.values() if v is not None]
    all_scores.append(judge_score_pct)
    overall_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0

    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "user_query": user_query,
        "metrics": metrics_pct,
        "metric_errors": metric_errors or {},
        "judge_score": judge_score_pct,
        "judge_confidence": _to_percent(judge_confidence) or 0.0,
        "judge_reasoning": judge_reasoning,
        "judge_strengths": judge_strengths,
        "judge_issues": judge_issues,
        "judge_suggestions": judge_suggestions,
        "judge_error": judge_error,
        "overall_score": overall_score,
        "status": determine_status(overall_score),
    }


def format_error_run(run_id: str, user_query: str, error: str, timestamp: Optional[str] = None) -> dict:
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "user_query": user_query,
        "metrics": {},
        "metric_errors": {},
        "judge_score": None,
        "judge_confidence": None,
        "judge_reasoning": None,
        "judge_strengths": [],
        "judge_issues": [],
        "judge_suggestions": [],
        "judge_error": None,
        "overall_score": None,
        "status": "ERROR",
        "error": error,
    }


def format_final_response(
    evaluation_id: str,
    agent_name: str,
    run_results: list,
    timestamp: Optional[str] = None,
) -> dict:
    successful = [r for r in run_results if r["status"] != "ERROR" and r.get("overall_score") is not None]
    failed_count = len(run_results) - len(successful)

    if successful:
        average_score = round(sum(r["overall_score"] for r in successful) / len(successful), 2)
    else:
        average_score = 0.0

    return {
        "evaluation_id": evaluation_id,
        "agent_name": agent_name,
        "timestamp": timestamp,
        "total_runs": len(run_results),
        "successful_runs": len(successful),
        "failed_runs": failed_count,
        "average_score": average_score,
        "average_status": determine_status(average_score),
        "runs": run_results,
    }
