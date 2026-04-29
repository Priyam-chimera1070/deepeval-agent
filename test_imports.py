"""
Quick import test to verify all modules load correctly
"""
print("Testing imports...")

try:
    from app.main import app
    print("✅ Main app")
except Exception as e:
    print(f"❌ Main app: {e}")

try:
    from app.api.routes import router
    print("✅ Routes")
except Exception as e:
    print(f"❌ Routes: {e}")

try:
    from app.api.schemas import EvaluationRequest, EvaluationResponse
    print("✅ Schemas")
except Exception as e:
    print(f"❌ Schemas: {e}")

try:
    from app.llm.llm_client import judge_output, get_llm, get_deepeval_llm
    print("✅ LLM client")
except Exception as e:
    print(f"❌ LLM client: {e}")

try:
    from app.evaluation.metric_predictor import build_guidelines_metrics
    print("✅ Metric predictor")
except Exception as e:
    print(f"❌ Metric predictor: {e}")

try:
    from app.evaluation.deepeval_runner import run_deepeval_metrics
    print("✅ DeepEval runner")
except Exception as e:
    print(f"❌ DeepEval runner: {e}")

try:
    from app.evaluation.guidelines import get_guidelines
    print("✅ Guidelines")
except Exception as e:
    print(f"❌ Guidelines: {e}")

try:
    from app.evaluation.result_formatter import format_component_result, format_final_response
    print("✅ Result formatter")
except Exception as e:
    print(f"❌ Result formatter: {e}")

try:
    from app.core.config import settings
    print("✅ Config")
except Exception as e:
    print(f"❌ Config: {e}")

try:
    from app.core.logger import get_session_logger
    print("✅ Logger")
except Exception as e:
    print(f"❌ Logger: {e}")

print("\n" + "="*50)
print("Testing basic functionality...")

try:
    guidelines = get_guidelines("rag agent")
    if guidelines:
        print(f"✅ Guidelines loaded: {len(guidelines)} chars")
    else:
        print("❌ Guidelines empty")
except Exception as e:
    print(f"❌ Guidelines loading: {e}")

try:
    from app.api.schemas import EvaluationRequest, ComponentPayload
    req = EvaluationRequest(
        user_query="test query",
        components=[ComponentPayload(name="RAG Agent", input="test", output="test")]
    )
    print(f"✅ Request validation works")
except Exception as e:
    print(f"❌ Request validation: {e}")

try:
    result = format_component_result(
        component_name="RAG Agent",
        deepeval_metrics={"metric1": 0.9, "metric2": 0.85},
        judge_score=0.88,
        judge_confidence=0.92,
        judge_reasoning="Test reasoning",
        judge_strengths=["strength1"],
        judge_issues=["issue1"],
        judge_suggestions=["suggestion1"]
    )
    print(f"✅ Result formatting works: {result['status']} with score {result['overall_score']}")
except Exception as e:
    print(f"❌ Result formatting: {e}")

print("\n" + "="*50)
print("All import tests complete!")
