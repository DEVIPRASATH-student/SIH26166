"""Physical Verification Pydantic Schemas."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class PhysicalGateResult(BaseModel):
    gate_id: str = Field(..., description="GATE1 through GATE6")
    gate_name: str = Field(..., description="Descriptive gate name")
    status: str = Field(..., description="PASS, REJECTED, or NOT_EVALUATED")
    reason: str = Field(..., description="Explanation of gate evaluation")
    threshold: Optional[str] = None
    observed_value: Optional[str] = None


class PhysicalVerificationResponse(BaseModel):
    correspondence_id: str
    passed: bool
    status: str
    gates: Dict[str, PhysicalGateResult]
    rejection_reasons: List[str]
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
