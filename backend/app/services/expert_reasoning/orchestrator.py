"""
Expert Orchestrator for Gods-Eye OS

This module orchestrates the complete expert reasoning pipeline:
1. Parse user query to identify relevant domains
2. Dispatch to appropriate expert agents
3. Collect initial assessments from all agents
4. Conduct structured debate for consensus building
5. Synthesize final report with full provenance

The orchestrator ensures:
- All relevant domains are consulted
- Evidence is properly cited
- Uncertainty is quantified
- Disagreements are documented
- Final output includes consensus and confidence
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json

from .framework import (
    AgentPosition,
    ConfidenceLevel,
    ConsensusReport,
    DebateRound,
    Evidence,
    ExpertAgent,
    ExpertInsight,
    UncertaintyBand,
    agent_registry,
)
from .debate_engine import DebateEngine, DebateConfig
from .consensus_engine import ConsensusEngine, ConsensusConfig
from .agents import create_all_expert_agents, get_agents_for_domains

logger = logging.getLogger(__name__)


@dataclass
class QueryAnalysis:
    """
    Analysis of user query to determine required domains and agents.
    """
    original_query: str
    detected_domains: List[str]
    key_entities: List[str]
    scenario_type: str  # "what_if", "assessment", "forecast", "comparison"
    time_horizon: str
    geographic_scope: List[str]
    variables_mentioned: Dict[str, Any]
    requires_simulation: bool
    urgency_level: str  # "routine", "elevated", "urgent", "critical"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_query": self.original_query,
            "detected_domains": self.detected_domains,
            "key_entities": self.key_entities,
            "scenario_type": self.scenario_type,
            "time_horizon": self.time_horizon,
            "geographic_scope": self.geographic_scope,
            "variables_mentioned": self.variables_mentioned,
            "requires_simulation": self.requires_simulation,
            "urgency_level": self.urgency_level,
        }


@dataclass
class OrchestratorConfig:
    """Configuration for the expert orchestrator."""
    max_agents: int = 7
    parallel_analysis: bool = True
    analysis_timeout_seconds: float = 60.0
    require_debate: bool = True
    max_debate_rounds: int = 3
    min_agents_for_consensus: int = 2
    include_uncertainty_bands: bool = True
    citation_required: bool = True


class ExpertOrchestrator:
    """
    Main orchestrator for the expert reasoning system.

    Coordinates multiple expert agents through:
    1. Query analysis and domain detection
    2. Parallel agent dispatch
    3. Structured debate
    4. Consensus building
    5. Final report generation
    """

    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        llm_callable=None,
    ):
        self.config = config or OrchestratorConfig()
        self.llm_callable = llm_callable
        self.debate_engine = DebateEngine(DebateConfig(
            max_rounds=self.config.max_debate_rounds,
            require_evidence_for_challenges=self.config.citation_required,
        ))
        self.consensus_engine = ConsensusEngine(ConsensusConfig(
            min_agents_for_consensus=self.config.min_agents_for_consensus,
            require_debate=self.config.require_debate,
        ))
        self.logger = logging.getLogger(__name__)
        self._agents_initialized = False

    def ensure_agents_initialized(self) -> List[ExpertAgent]:
        """Ensure all expert agents are created and registered."""
        if not self._agents_initialized:
            agents = create_all_expert_agents(self.llm_callable)
            self._agents_initialized = True
            self.logger.info(f"Initialized {len(agents)} expert agents")
            return agents
        return agent_registry.get_all()

    async def process_query(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> ConsensusReport:
        """
        Process a user query through the full expert reasoning pipeline.

        Args:
            query: The user's question or scenario
            context: Tool output data and additional context

        Returns:
            ConsensusReport with full analysis and provenance
        """
        start_time = time.time()
        self.logger.info(f"Processing query: {query[:100]}...")

        # Step 1: Ensure agents are initialized
        self.ensure_agents_initialized()

        # Step 2: Analyze query to detect domains
        query_analysis = self._analyze_query(query, context)
        self.logger.info(f"Detected domains: {query_analysis.detected_domains}")

        # Step 3: Select relevant agents
        agents = self._select_agents(query_analysis)
        self.logger.info(f"Selected {len(agents)} agents for analysis")

        if not agents:
            return self._no_agents_response(query)

        # Step 4: Run parallel analysis
        insights = await self._run_parallel_analysis(agents, query, context)
        self.logger.info(f"Collected {len(insights)} agent insights")

        # Step 5: Build consensus (includes debate)
        consensus = await self.consensus_engine.build_consensus(
            query=query,
            agents=agents,
            insights=insights,
            context=context,
        )

        # Step 6: Enhance with query analysis metadata
        consensus = self._enhance_consensus(consensus, query_analysis, context)

        elapsed_ms = (time.time() - start_time) * 1000
        consensus.total_processing_time_ms = elapsed_ms

        self.logger.info(f"Query processed in {elapsed_ms:.1f}ms, confidence: {consensus.confidence.value}")

        return consensus

    def _analyze_query(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> QueryAnalysis:
        """
        Analyze the query to extract domains, entities, and intent.

        Uses keyword matching and pattern detection for domain identification.
        """
        query_lower = query.lower()

        # Domain detection keywords
        domain_keywords = {
            "economic": ["gdp", "inflation", "trade", "economy", "market", "price", "cost", "growth", "recession", "fiscal", "monetary", "unemployment", "export", "import", "tariff"],
            "geopolitical": ["conflict", "war", "tension", "military", "alliance", "treaty", "sanctions", "diplomacy", "border", "territory", "strategic", "security", "defense"],
            "social": ["public", "sentiment", "protest", "unrest", "opinion", "approval", "social", "civil", "population", "demographic", "migration"],
            "climate": ["climate", "weather", "fire", "flood", "drought", "earthquake", "disaster", "environment", "emission", "carbon", "temperature"],
            "policy": ["policy", "government", "regulation", "law", "legislation", "subsidy", "tax", "reform", "election", "political"],
            "risk": ["risk", "threat", "vulnerability", "exposure", "impact", "consequence", "cascade", "systemic"],
            "simulation": ["what if", "what-if", "scenario", "forecast", "predict", "project", "simulate", "model", "future"],
        }

        # Detect domains
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            for kw in keywords:
                if kw in query_lower:
                    if domain not in detected_domains:
                        detected_domains.append(domain)
                    break

        # Default to economic and geopolitical if no specific domains detected
        if not detected_domains:
            detected_domains = ["economic", "geopolitical", "risk"]

        # Always include simulation for what-if queries
        if "what if" in query_lower or "what-if" in query_lower:
            if "simulation" not in detected_domains:
                detected_domains.append("simulation")

        # Always include risk assessment
        if "risk" not in detected_domains:
            detected_domains.append("risk")

        # Detect scenario type
        scenario_type = "assessment"
        if "what if" in query_lower or "what-if" in query_lower:
            scenario_type = "what_if"
        elif "forecast" in query_lower or "predict" in query_lower:
            scenario_type = "forecast"
        elif "compare" in query_lower or "versus" in query_lower:
            scenario_type = "comparison"

        # Extract geographic scope
        countries = ["india", "china", "usa", "russia", "middle east", "europe", "asia", "africa"]
        geographic_scope = [c for c in countries if c in query_lower]

        # Extract time horizon
        time_horizon = "medium_term"
        if "tomorrow" in query_lower or "week" in query_lower:
            time_horizon = "short_term"
        elif "year" in query_lower or "long" in query_lower:
            time_horizon = "long_term"

        # Extract variable mentions
        variables = {}
        if "%" in query:
            # Try to extract percentage changes
            import re
            pct_matches = re.findall(r'(\d+)%', query)
            if pct_matches:
                variables["percentage_change"] = int(pct_matches[0])

        if "oil" in query_lower:
            variables["commodity"] = "oil"
        if "price" in query_lower:
            variables["metric"] = "price"

        # Determine urgency
        urgency = "routine"
        if "urgent" in query_lower or "immediate" in query_lower:
            urgency = "critical"
        elif "important" in query_lower or "significant" in query_lower:
            urgency = "elevated"

        return QueryAnalysis(
            original_query=query,
            detected_domains=detected_domains,
            key_entities=geographic_scope,
            scenario_type=scenario_type,
            time_horizon=time_horizon,
            geographic_scope=geographic_scope,
            variables_mentioned=variables,
            requires_simulation=scenario_type in ["what_if", "forecast"],
            urgency_level=urgency,
        )

    def _select_agents(
        self,
        query_analysis: QueryAnalysis,
    ) -> List[ExpertAgent]:
        """Select relevant agents based on query analysis."""
        agents = []

        for domain in query_analysis.detected_domains:
            domain_agents = agent_registry.get_by_domain(domain)
            for agent in domain_agents:
                if agent not in agents:
                    agents.append(agent)
                    if len(agents) >= self.config.max_agents:
                        break

            if len(agents) >= self.config.max_agents:
                break

        return agents

    async def _run_parallel_analysis(
        self,
        agents: List[ExpertAgent],
        query: str,
        context: Dict[str, Any],
    ) -> List[ExpertInsight]:
        """Run analysis across all agents in parallel."""
        if not self.config.parallel_analysis:
            # Sequential execution
            insights = []
            for agent in agents:
                try:
                    insight = await asyncio.wait_for(
                        agent.analyze(query, context),
                        timeout=self.config.analysis_timeout_seconds / len(agents),
                    )
                    insights.append(insight)
                except asyncio.TimeoutError:
                    self.logger.warning(f"Agent {agent.agent_name} timed out")
                except Exception as e:
                    self.logger.error(f"Agent {agent.agent_name} error: {e}")
            return insights

        # Parallel execution
        tasks = [
            self._run_agent_with_timeout(agent, query, context)
            for agent in agents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        insights = []
        for i, result in enumerate(results):
            if isinstance(result, ExpertInsight):
                insights.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Agent {agents[i].agent_name} failed: {result}")

        return insights

    async def _run_agent_with_timeout(
        self,
        agent: ExpertAgent,
        query: str,
        context: Dict[str, Any],
    ) -> ExpertInsight:
        """Run a single agent with timeout."""
        try:
            return await asyncio.wait_for(
                agent.analyze(query, context),
                timeout=self.config.analysis_timeout_seconds,
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Agent {agent.agent_name} timed out")
            raise
        except Exception as e:
            self.logger.error(f"Agent {agent.agent_name} error: {e}")
            raise

    def _enhance_consensus(
        self,
        consensus: ConsensusReport,
        query_analysis: QueryAnalysis,
        context: Dict[str, Any],
    ) -> ConsensusReport:
        """Enhance consensus report with additional metadata."""
        # Add query analysis to methodology notes
        enhanced_notes = consensus.methodology_notes + f"""

QUERY ANALYSIS:
- Detected domains: {', '.join(query_analysis.detected_domains)}
- Scenario type: {query_analysis.scenario_type}
- Time horizon: {query_analysis.time_horizon}
- Geographic scope: {', '.join(query_analysis.geographic_scope) or 'Global'}
- Requires simulation: {query_analysis.requires_simulation}
- Urgency level: {query_analysis.urgency_level}
"""

        # Update scenario analysis with query-specific info
        if query_analysis.requires_simulation:
            consensus.scenario_analysis["query_variables"] = query_analysis.variables_mentioned
            consensus.scenario_analysis["scenario_type"] = query_analysis.scenario_type

        consensus.methodology_notes = enhanced_notes

        return consensus

    def _no_agents_response(self, query: str) -> ConsensusReport:
        """Return response when no agents are available."""
        return ConsensusReport(
            query=query,
            consensus_view="UNAVAILABLE: No expert agents could be activated for this query",
            consensus_probability=0.5,
            confidence=ConfidenceLevel.VERY_LOW,
            uncertainty_range=UncertaintyBand(
                point_estimate=0.5,
                lower_bound=0.1,
                upper_bound=0.9,
                confidence_level=ConfidenceLevel.VERY_LOW,
            ),
            key_agreements=[],
            disagreements=[],
            minority_views=[],
            contributing_agents=[],
            debate_rounds=[],
            evidence_synthesis=[],
            final_recommendations=["Initialize expert agents before processing queries"],
            risk_assessment={"overall_risk_level": "Unknown"},
            scenario_analysis={},
            confidence_breakdown={},
            methodology_notes="No agents available for analysis",
        )

    async def run_what_if_simulation(
        self,
        base_context: Dict[str, Any],
        what_if_query: str,
        variable_changes: Dict[str, Any],
    ) -> ConsensusReport:
        """
        Run a what-if simulation with variable modifications.

        Args:
            base_context: Original context/data
            what_if_query: The what-if question
            variable_changes: Variables to modify (e.g., {"oil_price_change": 0.20})

        Returns:
            ConsensusReport with simulation results
        """
        # Create modified context
        modified_context = base_context.copy()
        modified_context["what_if_variables"] = variable_changes
        modified_context["is_simulation"] = True

        # Process through normal pipeline
        return await self.process_query(what_if_query, modified_context)


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

async def run_expert_analysis(
    query: str,
    tool_outputs: Dict[str, Any],
    llm_callable=None,
) -> Dict[str, Any]:
    """
    Main entry point for expert analysis.

    Integrates with existing strategic agent tool outputs.

    Args:
        query: The user query
        tool_outputs: Outputs from OSINT tools
        llm_callable: Optional LLM callable for enhanced reasoning

    Returns:
        Dict containing the full consensus report
    """
    orchestrator = ExpertOrchestrator(llm_callable=llm_callable)

    # Build context from tool outputs
    context = {}
    for tool_name, output in tool_outputs.items():
        if isinstance(output, dict):
            context[tool_name] = output
        else:
            context[tool_name] = {"data": output}

    # Run analysis
    consensus = await orchestrator.process_query(query, context)

    return consensus.to_dict()


def format_expert_output(consensus: ConsensusReport) -> str:
    """
    Format consensus report for human-readable output.

    Creates a structured text representation of the analysis.
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("EXPERT INTELLIGENCE ASSESSMENT")
    lines.append("=" * 80)
    lines.append("")

    # Consensus View
    lines.append("CONSENSUS VIEW:")
    lines.append("-" * 40)
    lines.append(consensus.consensus_view)
    lines.append("")

    # Key Metrics
    lines.append(f"Consensus Probability: {consensus.consensus_probability:.0%}")
    lines.append(f"Confidence Level: {consensus.confidence.value.upper()}")
    lines.append(f"Uncertainty Range: {consensus.uncertainty_range.lower_bound:.0%} - {consensus.uncertainty_range.upper_bound:.0%}")
    lines.append("")

    # Contributing Agents
    lines.append(f"Contributing Experts: {', '.join(consensus.contributing_agents)}")
    lines.append("")

    # Key Agreements
    if consensus.key_agreements:
        lines.append("KEY AGREEMENTS:")
        lines.append("-" * 40)
        for agreement in consensus.key_agreements[:5]:
            lines.append(f"  - {agreement}")
        lines.append("")

    # Disagreements
    if consensus.disagreements:
        lines.append("NOTABLE DISAGREEMENTS:")
        lines.append("-" * 40)
        for disagreement in consensus.disagreements[:3]:
            lines.append(f"  - {disagreement.get('description', 'No description')}")
        lines.append("")

    # Risk Assessment
    lines.append("RISK ASSESSMENT:")
    lines.append("-" * 40)
    lines.append(f"  Overall Risk Level: {consensus.risk_assessment.get('overall_risk_level', 'Unknown')}")
    lines.append("")

    # Recommendations
    if consensus.final_recommendations:
        lines.append("RECOMMENDATIONS:")
        lines.append("-" * 40)
        for rec in consensus.final_recommendations[:5]:
            lines.append(f"  - {rec}")
        lines.append("")

    # Footer
    lines.append("=" * 80)
    lines.append(f"Analysis completed: {consensus.timestamp.isoformat()}")
    lines.append(f"Processing time: {consensus.total_processing_time_ms:.1f}ms")
    lines.append("=" * 80)

    return "\n".join(lines)
