"""
Enhanced Strategic Agent with Expert-Level Reasoning

This module extends the strategic agent with:
- Multi-agent expert reasoning
- Internal debate and consensus building
- Uncertainty quantification
- Evidence-based citations
- Cross-domain validation

Integrates seamlessly with existing strategic_agent.py pipeline.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.services.expert_reasoning import (
    ExpertOrchestrator,
    ConsensusReport,
    ConfidenceLevel,
    Evidence,
    Citation,
    agent_registry,
)
from app.services.expert_reasoning.agents import create_all_expert_agents
from app.services.expert_reasoning.framework import UncertaintyBand
from app.services.llm_provider import get_enterprise_llm

logger = logging.getLogger("expert_strategic_agent")


class ExpertStrategicAgent:
    """
    Enhanced strategic agent with expert-level reasoning capabilities.

    Features:
    - 7 specialized expert agents with domain expertise
    - Internal debate mechanism for contested claims
    - Consensus building with explicit disagreements
    - Full citation and evidence tracking
    - Probabilistic outputs with uncertainty bands
    - Cross-agent validation
    """

    def __init__(self, llm_callable=None):
        self.llm_callable = llm_callable
        self.orchestrator = ExpertOrchestrator(llm_callable=llm_callable)
        self._initialized = False
        self.logger = logger

    def _ensure_initialized(self):
        """Ensure expert agents are initialized."""
        if not self._initialized:
            self.orchestrator.ensure_agents_initialized()
            self._initialized = True

    async def run_expert_analysis(
        self,
        query: str,
        tool_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run full expert analysis pipeline.

        This method:
        1. Dispatches query to relevant expert agents
        2. Collects initial assessments
        3. Conducts structured debate
        4. Builds consensus
        5. Returns comprehensive report

        Args:
            query: User's question or scenario
            tool_outputs: Data from OSINT tools

        Returns:
            Comprehensive analysis with consensus, disagreements, and confidence
        """
        self._ensure_initialized()

        start_time = datetime.utcnow()
        self.logger.info(f"Starting expert analysis: {query[:100]}...")

        try:
            # Run through expert orchestrator
            consensus = await self.orchestrator.process_query(query, tool_outputs)

            # Convert to enhanced output format
            result = self._format_expert_output(consensus, query, tool_outputs)

            elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.logger.info(f"Expert analysis completed in {elapsed_ms:.1f}ms")

            return result

        except Exception as e:
            self.logger.error(f"Expert analysis failed: {e}", exc_info=True)
            return self._fallback_expert_analysis(query, str(e))

    def _format_expert_output(
        self,
        consensus: ConsensusReport,
        query: str,
        tool_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Format consensus report into strategic analysis structure.

        Maintains compatibility with existing frontend expectations
        while adding expert reasoning metadata.
        """
        # Extract probability-based severity
        severity_map = {
            ConfidenceLevel.VERY_LOW: "Critical",
            ConfidenceLevel.LOW: "High",
            ConfidenceLevel.MODERATE: "Medium",
            ConfidenceLevel.HIGH: "Low",
            ConfidenceLevel.VERY_HIGH: "Very Low",
            ConfidenceLevel.NEAR_CERTAIN: "Minimal",
        }

        uncertainty_severity = severity_map.get(consensus.confidence, "Medium")

        # Build scenario tree from debate rounds
        scenario_tree = self._build_scenario_tree(consensus)

        # Build timeline from evidence
        timeline = self._build_timeline(consensus)

        # Format risk factors with expert attribution
        key_risk_factors = []
        for risk in consensus.risk_assessment.get("critical_risks", []):
            key_risk_factors.append({
                "factor": risk.get("factor", "Unknown"),
                "severity": risk.get("severity", "medium").capitalize(),
                "description": risk.get("description", ""),
                "probability": f"{risk.get('probability', 0.5):.0%}",
                "source_agent": risk.get("source_agent", "Risk Assessment"),
            })
        for risk in consensus.risk_assessment.get("high_risks", []):
            key_risk_factors.append({
                "factor": risk.get("factor", "Unknown"),
                "severity": risk.get("severity", "high").capitalize(),
                "description": risk.get("description", ""),
                "probability": f"{risk.get('probability', 0.5):.0%}",
                "source_agent": risk.get("source_agent", "Risk Assessment"),
            })

        # Build forecasts from probabilistic outputs
        forecasts = self._build_forecasts(consensus)

        # Build scenarios from scenario analysis
        scenarios = self._build_scenarios(consensus)

        # Impact on India analysis
        impact_on_india = self._build_india_impact(consensus)

        return {
            # Core analysis (compatible with existing structure)
            "executive_summary": consensus.consensus_view,
            "situation_analysis": self._build_situation_analysis(consensus),
            "key_risk_factors": key_risk_factors[:10],
            "impact_on_india": impact_on_india,
            "forecasts": forecasts,
            "scenarios": scenarios[:5],
            "strategic_recommendations": consensus.final_recommendations[:10],
            "scenario_tree": scenario_tree,
            "timeline": timeline,

            # Expert reasoning enhancements
            "expert_consensus": {
                "consensus_probability": round(consensus.consensus_probability, 4),
                "confidence_level": consensus.confidence.value,
                "uncertainty_range": {
                    "lower": round(consensus.uncertainty_range.lower_bound, 4),
                    "upper": round(consensus.uncertainty_range.upper_bound, 4),
                    "point_estimate": round(consensus.uncertainty_range.point_estimate, 4),
                },
                "key_agreements": consensus.key_agreements[:5],
                "disagreements": self._format_disagreements(consensus.disagreements),
                "minority_views": consensus.minority_views[:3],
                "contributing_experts": consensus.contributing_agents,
                "confidence_by_domain": consensus.confidence_breakdown,
            },

            "debate_summary": {
                "rounds_conducted": len(consensus.debate_rounds),
                "challenges_raised": sum(
                    len(r.challenges_raised) for r in consensus.debate_rounds
                ),
                "positions_revised": sum(
                    len(r.position_revisions) for r in consensus.debate_rounds
                ),
                "final_convergence": (
                    consensus.debate_rounds[-1].convergence_score
                    if consensus.debate_rounds else 1.0
                ),
            },

            "evidence_base": {
                "total_citations": len(consensus.evidence_synthesis),
                "top_citations": [
                    {
                        "source": e.citations[0].source_name if e.citations else "Unknown",
                        "claim": e.claim[:200],
                        "quality_score": round(e.citation_quality_score, 3),
                    }
                    for e in consensus.evidence_synthesis[:5]
                ],
                "data_quality_assessment": self._assess_data_quality(consensus),
            },

            # Metadata
            "_meta": {
                "query": query,
                "tools_used": list(tool_outputs.keys()),
                "expert_agents_consulted": consensus.contributing_agents,
                "grounding_mode": "expert_consensus",
                "methodology": consensus.methodology_notes,
                "timestamp": consensus.timestamp.isoformat(),
                "processing_time_ms": consensus.total_processing_time_ms,
                "engine": "JanGraph Expert Intelligence v4.0",
            },
        }

    def _build_scenario_tree(self, consensus: ConsensusReport) -> List[Dict]:
        """Build hierarchical scenario tree from analysis."""
        tree = []

        # Root node: current assessment
        tree.append({
            "level": 0,
            "node": "Current Situation",
            "probability": round(consensus.consensus_probability, 2),
            "children": [],
        })

        # Level 1: scenario branches
        scenarios = consensus.scenario_analysis.get("scenarios", {})

        if scenarios.get("best_case"):
            tree[0]["children"].append({
                "level": 1,
                "node": "Best Case",
                "probability": scenarios["best_case"].get("probability", 0.2),
                "description": scenarios["best_case"].get("description", "Favorable outcome"),
            })

        if scenarios.get("most_likely"):
            tree[0]["children"].append({
                "level": 1,
                "node": "Most Likely",
                "probability": scenarios["most_likely"].get("probability", 0.5),
                "description": scenarios["most_likely"].get("description", "Expected trajectory"),
            })

        if scenarios.get("worst_case"):
            tree[0]["children"].append({
                "level": 1,
                "node": "Worst Case",
                "probability": scenarios["worst_case"].get("probability", 0.3),
                "description": scenarios["worst_case"].get("description", "Adverse outcome"),
            })

        return tree

    def _build_timeline(self, consensus: ConsensusReport) -> List[Dict]:
        """Build event timeline from evidence."""
        timeline = []

        # Add analysis timestamp
        timeline.append({
            "timestamp": consensus.timestamp.isoformat(),
            "event": "Expert Analysis Completed",
            "type": "analysis",
            "significance": "high",
        })

        # Extract timeline hints from evidence
        for evidence in consensus.evidence_synthesis[:5]:
            if evidence.citations:
                timeline.append({
                    "timestamp": evidence.citations[0].timestamp.isoformat(),
                    "event": evidence.claim[:100],
                    "type": "evidence",
                    "significance": "medium" if evidence.weight > 0.7 else "low",
                })

        return timeline[:10]

    def _build_forecasts(self, consensus: ConsensusReport) -> Dict[str, Any]:
        """Build forecast structure from consensus."""
        return {
            "short_term": {
                "period": "1-3 months",
                "outlook": "Based on current trajectory" if consensus.consensus_probability > 0.5 else "Elevated uncertainty",
                "confidence": consensus.confidence.value,
            },
            "medium_term": {
                "period": "3-12 months",
                "outlook": "Subject to scenario evolution",
                "confidence": "moderate" if consensus.confidence in [
                    ConfidenceLevel.MODERATE, ConfidenceLevel.HIGH
                ] else "low",
            },
            "long_term": {
                "period": "1-3 years",
                "outlook": "High uncertainty, multiple pathways",
                "confidence": "low",
            },
        }

    def _build_scenarios(self, consensus: ConsensusReport) -> List[Dict]:
        """Build scenario list from analysis."""
        scenarios_data = consensus.scenario_analysis.get("scenarios", {})
        scenarios = []

        for name, data in scenarios_data.items():
            if isinstance(data, dict):
                scenarios.append({
                    "name": name.replace("_", " ").title(),
                    "probability": self._probability_label(data.get("probability", 0.5)),
                    "outcome": data.get("description", ""),
                    "impact_severity": self._calculate_impact_severity(data.get("probability", 0.5)),
                    "key_drivers": data.get("key_drivers", []),
                })

        return scenarios

    def _probability_label(self, prob: float) -> str:
        """Convert probability to label."""
        if prob < 0.25:
            return "Low"
        elif prob < 0.5:
            return "Medium-Low"
        elif prob < 0.75:
            return "Medium-High"
        else:
            return "High"

    def _calculate_impact_severity(self, prob: float) -> int:
        """Calculate impact severity score (1-10)."""
        # Higher probability of adverse outcomes = higher severity
        return min(10, max(1, int(prob * 10) + 3))

    def _build_india_impact(self, consensus: ConsensusReport) -> Dict[str, str]:
        """Build India-specific impact assessment."""
        # Extract India-relevant findings
        india_findings = [
            f for f in consensus.key_agreements
            if "india" in f.lower() or "domestic" in f.lower()
        ]

        return {
            "economic": self._extract_domain_impact(consensus, "economic"),
            "political": self._extract_domain_impact(consensus, "policy"),
            "defense": self._extract_domain_impact(consensus, "geopolitical"),
            "social": self._extract_domain_impact(consensus, "social"),
        }

    def _extract_domain_impact(self, consensus: ConsensusReport, domain: str) -> str:
        """Extract impact statement for a domain."""
        confidence = consensus.confidence_breakdown.get(domain, 0.5)

        # Find relevant evidence
        for evidence in consensus.evidence_synthesis:
            if domain in str(evidence.supporting_data).lower():
                return f"{evidence.claim[:150]} (confidence: {confidence:.0%})"

        return f"Impact assessment at {confidence:.0%} confidence based on {domain} analysis"

    def _build_situation_analysis(self, consensus: ConsensusReport) -> str:
        """Build comprehensive situation analysis."""
        parts = []

        # Overall assessment
        parts.append(f"Expert panel consensus at {consensus.consensus_probability:.0%} probability.")

        # Contributing domains
        if consensus.contributing_agents:
            parts.append(f"Analysis integrates perspectives from {len(consensus.contributing_agents)} expert domains: {', '.join(consensus.contributing_agents)}.")

        # Key agreements
        if consensus.key_agreements:
            parts.append(f"Key agreement: {consensus.key_agreements[0]}")

        # Uncertainty note
        if consensus.confidence in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW]:
            parts.append("NOTE: High uncertainty in assessment - treat conclusions with caution.")

        return " ".join(parts)

    def _format_disagreements(self, disagreements: List[Dict]) -> List[Dict]:
        """Format disagreements for output."""
        formatted = []
        for d in disagreements[:5]:
            formatted.append({
                "agents_involved": d.get("agents", []),
                "type": d.get("type", "unknown"),
                "description": d.get("description", ""),
                "probability_gap": d.get("probability_difference", 0),
                "resolution": "unresolved" if d.get("unresolved") else "resolved",
            })
        return formatted

    def _assess_data_quality(self, consensus: ConsensusReport) -> Dict[str, Any]:
        """Assess overall data quality."""
        if not consensus.evidence_synthesis:
            return {
                "overall": "insufficient",
                "authoritative_sources": 0,
                "stale_data_warnings": 0,
            }

        quality_scores = [e.citation_quality_score for e in consensus.evidence_synthesis]
        avg_quality = sum(quality_scores) / len(quality_scores)

        authoritative = sum(
            1 for e in consensus.evidence_synthesis
            for c in e.citations
            if c.quality.value == "authoritative"
        )

        stale = sum(
            1 for e in consensus.evidence_synthesis
            for c in e.citations
            if c.is_stale
        )

        quality_label = (
            "high" if avg_quality > 0.75 else
            "moderate" if avg_quality > 0.5 else
            "low"
        )

        return {
            "overall": quality_label,
            "average_score": round(avg_quality, 3),
            "authoritative_sources": authoritative,
            "stale_data_warnings": stale,
            "total_evidence_items": len(consensus.evidence_synthesis),
        }

    def _fallback_expert_analysis(self, query: str, error: str) -> Dict[str, Any]:
        """Fallback response when expert analysis fails."""
        return {
            "executive_summary": f"Expert analysis unavailable for '{query}'. Fallback mode active.",
            "situation_analysis": f"Error: {error}. System operating in degraded mode.",
            "key_risk_factors": [
                {
                    "factor": "Analysis Engine Unavailable",
                    "severity": "High",
                    "description": "Expert reasoning pipeline encountered an error",
                    "probability": "N/A",
                }
            ],
            "impact_on_india": {
                "economic": "Assessment unavailable",
                "political": "Assessment unavailable",
                "defense": "Assessment unavailable",
                "social": "Assessment unavailable",
            },
            "forecasts": {},
            "scenarios": [],
            "strategic_recommendations": [
                "Retry analysis with simplified query",
                "Check data source connectivity",
                "Review system logs for root cause",
            ],
            "scenario_tree": [],
            "timeline": [],
            "expert_consensus": {
                "consensus_probability": 0.5,
                "confidence_level": "very_low",
                "uncertainty_range": {"lower": 0.1, "upper": 0.9, "point_estimate": 0.5},
                "key_agreements": [],
                "disagreements": [],
                "minority_views": [],
                "contributing_experts": [],
                "confidence_by_domain": {},
            },
            "debate_summary": {
                "rounds_conducted": 0,
                "challenges_raised": 0,
                "positions_revised": 0,
                "final_convergence": 0,
            },
            "evidence_base": {
                "total_citations": 0,
                "top_citations": [],
                "data_quality_assessment": {"overall": "unavailable"},
            },
            "_meta": {
                "query": query,
                "error": error,
                "grounding_mode": "fallback",
                "timestamp": datetime.utcnow().isoformat(),
                "engine": "JanGraph Expert Intelligence v4.0 (fallback)",
            },
        }

    async def run_expert_whatif(
        self,
        base_context: Dict[str, Any],
        whatif_query: str,
        variable_changes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Run what-if simulation with expert reasoning.

        Uses all expert agents to project impacts of variable changes.
        """
        self._ensure_initialized()

        try:
            consensus = await self.orchestrator.run_what_if_simulation(
                base_context, whatif_query, variable_changes
            )

            # Format output
            result = self._format_expert_output(consensus, whatif_query, base_context)

            # Add simulation-specific metadata
            result["_meta"]["simulation_mode"] = True
            result["_meta"]["variables_modified"] = variable_changes

            return result

        except Exception as e:
            self.logger.error(f"Expert what-if failed: {e}", exc_info=True)
            return self._fallback_expert_analysis(whatif_query, str(e))


# Singleton instance
expert_agent = ExpertStrategicAgent()


# ============================================================================
# INTEGRATION FUNCTIONS
# ============================================================================

async def run_expert_strategic_analysis(query: str, tool_outputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for expert strategic analysis.

    Drop-in enhancement for existing run_strategic_analysis function.
    """
    return await expert_agent.run_expert_analysis(query, tool_outputs)


async def run_expert_whatif_simulation(
    original_context: str,
    whatif_query: str,
    variables: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Run expert what-if simulation.

    Enhanced version of run_whatif_simulation with multi-agent reasoning.
    """
    # Parse context if it's a string
    if isinstance(original_context, str):
        try:
            base_context = json.loads(original_context)
        except json.JSONDecodeError:
            base_context = {"raw_context": original_context}
    else:
        base_context = original_context

    return await expert_agent.run_expert_whatif(base_context, whatif_query, variables)
