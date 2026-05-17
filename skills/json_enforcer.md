# Skill: Strict JSON Enforcer

**Purpose:** To guarantee that all final outputs, configurations, and API payloads are perfectly valid, parseable JSON.

**Trigger:** Use this skill as the mandatory final step before returning any data payload, frontend response, or configuration file.

**Execution Steps:**
1. Take the raw generated string intended for the final output.
2. Strip ALL conversational filler, pre-text, post-text, and Markdown formatting (e.g., remove ```json and ```).
3. Validate the payload internally to ensure it meets strict JSON standards (double quotes for keys, no trailing commas).
4. If the JSON is invalid, silently self-correct the syntax errors before outputting.
5. Output ONLY the raw JSON object. Do not output any other text whatsoever.