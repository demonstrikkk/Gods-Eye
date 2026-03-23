"""
Expert Agent Base Classes
=========================

Foundation for all expert-level reasoning agents in JanGraph OS.
Each agent operates with:
- Domain expertise
- Evidence-based reasoning
- Uncertainty quantification
- Cross-agent communication protocols
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Generic
from dataclasses import dataclass, field
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """Standardized confidence levels following intelligence community standards."""

    VERY_HIGH = "very_high"      # 90-99% - Almost certain
    HIGH = "high"                # 75-89% - Highly likely
    MODERATE = "moderate"        # 50-74% - Likely/Possible
    LOW = "low"                  # 25-49% - Unlikely
    VERY_LOW = "very_low"        # 1-24% - Remote chance
    INSUFFICIENT = "insufficient" # Cannot assess - data gaps

    @classmethod
    def from_probability(cls, prob: float) -> "ConfidenceLevel":
        """Convert probability (0-1) to confidence level."""
        if prob >= 0.90:
            return cls.VERY_HIGH
        elif prob >= 0.75:
            return cls.HIGH
        elif prob >= 0.50:
            return cls.MODERATE
        elif prob >= 0.25:
            return cls.LOW
        elif prob > 0:
            return cls.VERY_LOW
        else:
            return cls.INSUFFICIENT

    def to_probability_range(self) -> tuple[float, float]:
        """Return the probability range for this confidence level."""
        ranges = {
            self.VERY_HIGH: (0.90, 0.99),
            self.HIGH: (0.75, 0.89),
            self.MODERATE: (0.50, 0.74),
            self.LOW: (0.25, 0.49),
            self.VERY_LOW: (0.01, 0.24),
            self.INSUFFICIENT: (0.0, 0.0),
        }
        return ranges.get(self, (0.0, 1.0))


class ReasoningMode(str, Enum):
    """Modes of reasoning employed by expert agents."""

    ANALYTICAL = "analytical"           # Structured decomposition
    PROBABILISTIC = "probabilistic"     # Bayesian inference
    ABDUCTIVE = "abductive"             # Best explanation inference
    COUNTERFACTUAL = "counterfactual"   # What-if analysis
    ADVERSARIAL = "adversarial"         # Devil's advocate
    SYNTHETIC = "synthetic"             # Cross-domain integration
    TEMPORAL = "temporal"               # Time-series analysis
    CAUSAL = "causal"                   # Cause-effect chains


class AgentCapability(str, Enum):
    """Capabilities that expert agents can possess."""

    # Data Analysis
    QUANTITATIVE_ANALYSIS = "quantitative_analysis"
    QUALITATIVE_ANALYSIS = "qualitative_analysis"
    TREND_DETECTION = "trend_detection"
    ANOMALY_DETECTION = "anomaly_detection"

    # Reasoning
    CAUSAL_INFERENCE = "causal_inference"
    SCENARIO_MODELING = "scenario_modeling"
    RISK_ASSESSMENT = "risk_assessment"
    PREDICTIVE_MODELING = "predictive_modeling"

    # Domain Expertise
    ECONOMIC_EXPERTISE = "economic_expertise"
    GEOPOLITICAL_EXPERTISE = "geopolitical_expertise"
    SOCIAL_DYNAMICS = "social_dynamics"
    ENVIRONMENTAL_SCIENCE = "environmental_science"
    POLICY_ANALYSIS = "policy_analysis"

    # Communication
    CROSS_AGENT_VALIDATION = "cross_agent_validation"
    DEBATE_PARTICIPATION = "debate_participation"
    CONSENSUS_BUILDING = "consensus_building"


@dataclass
class AgentObservation:
    """A single observation made by an agent from data."""

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    content: str = ""
    data_source: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.5
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    methodology: str = ""
    caveats: List[str] = field(default_factory=list)


@dataclass
class AgentClaim:
    """A claim or assertion made by an agent."""

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    statement: str = ""
    probability: float = 0.5
    confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE
    supporting_observations: List[str] = field(default_factory=list)  # observation IDs
    reasoning_chain: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    methodology: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "probability": self.probability,
            "confidence_level": self.confidence_level.value if isinstance(self.confidence_level, ConfidenceLevel) else self.confidence_level,
            "supporting_observations": self.supporting_observations,
            "reasoning_chain": self.reasoning_chain,
            "assumptions": self.assumptions,
            "methodology": self.methodology,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AgentAssessment:
    """Complete assessment from an expert agent."""

    agent_id: str = ""
    agent_name: str = ""
    domain: str = ""
    query_context: str = ""

    # Core analysis
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    claims: List[AgentClaim] = field(default_factory=list)
    observations: List[AgentObservation] = field(default_factory=list)

    # Uncertainty & confidence
    overall_confidence: ConfidenceLevel = ConfidenceLevel.MODERATE
    confidence_score: float = 0.5
    uncertainty_factors: List[str] = field(default_factory=list)
    data_gaps: List[str] = field(default_factory=list)

    # Evidence chain
    data_sources_used: List[str] = field(default_factory=list)
    methodology: str = ""
    reasoning_modes: List[ReasoningMode] = field(default_factory=list)

    # Cross-validation
    agreements_with: Dict[str, List[str]] = field(default_factory=dict)  # agent_id -> claim_ids
    disagreements_with: Dict[str, List[str]] = field(default_factory=dict)
    validation_requests: List[str] = field(default_factory=list)

    # Meta
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = 0.0
    model_used: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "query_context": self.query_context,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "claims": [c.to_dict() for c in self.claims],
            "overall_confidence": self.overall_confidence.value if isinstance(self.overall_confidence, ConfidenceLevel) else self.overall_confidence,
            "confidence_score": self.confidence_score,
            "uncertainty_factors": self.uncertainty_factors,
            "data_gaps": self.data_gaps,
            "data_sources_used": self.data_sources_used,
            "methodology": self.methodology,
            "reasoning_modes": [m.value if isinstance(m, ReasoningMode) else m for m in self.reasoning_modes],
            "agreements_with": self.agreements_with,
            "disagreements_with": self.disagreements_with,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used,
        }


class ExpertAgentConfig(BaseModel):
    """Configuration for expert agents."""

    agent_id: str = Field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    domain: str = ""
    description: str = ""
    capabilities: List[AgentCapability] = Field(default_factory=list)
    reasoning_modes: List[ReasoningMode] = Field(default_factory=list)

    # LLM settings
    model_preference: str = "reasoning_best"
    temperature: float = 0.3
    max_tokens: int = 4096

    # Confidence thresholds
    min_confidence_to_assert: float = 0.3
    require_evidence_threshold: float = 0.5

    # Behavior
    enable_cross_validation: bool = True
    enable_debate: bool = True
    max_reasoning_depth: int = 5

    class Config:
        use_enum_values = True


class ExpertAgent(ABC):
    """
    Base class for all expert-level reasoning agents.

    Each expert agent:
    - Has domain expertise
    - Processes relevant datasets
    - Generates evidence-backed claims
    - Quantifies uncertainty
    - Communicates with other agents
    - Participates in debates
    """

    def __init__(self, config: ExpertAgentConfig):
        self.config = config
        self.agent_id = config.agent_id
        self.name = config.name
        self.domain = config.domain

        # State tracking
        self._observations: Dict[str, AgentObservation] = {}
        self._claims: Dict[str, AgentClaim] = {}
        self._peer_assessments: Dict[str, AgentAssessment] = {}
        self._current_context: str = ""

        # Logging
        self.logger = logging.getLogger(f"agent.{self.name}")

    @property
    @abstractmethod
    def expertise_description(self) -> str:
        """Return a description of this agent's expertise."""
        pass

    @property
    @abstractmethod
    def data_sources(self) -> List[str]:
        """Return list of data sources this agent can access."""
        pass

    @property
    @abstractmethod
    def analysis_prompt_template(self) -> str:
        """Return the prompt template for this agent's analysis."""
        pass

    @abstractmethod
    async def gather_evidence(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[AgentObservation]:
        """Gather evidence from data sources for the given query."""
        pass

    @abstractmethod
    async def formulate_claims(
        self,
        observations: List[AgentObservation],
        query: str,
        context: Dict[str, Any]
    ) -> List[AgentClaim]:
        """Formulate claims based on observations."""
        pass

    @abstractmethod
    async def validate_peer_claims(
        self,
        peer_claims: List[AgentClaim],
        peer_agent_id: str
    ) -> Dict[str, bool]:
        """Validate claims from peer agents. Returns claim_id -> is_valid."""
        pass

    async def analyze(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        peer_assessments: Optional[List[AgentAssessment]] = None
    ) -> AgentAssessment:
        """
        Perform complete expert analysis.

        Steps:
        1. Gather evidence from data sources
        2. Formulate claims with uncertainty
        3. Consider peer assessments if available
        4. Generate final assessment
        """
        import time
        start_time = time.time()

        context = context or {}
        peer_assessments = peer_assessments or []
        self._current_context = query

        # Store peer assessments for reference
        for pa in peer_assessments:
            self._peer_assessments[pa.agent_id] = pa

        self.logger.info(f"Starting analysis for: {query[:100]}...")

        # Step 1: Gather evidence
        observations = await self.gather_evidence(query, context)
        for obs in observations:
            self._observations[obs.id] = obs

        # Step 2: Formulate claims
        claims = await self.formulate_claims(observations, query, context)
        for claim in claims:
            self._claims[claim.id] = claim

        # Step 3: Cross-validate with peers
        agreements: Dict[str, List[str]] = {}
        disagreements: Dict[str, List[str]] = {}

        if self.config.enable_cross_validation and peer_assessments:
            for peer in peer_assessments:
                peer_validations = await self.validate_peer_claims(
                    peer.claims, peer.agent_id
                )
                agreed_claims = [cid for cid, valid in peer_validations.items() if valid]
                disagreed_claims = [cid for cid, valid in peer_validations.items() if not valid]

                if agreed_claims:
                    agreements[peer.agent_id] = agreed_claims
                if disagreed_claims:
                    disagreements[peer.agent_id] = disagreed_claims

        # Step 4: Calculate overall confidence
        confidence_score = self._calculate_overall_confidence(claims, observations)
        confidence_level = ConfidenceLevel.from_probability(confidence_score)

        # Step 5: Identify uncertainty factors and data gaps
        uncertainty_factors = self._identify_uncertainty_factors(observations, claims)
        data_gaps = self._identify_data_gaps(query, observations)

        # Step 6: Generate executive summary
        executive_summary = await self._generate_executive_summary(
            query, claims, observations, confidence_level
        )

        processing_time = (time.time() - start_time) * 1000

        assessment = AgentAssessment(
            agent_id=self.agent_id,
            agent_name=self.name,
            domain=self.domain,
            query_context=query,
            executive_summary=executive_summary,
            key_findings=[c.statement for c in claims if c.probability >= 0.5],
            claims=claims,
            observations=observations,
            overall_confidence=confidence_level,
            confidence_score=confidence_score,
            uncertainty_factors=uncertainty_factors,
            data_gaps=data_gaps,
            data_sources_used=list(set(obs.data_source for obs in observations)),
            methodology=self._describe_methodology(),
            reasoning_modes=self.config.reasoning_modes,
            agreements_with=agreements,
            disagreements_with=disagreements,
            processing_time_ms=processing_time,
            model_used=self.config.model_preference,
        )

        self.logger.info(
            f"Analysis complete. Confidence: {confidence_level.value}, "
            f"Claims: {len(claims)}, Time: {processing_time:.0f}ms"
        )

        return assessment

    def _calculate_overall_confidence(
        self,
        claims: List[AgentClaim],
        observations: List[AgentObservation]
    ) -> float:
        """Calculate overall confidence score for the assessment."""
        if not claims:
            return 0.0

        # Weight by claim probability
        claim_confidences = []
        for c in claims:
            confidence_level = c.confidence_level
            # Handle both enum and string cases
            if isinstance(confidence_level, ConfidenceLevel):
                prob_range = confidence_level.to_probability_range()[0]
            else:
                # If it's a string, map back to enum to get probability range
                try:
                    prob_range = ConfidenceLevel(confidence_level).to_probability_range()[0]
                except (ValueError, KeyError):
                    prob_range = 0.5  # Default to moderate
            claim_confidences.append(c.probability * prob_range)

        # Factor in observation quality
        obs_quality = sum(o.confidence for o in observations) / max(len(observations), 1)

        # Combined score
        claim_score = sum(claim_confidences) / len(claims) if claims else 0.5

        # Blend claim score with observation quality
        return 0.7 * claim_score + 0.3 * obs_quality

    def _identify_uncertainty_factors(
        self,
        observations: List[AgentObservation],
        claims: List[AgentClaim]
    ) -> List[str]:
        """Identify factors contributing to uncertainty."""
        factors = []

        # Low observation confidence
        low_conf_obs = [o for o in observations if o.confidence < 0.5]
        if low_conf_obs:
            factors.append(f"Low confidence in {len(low_conf_obs)} data observations")

        # Claims with many assumptions
        high_assumption_claims = [c for c in claims if len(c.assumptions) > 2]
        if high_assumption_claims:
            factors.append(f"{len(high_assumption_claims)} claims rely on multiple assumptions")

        # Collect all caveats
        all_caveats = []
        for obs in observations:
            all_caveats.extend(obs.caveats)
        if all_caveats:
            factors.extend(list(set(all_caveats))[:3])

        return factors

    def _identify_data_gaps(
        self,
        query: str,
        observations: List[AgentObservation]
    ) -> List[str]:
        """Identify gaps in available data."""
        gaps = []

        # Check for missing data sources
        all_sources = set(self.data_sources)
        used_sources = set(obs.data_source for obs in observations)
        missing_sources = all_sources - used_sources

        if missing_sources:
            gaps.append(f"Data not available from: {', '.join(missing_sources)}")

        # Check for temporal gaps
        timestamps = [obs.timestamp for obs in observations]
        if timestamps:
            oldest = min(timestamps)
            now = datetime.now(timezone.utc)
            age_hours = (now - oldest).total_seconds() / 3600
            if age_hours > 24:
                gaps.append(f"Some data is {age_hours:.0f} hours old")

        return gaps

    async def _generate_executive_summary(
        self,
        query: str,
        claims: List[AgentClaim],
        observations: List[AgentObservation],
        confidence: ConfidenceLevel
    ) -> str:
        """Generate an executive summary of the analysis."""
        high_confidence_claims = [c for c in claims if c.probability >= 0.7]
        moderate_claims = [c for c in claims if 0.4 <= c.probability < 0.7]

        summary_parts = []
        summary_parts.append(f"Assessment by {self.name} ({self.domain})")
        summary_parts.append(f"Overall confidence: {(confidence.value if isinstance(confidence, ConfidenceLevel) else confidence).replace('_', ' ').title()}")

        if high_confidence_claims:
            summary_parts.append("\nHigh-confidence findings:")
            for c in high_confidence_claims[:3]:
                summary_parts.append(f"  - {c.statement} ({c.probability:.0%})")

        if moderate_claims:
            summary_parts.append("\nModerate-confidence findings:")
            for c in moderate_claims[:2]:
                summary_parts.append(f"  - {c.statement} ({c.probability:.0%})")

        return "\n".join(summary_parts)

    def _describe_methodology(self) -> str:
        """Describe the methodology used by this agent."""
        modes = [(m.value if isinstance(m, ReasoningMode) else m).replace("_", " ").title() for m in self.config.reasoning_modes]
        return f"Applied {', '.join(modes)} reasoning to {len(self.data_sources)} data sources."

    # Debate interface methods
    async def propose_argument(
        self,
        topic: str,
        position: str,
        supporting_evidence: List[str]
    ) -> Dict[str, Any]:
        """Propose an argument on a topic for debate."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "topic": topic,
            "position": position,
            "supporting_evidence": supporting_evidence,
            "confidence": self._calculate_argument_confidence(supporting_evidence),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def respond_to_argument(
        self,
        argument: Dict[str, Any],
        stance: str  # "agree", "disagree", "partially_agree"
    ) -> Dict[str, Any]:
        """Respond to another agent's argument."""
        return {
            "agent_id": self.agent_id,
            "responding_to": argument.get("agent_id"),
            "topic": argument.get("topic"),
            "stance": stance,
            "reasoning": await self._generate_counter_reasoning(argument, stance),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_argument_confidence(self, evidence: List[str]) -> float:
        """Calculate confidence in an argument based on evidence quantity/quality."""
        if not evidence:
            return 0.3

        # Base on evidence count with diminishing returns
        base_conf = min(0.5 + (len(evidence) * 0.1), 0.9)
        return base_conf

    async def _generate_counter_reasoning(
        self,
        argument: Dict[str, Any],
        stance: str
    ) -> str:
        """Generate reasoning for a response to an argument."""
        if stance == "agree":
            return f"Concur with assessment based on {self.domain} analysis."
        elif stance == "disagree":
            return f"Disagree from {self.domain} perspective due to conflicting evidence."
        else:
            return f"Partially concur, but {self.domain} data suggests nuances."

    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get current state snapshot for debugging/logging."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "domain": self.domain,
            "observations_count": len(self._observations),
            "claims_count": len(self._claims),
            "peer_assessments_count": len(self._peer_assessments),
            "current_context": self._current_context[:100] if self._current_context else None,
        }
