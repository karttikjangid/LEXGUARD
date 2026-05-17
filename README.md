# LexGuard: AI Rights & Contract Intelligence System

## 1. PROJECT HEADLINE & CORE VALUE PROP

In the modern digital economy, individuals and enterprises routinely agree to predatory terms buried within impenetrable walls of legalese. Standard Natural Language Processing (NLP) solutions and naive retrieval-augmented generation (RAG) pipelines fail to adequately surface these risks; they provide opaque summaries that often miss critical cross-references, severing the legal context required to understand cascading obligations.

**LexGuard** is a highly sophisticated Graph-Augmented RAG and Multi-Agent verification pipeline designed to transition legal analysis from simple text summarization to deep legal awareness. By leveraging advanced geometric network mapping and an adversarial AI checker-maker loop, LexGuard precisely targets, extracts, and simulates the consequences of predatory clauses. It is not merely a tool for reading contracts—it is an enterprise-grade intelligence engine built to defend user rights in real-time.

---

## 2. ARCHITECTURAL ARCHITECTURE & PIPELINE DEPTH

### The Failure of Standard RAG in Legal Contexts
Standard, linear RAG pipelines treat documents as flat text sequences. In legal contracts, meaning is rarely sequential. A definition in Section 1 modifies an obligation in Section 4, which is then exempted by a liability waiver in Section 9. Flat RAG fragments this context, leading to dangerous LLM hallucinations and overlooked risks. 

### Graph-Augmented RAG Engine
LexGuard solves context fragmentation by converting contracts into multidimensional directed graphs.
- **Node Topology**: Legal concepts are parsed into discrete structural nodes—`Clauses`, `Definitions`, and `Obligations`.
- **Relationship Edges**: These nodes are linked via semantically typed edges such as `MODIFIES`, `EXEMPTS`, `DEFINES`, and `SUPERSEDES`.
This structural awareness ensures that when the system analyzes a liability clause, it automatically retrieves the exact definitions and exemptions that govern it.

### Adversarial Multi-Agent Loop
To guarantee analytical accuracy, LexGuard employs a Maker-Checker multi-agent pipeline driven by the `Instructor` client and the `gemini-3-flash-preview` model.
- **Maker Agent**: Navigates the Graph-RAG context to identify potential predatory clauses and legal risks based on the Pinecone vector index.
- **Checker Agent**: Adversarially interrogates the Maker’s findings, aggressively attempting to disprove the extracted risks against the source text to ensure zero hallucination.

### Deterministic Python Substring Verification Layer
Before any risk is surfaced to the user, LexGuard enforces a deterministic validation pass. Utilizing strict Python algorithms, the system verifies that the exact substrings cited by the LLM agents exist verbatim within the original, unmutated document text. If a string cannot be deterministically matched, the extraction is rejected.

---

## 3. TECHNICAL STACK & DEPLOYMENT PHYSICS

LexGuard is engineered on a modern, stateless, high-throughput technology stack designed for enterprise scalability.

*   **Core Engine**: Python 3.11+ / FastAPI — asynchronous, high-performance API transport.
*   **Containerization**: Docker — optimized stateless image build.
*   **Orchestration & Compute**: Google Cloud Run — Stateless, CPU-optimized configuration for auto-scaling HTTP workloads.
*   **Semantic Parsing**: `pymupdf4llm` — layout-preserving document ingestion.
*   **Client-Side Processing**: `BeautifulSoup` — Chrome Extension HTML sanitization and DOM scraping.
*   **Vector Infrastructure**: Pinecone — Managed vector cluster tracking 3072-dimensional embeddings via `gemini-embedding-2`.
*   **Cognitive Inference**: `gemini-3-flash-preview` & `Instructor` — Structured output generation and adversarial reasoning.

---

## 4. PRODUCTION DIRECTORY STRUCTURE

LexGuard strictly adheres to SOLID design principles and Separation of Concerns (SoC).

```text
lexguard/
├── app/
│   ├── api/
│   │   └── main.py              # FastAPI transport controllers (CORS exceptions, base64 padding correction)
│   ├── core/
│   │   └── models.py            # Strict Pydantic type definitions (no Union/Optional ambiguities)
│   └── services/
│       ├── analyzer.py          # Graph-RAG Cognitive core & Multi-Agent loop
│       ├── ingestion.py         # Abstract polymorphic parsing strategy layer
│       └── seeder.py            # Programmatic high-density asynchronous vector seeder (200-300 CUAD variations)
├── extension/
│   ├── content.js               # Content extraction and DOM injection
│   ├── manifest.json            # Chrome Manifest V3 definitions
│   └── popup.js                 # Chrome extension interface logic
├── frontend/
│   ├── app.js                   # Client-side SPA logic
│   └── index.html               # LexGuard dashboard interface
├── tests/
│   └── test_suite.py            # Adversarial testing matrix (false positive prevention, fuzzing, stress loads)
├── Dockerfile                   # Stateless production container specification
├── requirements.txt             # Pinned dependency graph
└── .env.example                 # Environment configuration template
```

---

## 5. PRODUCTION DEPLOYMENT & RUNTIME CONFIGURATION

The following instructions provide the exact, copy-pasteable commands required to deploy and run the LexGuard pipeline.

### Local Virtual Environment Initialization
```bash
# Clone the repository
git clone https://github.com/karttikjangid/LEXGUARD.git
cd LEXGUARD

# Initialize Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install strictly pinned dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Google Gemini API and Pinecone credentials
```

### Executing the Pinecone Vector Seeder Pipeline
Before running the analyzer, you must seed the managed vector cluster with benchmark legal data.
```bash
# Execute the high-density asynchronous seeder
python -m app.services.seeder
```

### Running the Local Development Server
Launch the FastAPI asynchronous engine for local development.
```bash
# Start the uvicorn transport controller
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running the Adversarial Local Test Suite
Ensure the Deterministic Python Substring Verification Layer and Multi-Agent Loop are functioning correctly.
```bash
# Execute the testing matrix
pytest tests/test_suite.py -v
```

### Google Cloud Run Deployment
Build and deploy the stateless container to GCP.
```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project [YOUR_PROJECT_ID]

# Build the Docker image via Google Cloud Build
gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/lexguard

# Deploy the image to Cloud Run (Stateless, CPU-optimized)
gcloud run deploy lexguard \
  --image gcr.io/[YOUR_PROJECT_ID]/lexguard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --cpu 2 \
  --memory 2Gi \
  --set-env-vars="GEMINI_API_KEY=YOUR_API_KEY,PINECONE_API_KEY=YOUR_API_KEY"
```

---

## 6. PROBLEM STATEMENT MATRIX ALIGNMENT

LexGuard addresses the hackathon's core objective categories through precision engineering. The matrix below demonstrates our 100% compliance with risk mitigation requirements.

| Risk Category | Hackathon Objective | LexGuard System Feature | Technical Implementation |
| :--- | :--- | :--- | :--- |
| **Privacy** | Detect unauthorized data selling or opaque tracking clauses. | Surveillance Node Extraction | Graph-RAG queries targeting `OBLIGATION` nodes mapped to data sharing verbs, verified by the Maker-Checker loop. |
| **Financial** | Flag hidden subscription traps, auto-renewals, or extreme penalties. | Asymmetric Liability Detection | Vector similarity search (3072-d embeddings) isolating auto-renewal terminology, processed through the Deterministic Substring Layer. |
| **Employment** | Identify predatory non-competes, IP assignment, and arbitration forcing. | Jurisdictional Conflict Mapping | Graph edge traversal (`SUPERSEDES`) to determine if forced arbitration clauses invalidate local labor protections. |
| **Intellectual Property**| Surface broad licenses that claim perpetual rights to user-generated content. | Temporal Licensing Analysis | Adversarial agents interrogate extracted text for "perpetual," "irrevocable," and "worldwide" modifiers applied to user IP. |
| **Compliance** | Map terms of service against evolving regulatory frameworks (e.g., GDPR, CCPA). | Regulatory Exemption Simulation | Semantic parsing matches contract clauses against seeded CUAD-variant regulatory benchmarks in the Pinecone cluster. |
