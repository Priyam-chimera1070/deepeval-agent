from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class RunPayload(BaseModel):
    run_id: Optional[str] = Field(None, description="Unique run identifier — auto-generated if missing")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of this run")
    user_query: str = Field(..., description="User query for this run")
    input: str = Field(..., description="Input received by the agent in this run")
    output: str = Field(..., description="Output produced by the agent in this run")


class EvaluationRequest(BaseModel):
    agent_name: Optional[str] = Field(None, description="Agent name (defaults to 'RAG Agent')")
    evaluation_id: Optional[str] = Field(None, description="Unique evaluation identifier — auto-generated if missing")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of the evaluation batch")
    runs: List[RunPayload] = Field(..., min_length=1, description="List of agent runs to evaluate")


class RunResult(BaseModel):
    run_id: str
    timestamp: Optional[str] = None
    user_query: str
    metrics: Dict[str, Optional[float]] = Field(default_factory=dict, description="Metric scores as percentages (0-100)")
    metric_errors: Dict[str, str] = Field(default_factory=dict, description="Per-metric human-readable failure reasons (only present when a metric returns null)")
    judge_score: Optional[float] = None
    judge_confidence: Optional[float] = None
    judge_reasoning: Optional[str] = None
    judge_strengths: List[str] = Field(default_factory=list)
    judge_issues: List[str] = Field(default_factory=list)
    judge_suggestions: List[str] = Field(default_factory=list)
    judge_error: Optional[str] = Field(None, description="Human-readable reason if the judge failed")
    overall_score: Optional[float] = None
    status: str  # PASS | WARN | FAIL | ERROR
    error: Optional[str] = Field(None, description="Human-readable reason if the entire run failed")


class EvaluationResponse(BaseModel):
    evaluation_id: str
    agent_name: str
    timestamp: Optional[str] = None
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_score: float
    average_status: str  # PASS | WARN | FAIL
    runs: List[RunResult]
