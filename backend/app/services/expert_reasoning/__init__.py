"""
Expert Reasoning Framework for JanGraph OS

This module provides the core infrastructure for expert-level AI reasoning:
- Structured evidence and citation tracking
- Uncertainty quantification with Bayesian confidence
- Probabilistic output generation
- Cross-agent validation protocols
- Internal debate mechanisms
- Consensus building with disagreement tracking

Usage:
    from app.services.expert_reasoning import run_expert_strategic_analysis

    result = await run_expert_strategic_analysis(query, tool_outputs)
"""

from .framework import (
    Evidence,
    Citation,
    UncertaintyBand,
    ProbabilisticOutput,
    ExpertInsight,
    AgentPosition,
    DebateRound,
    ConsensusReport,
    ExpertAgent,
    AgentRegistry,
    ConfidenceLevel,
    DataQuality,
    EvidenceType,
    DisagreementType,
    agent_registry,
)

from .debate_engine import DebateEngine
from .consensus_engine import ConsensusEngine
from .orchestrator import ExpertOrchestrator

from .agents import (
    EconomicAnalystAgent,
    GeopoliticalStrategistAgent,
    SocialSentimentAgent,
    ClimateEnvironmentAgent,
    PolicyImpactAgent,
    RiskAssessmentAgent,
    SimulationForecastAgent,
    create_all_expert_agents,
    get_agents_for_domains,
)

from .enhanced_strategic_agent import (
    ExpertStrategicAgent,
    expert_agent,
    run_expert_strategic_analysis,
    run_expert_whatif_simulation,
)

from .cross_validation import (
    CrossValidator,
    ConfidenceCalibrator,
    ConfidenceScore,
    ValidationReport,
    ValidationResult,
    cross_validator,
    confidence_calibrator,
)

__all__ = [
    # Core data structures
    "Evidence",
    "Citation",
    "UncertaintyBand",
    "ProbabilisticOutput",
    "ExpertInsight",
    "AgentPosition",
    "DebateRound",
    "ConsensusReport",
    # Enums
    "ConfidenceLevel",
    "DataQuality",
    "EvidenceType",
    "DisagreementType",
    # Agent infrastructure
    "ExpertAgent",
    "AgentRegistry",
    "agent_registry",
    # Specialized agents
    "EconomicAnalystAgent",
    "GeopoliticalStrategistAgent",
    "SocialSentimentAgent",
    "ClimateEnvironmentAgent",
    "PolicyImpactAgent",
    "RiskAssessmentAgent",
    "SimulationForecastAgent",
    # Factory functions
    "create_all_expert_agents",
    "get_agents_for_domains",
    # Engines
    "DebateEngine",
    "ConsensusEngine",
    "ExpertOrchestrator",
    # Enhanced strategic agent
    "ExpertStrategicAgent",
    "expert_agent",
    "run_expert_strategic_analysis",
    "run_expert_whatif_simulation",
    # Cross-validation
    "CrossValidator",
    "ConfidenceCalibrator",
    "ConfidenceScore",
    "ValidationReport",
    "ValidationResult",
    "cross_validator",
    "confidence_calibrator",
]
