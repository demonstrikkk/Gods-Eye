import unittest
from unittest.mock import patch

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.api.endpoints import data as data_endpoints
from app.main import app


app.router.on_startup.clear()
app.router.on_shutdown.clear()


class GlobalDataEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_global_overview_returns_wrapped_payload(self):
        overview = {
            "systemic_stress": 63,
            "critical_zones": 4,
            "total_assets": 11,
            "last_refresh": "2026-03-22T10:00:00",
            "provenance": {
                "live_sources": 2,
                "limited_sources": 1,
                "unavailable_sources": 0,
                "fallback_sources": 0,
                "error_sources": 0,
                "total_sources": 3,
                "seeded_context": True,
                "runtime_state_backed": True,
                "last_refresh": "2026-03-22T10:00:00",
            },
        }

        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_global_overview",
            return_value=overview,
        ):
            response = self.client.get("/api/v1/data/global/overview")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["systemic_stress"], overview["systemic_stress"])
        self.assertEqual(body["data"]["critical_zones"], overview["critical_zones"])
        self.assertEqual(body["data"]["total_assets"], overview["total_assets"])
        self.assertIn("provenance", body["data"])

    def test_global_countries_applies_region_and_min_risk_filters(self):
        countries = [
            {"id": "CTR-IND", "name": "India", "region": "Asia", "risk_index": 72},
            {"id": "CTR-JPN", "name": "Japan", "region": "Asia", "risk_index": 48},
            {"id": "CTR-DEU", "name": "Germany", "region": "Europe", "risk_index": 81},
        ]

        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_enriched_countries",
            return_value=countries,
        ):
            response = self.client.get("/api/v1/data/global/countries?region=Asia&min_risk=60")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["data"][0]["id"], "CTR-IND")

    def test_global_signals_applies_country_and_layer_filters(self):
        signals = [
            {
                "id": "sig-1",
                "country_id": "CTR-IND",
                "category": "Geopolitics",
                "severity": "High",
                "layer": "conflict",
            },
            {
                "id": "sig-2",
                "country_id": "CTR-IND",
                "category": "Economics",
                "severity": "Medium",
                "layer": "economics",
            },
            {
                "id": "sig-3",
                "country_id": "CTR-USA",
                "category": "Geopolitics",
                "severity": "High",
                "layer": "conflict",
            },
        ]

        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_dynamic_signals",
            return_value=signals,
        ):
            response = self.client.get(
                "/api/v1/data/global/signals?country_id=CTR-IND&layer=conflict"
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["data"][0]["id"], "sig-1")

    def test_global_signals_can_filter_to_runtime_only(self):
        runtime_signals = [
            {
                "id": "run-1",
                "country_id": "CTR-IND",
                "category": "Geopolitics",
                "severity": "High",
                "layer": "conflict",
                "source_mode": "runtime",
            }
        ]

        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_runtime_signals",
            return_value=runtime_signals,
        ) as mock_get_runtime_signals:
            response = self.client.get("/api/v1/data/global/signals?source_mode=runtime")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["data"][0]["source_mode"], "runtime")
        mock_get_runtime_signals.assert_called_once_with()

    def test_global_assets_passes_filters_to_runtime_engine(self):
        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_structural_assets",
            return_value=[{"id": "asset-1", "country_id": "CTR-IND", "layer": "infrastructure"}],
        ) as mock_get_structural_assets:
            response = self.client.get(
                "/api/v1/data/global/assets?country_id=CTR-IND&layer=infrastructure"
            )

        self.assertEqual(response.status_code, 200)
        mock_get_structural_assets.assert_called_once_with(
            country_id="CTR-IND",
            layer="infrastructure",
        )

    def test_global_assets_can_filter_to_seeded_only(self):
        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_seeded_assets",
            return_value=[{"id": "asset-1", "source_mode": "seeded"}],
        ) as mock_get_seeded_assets:
            response = self.client.get("/api/v1/data/global/assets?source_mode=seeded")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["data"][0]["source_mode"], "seeded")
        mock_get_seeded_assets.assert_called_once_with(country_id=None, layer=None)

    def test_global_corridors_can_filter_to_seeded_only(self):
        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_seeded_corridors",
            return_value=[{"id": "cor-1", "source_mode": "seeded"}],
        ) as mock_get_seeded_corridors:
            response = self.client.get("/api/v1/data/global/corridors?source_mode=seeded")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["data"][0]["source_mode"], "seeded")
        mock_get_seeded_corridors.assert_called_once_with()

    def test_country_analysis_returns_not_found_for_unknown_country(self):
        with patch(
            "app.services.runtime_intelligence.runtime_engine.get_country_analysis",
            return_value=None,
        ):
            response = self.client.get("/api/v1/data/global/country-analysis/CTR-UNKNOWN")

        self.assertEqual(response.status_code, 404)

    def test_data_router_has_unique_method_path_pairs(self):
        pairs = []
        for route in data_endpoints.router.routes:
            if not isinstance(route, APIRoute):
                continue
            for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
                pairs.append((method, route.path))

        self.assertEqual(len(pairs), len(set(pairs)))


if __name__ == "__main__":
    unittest.main()
