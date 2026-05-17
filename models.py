from enum import Enum
from pydantic import BaseModel, Field

class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class LegalCategory(str, Enum):
    PRIVACY = "PRIVACY"
    INTELLECTUAL_PROPERTY = "INTELLECTUAL_PROPERTY"
    LIABILITY_AND_FEES = "LIABILITY_AND_FEES"
    TERMINATION = "TERMINATION"
    MISCELLANEOUS = "MISCELLANEOUS"

class RiskAnalysis(BaseModel):
    category: LegalCategory
    severity: SeverityLevel
    original_text: str
    plain_language_explanation: str
    recommendation: str

class FinalAuditReport(BaseModel):
    overall_risk_score: int = Field(ge=1, le=10)
    executive_summary: str
    flagged_risks: list[RiskAnalysis]

class ContractPayload(BaseModel):
    raw_content: str
    file_format: str
    source: str
