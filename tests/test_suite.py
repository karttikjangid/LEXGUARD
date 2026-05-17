import requests
import json
import sys
import os
from typing import Dict, Any

# Import Pydantic models for strict output schema validation (json_enforcer.md guidelines)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from app.core.models import FinalAuditReport
    HAS_MODELS = True
except ImportError:
    print("[WARN] Could not import FinalAuditReport for strict Pydantic validation. Validating at JSON layer only.")
    HAS_MODELS = False

BASE_URL = "http://127.0.0.1:8000"
ANALYZE_ENDPOINT = f"{BASE_URL}/api/analyze-contract"

def log_debug_info(test_name: str, response: requests.Response):
    """Logs detailed tracing info so autonomous_debugger.md workflows can parse and self-heal."""
    print(f"\n[DEBUGGER TRACE] {test_name} failed.")
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {response.headers}")
    try:
        print(f"Response JSON: {json.dumps(response.json(), indent=2)}")
    except ValueError:
        print(f"Response Content: {response.text}")

def validate_response_structure(test_name: str, payload_data: Dict[Any, Any]):
    """Strictly validates that the response maps exactly to FinalAuditReport."""
    if HAS_MODELS:
        try:
            FinalAuditReport(**payload_data)
        except Exception as e:
            print(f"\n[DEBUGGER TRACE] {test_name} schema validation failed:")
            print(str(e))
            raise AssertionError("Response JSON strictly violates FinalAuditReport Pydantic schema.")

def test_predatory_contract():
    print("Running test_predatory_contract...")
    payload = {
        "raw_content": "The Company may terminate this Agreement at any time, for any reason, without prior notice. All intellectual property rights in User Content shall immediately vest in and become the sole, exclusive property of the Company upon creation.",
        "file_format": "text/plain",
        "source": "automated_test"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload)
    if response.status_code != 200:
        log_debug_info("test_predatory_contract", response)
        raise AssertionError(f"Expected 200 OK, got {response.status_code}")
    
    data = response.json()
    validate_response_structure("test_predatory_contract", data)
    
    assert data.get("overall_risk_score", 0) > 5, f"Expected a high risk score, got {data.get('overall_risk_score')}"
    assert len(data.get("flagged_risks", [])) > 0, "Expected at least one flagged risk."
    print("✓ test_predatory_contract passed.")

def test_clean_contract_false_positives():
    print("Running test_clean_contract_false_positives...")
    payload = {
        "raw_content": "This agreement is governed by the laws of the State of California. Both parties agree to act in good faith. You retain all ownership of your intellectual property.",
        "file_format": "text/plain",
        "source": "automated_test"
    }
    
    response = requests.post(ANALYZE_ENDPOINT, json=payload)
    if response.status_code != 200:
        log_debug_info("test_clean_contract_false_positives", response)
        raise AssertionError(f"Expected 200 OK, got {response.status_code}")
    
    data = response.json()
    validate_response_structure("test_clean_contract_false_positives", data)
    
    assert data.get("overall_risk_score", 10) <= 3, f"Expected a low risk score, got {data.get('overall_risk_score')}"
    assert len(data.get("flagged_risks", [])) == 0, "Expected zero flagged risks."
    print("✓ test_clean_contract_false_positives passed.")

def test_malformed_fuzz_payload():
    print("Running test_malformed_fuzz_payload...")
    bad_payloads = [
        {"incorrect_key": "malformed data snippet"},
        {"raw_content": None, "file_format": 123},
        {"raw_content": "aGVsbG8gd29ybGQK" * 50, "file_format": "base64", "source": {"invalid": "type"}}
    ]
    
    for idx, bad_payload in enumerate(bad_payloads):
        response = requests.post(ANALYZE_ENDPOINT, json=bad_payload)
        
        if response.status_code == 500:
            log_debug_info(f"test_malformed_fuzz_payload_case_{idx}", response)
            raise AssertionError(f"Expected 4xx graceful error, but application crashed with 500 on payload: {bad_payload}")
            
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
    
    print("✓ test_malformed_fuzz_payload passed.")

def test_empty_or_blank_input():
    print("Running test_empty_or_blank_input...")
    bad_payloads = [
        {}, 
        {"raw_content": "", "file_format": "text/plain", "source": "test"},
        {"raw_content": "   \n  \t ", "file_format": "text/plain", "source": "test"}
    ]
    
    for idx, bad_payload in enumerate(bad_payloads):
        response = requests.post(ANALYZE_ENDPOINT, json=bad_payload)
        
        if response.status_code == 500:
            log_debug_info(f"test_empty_or_blank_input_case_{idx}", response)
            raise AssertionError(f"Expected 4xx error for blank/empty payload, but got 500: {bad_payload}")
            
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
    print("✓ test_empty_or_blank_input passed.")

if __name__ == "__main__":
    print("Initializing LexGuard Adversarial Testing Engine...\n")
    try:
        requests.get(f"{BASE_URL}/docs", timeout=3)
    except requests.exceptions.ConnectionError:
        print(f"[FATAL] Could not reach FastAPI instance at {BASE_URL}. Ensure it is running via Uvicorn.")
        sys.exit(1)
        
    try:
        test_predatory_contract()
        test_clean_contract_false_positives()
        test_malformed_fuzz_payload()
        test_empty_or_blank_input()
        print("\nAll adversarial tests completed successfully! Ready for production deployment.")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[TEST SUITE FAILURE] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[TEST SUITE EXCEPTION] Unhandled internal test error: {e}")
        sys.exit(1)
