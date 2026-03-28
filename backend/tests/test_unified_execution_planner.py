import asyncio
import unittest

from app.models.unified_intelligence import CapabilitySet, UnifiedExecutionMode, UnifiedIntelligenceRequest
from app.services.unified_intelligence_engine import QueryAssessor, UnifiedExecutionPlanner


class UnifiedExecutionPlannerTests(unittest.TestCase):
    def setUp(self):
        self.assessor = QueryAssessor()
        self.planner = UnifiedExecutionPlanner()

    def _assess(self, query: str):
        return asyncio.run(self.assessor.assess_query(query, {}))

    def test_fast_mode_prefers_brief_parallel_sources_and_limited_agents(self):
        query = "Latest India China border risk update and what matters now"
        assessment = self._assess(query)
        request = UnifiedIntelligenceRequest(query=query, execution_mode=UnifiedExecutionMode.FAST)
        capabilities = CapabilitySet(reasoning=True, tools=True)

        plan = self.planner.build_plan(query, assessment, request, capabilities)

        self.assertEqual(plan.execution_mode, "fast")
        self.assertEqual(plan.capabilities, ["reasoning", "tools"])
        self.assertLessEqual(len(plan.reasoning_agents), 2)
        self.assertIn("risk", plan.reasoning_agents)
        self.assertIn("search_bundle", plan.tools)
        self.assertIn("recent_briefs", plan.tools)
        self.assertTrue(any(step.id == "tools" and step.parallelizable for step in plan.steps))
        self.assertTrue(any(step.id == "reasoning" and step.parallelizable for step in plan.steps))

    def test_tools_only_plan_keeps_economic_fetches_and_disables_reasoning_agents(self):
        query = "Current GDP inflation and market outlook for India"
        assessment = self._assess(query)
        request = UnifiedIntelligenceRequest(query=query, execution_mode=UnifiedExecutionMode.TOOLS_ONLY)
        capabilities = CapabilitySet(tools=True)

        plan = self.planner.build_plan(query, assessment, request, capabilities)

        self.assertEqual(plan.capabilities, ["tools"])
        self.assertEqual(plan.reasoning_agents, [])
        self.assertIn("market_snapshot", plan.tools)
        self.assertIn("search_bundle", plan.tools)
        self.assertTrue(any("External-data" in reason or "live or cached source fetch" in reason for reason in plan.rationale))

    def test_visual_only_plan_builds_visual_lane_without_reasoning_or_tools(self):
        query = "Show a chart of India's GDP growth over time"
        assessment = self._assess(query)
        request = UnifiedIntelligenceRequest(query=query, execution_mode=UnifiedExecutionMode.VISUAL_ONLY)
        capabilities = CapabilitySet(visuals=True)

        plan = self.planner.build_plan(query, assessment, request, capabilities)

        self.assertEqual(plan.capabilities, ["visuals"])
        self.assertEqual(plan.reasoning_agents, [])
        self.assertEqual(plan.tools, [])
        self.assertTrue(any(step.id == "visuals" for step in plan.steps))
        self.assertFalse(any(step.id == "reasoning" for step in plan.steps))


if __name__ == "__main__":
    unittest.main()
