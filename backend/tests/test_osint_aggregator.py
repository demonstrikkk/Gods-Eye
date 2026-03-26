import unittest
from unittest.mock import patch

from app.services.osint_aggregator import OSINTAggregator
from app.core.config import settings


class OSINTAggregatorTests(unittest.TestCase):
    def test_extract_data_gov_entries_prefers_api_detail_links(self):
        html = """
        <html>
          <head><title>Power Generation Dataset</title></head>
          <body>
            <a href="/resource/mode-wise-sector-wise-break-power-generation">Dataset</a>
            <a href="/apis/100005bf-954a-4860-9407-189e132155eb">API</a>
          </body>
        </html>
        """

        entries = OSINTAggregator._extract_data_gov_entries(html, "power generation")

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["resource_id"], "100005bf-954a-4860-9407-189e132155eb")
        self.assertEqual(entries[0]["discovered_from"], "api_detail")
        self.assertEqual(entries[0]["title"], "Power Generation Dataset")

    def test_get_data_gov_snapshot_uses_explicit_resource_ids(self):
        payload = {
            "title": "Power Generation Dataset",
            "records": [{"year": 2024}, {"year": 2025}],
        }

        with patch.object(settings, "DATA_GOV_IN_KEY", "test-key"), patch.object(
            settings,
            "VITE_DATA_GOV_IN_KEY",
            "",
        ), patch.object(
            settings,
            "DATA_GOV_IN_RESOURCE_IDS",
            "100005bf-954a-4860-9407-189e132155eb",
        ), patch.object(
            OSINTAggregator,
            "_discover_data_gov_resources",
            side_effect=AssertionError("Discovery should not be used when resource IDs are configured"),
        ), patch(
            "app.services.osint_aggregator._json_get",
            return_value=payload,
        ) as mock_json_get:
            snapshot = OSINTAggregator.get_data_gov_snapshot()

        self.assertEqual(snapshot["status"], "live")
        self.assertEqual(snapshot["strategy"], "resource_ids")
        self.assertEqual(len(snapshot["datasets"]), 1)
        self.assertEqual(snapshot["datasets"][0]["title"], "Power Generation Dataset")
        self.assertEqual(snapshot["datasets"][0]["record_count"], 2)
        mock_json_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
