import json
import re
import time
import logging
from langchain_core.messages import SystemMessage, HumanMessage
from app.llm.cortex_llm import CortexAgentChatModel
from app.llm.deepeval_wrapper import CortexDeepEvalLLM
from app.core.config import settings

logger = logging.getLogger(__name__)

_llm_instance: CortexAgentChatModel = None
_deepeval_llm_instance: CortexDeepEvalLLM = None

# Retry policy for transient LLM failures (timeouts, server disconnects, 5xx, 429, etc.)
JUDGE_MAX_ATTEMPTS = 3
JUDGE_BACKOFF_SECONDS = (1.0, 2.0)  # waits before attempts 2 and 3


def get_llm() -> CortexAgentChatModel:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = CortexAgentChatModel(agent_name=settings.cortex_agent_name)
        logger.info(f"LLM initialized: {_llm_instance.get_profile()}")
    return _llm_instance


def get_deepeval_llm() -> CortexDeepEvalLLM:
    global _deepeval_llm_instance
    if _deepeval_llm_instance is None:
        _deepeval_llm_instance = CortexDeepEvalLLM(agent_name=settings.cortex_agent_name)
    return _deepeval_llm_instance


# =============================================================================
# Judge Evaluator — Guidelines Mode Only
# =============================================================================
JUDGE_GUIDELINES_SYSTEM_PROMPT = """You are a strict AI quality judge evaluating an agent's output
against a specific set of guidelines that define what a correct output must look like.

Score the actual output on a scale from 0.0 to 1.0 based on how well it adheres to the guidelines:
- 1.0 = Fully adheres to all guidelines
- 0.8-0.99 = Mostly adheres, minor violations
- 0.6-0.79 = Partial adherence, noticeable violations
- 0.4-0.59 = Poor adherence, significant violations
- 0.0-0.39 = Fails to follow guidelines

You MUST respond with ONLY a valid JSON object in this exact format:
{
  "score": <float between 0.0 and 1.0>,
  "confidence": <float between 0.0 and 1.0 — how confident you are in this judgment>,
  "reasoning": "<one paragraph explaining the score>",
  "strengths": ["<guideline followed well>"],
  "issues": ["<guideline violated>"],
  "suggestions": ["<how to fix each violation>"]
}"""


def judge_output(
    user_query: str,
    component_name: str,
    actual_output: str,
    guidelines: str,
) -> dict:
    """
    Judge actual output against guidelines.
    Returns score, confidence, reasoning, strengths, issues, suggestions.
    """
    llm = get_llm()

    prompt = f"""User Query: {user_query}

Component Name: {component_name}

Agent Guidelines:
{guidelines}

Actual Output:
{actual_output}

Evaluate the actual output against the guidelines and return your JSON judgment:"""

    messages = [
        SystemMessage(content=JUDGE_GUIDELINES_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = None
    last_exc = None
    for attempt in range(1, JUDGE_MAX_ATTEMPTS + 1):
        try:
            response = llm.invoke(messages)
            if attempt > 1:
                logger.info(f"Judge LLM call succeeded on retry attempt {attempt}.")
            break
        except Exception as e:
            last_exc = e
            logger.warning(
                f"Judge LLM call failed on attempt {attempt}/{JUDGE_MAX_ATTEMPTS}: "
                f"{type(e).__name__}: {str(e)[:200]}"
            )
            if attempt < JUDGE_MAX_ATTEMPTS:
                wait = JUDGE_BACKOFF_SECONDS[attempt - 1]
                logger.info(f"Retrying judge LLM call in {wait}s...")
                time.sleep(wait)

    if response is None:
        reason = _humanize_llm_error(last_exc)
        logger.error(
            f"Judge LLM call failed after {JUDGE_MAX_ATTEMPTS} attempts: "
            f"{type(last_exc).__name__}: {last_exc}",
            exc_info=True,
        )
        return {
            "score": 0.0,
            "confidence": 0.0,
            "reasoning": reason,
            "strengths": [],
            "issues": [],
            "suggestions": [],
            "error": reason,
        }

    raw = response.content.strip()

    parsed = _parse_judge_json(raw)
    if parsed is None:
        reason = (
            "The judge LLM returned a response that could not be parsed as valid JSON, "
            "so a numeric judgment could not be extracted."
        )
        logger.error(f"Judge response parse failed. Raw: {raw[:300]}")
        return {
            "score": 0.0,
            "confidence": 0.0,
            "reasoning": reason,
            "strengths": [],
            "issues": [raw[:200]],
            "suggestions": [],
            "error": reason,
        }

    def _clamp(val, default=0.0):
        try:
            return max(0.0, min(1.0, float(val)))
        except (TypeError, ValueError):
            return default

    return {
        "score": _clamp(parsed.get("score", 0.0)),
        "confidence": _clamp(parsed.get("confidence", 0.8), default=0.8),
        "reasoning": parsed.get("reasoning", ""),
        "strengths": parsed.get("strengths", []) or [],
        "issues": parsed.get("issues", []) or [],
        "suggestions": parsed.get("suggestions", []) or [],
        "error": None,
    }


def _humanize_llm_error(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc)
    low = msg.lower()
    if "timeout" in low or "timed out" in low:
        return "The judge LLM call timed out before a response was received."
    if "302" in msg or "cookie" in low or "redirect" in low:
        return "Authentication with the Cortex platform failed (cookie expired or invalid)."
    if "429" in msg or ("rate" in low and "limit" in low):
        return "The judge LLM rate limit was hit; the request could not complete."
    if any(code in msg for code in ("500", "502", "503", "504")):
        return "The judge LLM service returned a server error; the request could not complete."
    if "connection" in low or "network" in low:
        return "A network/connection error occurred while calling the judge LLM."
    return f"The judge LLM call failed unexpectedly ({name}). See server logs for the full traceback."


def _parse_judge_json(raw: str):
    """
    Robustly extract a judge JSON object from an LLM response.
    Tries: (1) direct parse, (2) the LARGEST ```json``` block,
    (3) the largest balanced {...} substring containing a "score" key.
    Returns dict on success, None on failure.
    """
    if not raw:
        return None

    # 1. Direct parse
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and "score" in obj:
            return obj
    except (json.JSONDecodeError, ValueError):
        pass

    # 2. All fenced code blocks — try largest first, prefer ones with "score"
    blocks = re.findall(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    candidates = sorted(blocks, key=len, reverse=True)
    for block in candidates:
        try:
            obj = json.loads(block)
            if isinstance(obj, dict) and "score" in obj:
                return obj
        except (json.JSONDecodeError, ValueError):
            continue

    # 3. Balanced-brace scan for the largest {...} containing "score"
    best = None
    for start in (i for i, ch in enumerate(raw) if ch == "{"):
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(raw)):
            ch = raw[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = raw[start:i + 1]
                        try:
                            obj = json.loads(candidate)
                            if isinstance(obj, dict) and "score" in obj:
                                if best is None or len(candidate) > len(best[1]):
                                    best = (obj, candidate)
                        except (json.JSONDecodeError, ValueError):
                            pass
                        break
    return best[0] if best else None
