from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import subprocess
import sys
import threading
from typing import Any, cast
import unittest


class _FinanceMockHandler(BaseHTTPRequestHandler):
    payload = {
        "currentBalance": 987654.0,
        "emergencyFundBalance": 222222.0,
        "expectedCardPaymentAmount": 12345.0,
        "daysUntilCardDue": 9,
    }
    status_code = 200

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(self.status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if self.status_code == 200:
            self.wfile.write(json.dumps(self.payload).encode("utf-8"))
        else:
            self.wfile.write(b'{"error":"boom"}')

    def log_message(self, format: str, *args: object) -> None:
        return


class MainFinanceIntegrationTest(unittest.TestCase):
    def _run_ai(self, *args: str) -> dict[str, Any]:
        completed = subprocess.run(
            [sys.executable, "-m", "ai", *args],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, msg=completed.stderr)
        payload = json.loads(completed.stdout.strip())
        self.assertIsInstance(payload, dict)
        return payload

    def _run_server(self, status_code: int) -> tuple[ThreadingHTTPServer, str]:
        _FinanceMockHandler.status_code = status_code
        server = ThreadingHTTPServer(("127.0.0.1", 0), _FinanceMockHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}/finance-profile"
        return server, base_url

    def test_main_uses_spring_finance_profile_when_api_succeeds(self) -> None:
        server, url = self._run_server(status_code=200)
        try:
            data = self._run_ai("--xai", "--finance-api-url", url, "--top-k", "2")
        finally:
            server.shutdown()
            server.server_close()

        analysis = data.get("analysis")
        self.assertIsInstance(analysis, dict)
        analysis_dict = cast(dict[str, Any], analysis)
        self.assertEqual(analysis_dict["finance_profile_source"], "spring_api")
        self.assertEqual(
            analysis_dict["finance_profile"],
            {
                "current_balance": 987654.0,
                "emergency_fund_balance": 222222.0,
                "expected_card_payment_amount": 12345.0,
                "days_until_card_due": 9,
            },
        )

    def test_main_falls_back_to_cli_finance_profile_on_api_failure(self) -> None:
        server, url = self._run_server(status_code=500)
        try:
            data = self._run_ai(
                "--xai",
                "--finance-api-url",
                url,
                "--current-balance",
                "111000",
                "--emergency-fund-balance",
                "333000",
                "--expected-card-payment-amount",
                "77777",
                "--days-until-card-due",
                "5",
            )
        finally:
            server.shutdown()
            server.server_close()

        analysis = data.get("analysis")
        self.assertIsInstance(analysis, dict)
        analysis_dict = cast(dict[str, Any], analysis)
        self.assertEqual(
            analysis_dict["finance_profile_source"],
            "cli_default_fallback",
        )
        self.assertEqual(
            analysis_dict["finance_profile"],
            {
                "current_balance": 111000.0,
                "emergency_fund_balance": 333000.0,
                "expected_card_payment_amount": 77777.0,
                "days_until_card_due": 5,
            },
        )


if __name__ == "__main__":
    unittest.main()
