# Skill: Autonomous Self-Healing Debugger

**Purpose:** To instantly diagnose and fix Python tracebacks, Docker build failures, or API 500 errors without waiting for human intervention.

**Trigger:** When a Python script crashes, a Docker container fails to build, or an API endpoint returns an error code.

**Execution Steps:**
1. **Read the Logs:** Use the `filesystem` tool to read the exact terminal output or error log. DO NOT guess the error.
2. **Isolate the Failure:** Identify the specific line of code or missing dependency causing the traceback.
3. **Apply the Fix:** Use the `filesystem` tool to directly modify the broken `.py` file or `requirements.txt`.
4. **No Placeholders:** Write the complete, fixed function. Never use comments like `# ... rest of code here ...`.
5. **Verify:** Instruct the user on the exact bash command to re-run the code or rebuild the container to verify the fix.