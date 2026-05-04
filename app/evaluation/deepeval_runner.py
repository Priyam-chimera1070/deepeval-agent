import logging
import time
from typing import List, Tuple
from deepeval.test_case import LLMTestCase

logger = logging.getLogger(__name__)

# Retry policy for transient evaluator-LLM failures inside DeepEval metrics.
# JSON-parse errors are NOT retried (deterministic prompt issue).
METRIC_MAX_ATTEMPTS = 3
METRIC_BACKOFF_SECONDS = (1.0, 2.0)  # waits before attempts 2 and 3


def _is_transient_metric_error(exc: Exception) -> bool:
    """Return True if the exception is the kind that often resolves on retry."""
    msg = str(exc).lower()
    name = type(exc).__name__.lower()
    transient_markers = (
        "timeout", "timed out", "connection", "network", "disconnect",
        "reset", "ssl", "429", "500", "502", "503", "504",
        "rate limit", "server disconnected", "remote end closed",
    )
    if any(m in msg for m in transient_markers):
        return True
    if any(m in name for m in ("timeout", "connection", "network")):
        return True
    # Non-transient: JSON parse / validation errors mean the LLM responded
    # but in the wrong shape — retrying usually won't fix it.
    if "json" in msg or "expecting value" in msg or "validation" in msg or "pydantic" in msg:
        return False
    # Default: retry on generic Exception too (safest for "failed unexpectedly").
    return True


def _humanize_metric_error(exc: Exception) -> str:
    """
    Translate raw exception text into a UI-friendly reason that explains
    WHY the metric could not produce a score.
    """
    name = type(exc).__name__
    msg = str(exc)
    low = msg.lower()

    if "json" in low or "expecting value" in low or "decode" in low:
        return (
            "The evaluator LLM returned a response that could not be parsed as valid JSON, "
            "so a numeric score could not be extracted."
        )
    if "timeout" in low or "timed out" in low:
        return "The evaluator LLM call timed out before a score could be returned."
    if "401" in msg or "unauthorized" in low or "token" in low:
        return "Authentication with the Cortex APIM gateway failed (check APIM_CLIENT_ID / APIM_CLIENT_SECRET / APIM_SCOPE)."
    if "rate" in low and "limit" in low:
        return "The evaluator LLM rate limit was hit; the metric could not complete."
    if "429" in msg:
        return "Too many requests to the evaluator LLM (HTTP 429); the metric could not complete."
    if any(code in msg for code in ("500", "502", "503", "504")):
        return "The evaluator LLM service returned a server error; the metric could not complete."
    if "connection" in low or "network" in low:
        return "A network/connection error occurred while calling the evaluator LLM."
    if "validation" in low or "pydantic" in low:
        return "The evaluator LLM response did not match the structure DeepEval expected."
    if "context" in low and ("required" in low or "missing" in low):
        return "DeepEval expected additional context (e.g. retrieval_context) that was not provided."
    return f"The metric failed unexpectedly ({name}). See server logs for the full traceback."


def run_deepeval_metrics(
    user_query: str,
    actual_output: str,
    metrics: List,
) -> Tuple[dict, dict]:
    """
    Build an LLMTestCase and run the provided DeepEval metrics against it.
    Returns:
        scores: {metric_name: score | None}
        errors: {metric_name: human-readable reason}  (only present for failed metrics)
    """
    test_case = LLMTestCase(
        input=user_query,
        actual_output=actual_output,
        expected_output="",
        retrieval_context=[],
    )

    scores = {}
    errors = {}
    for metric in metrics:
        metric_name = _get_metric_name(metric)
        last_exc = None
        succeeded = False
        for attempt in range(1, METRIC_MAX_ATTEMPTS + 1):
            try:
                metric.measure(test_case)
                scores[metric_name] = round(metric.score, 4)
                logger.info(
                    f"Metric OK | {metric_name}={metric.score} | attempt={attempt} | "
                    f"reason={getattr(metric, 'reason', '')[:200]}"
                )
                succeeded = True
                break
            except Exception as e:
                last_exc = e
                logger.warning(
                    f"Metric {metric_name} failed on attempt {attempt}/{METRIC_MAX_ATTEMPTS}: "
                    f"{type(e).__name__}: {str(e)[:200]}"
                )
                if attempt < METRIC_MAX_ATTEMPTS and _is_transient_metric_error(e):
                    wait = METRIC_BACKOFF_SECONDS[attempt - 1]
                    logger.info(f"Retrying metric {metric_name} in {wait}s...")
                    time.sleep(wait)
                    continue
                # Non-transient error or last attempt — give up.
                break

        if not succeeded:
            reason = _humanize_metric_error(last_exc)
            logger.error(
                f"Metric FAILED after {attempt} attempt(s) | {metric_name} | reason={reason} | "
                f"raw={type(last_exc).__name__}: {str(last_exc)[:300]}",
                exc_info=True,
            )
            scores[metric_name] = None
            errors[metric_name] = reason

    return scores, errors


def _get_metric_name(metric) -> str:
    """Extract a clean snake_case metric name."""
    name = getattr(metric, "name", None) or type(metric).__name__
    return name.lower().replace(" ", "_")
