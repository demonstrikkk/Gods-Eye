"""
Consensus Engine for Gods-Eye OS

This module synthesizes multi-agent outputs into unified assessments:
1. Aggregates probabilistic outputs using Bayesian combination
2. Identifies agreement and disagreement points
3. Documents minority views and their rationale
4. Calculates weighted confidence scores
5. Produces final consensus reports with full provenance

The consensus process respects epistemic humility:
- Disagreements are documented, not hidden
- Uncertainty is quantified, not minimized
- Minority views are preserved for decision-makers
"""

from __future__ import annotations

import asyncio
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import statistics

from .framework import (
    AgentPosition,
    Citation,
    ConfidenceLevel,
    ConsensusReport,
    DebateRound,
    Evidence,
    EvidenceType,
    ExpertAgent,
    ExpertInsight,
    ProbabilisticOutput,
    UncertaintyBand,
    agent_registry,
)
from .debate_engine import DebateEngine

logger = logging.getLogger(__name__)


@dataclass
class ConsensusConfig:
    """Configuration for the consensus building process."""
    min_agents_for_consensus: int = 2
    evidence_weight_by_quality: bool = True
    use_bayesian_combination: bool = True
    require_debate: bool = True
    max_debate_rounds: int = 3
    minority_threshold: float = 0.2  # % deviation to be considered minority
    confidence_aggregation: str = "weighted_average"  # or "minimum", "harmonic"


class ConsensusEngine:
    """
    Builds consensus from multiple expert agent insights.

    Implements a multi-stage consensus process:
    1. Collect and validate all agent insights
    2. Identify areas of agreement and disagreement
    3. Conduct structured debate to resolve disagreements
    4. Calculate weighted consensus estimates
    5. Document final consensus with full provenance
    """

    def __init__(
        self,
        config: Optional[ConsensusConfig] = None,
        debate_engine: Optional[DebateEngine] = None,
    ):
        self.config = config or ConsensusConfig()
        self.debate_engine = debate_engine or DebateEngine()
        self.logger = logging.getLogger(__name__)

    async def build_consensus(
        self,
        query: str,
        agents: List[ExpertAgent],
        insights: List[ExpertInsight],
        context: Dict[str, Any],
    ) -> ConsensusReport:
        """
        Build a comprehensive consensus report from multiple agent insights.

        Args:
            query: The original query being analyzed
            agents: List of participating expert agents
            insights: Initial insights from each agent
            context: Additional context for consensus building

        Returns:
            ConsensusReport with full synthesis and provenance
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Building consensus for: {query[:100]}... with {len(agents)} agents")

        if len(insights) < self.config.min_agents_for_consensus:
            return self._insufficient_agents_response(query, insights)

        # Step 1: Conduct debate (if enabled)
        debate_rounds = []
        final_positions = []
        convergence = 0.0

        if self.config.require_debate and len(agents) >= 2:
            debate_rounds, final_positions, convergence = await self.debate_engine.conduct_debate(
                topic=query,
                agents=agents,
                initial_insights=insights,
                context=context,
            )

        # Step 2: Aggregate probabilistic outputs
        consensus_prob, uncertainty = self._aggregate_probabilities(insights, final_positions)

        # Step 3: Identify agreements
        key_agreements = self._identify_agreements(insights)

        # Step 4: Document disagreements
        disagreements = []
        if final_positions:
            disagreements = self.debate_engine.identify_disagreements(final_positions)

        # Step 5: Extract minority views
        minority_views = []
        if final_positions:
            minority_views = self.debate_engine.extract_minority_views(final_positions)

        # Step 6: Synthesize evidence
        evidence_synthesis = self._synthesize_evidence(insights)

        # Step 7: Calculate confidence breakdown by domain
        confidence_breakdown = self._calculate_confidence_breakdown(insights)

        # Step 8: Generate consensus view
        consensus_view = self._generate_consensus_view(
            query=query,
            insights=insights,
            probability=consensus_prob,
            agreements=key_agreements,
            disagreements=disagreements,
        )

        # Step 9: Build final recommendations
        final_recommendations = self._synthesize_recommendations(insights)

        # Step 10: Aggregate risk assessment
        risk_assessment = self._aggregate_risk_assessment(insights)

        # Step 11: Build scenario analysis
        scenario_analysis = self._build_scenario_analysis(insights, uncertainty)

        # Step 12: Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(
            insights=insights,
            convergence=convergence,
            disagreements=disagreements,
        )

        # Step 13: Generate methodology notes
        methodology_notes = self._generate_methodology_notes(
            agents=agents,
            debate_rounds=debate_rounds,
            convergence=convergence,
        )

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ConsensusReport(
            query=query,
            consensus_view=consensus_view,
            consensus_probability=consensus_prob,
            confidence=overall_confidence,
            uncertainty_range=uncertainty,
            key_agreements=key_agreements,
            disagreements=disagreements,
            minority_views=minority_views,
            contributing_agents=[a.agent_name for a in agents],
            debate_rounds=debate_rounds,
            evidence_synthesis=evidence_synthesis,
            final_recommendations=final_recommendations,
            risk_assessment=risk_assessment,
            scenario_analysis=scenario_analysis,
            confidence_breakdown=confidence_breakdown,
            methodology_notes=methodology_notes,
            timestamp=datetime.utcnow(),
            total_processing_time_ms=elapsed_ms,
        )

    def _aggregate_probabilities(
        self,
        insights: List[ExpertInsight],
        positions: List[AgentPosition],
    ) -> Tuple[float, UncertaintyBand]:
        """
        Aggregate probability estimates from multiple agents.

        Uses Bayesian combination when enabled, otherwise weighted average.
        """
        # Collect all probability estimates
        probs = []
        weights = []

        # From positions (post-debate)
        if positions:
            for pos in positions:
                confidence_weight = {
                    ConfidenceLevel.VERY_LOW: 0.3,
                    ConfidenceLevel.LOW: 0.5,
                    ConfidenceLevel.MODERATE: 0.7,
                    ConfidenceLevel.HIGH: 0.85,
                    ConfidenceLevel.VERY_HIGH: 0.95,
                    ConfidenceLevel.NEAR_CERTAIN: 1.0,
                }.get(pos.confidence, 0.5)

                probs.append(pos.probability_estimate)
                weights.append(confidence_weight)
        else:
            # From initial insights
            for insight in insights:
                if insight.probabilistic_outputs:
                    prob = insight.probabilistic_outputs[0].probability
                    weight = {
                        ConfidenceLevel.VERY_LOW: 0.3,
                        ConfidenceLevel.LOW: 0.5,
                        ConfidenceLevel.MODERATE: 0.7,
                        ConfidenceLevel.HIGH: 0.85,
                        ConfidenceLevel.VERY_HIGH: 0.95,
                        ConfidenceLevel.NEAR_CERTAIN: 1.0,
                    }.get(insight.confidence_overall, 0.5)

                    probs.append(prob)
                    weights.append(weight)

        if not probs:
            # Default uncertainty
            return 0.5, UncertaintyBand(
                point_estimate=0.5,
                lower_bound=0.2,
                upper_bound=0.8,
                confidence_level=ConfidenceLevel.LOW,
                methodology_note="No probability estimates available",
            )

        # Calculate consensus probability
        if self.config.use_bayesian_combination:
            consensus_prob = self._bayesian_combination(probs, weights)
        else:
            # Weighted average
            total_weight = sum(weights)
            consensus_prob = sum(p * w for p, w in zip(probs, weights)) / total_weight

        # Calculate uncertainty band
        std_dev = statistics.stdev(probs) if len(probs) > 1 else 0.1
        margin = 1.96 * std_dev  # 95% confidence interval

        uncertainty = UncertaintyBand(
            point_estimate=consensus_prob,
            lower_bound=max(0.0, consensus_prob - margin),
            upper_bound=min(1.0, consensus_prob + margin),
            confidence_level=ConfidenceLevel.from_probability(1 - std_dev),
            distribution_type="normal",
            standard_error=std_dev,
            sample_size=len(probs),
            methodology_note=f"Aggregated from {len(probs)} agent estimates using {'Bayesian' if self.config.use_bayesian_combination else 'weighted average'} combination",
        )

        return consensus_prob, uncertainty

    def _bayesian_combination(
        self,
        probabilities: List[float],
        weights: List[float],
    ) -> float:
        """
        Combine probabilities using a Bayesian-inspired approach.

        Uses log-linear pooling with weights.
        """
        # Avoid log(0) issues
        probs = [max(0.01, min(0.99, p)) for p in probabilities]

        # Log-odds weighted combination
        log_odds = [math.log(p / (1 - p)) for p in probs]
        weighted_log_odds = sum(lo * w for lo, w in zip(log_odds, weights)) / sum(weights)

        # Convert back to probability
        combined_prob = 1 / (1 + math.exp(-weighted_log_odds))

        return combined_prob

    def _identify_agreements(
        self,
        insights: List[ExpertInsight],
    ) -> List[str]:
        """
        Identify key findings that multiple agents agree on.

        Returns findings mentioned by at least 2 agents.
        """
        finding_counts: Dict[str, int] = {}
        finding_agents: Dict[str, List[str]] = {}

        for insight in insights:
            for finding in insight.key_findings:
                # Normalize finding for comparison
                normalized = finding.lower().strip()[:100]

                if normalized not in finding_counts:
                    finding_counts[normalized] = 0
                    finding_agents[normalized] = []

                finding_counts[normalized] += 1
                finding_agents[normalized].append(insight.agent_name)

        # Find agreements (mentioned by 2+ agents)
        agreements = []
        for finding, count in finding_counts.items():
            if count >= 2:
                agents = ", ".join(set(finding_agents[finding]))
                agreements.append(f"{finding} (agreed by: {agents})")

        # Also include common themes from assessments
        if len(insights) >= 2:
            # Extract common themes
            all_assessments = " ".join(i.assessment for i in insights).lower()
            # Simple keyword matching for common themes
            themes = self._extract_common_themes(insights)
            for theme in themes[:3]:
                if theme not in agreements:
                    agreements.append(f"Common theme: {theme}")

        return agreements[:10]  # Limit to top 10

    def _extract_common_themes(
        self,
        insights: List[ExpertInsight],
    ) -> List[str]:
        """Extract common themes from multiple insights."""
        # Collect all text
        all_text = []
        for insight in insights:
            all_text.append(insight.assessment)
            all_text.extend(insight.key_findings)

        # Simple n-gram extraction for common phrases
        # (In production, this would use NLP techniques)
        common_phrases = []

        # Look for patterns that appear in multiple agent outputs
        keywords = ["risk", "impact", "growth", "decline", "increase", "decrease",
                    "volatility", "stability", "tension", "opportunity", "threat"]

        for keyword in keywords:
            keyword_count = sum(1 for text in all_text if keyword in text.lower())
            if keyword_count >= len(insights):
                common_phrases.append(f"All agents highlight {keyword} factors")

        return common_phrases

    def _synthesize_evidence(
        self,
        insights: List[ExpertInsight],
    ) -> List[Evidence]:
        """
        Synthesize evidence from all agents.

        Combines, deduplicates, and ranks evidence by quality.
        """
        all_evidence: List[Evidence] = []
        seen_claims: set = set()

        for insight in insights:
            for evidence in insight.evidence_base:
                # Deduplicate by claim
                claim_hash = evidence.claim[:50].lower()
                if claim_hash not in seen_claims:
                    seen_claims.add(claim_hash)
                    all_evidence.append(evidence)

        # Sort by quality score
        all_evidence.sort(
            key=lambda e: e.citation_quality_score * e.weight,
            reverse=True,
        )

        return all_evidence[:20]  # Top 20 evidence items

    def _calculate_confidence_breakdown(
        self,
        insights: List[ExpertInsight],
    ) -> Dict[str, float]:
        """
        Calculate confidence scores by domain.

        Returns a breakdown of confidence for each domain.
        """
        domain_confidence: Dict[str, List[float]] = {}

        for insight in insights:
            domain = insight.domain
            confidence_score = {
                ConfidenceLevel.VERY_LOW: 0.15,
                ConfidenceLevel.LOW: 0.35,
                ConfidenceLevel.MODERATE: 0.55,
                ConfidenceLevel.HIGH: 0.75,
                ConfidenceLevel.VERY_HIGH: 0.90,
                ConfidenceLevel.NEAR_CERTAIN: 0.97,
            }.get(insight.confidence_overall, 0.5)

            if domain not in domain_confidence:
                domain_confidence[domain] = []
            domain_confidence[domain].append(confidence_score)

        # Average confidence per domain
        breakdown = {}
        for domain, scores in domain_confidence.items():
            breakdown[domain] = round(statistics.mean(scores), 3)

        return breakdown

    def _generate_consensus_view(
        self,
        query: str,
        insights: List[ExpertInsight],
        probability: float,
        agreements: List[str],
        disagreements: List[Dict[str, Any]],
    ) -> str:
        """
        Generate a natural language consensus view.

        Combines insights into a coherent assessment statement.
        """
        # Get key assessments
        assessments = [i.assessment for i in insights]

        # Build consensus statement
        parts = []

        # Opening with confidence
        confidence_word = "high confidence" if probability > 0.7 else (
            "moderate confidence" if probability > 0.4 else "limited confidence"
        )
        parts.append(f"With {confidence_word} ({probability:.0%}), the expert panel assesses:")

        # Main findings
        if assessments:
            parts.append(f"\n\nPrimary assessment: {assessments[0][:300]}")

        # Key agreements
        if agreements:
            parts.append(f"\n\nKey agreements across domains:")
            for agreement in agreements[:3]:
                parts.append(f"  - {agreement[:150]}")

        # Note disagreements if any
        if disagreements:
            parts.append(f"\n\nNotable disagreements ({len(disagreements)} identified) require attention.")

        return "\n".join(parts)

    def _synthesize_recommendations(
        self,
        insights: List[ExpertInsight],
    ) -> List[str]:
        """
        Synthesize recommendations from all agents.

        Combines and prioritizes recommendations.
        """
        all_recs: Dict[str, int] = {}

        for insight in insights:
            for rec in insight.recommendations:
                # Simple deduplication by prefix
                key = rec[:50].lower()
                all_recs[key] = all_recs.get(key, 0) + 1

        # Sort by frequency
        sorted_recs = sorted(all_recs.items(), key=lambda x: x[1], reverse=True)

        # Return top recommendations
        final_recs = []
        for key, count in sorted_recs[:10]:
            # Find full recommendation
            for insight in insights:
                for rec in insight.recommendations:
                    if rec[:50].lower() == key:
                        priority = "HIGH" if count >= 2 else "Medium"
                        final_recs.append(f"[{priority}] {rec}")
                        break
                else:
                    continue
                break

        return final_recs

    def _aggregate_risk_assessment(
        self,
        insights: List[ExpertInsight],
    ) -> Dict[str, Any]:
        """
        Aggregate risk factors from all agents.

        Combines risk assessments with severity weighting.
        """
        all_risks: List[Dict[str, Any]] = []
        severity_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        for insight in insights:
            for risk in insight.risk_factors:
                risk["source_agent"] = insight.agent_name
                all_risks.append(risk)

        # Sort by severity
        all_risks.sort(
            key=lambda r: severity_map.get(r.get("severity", "medium"), 2),
            reverse=True,
        )

        # Categorize risks
        critical = [r for r in all_risks if r.get("severity") == "critical"]
        high = [r for r in all_risks if r.get("severity") == "high"]
        medium = [r for r in all_risks if r.get("severity") == "medium"]
        low = [r for r in all_risks if r.get("severity") == "low"]

        return {
            "overall_risk_level": "Critical" if critical else ("High" if high else "Moderate"),
            "critical_risks": critical[:5],
            "high_risks": high[:5],
            "medium_risks": medium[:5],
            "low_risks": low[:3],
            "total_risks_identified": len(all_risks),
            "agents_contributing": list(set(r.get("source_agent", "Unknown") for r in all_risks)),
        }

    def _build_scenario_analysis(
        self,
        insights: List[ExpertInsight],
        uncertainty: UncertaintyBand,
    ) -> Dict[str, Any]:
        """
        Build scenario analysis from agent insights.

        Creates best/most-likely/worst case scenarios.
        """
        # Collect all scenarios mentioned
        scenarios = {
            "best_case": {
                "probability": uncertainty.upper_bound,
                "description": "",
                "key_drivers": [],
            },
            "most_likely": {
                "probability": uncertainty.point_estimate,
                "description": "",
                "key_drivers": [],
            },
            "worst_case": {
                "probability": 1 - uncertainty.lower_bound,
                "description": "",
                "key_drivers": [],
            },
        }

        # Extract scenario information from insights
        for insight in insights:
            for output in insight.probabilistic_outputs:
                if "best" in output.outcome.lower() or output.probability > 0.7:
                    scenarios["best_case"]["description"] = output.outcome
                    scenarios["best_case"]["key_drivers"].extend(output.conditions[:2])
                elif "worst" in output.outcome.lower() or output.probability < 0.3:
                    scenarios["worst_case"]["description"] = output.outcome
                    scenarios["worst_case"]["key_drivers"].extend(output.conditions[:2])
                else:
                    scenarios["most_likely"]["description"] = output.outcome
                    scenarios["most_likely"]["key_drivers"].extend(output.conditions[:2])

        return {
            "scenarios": scenarios,
            "uncertainty_range": f"{uncertainty.lower_bound:.0%} - {uncertainty.upper_bound:.0%}",
            "time_horizon": "Variable based on domain",
            "methodology": "Multi-agent scenario synthesis",
        }

    def _calculate_overall_confidence(
        self,
        insights: List[ExpertInsight],
        convergence: float,
        disagreements: List[Dict[str, Any]],
    ) -> ConfidenceLevel:
        """
        Calculate overall confidence level for the consensus.

        Considers agent confidence, convergence, and disagreements.
        """
        # Base confidence from agent average
        confidence_scores = []
        for insight in insights:
            score = {
                ConfidenceLevel.VERY_LOW: 0.15,
                ConfidenceLevel.LOW: 0.35,
                ConfidenceLevel.MODERATE: 0.55,
                ConfidenceLevel.HIGH: 0.75,
                ConfidenceLevel.VERY_HIGH: 0.90,
                ConfidenceLevel.NEAR_CERTAIN: 0.97,
            }.get(insight.confidence_overall, 0.5)
            confidence_scores.append(score)

        avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.5

        # Adjust for convergence
        convergence_adjustment = (convergence - 0.5) * 0.2

        # Adjust for disagreements
        disagreement_penalty = min(len(disagreements) * 0.05, 0.2)

        final_score = avg_confidence + convergence_adjustment - disagreement_penalty
        final_score = max(0.1, min(0.95, final_score))

        return ConfidenceLevel.from_probability(final_score)

    def _generate_methodology_notes(
        self,
        agents: List[ExpertAgent],
        debate_rounds: List[DebateRound],
        convergence: float,
    ) -> str:
        """
        Generate methodology notes for transparency.

        Documents the consensus-building process.
        """
        notes = []

        # Agent participation
        notes.append(f"METHODOLOGY: Multi-agent consensus with {len(agents)} expert domains")
        notes.append(f"Contributing agents: {', '.join(a.agent_name for a in agents)}")

        # Debate process
        if debate_rounds:
            notes.append(f"Debate rounds conducted: {len(debate_rounds)}")
            notes.append(f"Final convergence score: {convergence:.0%}")

            total_challenges = sum(len(r.challenges_raised) for r in debate_rounds)
            total_revisions = sum(len(r.position_revisions) for r in debate_rounds)
            notes.append(f"Total challenges raised: {total_challenges}")
            notes.append(f"Position revisions: {total_revisions}")

        # Data sources
        all_sources = set()
        for agent in agents:
            all_sources.update(agent.data_sources)
        notes.append(f"Data sources consulted: {len(all_sources)}")

        # Confidence methodology
        notes.append(f"Confidence calculation: {self.config.confidence_aggregation}")
        notes.append(f"Probability aggregation: {'Bayesian combination' if self.config.use_bayesian_combination else 'Weighted average'}")

        return "\n".join(notes)

    def _insufficient_agents_response(
        self,
        query: str,
        insights: List[ExpertInsight],
    ) -> ConsensusReport:
        """
        Generate response when insufficient agents are available.

        Provides best available assessment without full consensus.
        """
        self.logger.warning("Insufficient agents for full consensus")

        if insights:
            insight = insights[0]
            return ConsensusReport(
                query=query,
                consensus_view=f"SINGLE AGENT VIEW (insufficient for consensus): {insight.assessment}",
                consensus_probability=insight.probabilistic_outputs[0].probability if insight.probabilistic_outputs else 0.5,
                confidence=ConfidenceLevel.LOW,
                uncertainty_range=UncertaintyBand(
                    point_estimate=0.5,
                    lower_bound=0.2,
                    upper_bound=0.8,
                    confidence_level=ConfidenceLevel.LOW,
                    methodology_note="Single agent assessment, consensus not possible",
                ),
                key_agreements=[],
                disagreements=[],
                minority_views=[],
                contributing_agents=[insight.agent_name],
                debate_rounds=[],
                evidence_synthesis=insight.evidence_base,
                final_recommendations=insight.recommendations,
                risk_assessment={"overall_risk_level": "Uncertain", "note": "Single agent assessment"},
                scenario_analysis={},
                confidence_breakdown={insight.domain: 0.5},
                methodology_notes="WARNING: Consensus not possible with fewer than 2 agents",
            )

        # No insights at all
        return ConsensusReport(
            query=query,
            consensus_view="UNAVAILABLE: No expert agents were able to provide assessments",
            consensus_probability=0.5,
            confidence=ConfidenceLevel.VERY_LOW,
            uncertainty_range=UncertaintyBand(
                point_estimate=0.5,
                lower_bound=0.0,
                upper_bound=1.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                methodology_note="No agent assessments available",
            ),
            key_agreements=[],
            disagreements=[],
            minority_views=[],
            contributing_agents=[],
            debate_rounds=[],
            evidence_synthesis=[],
            final_recommendations=["Seek additional expert input"],
            risk_assessment={"overall_risk_level": "Unknown"},
            scenario_analysis={},
            confidence_breakdown={},
            methodology_notes="No expert agents available for analysis",
        )
