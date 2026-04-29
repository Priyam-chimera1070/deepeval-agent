import logging
from typing import List

from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.test_case import LLMTestCaseParams
from deepeval.models.base_model import DeepEvalBaseLLM

logger = logging.getLogger(__name__)

_METRIC_THRESHOLD = 0.5


def build_guidelines_metrics(guidelines: str, deepeval_llm: DeepEvalBaseLLM) -> List:
    """
    Builds fixed metrics for guidelines-based evaluation:
    - GuidelinesAdherence GEval with agent guidelines as criteria
    - AnswerRelevancyMetric
    """
    return [
        GEval(
            name="GuidelinesAdherence",
            criteria=f"Evaluate whether the actual output strictly adheres to the following agent guidelines:\n{guidelines}",
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            threshold=_METRIC_THRESHOLD,
            model=deepeval_llm,
        ),
        AnswerRelevancyMetric(threshold=_METRIC_THRESHOLD, model=deepeval_llm, include_reason=True),
    ]
