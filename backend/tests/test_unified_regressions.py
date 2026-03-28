import asyncio
import unittest
from typing import Any, cast
from unittest.mock import AsyncMock

from app.models.unified_intelligence import CapabilityExecutionStatus, CapabilitySet, CapabilityType, QueryComplexity, QueryAssessment, ReasoningResult
from app.models.visual_intelligence import (
    DataFetchResult,
    DomainType,
    IntentType,
    MapIntelligenceOutput,
    ParsedIntent,
    TimeRange,
)
from app.services.data_fetch_layer import DataFetchLayer
from app.services.intent_parser import get_intent_parser
from app.services.unified_intelligence_engine import ConversationSession, UnifiedIntelligenceEngine


def _build_intent(
    raw_query: str,
    countries=None,
    regions=None,
    requires_map: bool = False,
    map_features=None,
) -> ParsedIntent:
    return ParsedIntent(
        query_id="test-intent",
        raw_query=raw_query,
        countries=list(countries or []),
        regions=list(regions or []),
        cities=[],
        primary_domain=DomainType.ECONOMICS,
        secondary_domains=[],
        domain_confidence={"economics": 1.0},
        intent_type=IntentType.TREND,
        time_range=TimeRange(2019, 2023),
        requires_chart=True,
        chart_type=None,
        requires_diagram=False,
        diagram_type=None,
        requires_map=requires_map,
        map_features=list(map_features or []),
        indicators=["GDP"],
        comparison_entities=[],
        parse_confidence=0.95,
    )


class _FakeVisualEngine:
    def __init__(self, intent: ParsedIntent):
        self.intent = intent

    async def parse_intent(self, query: str) -> ParsedIntent:
        return self.intent


class _FakeMapLayer:
    def __init__(self):
        self.last_requires_map = None

    async def generate_map_intelligence(self, intent: ParsedIntent, data_result: DataFetchResult) -> MapIntelligenceOutput:
        self.last_requires_map = intent.requires_map
        commands = []
        if intent.requires_map:
            commands.append({"type": "highlight", "country_ids": ["IND"]})
        return MapIntelligenceOutput(
            commands=commands,
            affected_regions=intent.countries,
            geo_entities=[],
            markers=[],
            routes=[],
        )


class _FakeLLM:
    async def ainvoke(self, prompt: str):
        class _Response:
            content = (
                '{"title":"Generic","executive_brief":"Analysis completed.",'
                '"key_takeaways":[],"next_actions":[],"suggested_follow_ups":[],'
                '"memory_summary":"","response_blocks":[]}'
            )

        return _Response()


class UnifiedRegressionTests(unittest.TestCase):
    def test_intent_parser_normalizes_region_country_aliases(self):
        parser = get_intent_parser()
        intent = asyncio.run(parser.parse("Compare trade risk in Middle East and Europe"))

        self.assertIn("United Arab Emirates", intent.countries)
        self.assertIn("United Kingdom", intent.countries)
        self.assertNotIn("UAE", intent.countries)
        self.assertNotIn("UK", intent.countries)

    def test_data_fetch_layer_uses_default_country_basket_for_global_queries(self):
        layer = DataFetchLayer()
        layer._world_bank.fetch_indicator = AsyncMock(return_value=[])
        layer._data_commons.fetch_stats = AsyncMock(return_value=[])

        intent = _build_intent(raw_query="Global GDP trend over time", countries=[])
        result = asyncio.run(layer.fetch_for_intent(intent))
        asyncio.run(layer.close())

        self.assertIn("GDP", result.datasets)
        countries = {entry.get("country") for entry in result.datasets["GDP"].values}
        self.assertTrue({"United States", "China", "India"}.issubset(countries))

    def test_map_execution_forces_map_lane_when_map_mode_selected(self):
        engine = UnifiedIntelligenceEngine()
        engine._visual_engine = cast(
            Any,
            _FakeVisualEngine(
                _build_intent(
                    raw_query="Show map briefing for India",
                    countries=["India"],
                    requires_map=False,
                    map_features=[],
                )
            )
        )
        fake_map_layer = _FakeMapLayer()
        engine._map_intelligence = cast(Any, fake_map_layer)

        result = asyncio.run(
            engine._execute_map_intelligence(
                query_id="q1",
                query="Show map briefing for India",
                context={"execution_mode": "map_only", "_capabilities": ["map"]},
            )
        )

        self.assertIsNotNone(result)
        if result is None:
            self.fail("Map intelligence should return a result in map_only mode")
        self.assertTrue(fake_map_layer.last_requires_map)
        self.assertGreaterEqual(len(result.commands), 1)

    def test_low_signal_llm_payload_falls_back_to_deterministic_response(self):
        engine = UnifiedIntelligenceEngine()
        engine._llm = cast(Any, _FakeLLM())

        assessment = QueryAssessment(
            complexity=QueryComplexity.MODERATE,
            domains=["geopolitics"],
            has_geographic_entities=True,
            has_data_indicators=False,
            has_time_dimension=True,
            requires_external_data=False,
            requires_multi_perspective=True,
            confidence=0.8,
            suggested_capabilities=CapabilitySet(reasoning=True),
        )

        reasoning = ReasoningResult(
            executive_summary="Border posture has intensified with elevated escalation risk.",
            analysis="Detailed analysis",
            key_findings=["Border posture has hardened over the last 30 days."],
            confidence=0.82,
            expert_agents_used=["risk"],
            consensus_achieved=True,
            processing_time_ms=10.0,
            risk_factors=[],
            strategic_recommendations=["Increase satellite and ISR cadence in vulnerable sectors."],
            uncertainty_factors=[],
            timeline=[],
        )

        payload = asyncio.run(
            engine._build_assistant_response(
                query="Assess current India-China border risk",
                assessment=assessment,
                results={"reasoning": reasoning},
                statuses=[
                    CapabilityExecutionStatus(
                        capability=CapabilityType.REASONING,
                        success=True,
                        execution_time_ms=10.0,
                    )
                ],
                unified_summary=reasoning.executive_summary,
                session=ConversationSession(conversation_id="c1"),
                allow_cloud_synthesis=True,
            )
        )

        self.assertIn("Border posture has hardened", " ".join(payload.key_takeaways))
        self.assertNotEqual(payload.executive_brief.strip(), "Analysis completed.")


if __name__ == "__main__":
    unittest.main()
