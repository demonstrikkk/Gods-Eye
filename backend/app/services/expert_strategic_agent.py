"""
Expert Strategic Agent Integration
===================================

Connects the Strategic Agent with the Expert Agent Framework for:
- Expert-level reasoning with uncertainty quantification
- Multi-agent debate and consensus building
- Evidence citation and source tracking
- Probabilistic outputs with confidence intervals
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.agents.agent_orchestrator import (
    ExpertAgentOrchestrator,
    OrchestratedResponse,
    run_expert_analysis,
)
from app.agents.expert_base import ConfidenceLevel
from app.agents.consensus_builder import ConsensusStrength
from app.agents.evidence_tracker import evidence_tracker
from app.agents.uncertainty_engine import uncertainty_quantifier

from . import strategic_agent

logger = logging.getLogger("expert_strategic_agent")


class ExpertStrategicAgent:
    """
    Expert-level Strategic Agent wrapper.

    Enhances the base strategic agent with:
    - Expert agent consultation
    - Multi-agent debate
    - Uncertainty quantification
    - Evidence citation
    - Consensus/disagreement tracking
    """

    def __init__(self, enable_debate: bool = True):
        self.orchestrator = ExpertAgentOrchestrator(enable_debate=enable_debate)
        self.logger = logging.getLogger("expert_strategic_agent")

    async def run_expert_strategic_analysis(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run expert-level strategic analysis with full reasoning capabilities.

        This combines:
        1. Base strategic agent tool execution
        2. Expert agent reasoning
        3. Multi-agent debate (if divergence detected)
        4. Consensus building
        5. Uncertainty quantification

        Returns enhanced analysis with confidence levels and citations.
        """
        import time
        start_time = time.time()

        self.logger.info(f"Running expert strategic analysis: {query[:100]}...")

        # Step 1: Get base strategic analysis (tools + basic reasoning)
        base_analysis = await strategic_agent.run_strategic_analysis(query)

        # Step 2: Run expert agent analysis
        expert_response = await run_expert_analysis(query, context or {})

        # Step 3: Merge and enhance the analysis
        enhanced_analysis = self._merge_analyses(
            base_analysis=base_analysis,
            expert_response=expert_response,
            query=query,
        )

        processing_time = (time.time() - start_time) * 1000
        enhanced_analysis["_meta"]["expert_processing_time_ms"] = processing_time

        self.logger.info(f"Expert analysis complete in {processing_time:.0f}ms")

        return enhanced_analysis

    def _merge_analyses(
        self,
        base_analysis: Dict[str, Any],
        expert_response: OrchestratedResponse,
        query: str,
    ) -> Dict[str, Any]:
        """Merge base strategic analysis with expert agent insights."""

        # Start with base analysis
        merged = dict(base_analysis)

        # Add expert reasoning layer
        merged["expert_assessment"] = {
            "consensus_view": expert_response.consensus.consensus_view if expert_response.consensus else None,
            "confidence": {
                "level": expert_response.overall_confidence,
                "score": expert_response.confidence_score,
                "strength": expert_response.consensus.consensus_strength.value if expert_response.consensus else "unknown",
            },
            "key_findings": expert_response.key_findings,
            "data_sources_cited": expert_response.data_sources_cited,
        }

        # Add disagreements if any
        if expert_response.disagreements:
            merged["expert_assessment"]["disagreements"] = expert_response.disagreements
            merged["expert_assessment"]["disagreement_summary"] = (
                f"{len(expert_response.disagreements)} areas of disagreement among expert agents"
            )

        # Add minority opinions
        if expert_response.minority_opinions:
            merged["expert_assessment"]["minority_opinions"] = expert_response.minority_opinions

        # Enhance uncertainty quantification
        merged["uncertainty_quantification"] = {
            "overall_confidence": expert_response.confidence_score,
            "confidence_level": expert_response.overall_confidence,
            "uncertainty_factors": expert_response.uncertainty_factors,
            "key_assumptions": expert_response.key_assumptions,
            "data_gaps": expert_response.consensus.data_gaps if expert_response.consensus else [],
        }

        # Add probabilistic scenarios
        if expert_response.scenarios:
            merged["probabilistic_scenarios"] = expert_response.scenarios

        # Add causal chain
        if expert_response.causal_chain:
            merged["causal_reasoning_chain"] = expert_response.causal_chain

        # Add debate summary if debate occurred
        if expert_response.debate_conducted:
            merged["debate_summary"] = expert_response.debate_summary

        # Add map visualization data
        merged["map_visualization"] = {
            "layers": expert_response.map_layers,
            "affected_regions": expert_response.affected_regions,
        }

        # Add agent contributions
        merged["agent_contributions"] = expert_response.consensus.agent_contributions if expert_response.consensus else {}

        # Enhanced recommendations blending both sources
        base_recs = merged.get("strategic_recommendations", [])
        expert_recs = expert_response.recommendations
        merged["strategic_recommendations"] = self._blend_recommendations(base_recs, expert_recs)

        # Update metadata
        if "_meta" not in merged:
            merged["_meta"] = {}

        merged["_meta"].update({
            "expert_agents_consulted": expert_response.agents_consulted,
            "debate_conducted": expert_response.debate_conducted,
            "consensus_strength": expert_response.consensus.consensus_strength.value if expert_response.consensus else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine": "JanGraph Expert Strategic Intelligence v4.0",
        })

        return merged

    def _blend_recommendations(
        self,
        base_recs: List[str],
        expert_recs: List[str]
    ) -> List[str]:
        """Blend recommendations from base and expert analysis."""
        seen = set()
        blended = []

        # Expert recommendations first (higher confidence)
        for rec in expert_recs:
            normalized = rec.lower()[:50]
            if normalized not in seen:
                blended.append(f"[Expert] {rec}")
                seen.add(normalized)

        # Then base recommendations
        for rec in base_recs:
            normalized = rec.lower()[:50]
            if normalized not in seen:
                blended.append(rec)
                seen.add(normalized)

        return blended[:8]

    def format_expert_output(self, analysis: Dict[str, Any]) -> str:
        """Format expert analysis for display."""
        lines = []

        lines.append("=" * 80)
        lines.append("JANGRAPH OS — EXPERT STRATEGIC INTELLIGENCE ASSESSMENT")
        lines.append("=" * 80)
        lines.append("")

        # Executive summary
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 60)
        lines.append(analysis.get("executive_summary", "N/A"))
        lines.append("")

        # Expert assessment
        expert = analysis.get("expert_assessment", {})
        if expert:
            lines.append("EXPERT CONSENSUS")
            lines.append("-" * 60)
            if expert.get("consensus_view"):
                lines.append(expert["consensus_view"])
            lines.append("")

            conf = expert.get("confidence", {})
            lines.append(f"Confidence Level: {conf.get('level', 'N/A')} ({conf.get('score', 0):.0%})")
            lines.append(f"Consensus Strength: {conf.get('strength', 'N/A')}")
            lines.append("")

        # Disagreements
        disagreements = expert.get("disagreements", [])
        if disagreements:
            lines.append("AREAS OF DISAGREEMENT")
            lines.append("-" * 60)
            for d in disagreements[:3]:
                lines.append(f"  - {d.get('topic', 'Unknown')}")
                lines.append(f"    Severity: {d.get('severity', 'N/A')}")
            lines.append("")

        # Uncertainty
        uncertainty = analysis.get("uncertainty_quantification", {})
        if uncertainty.get("uncertainty_factors"):
            lines.append("UNCERTAINTY FACTORS")
            lines.append("-" * 60)
            for uf in uncertainty["uncertainty_factors"][:5]:
                lines.append(f"  ! {uf}")
            lines.append("")

        # Key assumptions
        if uncertainty.get("key_assumptions"):
            lines.append("KEY ASSUMPTIONS")
            lines.append("-" * 60)
            for ka in uncertainty["key_assumptions"][:5]:
                lines.append(f"  * {ka}")
            lines.append("")

        # Scenarios
        scenarios = analysis.get("probabilistic_scenarios", {})
        if scenarios:
            lines.append("PROBABILISTIC SCENARIOS")
            lines.append("-" * 60)
            for name, data in scenarios.items():
                if isinstance(data, dict):
                    prob = data.get("probability", 0)
                    lines.append(f"  {name.title()}: {prob:.0%}")
            lines.append("")

        # Recommendations
        recs = analysis.get("strategic_recommendations", [])
        if recs:
            lines.append("STRATEGIC RECOMMENDATIONS")
            lines.append("-" * 60)
            for rec in recs[:5]:
                lines.append(f"  > {rec}")
            lines.append("")

        # Data sources
        sources = expert.get("data_sources_cited", [])
        if sources:
            lines.append("DATA SOURCES CITED")
            lines.append("-" * 60)
            for src in sources[:10]:
                lines.append(f"  - {src}")
            lines.append("")

        # Agent contributions
        agents = analysis.get("agent_contributions", {})
        if agents:
            lines.append("AGENT CONTRIBUTIONS")
            lines.append("-" * 60)
            for agent_id, contrib in agents.items():
                lines.append(f"  - {contrib.get('name', agent_id)}: {contrib.get('domain', 'N/A')} (confidence: {contrib.get('confidence', 0):.0%})")
            lines.append("")

        # Metadata
        meta = analysis.get("_meta", {})
        lines.append("=" * 80)
        lines.append(f"Generated: {meta.get('timestamp', 'N/A')}")
        lines.append(f"Engine: {meta.get('engine', 'N/A')}")
        lines.append(f"Debate Conducted: {'Yes' if meta.get('debate_conducted') else 'No'}")
        lines.append(f"Consensus: {meta.get('consensus_strength', 'N/A')}")
        lines.append("=" * 80)

        return "\n".join(lines)


# Global expert agent instance
expert_strategic_agent = ExpertStrategicAgent()


async def run_expert_strategic_analysis(
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Main entry point for expert-level strategic analysis.

    This is the highest-level reasoning function combining:
    - Base strategic agent tools
    - Expert domain agents
    - Multi-agent debate
    - Consensus building
    - Uncertainty quantification
    - Evidence citation
    """
    return await expert_strategic_agent.run_expert_strategic_analysis(query, context)


# Enhanced what-if with uncertainty
async def run_expert_whatif_simulation(
    original_context: str,
    whatif_query: str,
    variables: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enhanced what-if simulation with uncertainty quantification.
    """
    # Get base simulation
    base_sim = await strategic_agent.run_whatif_simulation(
        original_context, whatif_query, variables
    )

    # Add Monte Carlo uncertainty
    mc_result = uncertainty_quantifier.monte_carlo_simulation(
        variables={
            k: {"distribution": "normal", "params": {"mean": v.get("value", 0.5), "std": 0.15}}
            for k, v in variables.items() if isinstance(v, dict)
        },
        model_function=lambda **kwargs: sum(kwargs.values()) / len(kwargs) if kwargs else 0.5,
        n_iterations=1000,
    )

    base_sim["uncertainty_analysis"] = {
        "monte_carlo": {
            "mean": mc_result["mean"],
            "std": mc_result["std"],
            "confidence_interval_90": mc_result["confidence_interval_90"],
            "percentiles": mc_result["percentiles"],
        },
        "methodology": "Monte Carlo simulation with 1000 iterations",
    }

    return base_sim
