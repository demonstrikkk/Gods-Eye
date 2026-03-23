"""
Core Framework for Expert-Level Agent Reasoning

Provides structured data types and base classes for:
- Evidence-based reasoning with full provenance
- Uncertainty quantification using confidence intervals and Bayesian estimates
- Probabilistic outputs with explicit distributions
- Cross-agent validation and challenge protocols
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable, TypeVar, Generic
import asyncio
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMERATIONS
# ============================================================================

class ConfidenceLevel(Enum):
    """Standardized confidence levels for intelligence assessments."""
    VERY_LOW = "very_low"        # <20% confidence
    LOW = "low"                  # 20-40% confidence
    MODERATE = "moderate"        # 40-60% confidence
    HIGH = "high"                # 60-80% confidence
    VERY_HIGH = "very_high"      # 80-95% confidence
    NEAR_CERTAIN = "near_certain"  # >95% confidence

    @classmethod
    def from_probability(cls, prob: float) -> "ConfidenceLevel":
        """Convert probability to confidence level."""
        if prob < 0.20:
            return cls.VERY_LOW
        elif prob < 0.40:
            return cls.LOW
        elif prob < 0.60:
            return cls.MODERATE
        elif prob < 0.80:
            return cls.HIGH
        elif prob < 0.95:
            return cls.VERY_HIGH
        else:
            return cls.NEAR_CERTAIN


class DataQuality(Enum):
    """Quality assessment of data sources."""
    AUTHORITATIVE = "authoritative"    # Official government/institutional
    RELIABLE = "reliable"              # Established credible sources
    MIXED = "mixed"                    # Some credible, some uncertain
    UNCERTAIN = "uncertain"            # Limited verification
    SPECULATIVE = "speculative"        # Rumors, unverified claims
    FALLBACK = "fallback"              # Synthetic/simulated data


class EvidenceType(Enum):
    """Classification of evidence types."""
    STATISTICAL = "statistical"         # Quantitative data
    HISTORICAL = "historical"           # Past events/patterns
    EXPERT_ASSESSMENT = "expert_assessment"
    MODEL_PREDICTION = "model_prediction"
    REAL_TIME_SIGNAL = "real_time_signal"
    COMPARATIVE = "comparative"          # Cross-country/region comparison
    CAUSAL_INFERENCE = "causal_inference"
    CORRELATION = "correlation"


class DisagreementType(Enum):
    """Types of disagreements between agents."""
    FACTUAL = "factual"                 # Different interpretation of facts
    METHODOLOGICAL = "methodological"   # Different analytical approaches
    PROBABILISTIC = "probabilistic"     # Different probability estimates
    TEMPORAL = "temporal"               # Different timeline expectations
    CAUSAL = "causal"                   # Different causal chains
    SEVERITY = "severity"               # Different impact assessments


# ============================================================================
# CORE DATA STRUCTURES
# ============================================================================

@dataclass
class Citation:
    """
    Represents a data source citation with full provenance tracking.

    Every claim made by an agent must be backed by one or more citations.
    """
    source_name: str                    # e.g., "World Bank API", "GDELT"
    source_type: str                    # e.g., "api", "dataset", "report"
    data_point: str                     # The specific data referenced
    value: Any                          # The actual value
    timestamp: datetime                 # When data was retrieved
    url: Optional[str] = None           # Source URL if available
    methodology: Optional[str] = None   # How data was collected
    freshness_hours: float = 0.0        # Hours since last update
    quality: DataQuality = DataQuality.RELIABLE

    @property
    def citation_id(self) -> str:
        """Generate unique ID for this citation."""
        content = f"{self.source_name}:{self.data_point}:{self.value}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    @property
    def is_stale(self) -> bool:
        """Check if data is potentially stale (>24 hours)."""
        return self.freshness_hours > 24

    def to_dict(self) -> Dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "data_point": self.data_point,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "url": self.url,
            "methodology": self.methodology,
            "freshness_hours": self.freshness_hours,
            "quality": self.quality.value,
            "is_stale": self.is_stale,
        }


@dataclass
class UncertaintyBand:
    """
    Represents uncertainty in a numerical estimate.

    Uses multiple methods to quantify uncertainty:
    - Point estimate with confidence interval
    - Distribution parameters
    - Scenario range (best/expected/worst)
    """
    point_estimate: float
    lower_bound: float                  # 5th percentile
    upper_bound: float                  # 95th percentile
    confidence_level: ConfidenceLevel
    distribution_type: str = "normal"   # normal, log-normal, uniform, etc.
    standard_error: Optional[float] = None
    sample_size: Optional[int] = None
    methodology_note: str = ""

    @property
    def range_width(self) -> float:
        """Width of the uncertainty band."""
        return self.upper_bound - self.lower_bound

    @property
    def coefficient_of_variation(self) -> float:
        """Relative uncertainty measure."""
        if self.point_estimate == 0:
            return float('inf')
        return self.range_width / (2 * abs(self.point_estimate))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_estimate": self.point_estimate,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence_level": self.confidence_level.value,
            "distribution_type": self.distribution_type,
            "standard_error": self.standard_error,
            "sample_size": self.sample_size,
            "range_width": self.range_width,
            "coefficient_of_variation": round(self.coefficient_of_variation, 4),
            "methodology_note": self.methodology_note,
        }


@dataclass
class Evidence:
    """
    A piece of evidence supporting a claim or assessment.

    Combines data, citations, and reasoning chain.
    """
    claim: str                          # What is being asserted
    evidence_type: EvidenceType
    citations: List[Citation]
    supporting_data: Dict[str, Any]
    reasoning_chain: List[str]          # Step-by-step logic
    weight: float = 1.0                 # Relative importance (0-1)
    contradicts: List[str] = field(default_factory=list)  # IDs of contradicting evidence
    corroborates: List[str] = field(default_factory=list) # IDs of supporting evidence

    @property
    def evidence_id(self) -> str:
        """Generate unique ID for this evidence."""
        content = f"{self.claim}:{len(self.citations)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    @property
    def citation_quality_score(self) -> float:
        """Average quality score of citations (0-1)."""
        if not self.citations:
            return 0.0
        quality_map = {
            DataQuality.AUTHORITATIVE: 1.0,
            DataQuality.RELIABLE: 0.8,
            DataQuality.MIXED: 0.6,
            DataQuality.UNCERTAIN: 0.4,
            DataQuality.SPECULATIVE: 0.2,
            DataQuality.FALLBACK: 0.1,
        }
        scores = [quality_map.get(c.quality, 0.5) for c in self.citations]
        return sum(scores) / len(scores)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "claim": self.claim,
            "evidence_type": self.evidence_type.value,
            "citations": [c.to_dict() for c in self.citations],
            "supporting_data": self.supporting_data,
            "reasoning_chain": self.reasoning_chain,
            "weight": self.weight,
            "citation_quality_score": round(self.citation_quality_score, 3),
            "contradicts": self.contradicts,
            "corroborates": self.corroborates,
        }


@dataclass
class ProbabilisticOutput:
    """
    A probabilistic assessment with explicit uncertainty.

    Every prediction or assessment should use this structure.
    """
    outcome: str                        # What is being predicted
    probability: float                  # 0-1 probability
    confidence: ConfidenceLevel
    uncertainty: Optional[UncertaintyBand] = None
    evidence: List[Evidence] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)  # Assumptions/conditions
    time_horizon: str = "unknown"       # "1 week", "3 months", etc.
    alternative_outcomes: Dict[str, float] = field(default_factory=dict)

    @property
    def evidence_strength(self) -> float:
        """Combined strength of supporting evidence."""
        if not self.evidence:
            return 0.0
        return sum(e.weight * e.citation_quality_score for e in self.evidence) / len(self.evidence)

    @property
    def adjusted_probability(self) -> float:
        """Probability adjusted for evidence quality."""
        strength = self.evidence_strength
        # Pull probability toward 0.5 (maximum uncertainty) if evidence is weak
        return self.probability * strength + 0.5 * (1 - strength)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome,
            "probability": round(self.probability, 4),
            "adjusted_probability": round(self.adjusted_probability, 4),
            "confidence": self.confidence.value,
            "uncertainty": self.uncertainty.to_dict() if self.uncertainty else None,
            "evidence": [e.to_dict() for e in self.evidence],
            "evidence_strength": round(self.evidence_strength, 3),
            "conditions": self.conditions,
            "time_horizon": self.time_horizon,
            "alternative_outcomes": self.alternative_outcomes,
        }


@dataclass
class ExpertInsight:
    """
    A complete insight from an expert agent.

    Contains the assessment, all supporting evidence, uncertainty,
    and cross-validation results.
    """
    agent_id: str
    agent_name: str
    domain: str                         # e.g., "economic", "geopolitical"
    query: str                          # Original query
    assessment: str                     # Main finding/assessment
    probabilistic_outputs: List[ProbabilisticOutput]
    key_findings: List[str]
    risk_factors: List[Dict[str, Any]]
    recommendations: List[str]
    evidence_base: List[Evidence]
    confidence_overall: ConfidenceLevel
    uncertainty_statement: str
    caveats: List[str]
    cross_validation_notes: List[str] = field(default_factory=list)
    challenged_by: List[str] = field(default_factory=list)  # Agent IDs that disagreed
    validated_by: List[str] = field(default_factory=list)   # Agent IDs that agreed
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "query": self.query,
            "assessment": self.assessment,
            "probabilistic_outputs": [p.to_dict() for p in self.probabilistic_outputs],
            "key_findings": self.key_findings,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
            "evidence_base": [e.to_dict() for e in self.evidence_base],
            "confidence_overall": self.confidence_overall.value,
            "uncertainty_statement": self.uncertainty_statement,
            "caveats": self.caveats,
            "cross_validation_notes": self.cross_validation_notes,
            "challenged_by": self.challenged_by,
            "validated_by": self.validated_by,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
        }


# ============================================================================
# DEBATE STRUCTURES
# ============================================================================

@dataclass
class AgentPosition:
    """
    An agent's position in a debate.

    Includes their stance, arguments, and willingness to revise.
    """
    agent_id: str
    agent_name: str
    stance: str                         # Main position
    probability_estimate: float         # Their probability estimate
    confidence: ConfidenceLevel
    key_arguments: List[str]
    supporting_evidence: List[Evidence]
    counterarguments_addressed: List[str]
    willingness_to_revise: float        # 0-1, how open to changing position
    revision_conditions: List[str]      # What would change their mind

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "stance": self.stance,
            "probability_estimate": round(self.probability_estimate, 4),
            "confidence": self.confidence.value,
            "key_arguments": self.key_arguments,
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "counterarguments_addressed": self.counterarguments_addressed,
            "willingness_to_revise": self.willingness_to_revise,
            "revision_conditions": self.revision_conditions,
        }


@dataclass
class DebateRound:
    """
    A single round of agent debate.

    Captures positions, challenges, and any position revisions.
    """
    round_number: int
    topic: str
    positions: List[AgentPosition]
    challenges_raised: List[Dict[str, Any]]  # {challenger, target, challenge}
    challenges_addressed: List[Dict[str, Any]]
    position_revisions: List[Dict[str, Any]]  # {agent_id, old_pos, new_pos, reason}
    convergence_score: float            # 0-1, how much agents agree

    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_number": self.round_number,
            "topic": self.topic,
            "positions": [p.to_dict() for p in self.positions],
            "challenges_raised": self.challenges_raised,
            "challenges_addressed": self.challenges_addressed,
            "position_revisions": self.position_revisions,
            "convergence_score": round(self.convergence_score, 3),
        }


@dataclass
class ConsensusReport:
    """
    Final consensus report after agent deliberation.

    Synthesizes all agent inputs into a unified assessment.
    """
    query: str
    consensus_view: str                 # The agreed-upon assessment
    consensus_probability: float        # Weighted average probability
    confidence: ConfidenceLevel
    uncertainty_range: UncertaintyBand
    key_agreements: List[str]           # Points all agents agree on
    disagreements: List[Dict[str, Any]] # Remaining disagreements
    minority_views: List[Dict[str, Any]]  # Dissenting opinions
    contributing_agents: List[str]
    debate_rounds: List[DebateRound]
    evidence_synthesis: List[Evidence]
    final_recommendations: List[str]
    risk_assessment: Dict[str, Any]
    scenario_analysis: Dict[str, Any]
    confidence_breakdown: Dict[str, float]  # Per-domain confidence
    methodology_notes: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    total_processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "consensus_view": self.consensus_view,
            "consensus_probability": round(self.consensus_probability, 4),
            "confidence": self.confidence.value,
            "uncertainty_range": self.uncertainty_range.to_dict(),
            "key_agreements": self.key_agreements,
            "disagreements": self.disagreements,
            "minority_views": self.minority_views,
            "contributing_agents": self.contributing_agents,
            "debate_rounds": [r.to_dict() for r in self.debate_rounds],
            "evidence_synthesis": [e.to_dict() for e in self.evidence_synthesis],
            "final_recommendations": self.final_recommendations,
            "risk_assessment": self.risk_assessment,
            "scenario_analysis": self.scenario_analysis,
            "confidence_breakdown": self.confidence_breakdown,
            "methodology_notes": self.methodology_notes,
            "timestamp": self.timestamp.isoformat(),
            "total_processing_time_ms": self.total_processing_time_ms,
        }


# ============================================================================
# BASE EXPERT AGENT CLASS
# ============================================================================

T = TypeVar('T')

class ExpertAgent(ABC, Generic[T]):
    """
    Base class for all expert agents in the system.

    Every agent must implement:
    - analyze(): Core analysis method
    - validate(): Cross-validate another agent's output
    - challenge(): Challenge another agent's position
    - revise(): Revise position based on challenges

    Every agent automatically:
    - Tracks all citations
    - Quantifies uncertainty
    - Produces probabilistic outputs
    - Participates in debates
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        domain: str,
        description: str,
        data_sources: List[str],
        llm_callable: Optional[Callable] = None,
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.domain = domain
        self.description = description
        self.data_sources = data_sources
        self.llm_callable = llm_callable
        self._citations: List[Citation] = []
        self._evidence: List[Evidence] = []
        self.logger = logging.getLogger(f"agent.{agent_id}")

    def add_citation(
        self,
        source_name: str,
        source_type: str,
        data_point: str,
        value: Any,
        url: Optional[str] = None,
        methodology: Optional[str] = None,
        quality: DataQuality = DataQuality.RELIABLE,
        freshness_hours: float = 0.0,
    ) -> Citation:
        """Add a citation for data used in analysis."""
        citation = Citation(
            source_name=source_name,
            source_type=source_type,
            data_point=data_point,
            value=value,
            timestamp=datetime.utcnow(),
            url=url,
            methodology=methodology,
            quality=quality,
            freshness_hours=freshness_hours,
        )
        self._citations.append(citation)
        return citation

    def create_evidence(
        self,
        claim: str,
        evidence_type: EvidenceType,
        citations: List[Citation],
        supporting_data: Dict[str, Any],
        reasoning_chain: List[str],
        weight: float = 1.0,
    ) -> Evidence:
        """Create structured evidence for a claim."""
        evidence = Evidence(
            claim=claim,
            evidence_type=evidence_type,
            citations=citations,
            supporting_data=supporting_data,
            reasoning_chain=reasoning_chain,
            weight=weight,
        )
        self._evidence.append(evidence)
        return evidence

    def quantify_uncertainty(
        self,
        point_estimate: float,
        confidence: ConfidenceLevel,
        methodology_note: str = "",
        distribution_type: str = "normal",
    ) -> UncertaintyBand:
        """
        Generate uncertainty band based on confidence level.

        Uses standard error multipliers based on confidence level.
        """
        # Confidence level determines uncertainty width
        multipliers = {
            ConfidenceLevel.VERY_LOW: 0.40,
            ConfidenceLevel.LOW: 0.30,
            ConfidenceLevel.MODERATE: 0.20,
            ConfidenceLevel.HIGH: 0.12,
            ConfidenceLevel.VERY_HIGH: 0.06,
            ConfidenceLevel.NEAR_CERTAIN: 0.03,
        }

        multiplier = multipliers.get(confidence, 0.25)
        margin = abs(point_estimate) * multiplier

        return UncertaintyBand(
            point_estimate=point_estimate,
            lower_bound=point_estimate - margin,
            upper_bound=point_estimate + margin,
            confidence_level=confidence,
            distribution_type=distribution_type,
            methodology_note=methodology_note,
        )

    def create_probabilistic_output(
        self,
        outcome: str,
        probability: float,
        evidence: List[Evidence],
        conditions: List[str],
        time_horizon: str,
        alternatives: Optional[Dict[str, float]] = None,
    ) -> ProbabilisticOutput:
        """Create a probabilistic output with uncertainty."""
        confidence = ConfidenceLevel.from_probability(
            sum(e.citation_quality_score for e in evidence) / len(evidence) if evidence else 0.5
        )

        uncertainty = self.quantify_uncertainty(
            probability,
            confidence,
            f"Based on {len(evidence)} evidence items from {self.agent_name}",
        )

        return ProbabilisticOutput(
            outcome=outcome,
            probability=probability,
            confidence=confidence,
            uncertainty=uncertainty,
            evidence=evidence,
            conditions=conditions,
            time_horizon=time_horizon,
            alternative_outcomes=alternatives or {},
        )

    @abstractmethod
    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """
        Core analysis method.

        Must:
        - Cite all data sources
        - Quantify uncertainty
        - Produce probabilistic outputs
        """
        pass

    @abstractmethod
    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        """
        Cross-validate another agent's insight.

        Returns validation result with:
        - agreement_score (0-1)
        - validated_claims
        - questionable_claims
        - additional_evidence
        """
        pass

    @abstractmethod
    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        """
        Challenge another agent's position.

        Returns:
        - challenge_type
        - challenge_statement
        - counter_evidence
        - suggested_revision
        """
        pass

    @abstractmethod
    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        """
        Revise position based on challenges and new evidence.

        Must explain revision reasoning.
        """
        pass

    def clear_session_data(self):
        """Clear citations and evidence for new session."""
        self._citations = []
        self._evidence = []

    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "description": self.description,
            "data_sources": self.data_sources,
            "citations_count": len(self._citations),
            "evidence_count": len(self._evidence),
        }


# ============================================================================
# AGENT REGISTRY
# ============================================================================

class AgentRegistry:
    """
    Central registry for all expert agents.

    Manages agent lifecycle and enables cross-agent communication.
    """

    _instance: Optional["AgentRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: Dict[str, ExpertAgent] = {}
            cls._instance._domains: Dict[str, List[str]] = {}
        return cls._instance

    def register(self, agent: ExpertAgent) -> None:
        """Register an expert agent."""
        self._agents[agent.agent_id] = agent
        if agent.domain not in self._domains:
            self._domains[agent.domain] = []
        if agent.agent_id not in self._domains[agent.domain]:
            self._domains[agent.domain].append(agent.agent_id)
        logger.info(f"Registered agent: {agent.agent_name} ({agent.agent_id})")

    def get(self, agent_id: str) -> Optional[ExpertAgent]:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def get_by_domain(self, domain: str) -> List[ExpertAgent]:
        """Get all agents for a domain."""
        agent_ids = self._domains.get(domain, [])
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]

    def get_all(self) -> List[ExpertAgent]:
        """Get all registered agents."""
        return list(self._agents.values())

    def get_domains(self) -> List[str]:
        """Get all registered domains."""
        return list(self._domains.keys())

    def get_relevant_agents(self, query: str, domains: Optional[List[str]] = None) -> List[ExpertAgent]:
        """Get agents relevant to a query."""
        if domains:
            agents = []
            for domain in domains:
                agents.extend(self.get_by_domain(domain))
            return agents
        # Return all agents if no domains specified
        return self.get_all()

    def clear(self) -> None:
        """Clear all registered agents (for testing)."""
        self._agents = {}
        self._domains = {}


# Singleton instance
agent_registry = AgentRegistry()
