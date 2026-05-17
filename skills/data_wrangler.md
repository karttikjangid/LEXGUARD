# Skill: Python Data Wrangler

**Purpose:** To ingest, clean, and structure messy hackathon data (CSV, JSON, or raw text) using Python.

**Trigger:** Whenever the user provides a dataset, file path, or raw data that needs analysis or structuring.

**Execution Steps:**
1. Acknowledge the data source and identify the core entities needed.
2. Write a robust Python script (using `pandas` or built-in `json`/`csv` modules) to read and parse the data.
3. Implement strict error handling: use `try-except` blocks, gracefully handle missing values (`NaN` or `None`), and skip corrupted rows. The script MUST NOT crash on edge cases.
4. Use the `filesystem` tool to save the script to the workspace and execute it to verify it works.
5. Extract the required insights and prepare them for the next stage of the pipeline.