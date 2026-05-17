# Skill: MLOps Backend Architect

**Purpose:** To instantly generate a modular, containerized Python backend optimized for Google Cloud Run deployment.

**Trigger:** When instructed to build the application backend, API, or prepare for deployment.

**Execution Steps:**
1. **Initialize API:** Create a `main.py` file using `FastAPI`. Set up a health-check endpoint (`/`) and the core operational endpoints required by the problem statement.
2. **Modularity:** Separate routing, ML inference/logic, and data models (Pydantic) into clean functions. Do not put a 500-line script in one file.
3. **Dependencies:** Generate a strict `requirements.txt` containing only the necessary libraries (e.g., `fastapi`, `uvicorn`, `pandas`, `pinecone-client`).
4. **Containerization (Cloud Run Standard):** Generate a `Dockerfile` with the following strict requirements:
   - Use a lightweight base image (e.g., `python:3.10-slim`).
   - Expose port `8080` (Mandatory for Cloud Run).
   - Use `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]`.
5. **Validation:** Use the `filesystem` tool to write these files to disk. Ensure all API responses pass through the `Strict JSON Enforcer` skill.