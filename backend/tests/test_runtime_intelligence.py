import unittest
from unittest.mock import patch

from app.services.runtime_intelligence import RuntimeIntelligenceEngine


class RuntimeIntelligenceEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RuntimeIntelligenceEngine()
        self.engine._state = self.engine._default_state()

    @patch("app.services.runtime_intelligence.store.get_global_signals")
    def test_get_dynamic_signals_deduplicates_and_prefers_runtime_state(self, mock_get_global_signals):
        mock_get_global_signals.return_value = [
            {
                "id": "shared-signal",
                "country_id": "CTR-IND",
                "title": "Seed signal",
                "category": "Economics",
                "severity": "Low",
            },
            {
                "id": "seed-only",
                "country_id": "CTR-USA",
                "title": "Seed only",
                "category": "Defense",
                "severity": "Medium",
            },
        ]
        self.engine._state["dynamic_signals"] = [
            {
                "id": "shared-signal",
                "country_id": "CTR-IND",
                "title": "Runtime signal",
                "category": "Conflict",
                "severity": "High",
            }
        ]

        signals = self.engine.get_dynamic_signals()

        self.assertEqual(len(signals), 2)
        self.assertEqual(signals[0]["title"], "Runtime signal")
        self.assertEqual(signals[1]["id"], "seed-only")
        self.assertEqual(signals[0]["source_mode"], "runtime")
        self.assertEqual(signals[1]["source_mode"], "seeded")

    @patch("app.services.runtime_intelligence.store.get_global_signals")
    def test_runtime_and_seeded_signal_accessors_are_separated(self, mock_get_global_signals):
        mock_get_global_signals.return_value = [
            {"id": "seed-1", "country_id": "CTR-IND", "title": "Seed signal"}
        ]
        self.engine._state["dynamic_signals"] = [
            {"id": "run-1", "country_id": "CTR-USA", "title": "Runtime signal"}
        ]

        runtime_signals = self.engine.get_runtime_signals()
        seeded_signals = self.engine.get_seeded_signals()

        self.assertEqual([signal["id"] for signal in runtime_signals], ["run-1"])
        self.assertEqual([signal["id"] for signal in seeded_signals], ["seed-1"])
        self.assertEqual(runtime_signals[0]["source_origin"], "runtime_state")
        self.assertEqual(seeded_signals[0]["source_origin"], "seeded_ontology")

    @patch("app.services.runtime_intelligence.store.get_global_assets")
    @patch("app.services.runtime_intelligence.store.get_global_countries")
    def test_get_enriched_countries_merges_runtime_counts_into_seeded_country(
        self,
        mock_get_global_countries,
        mock_get_global_assets,
    ):
        mock_get_global_countries.return_value = [
            {
                "id": "CTR-IND",
                "name": "India",
                "region": "Asia",
                "lat": 20.5937,
                "lng": 78.9629,
                "risk_index": 52,
                "influence_index": 75,
                "sentiment": 61,
                "stability": "Watch",
                "pressure": "Existing pressure",
                "top_domains": [],
                "active_signals": 1,
                "asset_count": 1,
                "capital": "New Delhi",
                "population": 1_400_000_000,
            }
        ]
        mock_get_global_assets.return_value = [
            {"id": "asset-1", "country_id": "CTR-IND", "layer": "infrastructure"},
            {"id": "asset-2", "country_id": "CTR-IND", "layer": "cyber"},
        ]
        runtime_signals = [
            {"id": "sig-1", "country_id": "CTR-IND", "layer": "conflict", "category": "Geopolitics"},
            {"id": "sig-2", "country_id": "CTR-IND", "layer": "cyber", "category": "Cyber"},
            {"id": "sig-3", "country_id": "CTR-IND", "layer": "climate", "category": "Climate"},
        ]
        self.engine.get_runtime_signals = lambda: runtime_signals
        self.engine.get_seeded_signals = lambda: []
        self.engine.get_dynamic_signals = lambda include_seeded=True: list(runtime_signals)

        countries = self.engine.get_enriched_countries()

        self.assertEqual(len(countries), 1)
        self.assertEqual(countries[0]["active_signals"], 3)
        self.assertEqual(countries[0]["asset_count"], 2)
        self.assertIn("Cyber", countries[0]["top_domains"])
        self.assertEqual(countries[0]["runtime_signal_count"], 3)
        self.assertEqual(countries[0]["seeded_signal_count"], 0)
        self.assertEqual(countries[0]["signal_source_mode"], "runtime_only")

    @patch("app.services.runtime_intelligence.osint_engine.get_country_search_briefs")
    @patch("app.services.runtime_intelligence.osint_engine.get_world_bank_snapshot")
    @patch("app.services.runtime_intelligence.osint_engine.get_open_meteo_weather")
    @patch("app.services.runtime_intelligence.store.get_recent_feed_briefs")
    def test_country_analysis_marks_search_as_unavailable_when_live_results_absent(
        self,
        mock_get_recent_feed_briefs,
        mock_get_open_meteo_weather,
        mock_get_world_bank_snapshot,
        mock_get_country_search_briefs,
    ):
        self.engine.get_country = lambda country_id: {
            "id": country_id,
            "name": "India",
            "capital": "New Delhi",
            "iso3": "IND",
            "lat": 28.6139,
            "lng": 77.209,
            "stability": "Watch",
            "risk_index": 68,
            "influence_index": 82,
            "pressure": "Cross-domain stress",
            "top_domains": ["Economics", "Infrastructure", "Cyber"],
            "active_signals": 2,
            "asset_count": 1,
        }
        runtime_signals = [
            {
                "id": "sig-1",
                "country_id": "CTR-IND",
                "title": "Shipping disruption alert",
                "summary": "Corridor pressure rising.",
                "severity": "High",
                "layer": "mobility",
            }
        ]
        self.engine.get_runtime_signals = lambda: runtime_signals
        self.engine.get_seeded_signals = lambda: []
        self.engine.get_dynamic_signals = lambda include_seeded=True: list(runtime_signals)
        self.engine.get_structural_assets = lambda country_id=None, layer=None: [
            {
                "id": "asset-1",
                "country_id": "CTR-IND",
                "kind": "Port",
                "importance": 90,
                "description": "Major strategic port",
            }
        ]
        mock_get_recent_feed_briefs.return_value = [
            {"text": "New Delhi reviewing corridor posture", "summary": "Capital-linked coverage"}
        ]
        mock_get_open_meteo_weather.return_value = {
            "status": "live",
            "current": {"temperature_2m": 31, "wind_speed_10m": 12},
            "daily": {"precipitation_sum": 1.8},
        }
        mock_get_world_bank_snapshot.return_value = {
            "countries": {
                "IND": {
                    "gdp_current_usd": {"value": 3_500_000_000_000, "date": "2024"},
                    "inflation_consumer": {"value": 5.4, "date": "2024"},
                }
            }
        }
        mock_get_country_search_briefs.return_value = {
            "status": "fallback",
            "results": [{"title": "Unsupported result"}],
        }

        analysis = self.engine.get_country_analysis("CTR-IND")

        self.assertIsNotNone(analysis)
        self.assertEqual(analysis["search_briefs"]["status"], "unavailable")
        self.assertEqual(analysis["search_briefs"]["results"], [])
        self.assertIn(
            "unsupported search claims",
            analysis["research_brief"].lower(),
        )
        open_search = next(
            item for item in analysis["source_status"] if item["label"] == "Open Search"
        )
        self.assertEqual(open_search["status"], "unavailable")
        self.assertEqual(
            analysis["provenance"]["analysis_mode"],
            "seeded_context_plus_live_enrichment",
        )
        self.assertIn("Open-Meteo", analysis["provenance"]["live_source_labels"])
        self.assertEqual(analysis["provenance"]["runtime_signal_count"], 1)
        self.assertEqual(analysis["provenance"]["seeded_signal_count"], 0)

    @patch("app.services.runtime_intelligence.store.get_global_overview")
    def test_global_overview_includes_provenance_summary(self, mock_get_global_overview):
        mock_get_global_overview.return_value = {
            "systemic_stress": 51,
            "critical_zones": 2,
        }
        self.engine._state.update(
            {
                "last_refresh": "2026-03-22T12:00:00",
                "source_health": [
                    {"id": "a", "status": "live"},
                    {"id": "b", "status": "limited"},
                    {"id": "c", "status": "unavailable"},
                    {"id": "d", "status": "fallback"},
                    {"id": "e", "status": "error"},
                ],
                "market_snapshot": [{"ticker": "SPY"}],
            }
        )
        self.engine.get_enriched_countries = lambda: [{"id": "CTR-IND"}]
        self.engine.get_dynamic_signals = lambda include_seeded=True: [{"id": "sig-1"}]
        self.engine.get_runtime_signals = lambda: [{"id": "sig-1"}]
        self.engine.get_seeded_signals = lambda: []
        self.engine.get_structural_assets = lambda country_id=None, layer=None: [{"id": "asset-1"}]
        self.engine.get_runtime_assets = lambda country_id=None, layer=None: []
        self.engine.get_seeded_assets = lambda country_id=None, layer=None: [{"id": "asset-1"}]
        self.engine.get_global_corridors = lambda include_seeded=True: [{"id": "cor-1"}]
        self.engine.get_runtime_corridors = lambda: []
        self.engine.get_seeded_corridors = lambda: [{"id": "cor-1"}]

        overview = self.engine.get_global_overview()

        self.assertEqual(overview["provenance"]["live_sources"], 1)
        self.assertEqual(overview["provenance"]["limited_sources"], 1)
        self.assertEqual(overview["provenance"]["unavailable_sources"], 1)
        self.assertEqual(overview["provenance"]["fallback_sources"], 1)
        self.assertEqual(overview["provenance"]["error_sources"], 1)
        self.assertEqual(overview["provenance"]["last_refresh"], "2026-03-22T12:00:00")
        self.assertEqual(overview["seeded_assets"], 1)
        self.assertEqual(overview["seeded_corridors"], 1)

    @patch("app.services.runtime_intelligence.store.get_global_corridors")
    @patch("app.services.runtime_intelligence.store.get_global_assets")
    def test_assets_and_corridors_are_annotated_as_seeded(
        self,
        mock_get_global_assets,
        mock_get_global_corridors,
    ):
        mock_get_global_assets.return_value = [{"id": "asset-1", "country_id": "CTR-IND"}]
        mock_get_global_corridors.return_value = [{"id": "cor-1", "from_country": "CTR-IND", "to_country": "CTR-USA"}]

        assets = self.engine.get_seeded_assets()
        corridors = self.engine.get_seeded_corridors()

        self.assertEqual(assets[0]["source_mode"], "seeded")
        self.assertEqual(corridors[0]["source_origin"], "seeded_ontology")


if __name__ == "__main__":
    unittest.main()
