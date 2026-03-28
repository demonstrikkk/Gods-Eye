import unittest
from unittest.mock import patch
import time
import urllib.error

from app.services.osint_aggregator import OSINTAggregator
from app.core.config import settings


class OSINTAggregatorTests(unittest.TestCase):
    def setUp(self):
        OSINTAggregator._cache.clear()

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

    @patch.object(OSINTAggregator, "get_feed_cache_search_results")
    @patch.object(OSINTAggregator, "get_google_news_search_results")
    @patch.object(OSINTAggregator, "get_serpapi_search_results")
    @patch.object(OSINTAggregator, "get_yahoo_search_results")
    @patch.object(OSINTAggregator, "get_duckduckgo_search_results")
    def test_search_query_bundle_merges_fastest_completed_sources(
        self,
        mock_ddg,
        mock_yahoo,
        mock_serpapi,
        mock_google_news,
        mock_feed_cache,
    ):
        def delayed_payload(source: str, delay: float, url: str, status: str = "live"):
            time.sleep(delay)
            return {
                "source": source,
                "query": "india strategic outlook",
                "results": [{"title": f"{source} result", "url": url}],
                "status": status,
                "strategy": "test",
            }

        mock_ddg.side_effect = lambda query=None: delayed_payload("DuckDuckGo", 0.01, "https://example.com/a")
        mock_yahoo.side_effect = lambda query=None: delayed_payload("Yahoo", 0.02, "https://example.com/b")
        mock_serpapi.side_effect = lambda query=None: delayed_payload("SerpAPI", 0.03, "https://example.com/c")
        mock_google_news.side_effect = lambda query=None: delayed_payload("Google News", 0.04, "https://example.com/a")
        mock_feed_cache.side_effect = lambda query=None: delayed_payload("Feed Cache", 0.2, "https://example.com/d", status="limited")

        bundle = OSINTAggregator.search_query_bundle("india strategic outlook", limit=10, max_providers=4)

        self.assertEqual(bundle["status"], "live")
        self.assertEqual(bundle["selected_provider_count"], 4)
        self.assertLessEqual(len(bundle["results"]), 3)
        self.assertTrue(any(provider["source"] == "DuckDuckGo" for provider in bundle["providers"]))
        self.assertTrue(any(provider["category"] == "news_search" for provider in bundle["providers"]))
        self.assertTrue(all("latency_ms" in provider for provider in bundle["providers"]))

    @patch("urllib.request.urlopen")
    def test_yahoo_search_classifies_rate_limit_errors(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://search.yahoo.com/search?p=india",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=None,
        )

        payload = OSINTAggregator.get_yahoo_search_results(query="india rate limit probe")

        self.assertEqual(payload["status"], "rate_limited")
        self.assertIn("too many requests", payload["message"].lower())


if __name__ == "__main__":
    unittest.main()
