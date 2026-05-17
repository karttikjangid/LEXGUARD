import os
import instructor
from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone
from pydantic import ValidationError

# Always resolve .env first so the module works under conda, uvicorn, or direct invocation
load_dotenv()

from app.core.models import FinalAuditReport, RiskAnalysis, GraphEdge

# ── Model configuration ────────────────────────────────────────────────────────
LEGAL_MODEL     = os.environ.get("LEGAL_MODEL", "gemini-3-flash-preview")
EMBEDDING_MODEL = "gemini-embedding-2"
RAG_TOP_K       = int(os.environ.get("RAG_TOP_K", "8"))

# Subset of contract used for retrieval query: first 2000 chars keeps token cost low
# while capturing the clause-density that drives retrieval relevance.
RAG_QUERY_CHARS = int(os.environ.get("RAG_QUERY_CHARS", "2000"))


class ContractAnalysisEngine:
    def __init__(self):
        # ── Instructor client (structured-output generation) ───────────────────
        # from_provider bakes the model into the client; .create() needs no model= arg
        self.client = instructor.from_provider(f"google/{LEGAL_MODEL}")

        # ── Raw GenAI client (embedding only) ─────────────────────────────────
        self.genai_client = genai.Client()

        # ── Pinecone retrieval client ──────────────────────────────────────────
        pinecone_api_key   = os.environ.get("PINECONE_API_KEY")
        pinecone_index_name = os.environ.get("PINECONE_INDEX_NAME", "lexguard-knowledge")

        if pinecone_api_key:
            pc = Pinecone(api_key=pinecone_api_key)
            self.pc_index = pc.Index(pinecone_index_name)
            print(f"[RAG] Connected to Pinecone index: {pinecone_index_name}")
        else:
            self.pc_index = None
            print("[RAG] WARNING: PINECONE_API_KEY not set — RAG retrieval disabled.")

    # ── Private helpers ────────────────────────────────────────────────────────

    def _embed_text(self, text: str) -> list[float]:
        """Embed a text string using gemini-embedding-2 (3072 dims)."""
        response = self.genai_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text
        )
        return response.embeddings[0].values

    def _retrieve_reference_clauses(self, contract_text: str) -> str:
        """
        Embed the first RAG_QUERY_CHARS of the contract and query Pinecone
        for the top-k most semantically similar benchmark clauses.
        Returns a formatted string block ready for injection into the prompt.
        """
        if self.pc_index is None:
            return ""

        try:
            query_text = contract_text[:RAG_QUERY_CHARS].strip()
            query_vector = self._embed_text(query_text)

            results = self.pc_index.query(
                vector=query_vector,
                top_k=RAG_TOP_K,
                include_metadata=True
            )

            if not results.matches:
                return ""

            lines = ["## REFERENCE STANDARD — Expert Predatory Clause Library"]
            lines.append(
                "The following clauses are semantically similar benchmark examples "
                "retrieved from a curated legal knowledge base. Use them as grounding "
                "evidence when identifying risks in the contract below.\n"
            )
            for i, match in enumerate(results.matches, 1):
                meta = match.metadata or {}
                clause_text   = meta.get("original_text", "[text unavailable]")
                category      = meta.get("category", "UNKNOWN")
                rejection_why = meta.get("standard_rejection_reason", "")
                lines.append(f"[{i}] Category: {category}")
                lines.append(f"    Clause  : {clause_text}")
                if rejection_why:
                    lines.append(f"    Why bad : {rejection_why}")
                lines.append("")

            print(f"[RAG] Retrieved {len(results.matches)} reference clauses from Pinecone.")
            return "\n".join(lines)

        except Exception as e:
            # RAG failure must never crash the analysis — degrade gracefully
            print(f"[RAG] Retrieval error (degrading to no-RAG mode): {e}")
            return ""

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyze_document(self, markdown_text: str) -> FinalAuditReport:
        # Step 1: Retrieve relevant benchmark clauses from Pinecone
        rag_block = self._retrieve_reference_clauses(markdown_text)

        # Step 2: Build the grounded prompt
        rag_section = f"\n{rag_block}\n" if rag_block else ""

        prompt = f"""You are an adversarial contract auditor designed to audit contracts for predatory clauses.
{rag_section}
Read the following contract carefully. Use the REFERENCE STANDARD above (if present) as grounding \
evidence to identify clauses that match or exceed known predatory patterns.

For each identified vulnerability:
1. Classify it using the appropriate LegalCategory and SeverityLevel.
2. Extract the EXACT substring from the contract into `original_text`. \
   It MUST be an exact verbatim match to a substring in the document below — do not paraphrase.
3. Write a plain-language explanation for non-technical users.
4. Give an actionable mitigation recommendation.
5. List any explicit legal cross-references in `referenced_sections` (e.g. "Section 4.1").

Additionally, populate `contract_graph` with GraphEdge items mapping structural dependencies \
between sections (e.g. source_node: "Section 3.2", target_node: "Section 24", \
relationship_type: "MODIFIES" | "EXEMPTS" | "DEFINES").

Contract Document:
---
{markdown_text}
---
"""

        try:
            # Step 3: Structured-output generation via Instructor + Gemini
            report: FinalAuditReport = self.client.create(
                messages=[{"role": "user", "content": prompt}],
                response_model=FinalAuditReport,
                max_retries=3
            )

            # Step 4: Exact-match hallucination filter on original_text
            validated_risks = []
            for risk in report.flagged_risks:
                if risk.original_text in markdown_text:
                    validated_risks.append(risk)
                else:
                    # Whitespace-normalised fallback check
                    norm_src  = " ".join(markdown_text.split())
                    norm_risk = " ".join(risk.original_text.split())
                    if norm_risk in norm_src:
                        validated_risks.append(risk)
                    else:
                        print(
                            f"[DEBUGGER] Hallucination Caught: "
                            f"Stripping invalid original_text: {risk.original_text[:60]}..."
                        )

            report.flagged_risks = validated_risks
            return report

        except ValidationError as e:
            print(f"[DEBUGGER] Schema Validation Error: {e}")
            raise
        except Exception as e:
            print(f"[DEBUGGER] Unexpected Error: {e}")
            raise


if __name__ == "__main__":
    engine = ContractAnalysisEngine()
    print("ContractAnalysisEngine initialized successfully.")
