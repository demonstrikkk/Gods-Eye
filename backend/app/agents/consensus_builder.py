"""
Consensus Building Engine
=========================

Synthesizes multi-agent outputs into coherent consensus:
- Weighted aggregation
- Disagreement documentation
- Confidence calculation
- Final output generation
- Minority opinion preservation
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from uuid import uuid4

import numpy as np

if TYPE_CHECKING:
    from .expert_base import AgentAssessment, AgentClaim

logger = logging.getLogger(__name__)


class VotingMechanism(str, Enum):
    """Voting mechanisms for consensus building."""

    WEIGHTED_AVERAGE = "weighted_average"  # Weight by confidence
    MAJORITY_RULE = "majority_rule"         # Simple majority
    SUPERMAJORITY = "supermajority"         # 2/3 agreement
    UNANIMITY = "unanimity"                 # All must agree
    BORDA_COUNT = "borda_count"             # Ranked preference
    CONFIDENCE_WEIGHTED = "confidence_weighted"  # Weight by uncertainty


class ConsensusStrength(str, Enum):
    """Strength of achieved consensus."""

    UNANIMOUS = "unanimous"         # All agents fully agree
    STRONG = "strong"               # 80%+ agreement
    MODERATE = "moderate"           # 60-80% agreement
    WEAK = "weak"                   # 40-60% agreement
    DIVERGENT = "divergent"         # <40% agreement
    NO_CONSENSUS = "no_consensus"   # Cannot determine


@dataclass
class Disagreement:
    """
    Documented disagreement between agents.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])

    # Parties involved
    agent_ids: List[str] = field(default_factory=list)
    agent_names: List[str] = field(default_factory=list)

    # Nature of disagreement
    topic: str = ""
    nature: str = ""  # factual, interpretive, methodological, values-based
    severity: str = "moderate"  # minor, moderate, major, fundamental

    # Positions
    positions: Dict[str, str] = field(default_factory=dict)  # agent_id -> position
    probabilities: Dict[str, float] = field(default_factory=dict)  # agent_id -> prob

    # Resolution attempts
    resolution_attempted: bool = False
    partial_resolution: Optional[str] = None

    # Evidence
    conflicting_evidence: List[str] = field(default_factory=list)

    # Impact
    impact_on_conclusion: str = "moderate"  # low, moderate, high

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agents": self.agent_names,
            "topic": self.topic,
            "nature": self.nature,
            "severity": self.severity,
            "positions": self.positions,
            "probabilities": self.probabilities,
            "resolution_attempted": self.resolution_attempted,
            "partial_resolution": self.partial_resolution,
            "conflicting_evidence": self.conflicting_evidence,
            "impact_on_conclusion": self.impact_on_conclusion,
        }


@dataclass
class ConsensusResult:
    """
    Complete consensus result from multi-agent deliberation.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])

    # Query context
    query: str = ""
    domains_involved: List[str] = field(default_factory=list)

    # Consensus outcome
    consensus_view: str = ""
    consensus_probability: float = 0.5
    consensus_strength: ConsensusStrength = ConsensusStrength.MODERATE
    confidence_level: str = ""  # verbal (e.g., "High confidence")
    confidence_score: float = 0.5

    # Supporting analysis
    key_findings: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)

    # Disagreements
    disagreements: List[Disagreement] = field(default_factory=list)
    minority_opinions: List[Dict[str, Any]] = field(default_factory=list)

    # Uncertainty
    uncertainty_factors: List[str] = field(default_factory=list)
    key_assumptions: List[str] = field(default_factory=list)
    data_gaps: List[str] = field(default_factory=list)

    # Agent contributions
    agent_contributions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    voting_mechanism_used: VotingMechanism = VotingMechanism.WEIGHTED_AVERAGE

    # Scenarios
    scenarios: Dict[str, Any] = field(default_factory=dict)

    # Meta
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = 0.0
    debate_rounds: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "query": self.query,
            "domains_involved": self.domains_involved,
            "consensus": {
                "view": self.consensus_view,
                "probability": self.consensus_probability,
                "strength": self.consensus_strength.value if isinstance(self.consensus_strength, ConsensusStrength) else self.consensus_strength,
                "confidence_level": self.confidence_level,
                "confidence_score": self.confidence_score,
            },
            "key_findings": self.key_findings,
            "supporting_evidence": self.supporting_evidence,
            "data_sources": self.data_sources,
            "disagreements": [d.to_dict() for d in self.disagreements],
            "minority_opinions": self.minority_opinions,
            "uncertainty": {
                "factors": self.uncertainty_factors,
                "assumptions": self.key_assumptions,
                "data_gaps": self.data_gaps,
            },
            "agent_contributions": self.agent_contributions,
            "voting_mechanism": self.voting_mechanism_used.value if isinstance(self.voting_mechanism_used, VotingMechanism) else self.voting_mechanism_used,
            "scenarios": self.scenarios,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "debate_rounds": self.debate_rounds,
        }


class ConsensusBuilder:
    """
    Builds consensus from multi-agent assessments and debates.

    Responsibilities:
    - Aggregate agent assessments
    - Document disagreements
    - Calculate consensus confidence
    - Generate final output
    - Preserve minority opinions
    """

    def __init__(
        self,
        default_mechanism: VotingMechanism = VotingMechanism.WEIGHTED_AVERAGE,
        min_consensus_threshold: float = 0.6
    ):
        self.default_mechanism = default_mechanism
        self.min_consensus_threshold = min_consensus_threshold
        self.logger = logging.getLogger("consensus_builder")

    def build_consensus(
        self,
        query: str,
        assessments: List["AgentAssessment"],
        debate_summary: Optional[Dict[str, Any]] = None,
        mechanism: Optional[VotingMechanism] = None
    ) -> ConsensusResult:
        """
        Build consensus from agent assessments and optional debate.

        Args:
            query: Original query
            assessments: List of agent assessments
            debate_summary: Summary from debate system if debate occurred
            mechanism: Voting mechanism to use

        Returns:
            ConsensusResult with full consensus documentation
        """
        import time
        start_time = time.time()

        mechanism = mechanism or self.default_mechanism
        self.logger.info(f"Building consensus using {mechanism.value}")

        if not assessments:
            return self._empty_consensus(query)

        # Extract domains
        domains = list(set(a.domain for a in assessments))

        # Aggregate probabilities and confidences
        aggregation = self._aggregate_assessments(assessments, mechanism)

        # Calculate consensus strength
        strength = self._calculate_consensus_strength(assessments)

        # Identify disagreements
        disagreements = self._identify_disagreements(assessments)

        # Extract minority opinions
        minority_opinions = self._extract_minority_opinions(
            assessments, aggregation["consensus_probability"]
        )

        # Merge key findings
        key_findings = self._merge_key_findings(assessments)

        # Collect evidence and sources
        all_evidence = []
        all_sources = []
        for a in assessments:
            all_sources.extend(a.data_sources_used)
            all_evidence.extend([f.statement for f in a.claims[:2]])

        # Collect uncertainty factors
        uncertainty_factors = []
        assumptions = []
        data_gaps = []
        for a in assessments:
            uncertainty_factors.extend(a.uncertainty_factors)
            data_gaps.extend(a.data_gaps)
            for c in a.claims:
                assumptions.extend(c.assumptions)

        # Agent contributions
        contributions = {}
        for a in assessments:
            contributions[a.agent_id] = {
                "name": a.agent_name,
                "domain": a.domain,
                "confidence": a.confidence_score,
                "key_claims": len(a.claims),
                "data_sources": len(a.data_sources_used),
            }

        # Generate consensus view text
        consensus_view = self._generate_consensus_view(
            query, assessments, aggregation, strength
        )

        # Confidence level text
        confidence_level = self._confidence_to_text(aggregation["consensus_confidence"])

        # Scenarios
        scenarios = self._build_scenarios(assessments)

        processing_time = (time.time() - start_time) * 1000

        result = ConsensusResult(
            query=query,
            domains_involved=domains,
            consensus_view=consensus_view,
            consensus_probability=aggregation["consensus_probability"],
            consensus_strength=strength,
            confidence_level=confidence_level,
            confidence_score=aggregation["consensus_confidence"],
            key_findings=key_findings[:10],
            supporting_evidence=list(set(all_evidence))[:10],
            data_sources=list(set(all_sources)),
            disagreements=disagreements,
            minority_opinions=minority_opinions,
            uncertainty_factors=list(set(uncertainty_factors))[:5],
            key_assumptions=list(set(assumptions))[:5],
            data_gaps=list(set(data_gaps))[:5],
            agent_contributions=contributions,
            voting_mechanism_used=mechanism,
            scenarios=scenarios,
            processing_time_ms=processing_time,
            debate_rounds=debate_summary.get("rounds_conducted", 0) if debate_summary else 0,
        )

        self.logger.info(
            f"Consensus built: {strength.value}, "
            f"confidence={aggregation['consensus_confidence']:.2f}, "
            f"disagreements={len(disagreements)}"
        )

        return result

    def _aggregate_assessments(
        self,
        assessments: List["AgentAssessment"],
        mechanism: VotingMechanism
    ) -> Dict[str, float]:
        """Aggregate assessment probabilities and confidences."""
        if mechanism == VotingMechanism.WEIGHTED_AVERAGE:
            return self._weighted_average_aggregation(assessments)
        elif mechanism == VotingMechanism.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted_aggregation(assessments)
        elif mechanism == VotingMechanism.MAJORITY_RULE:
            return self._majority_aggregation(assessments)
        else:
            return self._weighted_average_aggregation(assessments)

    def _weighted_average_aggregation(
        self,
        assessments: List["AgentAssessment"]
    ) -> Dict[str, float]:
        """Aggregate using inverse-uncertainty weighting."""
        if not assessments:
            return {"consensus_probability": 0.5, "consensus_confidence": 0.0}

        # Extract values
        probabilities = [a.confidence_score for a in assessments]
        uncertainties = [1 - a.confidence_score for a in assessments]

        # Weight by inverse uncertainty
        weights = [1 / max(u, 0.01) for u in uncertainties]
        weight_sum = sum(weights)
        normalized_weights = [w / weight_sum for w in weights]

        # Weighted probability
        consensus_prob = sum(p * w for p, w in zip(probabilities, normalized_weights))

        # Consensus confidence (increases with agreement)
        variance = sum((p - consensus_prob) ** 2 * w
                       for p, w in zip(probabilities, normalized_weights))
        agreement_bonus = max(0, 1 - math.sqrt(variance) * 3)

        base_confidence = sum(a.confidence_score * w
                              for a, w in zip(assessments, normalized_weights))
        consensus_confidence = base_confidence * (0.7 + 0.3 * agreement_bonus)

        return {
            "consensus_probability": consensus_prob,
            "consensus_confidence": min(consensus_confidence, 0.95),
        }

    def _confidence_weighted_aggregation(
        self,
        assessments: List["AgentAssessment"]
    ) -> Dict[str, float]:
        """Weight directly by agent confidence scores."""
        if not assessments:
            return {"consensus_probability": 0.5, "consensus_confidence": 0.0}

        confidences = [a.confidence_score for a in assessments]
        probabilities = [a.confidence_score for a in assessments]

        # Normalize confidence weights
        total_conf = sum(confidences)
        if total_conf == 0:
            weights = [1 / len(assessments)] * len(assessments)
        else:
            weights = [c / total_conf for c in confidences]

        consensus_prob = sum(p * w for p, w in zip(probabilities, weights))

        # Confidence is weighted average
        consensus_confidence = sum(c * w for c, w in zip(confidences, weights))

        return {
            "consensus_probability": consensus_prob,
            "consensus_confidence": consensus_confidence,
        }

    def _majority_aggregation(
        self,
        assessments: List["AgentAssessment"]
    ) -> Dict[str, float]:
        """Simple majority voting aggregation."""
        if not assessments:
            return {"consensus_probability": 0.5, "consensus_confidence": 0.0}

        # Count high vs low probability assessments
        high_prob = sum(1 for a in assessments if a.confidence_score >= 0.5)
        total = len(assessments)

        majority_ratio = high_prob / total

        if majority_ratio >= 0.5:
            # Majority says high probability
            high_probs = [a.confidence_score for a in assessments
                          if a.confidence_score >= 0.5]
            consensus_prob = sum(high_probs) / len(high_probs)
        else:
            # Majority says low probability
            low_probs = [a.confidence_score for a in assessments
                         if a.confidence_score < 0.5]
            consensus_prob = sum(low_probs) / len(low_probs)

        # Confidence based on majority strength
        consensus_confidence = abs(majority_ratio - 0.5) * 2

        return {
            "consensus_probability": consensus_prob,
            "consensus_confidence": consensus_confidence,
        }

    def _calculate_consensus_strength(
        self,
        assessments: List["AgentAssessment"]
    ) -> ConsensusStrength:
        """Calculate the strength of consensus."""
        if not assessments:
            return ConsensusStrength.NO_CONSENSUS

        probabilities = [a.confidence_score for a in assessments]

        # Calculate agreement metrics
        std_dev = float(np.std(probabilities))
        range_val = max(probabilities) - min(probabilities)

        # All within 5%
        if range_val < 0.05 and std_dev < 0.03:
            return ConsensusStrength.UNANIMOUS

        # All within 15%
        if range_val < 0.15 and std_dev < 0.08:
            return ConsensusStrength.STRONG

        # Moderate agreement
        if range_val < 0.30 and std_dev < 0.15:
            return ConsensusStrength.MODERATE

        # Weak agreement
        if range_val < 0.50:
            return ConsensusStrength.WEAK

        # Significant divergence
        return ConsensusStrength.DIVERGENT

    def _identify_disagreements(
        self,
        assessments: List["AgentAssessment"]
    ) -> List[Disagreement]:
        """Identify and document disagreements between agents."""
        disagreements = []

        # Compare all pairs
        for i, a1 in enumerate(assessments):
            for a2 in assessments[i + 1:]:
                # Check probability divergence
                prob_diff = abs(a1.confidence_score - a2.confidence_score)

                if prob_diff > 0.25:
                    # Significant disagreement
                    severity = "minor" if prob_diff < 0.35 else (
                        "moderate" if prob_diff < 0.50 else "major"
                    )

                    # Identify conflicting claims
                    conflicting = self._find_conflicting_claims(a1.claims, a2.claims)

                    disagreement = Disagreement(
                        agent_ids=[a1.agent_id, a2.agent_id],
                        agent_names=[a1.agent_name, a2.agent_name],
                        topic=a1.query_context[:100],
                        nature="interpretive",
                        severity=severity,
                        positions={
                            a1.agent_id: a1.executive_summary[:200],
                            a2.agent_id: a2.executive_summary[:200],
                        },
                        probabilities={
                            a1.agent_id: a1.confidence_score,
                            a2.agent_id: a2.confidence_score,
                        },
                        conflicting_evidence=conflicting,
                        impact_on_conclusion=severity,
                    )
                    disagreements.append(disagreement)

        return disagreements

    def _find_conflicting_claims(
        self,
        claims1: List["AgentClaim"],
        claims2: List["AgentClaim"]
    ) -> List[str]:
        """Find potentially conflicting claims between two sets."""
        conflicts = []

        # Simple keyword-based conflict detection
        conflict_pairs = [
            ("increase", "decrease"),
            ("growth", "decline"),
            ("positive", "negative"),
            ("stable", "volatile"),
            ("strengthen", "weaken"),
            ("likely", "unlikely"),
        ]

        for c1 in claims1:
            for c2 in claims2:
                c1_lower = c1.statement.lower()
                c2_lower = c2.statement.lower()

                for pos, neg in conflict_pairs:
                    if (pos in c1_lower and neg in c2_lower) or \
                       (neg in c1_lower and pos in c2_lower):
                        conflicts.append(f"Conflict on: {c1.statement[:50]} vs {c2.statement[:50]}")
                        break

        return conflicts[:5]

    def _extract_minority_opinions(
        self,
        assessments: List["AgentAssessment"],
        consensus_prob: float
    ) -> List[Dict[str, Any]]:
        """Extract minority opinions that differ from consensus."""
        minority = []

        for a in assessments:
            diff = abs(a.confidence_score - consensus_prob)

            if diff > 0.20:  # Significantly different from consensus
                minority.append({
                    "agent": a.agent_name,
                    "domain": a.domain,
                    "position": a.executive_summary[:300],
                    "probability": a.confidence_score,
                    "difference_from_consensus": diff,
                    "reasoning": [c.statement for c in a.claims[:2]],
                    "key_evidence": a.data_sources_used[:3],
                })

        return minority

    def _merge_key_findings(
        self,
        assessments: List["AgentAssessment"]
    ) -> List[str]:
        """Merge and deduplicate key findings from all agents."""
        all_findings = []
        seen = set()

        for a in assessments:
            for finding in a.key_findings:
                # Simple deduplication
                normalized = finding.lower()[:50]
                if normalized not in seen:
                    all_findings.append(f"[{a.agent_name}] {finding}")
                    seen.add(normalized)

        # Sort by confidence (implied by order in agent's list)
        return all_findings

    def _generate_consensus_view(
        self,
        query: str,
        assessments: List["AgentAssessment"],
        aggregation: Dict[str, float],
        strength: ConsensusStrength
    ) -> str:
        """Generate the consensus view text."""
        if strength == ConsensusStrength.UNANIMOUS:
            prefix = "All agents unanimously conclude that"
        elif strength == ConsensusStrength.STRONG:
            prefix = "There is strong agreement that"
        elif strength == ConsensusStrength.MODERATE:
            prefix = "A moderate consensus suggests that"
        elif strength == ConsensusStrength.WEAK:
            prefix = "A tentative assessment indicates that"
        else:
            prefix = "Despite divergent views, the aggregate analysis suggests that"

        # Get highest confidence assessment as anchor
        sorted_assessments = sorted(assessments, key=lambda a: -a.confidence_score)
        anchor = sorted_assessments[0] if sorted_assessments else None

        if anchor:
            core_view = anchor.executive_summary[:500]
        else:
            core_view = f"analysis of '{query}' remains inconclusive"

        probability = aggregation["consensus_probability"]
        verbal_prob = self._probability_to_verbal(probability)

        return f"{prefix} {core_view}\n\nProbability assessment: {verbal_prob} ({probability:.0%})"

    def _build_scenarios(
        self,
        assessments: List["AgentAssessment"]
    ) -> Dict[str, Any]:
        """Build scenario projections from assessments."""
        scenarios = {
            "best_case": {
                "description": "Favorable conditions materialize",
                "probability": 0.0,
                "key_factors": [],
            },
            "most_likely": {
                "description": "Baseline trajectory continues",
                "probability": 0.0,
                "key_factors": [],
            },
            "worst_case": {
                "description": "Risk factors compound",
                "probability": 0.0,
                "key_factors": [],
            },
        }

        if not assessments:
            return scenarios

        # Aggregate scenario probabilities
        best_probs = []
        worst_probs = []
        likely_probs = []

        for a in assessments:
            # Extract from claims or use defaults
            high_conf = [c for c in a.claims if c.probability >= 0.7]
            low_conf = [c for c in a.claims if c.probability <= 0.3]

            if high_conf:
                best_probs.append(max(c.probability for c in high_conf))
                scenarios["best_case"]["key_factors"].extend(
                    [c.statement[:100] for c in high_conf[:1]]
                )

            if low_conf:
                worst_probs.append(min(c.probability for c in low_conf))
                scenarios["worst_case"]["key_factors"].extend(
                    [c.statement[:100] for c in low_conf[:1]]
                )

            likely_probs.append(a.confidence_score)

        # Set probabilities
        scenarios["best_case"]["probability"] = sum(best_probs) / max(len(best_probs), 1) if best_probs else 0.2
        scenarios["worst_case"]["probability"] = sum(worst_probs) / max(len(worst_probs), 1) if worst_probs else 0.2
        scenarios["most_likely"]["probability"] = sum(likely_probs) / max(len(likely_probs), 1)

        return scenarios

    def _confidence_to_text(self, confidence: float) -> str:
        """Convert confidence score to verbal description."""
        if confidence >= 0.90:
            return "Very High Confidence"
        elif confidence >= 0.75:
            return "High Confidence"
        elif confidence >= 0.55:
            return "Moderate Confidence"
        elif confidence >= 0.35:
            return "Low Confidence"
        else:
            return "Very Low Confidence"

    def _probability_to_verbal(self, probability: float) -> str:
        """Convert probability to verbal expression."""
        if probability >= 0.90:
            return "Almost certain"
        elif probability >= 0.80:
            return "Highly likely"
        elif probability >= 0.65:
            return "Likely"
        elif probability >= 0.50:
            return "Probable"
        elif probability >= 0.35:
            return "Possible"
        elif probability >= 0.20:
            return "Unlikely"
        elif probability >= 0.10:
            return "Highly unlikely"
        else:
            return "Remote chance"

    def _empty_consensus(self, query: str) -> ConsensusResult:
        """Return empty consensus when no assessments available."""
        return ConsensusResult(
            query=query,
            consensus_view="Unable to form consensus - no agent assessments available",
            consensus_probability=0.5,
            consensus_strength=ConsensusStrength.NO_CONSENSUS,
            confidence_level="Cannot Assess",
            confidence_score=0.0,
            uncertainty_factors=["No agent responses received"],
        )

    def format_for_user(self, result: ConsensusResult) -> str:
        """Format consensus result for user display."""
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("MULTI-AGENT CONSENSUS ASSESSMENT")
        lines.append("=" * 60)
        lines.append("")

        # Consensus view
        lines.append("CONSENSUS VIEW")
        lines.append("-" * 40)
        lines.append(result.consensus_view)
        lines.append("")

        # Confidence
        lines.append(f"Confidence: {result.confidence_level} ({result.confidence_score:.0%})")
        lines.append(f"Agreement: {(result.consensus_strength.value if isinstance(result.consensus_strength, ConsensusStrength) else result.consensus_strength).replace('_', ' ').title()}")
        lines.append("")

        # Key findings
        if result.key_findings:
            lines.append("KEY FINDINGS")
            lines.append("-" * 40)
            for finding in result.key_findings[:5]:
                lines.append(f"  - {finding}")
            lines.append("")

        # Disagreements
        if result.disagreements:
            lines.append("DISAGREEMENTS")
            lines.append("-" * 40)
            for d in result.disagreements:
                lines.append(f"  - {' vs '.join(d.agent_names)}: {d.topic[:80]}")
                lines.append(f"    Severity: {d.severity}, Impact: {d.impact_on_conclusion}")
            lines.append("")

        # Minority opinions
        if result.minority_opinions:
            lines.append("MINORITY OPINIONS")
            lines.append("-" * 40)
            for mo in result.minority_opinions:
                lines.append(f"  - {mo['agent']} ({mo['domain']}): {mo['position'][:100]}...")
            lines.append("")

        # Data sources
        if result.data_sources:
            lines.append("DATA SOURCES")
            lines.append("-" * 40)
            for src in result.data_sources[:8]:
                lines.append(f"  - {src}")
            lines.append("")

        # Uncertainty
        if result.uncertainty_factors:
            lines.append("UNCERTAINTY FACTORS")
            lines.append("-" * 40)
            for uf in result.uncertainty_factors:
                lines.append(f"  - {uf}")
            lines.append("")

        # Footer
        lines.append("=" * 60)
        lines.append(f"Generated: {result.timestamp.strftime('%Y-%m-%d %H:%M UTC')}")
        lines.append(f"Domains: {', '.join(result.domains_involved)}")
        lines.append(f"Processing time: {result.processing_time_ms:.0f}ms")

        return "\n".join(lines)


# Global instance
consensus_builder = ConsensusBuilder()
