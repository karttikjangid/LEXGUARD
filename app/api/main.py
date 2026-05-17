import binascii
import base64
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.models import ContractPayload, FinalAuditReport
from app.services.ingestion import ContractIngestionEngine, IngestionError
from app.services.analyzer import ContractAnalysisEngine
from app.services.ingestion import ContractIngestionEngine

logger = logging.getLogger(__name__)

app = FastAPI(title="LexGuard API", version="1.0.0")

# Wide-open CORS so unpacked Chrome Extension can reach the local server without origin blocks.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingestion_engine = ContractIngestionEngine()
analysis_engine = ContractAnalysisEngine()

# Normalisation map — all aliases collapse to a canonical routing key.
FORMAT_ALIASES: dict[str, str] = {
    "pdf":         "pdf",
    "html":        "html",
    "text/plain":  "plain",
    "text":        "plain",
    "txt":         "plain",
    "plain":       "plain",
    # DOCX variants
    "docx":        "docx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",
    "doc":         "docx",
}


@app.get("/")
def health_check():
    return {"status": "healthy"}


@app.post("/api/analyze-contract", response_model=FinalAuditReport)
def analyze_contract(payload: ContractPayload):
    """
    Primary analysis endpoint.

    Routing logic (transport defence):
      • text/plain / text / txt / plain  → bypass ingestion engines entirely,
                                           pass raw string straight to the analyzer.
      • pdf                              → base64-decode with padding repair,
                                           then push through PDF ingestion strategy.
      • html                             → UTF-8 encode, push through HTML ingestion strategy.

    All failure modes return 400 (never an unhandled 500 stack trace).
    """
    try:
        # ── GATE 1: empty / whitespace-only body ──────────────────────────────
        if not payload.raw_content or not payload.raw_content.strip():
            raise HTTPException(
                status_code=400,
                detail="raw_content must not be empty or purely whitespace."
            )

        # ── GATE 2: format normalisation & allowlist ──────────────────────────
        canonical = FORMAT_ALIASES.get(payload.file_format.lower().strip())
        if canonical is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file_format '{payload.file_format}'. "
                    f"Accepted values: {sorted(FORMAT_ALIASES.keys())}"
                )
            )

        # ── ROUTING BYPASS: plain text skips all ingestion scrubbers ──────────
        if canonical == "plain":
            # Lightweight sanitisation only — no pymupdf, no BeautifulSoup.
            cleaned_markdown = ContractIngestionEngine._clean_text(payload.raw_content)
            if not cleaned_markdown:
                raise HTTPException(
                    status_code=400,
                    detail="raw_content resolved to an empty string after sanitisation."
                )
        elif canonical == "pdf":
            # ── GATE 3: Base64 padding repair + strict decode ─────────────────
            raw_b64 = payload.raw_content.strip()
            # RFC 4648: base64 payload length must be a multiple of 4; pad if short.
            remainder = len(raw_b64) % 4
            if remainder:
                raw_b64 += "=" * (4 - remainder)
            try:
                file_bytes = base64.b64decode(raw_b64, validate=True)
            except (binascii.Error, ValueError) as exc:
                logger.warning("Base64 decode failure: %s", exc)
                raise HTTPException(
                    status_code=400,
                    detail="raw_content contains invalid Base64 data for a PDF payload."
                )
            cleaned_markdown = ingestion_engine.process_file(
                extension="pdf",
                file_bytes=file_bytes,
            )
        elif canonical == "docx":
            # DOCX payloads arrive as Base64-encoded binary (same as PDF).
            # Repair padding, decode, then route through DOCXIngestionStrategy.
            raw_b64 = payload.raw_content.strip()
            remainder = len(raw_b64) % 4
            if remainder:
                raw_b64 += "=" * (4 - remainder)
            try:
                file_bytes = base64.b64decode(raw_b64, validate=True)
            except (binascii.Error, ValueError) as exc:
                logger.warning("DOCX Base64 decode failure: %s", exc)
                raise HTTPException(
                    status_code=400,
                    detail="raw_content contains invalid Base64 data for a DOCX payload."
                )
            try:
                cleaned_markdown = ingestion_engine.process_file(
                    extension="docx",
                    file_bytes=file_bytes,
                )
            except IngestionError as exc:
                raise HTTPException(status_code=400, detail=f"DOCX Parsing Error: {exc}")
        else:
            # html (or any future registered strategy)
            file_bytes = payload.raw_content.encode("utf-8")
            cleaned_markdown = ingestion_engine.process_file(
                extension=canonical,
                file_bytes=file_bytes,
            )

        # ── ANALYSIS ──────────────────────────────────────────────────────────
        report = analysis_engine.analyze_document(cleaned_markdown)
        return report

    # ── ERROR CONTAINMENT LAYER ───────────────────────────────────────────────
    except HTTPException:
        # Re-raise explicit 4xx responses without re-wrapping them as 500s.
        raise
    except IngestionError as exc:
        logger.error("Ingestion error: %s", exc)
        raise HTTPException(status_code=400, detail=f"Ingestion Error: {exc}")
    except Exception as exc:
        # Last-resort catch — log the full trace server-side, return clean 500.
        logger.exception("Unhandled exception in analyze_contract")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {exc}")
