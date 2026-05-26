from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class StreamEventType(str, Enum):
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    TOKEN_CHUNK = "token_chunk"
    METRIC_UPDATE = "metric_update"
    ADVERSARIAL_REJECT = "adversarial_reject"
    PIPELINE_FAILED = "pipeline_failed"

class SegmentMetric(BaseModel):
    segment: str
    label: str
    friction_rate: float

class QuantitativeMetrics(BaseModel):
    willingness_to_pay_score: float = 0.0
    overall_cart_abandonment_risk: float = 0.0
    segment_friction_distribution: List[SegmentMetric] = Field(default_factory=list)

class EvidenceChainItem(BaseModel):
    persona_name: str
    exact_quote: str
    circumstance: str
    context_score: float

class ExtractedTheme(BaseModel):
    theme_id: str
    title: str
    prevalence: float
    risk_priority: str
    summary: str
    evidence_chain: List[EvidenceChainItem]

# --- ÖN YÜZE AKTARILAN UNIFIED EVENT WRAPPER ---
class RealtimeStreamEvent(BaseModel):
    event_type: StreamEventType
    research_id: str
    current_stage: int
    status: str
    message: Optional[str] = None
    metrics: Optional[QuantitativeMetrics] = None
    themes: Optional[List[ExtractedTheme]] = None
