"""
JanGraph OS Expert Agent System
==============================

Elite-level multi-agent reasoning system with:
- Expert domain agents
- Uncertainty quantification
- Cross-agent validation
- Internal debate mechanisms
- Consensus building
- Evidence-based citations
"""

from .expert_base import (
    ExpertAgent,
    AgentCapability,
    ReasoningMode,
    ConfidenceLevel,
)
from .evidence_tracker import (
    EvidenceTracker,
    Citation,
    DataSource,
    EvidenceChain,
)
from .uncertainty_engine import (
    UncertaintyQuantifier,
    ProbabilisticAssessment,
    ConfidenceInterval,
    BayesianUpdater,
)
from .debate_system import (
    AgentDebateSystem,
    DebateRound,
    Position,
    Argument,
    Rebuttal,
)
from .consensus_builder import (
    ConsensusBuilder,
    ConsensusResult,
    Disagreement,
    VotingMechanism,
)
from .expert_agents import (
    EconomicAnalystAgent,
    GeopoliticalStrategistAgent,
    SocialSentimentAgent,
    ClimateEnvironmentAgent,
    PolicyImpactAgent,
    RiskAssessmentAgent,
    SimulationForecastAgent,
)
from .agent_orchestrator import (
    ExpertAgentOrchestrator,
    QueryContext,
    OrchestratedResponse,
)

__all__ = [
    # Base classes
    "ExpertAgent",
    "AgentCapability",
    "ReasoningMode",
    "ConfidenceLevel",
    # Evidence tracking
    "EvidenceTracker",
    "Citation",
    "DataSource",
    "EvidenceChain",
    # Uncertainty
    "UncertaintyQuantifier",
    "ProbabilisticAssessment",
    "ConfidenceInterval",
    "BayesianUpdater",
    # Debate
    "AgentDebateSystem",
    "DebateRound",
    "Position",
    "Argument",
    "Rebuttal",
    # Consensus
    "ConsensusBuilder",
    "ConsensusResult",
    "Disagreement",
    "VotingMechanism",
    # Expert Agents
    "EconomicAnalystAgent",
    "GeopoliticalStrategistAgent",
    "SocialSentimentAgent",
    "ClimateEnvironmentAgent",
    "PolicyImpactAgent",
    "RiskAssessmentAgent",
    "SimulationForecastAgent",
    # Orchestration
    "ExpertAgentOrchestrator",
    "QueryContext",
    "OrchestratedResponse",
]
