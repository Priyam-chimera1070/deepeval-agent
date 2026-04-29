import asyncio
import uuid
from fastapi import APIRouter, HTTPException
from app.api.schemas import EvaluationRequest, EvaluationResponse
from app.evaluation.metric_predictor import build_guidelines_metrics
from app.evaluation.deepeval_runner import run_deepeval_metrics
from app.evaluation.result_formatter import format_run_result, format_error_run, format_final_response
from app.evaluation.guidelines import get_guidelines
from app.llm.llm_client import judge_output, get_deepeval_llm
from app.core.logger import get_session_logger

router = APIRouter()

# Hardcoded for now — change here when evaluating a different agent
DEFAULT_AGENT_NAME = "RAG Agent"

# Bounded concurrency for per-run evaluation. Tune based on Cortex tolerance.
# 5 = safe default. Raise to 8–10 if you observe no 429s / disconnects.
MAX_PARALLEL_RUNS = 10


def _humanize_run_error(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc)
    low = msg.lower()
    if "timeout" in low or "timed out" in low:
        return "Evaluation could not complete because an LLM call timed out."
    if "302" in msg or "cookie" in low or "redirect" in low:
        return "Evaluation aborted: Cortex authentication failed (cookie expired or invalid)."
    if "429" in msg or ("rate" in low and "limit" in low):
        return "Evaluation aborted: rate limit hit on the evaluator LLM."
    if any(code in msg for code in ("500", "502", "503", "504")):
        return "Evaluation aborted: the evaluator LLM service returned a server error."
    if "connection" in low or "network" in low:
        return "Evaluation aborted: network error contacting the evaluator LLM."
    return f"Evaluation failed unexpectedly ({name}). See server logs for details."


@router.post("/evaluate", response_model=EvaluationResponse, summary="Evaluate multiple runs of a single agent using guidelines")
async def evaluate(request: EvaluationRequest):
    logger = get_session_logger()

    if not request.evaluation_id:
        request.evaluation_id = f"eval-{uuid.uuid4().hex[:8]}"

    agent_name = request.agent_name or DEFAULT_AGENT_NAME

    logger.info(
        f"REQUEST RECEIVED | evaluation_id={request.evaluation_id} | agent={agent_name} | runs={len(request.runs)}"
    )

    # Load guidelines once for the entire batch (single agent)
    guidelines = get_guidelines(agent_name)
    if not guidelines:
        raise HTTPException(
            status_code=500,
            detail=f"Guidelines not found in registry for agent: '{agent_name}'",
        )

    deepeval_llm = get_deepeval_llm()
    # Build metrics once and reuse across all runs (same agent, same guidelines)
    metrics = build_guidelines_metrics(guidelines, deepeval_llm)

    semaphore = asyncio.Semaphore(MAX_PARALLEL_RUNS)

    async def _process_single_run(idx: int, run):
        run_id = run.run_id or f"run-{idx:03d}"
        async with semaphore:
            try:
                logger.info(f"RUN START | run_id={run_id}")

                # deepeval + judge are sync/blocking — offload to threads so
                # bounded parallelism actually overlaps the network waits.
                deepeval_scores, deepeval_errors = await asyncio.to_thread(
                    run_deepeval_metrics,
                    run.user_query,
                    run.output,
                    metrics,
                )
                logger.info(f"DEEPEVAL SCORES | run_id={run_id} | {deepeval_scores}")
                if deepeval_errors:
                    logger.warning(f"DEEPEVAL METRIC ERRORS | run_id={run_id} | {deepeval_errors}")

                judge_result = await asyncio.to_thread(
                    judge_output,
                    run.user_query,
                    agent_name,
                    run.output,
                    guidelines,
                )
                logger.info(
                    f"JUDGE | run_id={run_id} | score={judge_result['score']} | confidence={judge_result['confidence']}"
                )

                result = format_run_result(
                    run_id=run_id,
                    user_query=run.user_query,
                    deepeval_metrics=deepeval_scores,
                    metric_errors=deepeval_errors,
                    judge_score=judge_result["score"],
                    judge_confidence=judge_result["confidence"],
                    judge_reasoning=judge_result["reasoning"],
                    judge_strengths=judge_result["strengths"],
                    judge_issues=judge_result["issues"],
                    judge_suggestions=judge_result["suggestions"],
                    judge_error=judge_result.get("error"),
                    timestamp=run.timestamp,
                )
                logger.info(
                    f"RUN DONE | run_id={run_id} | overall_score={result['overall_score']} | status={result['status']}"
                )
                return idx, result

            except Exception as e:
                logger.error(f"RUN FAILED | run_id={run_id} | error={str(e)}", exc_info=True)
                return idx, format_error_run(
                    run_id=run_id,
                    user_query=run.user_query,
                    error=_humanize_run_error(e),
                    timestamp=run.timestamp,
                )

    tasks = [
        _process_single_run(idx, run)
        for idx, run in enumerate(request.runs, start=1)
    ]
    completed = await asyncio.gather(*tasks)
    # Preserve original input order
    completed.sort(key=lambda pair: pair[0])
    run_results = [result for _, result in completed]

    response = format_final_response(
        evaluation_id=request.evaluation_id,
        agent_name=agent_name,
        run_results=run_results,
        timestamp=request.timestamp,
    )
    logger.info(
        f"REQUEST COMPLETE | evaluation_id={request.evaluation_id} | "
        f"average_score={response['average_score']} | status={response['average_status']} | "
        f"successful={response['successful_runs']}/{response['total_runs']}"
    )
    return response
