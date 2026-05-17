from enum import Enum
from pydantic import BaseModel, Field, model_validator
from pydantic import ConfigDict

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
    model_config = ConfigDict(use_enum_values=True, strict=False)

    category: str = "MISCELLANEOUS"
    severity: str = "LOW"
    original_text: str
    plain_language_explanation: str
    recommendation: str
    referenced_sections: list[str]

class GraphEdge(BaseModel):
    model_config = ConfigDict(use_enum_values=True, strict=False)

    source_node: str
    target_node: str
    relationship_type: str

class FinalAuditReport(BaseModel):
    model_config = ConfigDict(use_enum_values=True, strict=False)

    overall_risk_score: int = Field(
        ..., ge=1, le=10,
        description="Absolute risk score strictly between 1 and 10."
    )
    executive_summary: str
    flagged_risks: list[RiskAnalysis]
    contract_graph: list[GraphEdge]

    @model_validator(mode='after')
    def strip_orphan_graph_edges(self) -> 'FinalAuditReport':
        """
        Removes GraphEdge entries whose source_node or target_node does not
        correspond to any section reference present in the flagged_risks.
        Prevents LLM-hallucinated edges from corrupting the graph topology.
        """
        # Compile the universe of valid node identifiers from all flagged risks
        valid_nodes: set[str] = set()
        for risk in self.flagged_risks:
            for section in risk.referenced_sections:
                valid_nodes.add(section)

        # If no referenced sections exist at all, keep the graph as-is to avoid
        # nuking a legitimate (though unvalidated) graph on sparse contracts
        if not valid_nodes:
            return self

        # Filter: only keep edges where BOTH endpoints are in the valid node set
        self.contract_graph = [
            edge for edge in self.contract_graph
            if edge.source_node in valid_nodes and edge.target_node in valid_nodes
        ]
        return self

class ContractPayload(BaseModel):
    raw_content: str
    file_format: str
    source: str
