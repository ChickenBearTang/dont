from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from ai.crawler.quasarzone_check import check_keywords, fetch_response_body


class QuasarZoneCheckTest(unittest.TestCase):
    def test_check_keywords_reports_matches(self) -> None:
        body = "포카리스웨트 21,200 /bbs/qb_saleinfo/views/1932646"

        result = check_keywords(body, ["포카리스웨트", "없는값"])

        self.assertEqual(result, {"포카리스웨트": True, "없는값": False})

    @patch("ai.crawler.quasarzone_check.requests.get")
    def test_fetch_response_body_returns_status_and_body(self, mock_get: MagicMock) -> None:
        response = MagicMock()
        response.status_code = 200
        response.text = "response body"
        response.raise_for_status.return_value = None
        mock_get.return_value = response

        status_code, body = fetch_response_body()

        self.assertEqual(status_code, 200)
        self.assertEqual(body, "response body")
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
