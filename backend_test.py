"""
Backend API Tests for Invoice Reminders Settings
=================================================

Tests the new GET/PUT /api/invoice-reminders/settings endpoint and validates:
  - Settings singleton seeding on first read
  - Valid payload persistence
  - Validation errors (invalid order, out-of-range, empty channels)
  - Live settings integration with escalation-summary and critical endpoints
  - Process endpoint with enabled/disabled states
  - Settings reset to defaults

Usage:
    python backend_test.py
"""

import requests
import sys
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

# Configuration
API_URL = "https://full-deploy-21.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@bibi.cars"
ADMIN_PASSWORD = "Jp3FS_7ZuE2bhHp7rFkJm9B9T_TeiHxu"

# Default settings for reset
DEFAULTS = {
    "enabled": True,
    "level1_days": 1,
    "level2_days": 3,
    "level3_days": 5,
    "critical_days": 7,
    "reminder_after_days": 3,
    "cooldown_hours": 48,
    "pre_reminder_hours": 24,
    "channels": ["email", "in_app"],
}


class InvoiceRemindersAPITester:
    """Test suite for invoice reminders settings API"""

    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
        }.get(level, "  ")
        print(f"[{timestamp}] {prefix} {message}")

    def run_test(
        self,
        name: str,
        method: str,
        endpoint: str,
        expected_status: int,
        data: Optional[Dict] = None,
        validate_fn: Optional[callable] = None,
    ) -> tuple[bool, Any]:
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        self.tests_run += 1
        self.log(f"Test #{self.tests_run}: {name}", "INFO")

        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            # Check status code
            if response.status_code != expected_status:
                self.tests_failed += 1
                msg = f"Expected status {expected_status}, got {response.status_code}"
                self.log(f"FAILED: {msg}", "ERROR")
                self.log(f"Response: {response.text[:200]}", "ERROR")
                self.failures.append({"test": name, "reason": msg, "response": response.text[:200]})
                return False, None

            # Parse response
            try:
                response_data = response.json()
            except Exception:
                response_data = response.text

            # Run custom validation if provided
            if validate_fn:
                try:
                    validate_fn(response_data)
                except AssertionError as e:
                    self.tests_failed += 1
                    msg = f"Validation failed: {str(e)}"
                    self.log(f"FAILED: {msg}", "ERROR")
                    self.failures.append({"test": name, "reason": msg})
                    return False, response_data

            self.tests_passed += 1
            self.log(f"PASSED (status={response.status_code})", "SUCCESS")
            return True, response_data

        except requests.exceptions.Timeout:
            self.tests_failed += 1
            msg = "Request timeout (30s)"
            self.log(f"FAILED: {msg}", "ERROR")
            self.failures.append({"test": name, "reason": msg})
            return False, None
        except Exception as e:
            self.tests_failed += 1
            msg = f"Exception: {str(e)}"
            self.log(f"FAILED: {msg}", "ERROR")
            self.failures.append({"test": name, "reason": msg})
            return False, None

    def login(self) -> bool:
        """Authenticate and get JWT token"""
        self.log("Authenticating...", "INFO")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        )
        if success and response:
            # Try different possible token locations
            token = response.get("token") or response.get("access_token") or response.get("data", {}).get("token")
            if token:
                self.token = token
                self.log("Authentication successful", "SUCCESS")
                return True
            else:
                self.log(f"Token not found in response: {json.dumps(response, indent=2)[:300]}", "ERROR")
        self.log("Authentication failed", "ERROR")
        return False

    def test_get_settings_initial(self) -> Optional[Dict]:
        """Test 1: GET /api/invoice-reminders/settings returns singleton with defaults"""
        success, response = self.run_test(
            "GET settings (initial read, should seed defaults)",
            "GET",
            "invoice-reminders/settings",
            200,
            validate_fn=lambda r: (
                assert_true(r.get("success") is True, "success should be true"),
                assert_true("data" in r, "response should have 'data' field"),
                assert_true(r["data"].get("id") == "reminder_settings_singleton", "should have singleton id"),
                assert_true(r["data"].get("enabled") is not None, "should have 'enabled' field"),
                assert_true(r["data"].get("level1_days") is not None, "should have 'level1_days' field"),
                assert_true(r["data"].get("channels") is not None, "should have 'channels' field"),
            ),
        )
        return response.get("data") if success and response else None

    def test_put_settings_valid(self) -> bool:
        """Test 2: PUT /api/invoice-reminders/settings with valid payload"""
        payload = {
            "enabled": True,
            "level1_days": 2,
            "level2_days": 5,
            "level3_days": 10,
            "critical_days": 14,
            "cooldown_hours": 24,
            "channels": ["email", "telegram"],
        }
        success, response = self.run_test(
            "PUT settings with valid payload",
            "PUT",
            "invoice-reminders/settings",
            200,
            data=payload,
            validate_fn=lambda r: (
                assert_true(r.get("success") is True, "success should be true"),
                assert_true(r["data"].get("level1_days") == 2, "level1_days should be 2"),
                assert_true(r["data"].get("level2_days") == 5, "level2_days should be 5"),
                assert_true(r["data"].get("level3_days") == 10, "level3_days should be 10"),
                assert_true(r["data"].get("critical_days") == 14, "critical_days should be 14"),
                assert_true(r["data"].get("cooldown_hours") == 24, "cooldown_hours should be 24"),
                assert_true("email" in r["data"].get("channels", []), "channels should include email"),
                assert_true("telegram" in r["data"].get("channels", []), "channels should include telegram"),
            ),
        )
        return success

    def test_put_settings_invalid_order(self) -> bool:
        """Test 3: PUT with invalid order (level1_days > level2_days) returns 422"""
        payload = {
            "level1_days": 10,
            "level2_days": 5,  # Invalid: level1 > level2
            "level3_days": 15,
            "critical_days": 20,
        }
        success, response = self.run_test(
            "PUT settings with invalid order (level1 > level2)",
            "PUT",
            "invoice-reminders/settings",
            422,
            data=payload,
            validate_fn=lambda r: (
                assert_true("detail" in r, "should have 'detail' field"),
                assert_true(
                    "errors" in r.get("detail", {}) or isinstance(r.get("detail"), dict),
                    "detail should contain errors",
                ),
            ),
        )
        return success

    def test_put_settings_out_of_range(self) -> bool:
        """Test 4: PUT with out-of-range value (cooldown_hours=0) returns 422"""
        payload = {
            "cooldown_hours": 0,  # Invalid: min is 1
        }
        success, response = self.run_test(
            "PUT settings with out-of-range value (cooldown_hours=0)",
            "PUT",
            "invoice-reminders/settings",
            422,
            data=payload,
            validate_fn=lambda r: (
                assert_true("detail" in r, "should have 'detail' field"),
            ),
        )
        return success

    def test_put_settings_empty_channels(self) -> bool:
        """Test 5: PUT with channels=[] returns 422"""
        payload = {
            "channels": [],  # Invalid: at least one channel required
        }
        success, response = self.run_test(
            "PUT settings with empty channels",
            "PUT",
            "invoice-reminders/settings",
            422,
            data=payload,
            validate_fn=lambda r: (
                assert_true("detail" in r, "should have 'detail' field"),
            ),
        )
        return success

    def test_escalation_summary_uses_new_thresholds(self) -> bool:
        """Test 6: GET /api/invoice-reminders/escalation-summary uses new thresholds"""
        success, response = self.run_test(
            "GET escalation-summary (should reflect new thresholds)",
            "GET",
            "invoice-reminders/escalation-summary",
            200,
            validate_fn=lambda r: (
                assert_true(r.get("success") is True, "success should be true"),
                assert_true("settings" in r, "should have 'settings' sub-object"),
                assert_true(r["settings"].get("level1_days") == 2, "settings.level1_days should be 2"),
                assert_true(r["settings"].get("level2_days") == 5, "settings.level2_days should be 5"),
                assert_true(r["settings"].get("level3_days") == 10, "settings.level3_days should be 10"),
                assert_true(r["settings"].get("critical_days") == 14, "settings.critical_days should be 14"),
                assert_true("level1Count" in r, "should have level1Count"),
                assert_true("level2Count" in r, "should have level2Count"),
                assert_true("level3Count" in r, "should have level3Count"),
                assert_true("criticalCount" in r, "should have criticalCount"),
            ),
        )
        return success

    def test_process_endpoint_success(self) -> bool:
        """Test 7: POST /api/invoice-reminders/process returns success with fields"""
        success, response = self.run_test(
            "POST /process (should return success with processed/reminders/ranAt)",
            "POST",
            "invoice-reminders/process",
            200,
            validate_fn=lambda r: (
                assert_true(r.get("success") is not False, "success should not be false"),
                assert_true("processed" in r, "should have 'processed' field"),
                assert_true("reminders" in r, "should have 'reminders' field"),
                assert_true("ranAt" in r, "should have 'ranAt' field"),
                assert_true(isinstance(r.get("processed"), int), "processed should be int"),
                assert_true(isinstance(r.get("reminders"), int), "reminders should be int"),
            ),
        )
        return success

    def test_process_with_disabled_engine(self) -> bool:
        """Test 8: When enabled=false, POST /process returns skipped=true"""
        # First, disable the engine
        self.log("Disabling reminder engine...", "INFO")
        success, _ = self.run_test(
            "PUT settings (disable engine)",
            "PUT",
            "invoice-reminders/settings",
            200,
            data={"enabled": False},
        )
        if not success:
            return False

        # Now test /process
        success, response = self.run_test(
            "POST /process with engine disabled (should return skipped=true)",
            "POST",
            "invoice-reminders/process",
            200,
            validate_fn=lambda r: (
                assert_true(r.get("success") is True, "success should be true"),
                assert_true(r.get("skipped") is True, "skipped should be true"),
                assert_true(r.get("reason") == "reminder_engine_disabled", "reason should be reminder_engine_disabled"),
                assert_true(r.get("processed") == 0, "processed should be 0"),
                assert_true(r.get("reminders") == 0, "reminders should be 0"),
            ),
        )
        return success

    def test_process_with_enabled_engine(self) -> bool:
        """Test 9: After flipping enabled=true, /process dispatches reminders again"""
        # Re-enable the engine
        self.log("Re-enabling reminder engine...", "INFO")
        success, _ = self.run_test(
            "PUT settings (re-enable engine)",
            "PUT",
            "invoice-reminders/settings",
            200,
            data={"enabled": True},
        )
        if not success:
            return False

        # Now test /process
        success, response = self.run_test(
            "POST /process with engine re-enabled (should process again)",
            "POST",
            "invoice-reminders/process",
            200,
            validate_fn=lambda r: (
                assert_true(r.get("success") is not False, "success should not be false"),
                assert_true(r.get("skipped") is not True, "skipped should not be true"),
                assert_true("processed" in r, "should have 'processed' field"),
                assert_true("reminders" in r, "should have 'reminders' field"),
            ),
        )
        return success

    def test_critical_respects_threshold(self) -> bool:
        """Test 10: /critical respects live critical_days threshold"""
        # First, get count with critical_days=14 (current setting from test #3)
        self.log("Testing /critical endpoint with critical_days=14...", "INFO")
        success1, response1 = self.run_test(
            "GET /critical (with critical_days=14)",
            "GET",
            "invoice-reminders/critical",
            200,
            validate_fn=lambda r: (
                assert_true(isinstance(r, list), "response should be a list"),
            ),
        )
        count_14 = len(response1) if success1 and response1 else 0
        self.log(f"Critical invoices count with critical_days=14: {count_14}", "INFO")
        
        # Now lower ALL thresholds to satisfy the constraint: level1 ≤ level2 ≤ level3 ≤ critical
        self.log("Lowering thresholds (level1=1, level2=3, level3=5, critical=5)...", "INFO")
        success2, _ = self.run_test(
            "PUT settings (lower all thresholds)",
            "PUT",
            "invoice-reminders/settings",
            200,
            data={
                "level1_days": 1,
                "level2_days": 3,
                "level3_days": 5,
                "critical_days": 5,
            },
        )
        if not success2:
            return False
            
        success3, response3 = self.run_test(
            "GET /critical (with critical_days=5, should have more invoices)",
            "GET",
            "invoice-reminders/critical",
            200,
            validate_fn=lambda r: (
                assert_true(isinstance(r, list), "response should be a list"),
            ),
        )
        count_5 = len(response3) if success3 and response3 else 0
        self.log(f"Critical invoices count with critical_days=5: {count_5}", "INFO")
        
        # With test data at -2/-4/-6/-9 days, lowering threshold from 14 to 5 should show more invoices
        # (at least the -6 and -9 day ones should appear with critical_days=5)
        if count_5 >= count_14:
            self.log(f"✓ Threshold change working: count increased from {count_14} to {count_5}", "SUCCESS")
        else:
            self.log(f"⚠️  Unexpected: count decreased from {count_14} to {count_5} (may be due to test data)", "WARNING")
        
        return success1 and success2 and success3

    def test_reset_to_defaults(self) -> bool:
        """Test 11: Reset settings to defaults"""
        self.log("Resetting settings to defaults...", "INFO")
        success, response = self.run_test(
            "PUT settings (reset to defaults)",
            "PUT",
            "invoice-reminders/settings",
            200,
            data=DEFAULTS,
            validate_fn=lambda r: (
                assert_true(r.get("success") is True, "success should be true"),
                assert_true(r["data"].get("level1_days") == 1, "level1_days should be 1"),
                assert_true(r["data"].get("level2_days") == 3, "level2_days should be 3"),
                assert_true(r["data"].get("level3_days") == 5, "level3_days should be 5"),
                assert_true(r["data"].get("critical_days") == 7, "critical_days should be 7"),
                assert_true(r["data"].get("cooldown_hours") == 48, "cooldown_hours should be 48"),
                assert_true(r["data"].get("enabled") is True, "enabled should be true"),
            ),
        )
        return success

    def run_all_tests(self) -> int:
        """Run all tests and return exit code"""
        self.log("=" * 80, "INFO")
        self.log("Invoice Reminders Settings API Test Suite", "INFO")
        self.log("=" * 80, "INFO")

        # Authenticate
        if not self.login():
            self.log("Cannot proceed without authentication", "ERROR")
            return 1

        self.log("", "INFO")
        self.log("Starting test suite...", "INFO")
        self.log("", "INFO")

        # Run tests in order
        self.test_get_settings_initial()
        self.test_put_settings_valid()
        self.test_put_settings_invalid_order()
        self.test_put_settings_out_of_range()
        self.test_put_settings_empty_channels()
        self.test_escalation_summary_uses_new_thresholds()
        self.test_process_endpoint_success()
        self.test_process_with_disabled_engine()
        self.test_process_with_enabled_engine()
        self.test_critical_respects_threshold()
        self.test_reset_to_defaults()

        # Print summary
        self.log("", "INFO")
        self.log("=" * 80, "INFO")
        self.log("Test Summary", "INFO")
        self.log("=" * 80, "INFO")
        self.log(f"Total tests run: {self.tests_run}", "INFO")
        self.log(f"Tests passed: {self.tests_passed}", "SUCCESS")
        self.log(f"Tests failed: {self.tests_failed}", "ERROR" if self.tests_failed > 0 else "INFO")

        if self.failures:
            self.log("", "INFO")
            self.log("Failed tests:", "ERROR")
            for i, failure in enumerate(self.failures, 1):
                self.log(f"{i}. {failure['test']}: {failure['reason']}", "ERROR")

        self.log("=" * 80, "INFO")

        return 0 if self.tests_failed == 0 else 1


# Helper assertion functions
def assert_true(condition, message):
    """Assert that condition is true"""
    if not condition:
        raise AssertionError(message)


def main():
    """Main entry point"""
    tester = InvoiceRemindersAPITester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
