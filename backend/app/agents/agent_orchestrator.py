"""
Expert Agent Orchestrator
=========================

Central orchestration engine for multi-agent expert reasoning:
- Query parsing and domain identification
- Agent selection and parallel execution
- Cross-validation coordination
- Debate orchestration
- Consensus synthesis
- Final output generation
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel, Field

from .expert_base import (
    ExpertAgent,
    AgentAssessment,
    AgentClaim,
    ConfidenceLevel,
    ReasoningMode,
)
from .expert_agents import create_all_expert_agents, create_expert_agent
from .debate_system import AgentDebateSystem, agent_debate_system
from .consensus_builder import ConsensusBuilder, ConsensusResult, consensus_builder
from .uncertainty_engine import uncertainty_quantifier
from .evidence_tracker import evidence_tracker

logger = logging.getLogger(__name__)


class QueryDomain(str, Enum):
    """Recognized query domains."""

    ECONOMIC = "economic"
    GEOPOLITICAL = "geopolitical"
    SOCIAL = "social"
    CLIMATE = "climate"
    POLICY = "policy"
    RISK = "risk"
    SIMULATION = "simulation"
    MULTI_DOMAIN = "multi_domain"


@dataclass
class QueryContext:
    """
    Parsed and enriched query context.
    """

    query_id: str = field(default_factory=lambda: str(uuid4())[:8])
    raw_query: str = ""
    normalized_query: str = ""

    # Domain analysis
    primary_domain: QueryDomain = QueryDomain.MULTI_DOMAIN
    secondary_domains: List[QueryDomain] = field(default_factory=list)
    domain_confidence: Dict[str, float] = field(default_factory=dict)

    # Entity extraction
    countries: List[str] = field(default_factory=list)
    regions: List[str] = field(default_factory=list)
    time_references: List[str] = field(default_factory=list)
    key_entities: List[str] = field(default_factory=list)

    # Query type
    is_what_if: bool = False
    is_comparison: bool = False
    is_forecast: bool = False
    is_historical: bool = False

    # Variables for simulation
    simulation_variables: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "raw_query": self.raw_query,
            "primary_domain": self.primary_domain.value,
            "secondary_domains": [d.value for d in self.secondary_domains],
            "domain_confidence": self.domain_confidence,
            "countries": self.countries,
            "regions": self.regions,
            "is_what_if": self.is_what_if,
            "is_forecast": self.is_forecast,
            "simulation_variables": self.simulation_variables,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class OrchestratedResponse:
    """
    Complete orchestrated response from multi-agent system.
    """

    query_context: QueryContext = field(default_factory=QueryContext)

    # Consensus result
    consensus: Optional[ConsensusResult] = None

    # Individual agent assessments
    agent_assessments: Dict[str, AgentAssessment] = field(default_factory=dict)

    # Debate record
    debate_conducted: bool = False
    debate_summary: Optional[Dict[str, Any]] = None

    # Executive output
    executive_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Confidence metrics
    overall_confidence: str = ""
    confidence_score: float = 0.0

    # Disagreements (if any)
    disagreements: List[Dict[str, Any]] = field(default_factory=list)
    minority_opinions: List[Dict[str, Any]] = field(default_factory=list)

    # Evidence & citations
    data_sources_cited: List[str] = field(default_factory=list)
    citations: List[Dict[str, Any]] = field(default_factory=list)

    # Uncertainty
    uncertainty_factors: List[str] = field(default_factory=list)
    key_assumptions: List[str] = field(default_factory=list)

    # Scenarios
    scenarios: Dict[str, Any] = field(default_factory=dict)

    # Map visualization data
    map_layers: List[Dict[str, Any]] = field(default_factory=list)
    affected_regions: List[str] = field(default_factory=list)

    # Timeline
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    # Causal chain
    causal_chain: List[str] = field(default_factory=list)

    # Processing metadata
    agents_consulted: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_context": self.query_context.to_dict(),
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "recommendations": self.recommendations,
            "consensus": self.consensus.to_dict() if self.consensus else None,
            "confidence": {
                "level": self.overall_confidence,
                "score": self.confidence_score,
            },
            "disagreements": self.disagreements,
            "minority_opinions": self.minority_opinions,
            "data_sources": self.data_sources_cited,
            "citations": self.citations,
            "uncertainty": {
                "factors": self.uncertainty_factors,
                "assumptions": self.key_assumptions,
            },
            "scenarios": self.scenarios,
            "map_visualization": {
                "layers": self.map_layers,
                "affected_regions": self.affected_regions,
            },
            "timeline": self.timeline,
            "causal_chain": self.causal_chain,
            "debate": {
                "conducted": self.debate_conducted,
                "summary": self.debate_summary,
            },
            "agent_assessments": {
                k: v.to_dict() for k, v in self.agent_assessments.items()
            },
            "metadata": {
                "agents_consulted": self.agents_consulted,
                "processing_time_ms": self.processing_time_ms,
                "timestamp": self.timestamp.isoformat(),
            },
        }


class ExpertAgentOrchestrator:
    """
    Orchestrates multi-agent expert reasoning system.

    Workflow:
    1. Parse and understand query
    2. Identify relevant domains
    3. Select and invoke appropriate agents
    4. Run cross-validation
    5. Conduct debate (if significant disagreement)
    6. Build consensus
    7. Generate final output
    """

    # Domain keyword mappings
    DOMAIN_KEYWORDS = {
        QueryDomain.ECONOMIC: [
            "gdp", "inflation", "economy", "economic", "trade", "currency",
            "market", "finance", "fiscal", "monetary", "growth", "recession",
            "oil price", "interest rate", "unemployment", "debt", "deficit",
        ],
        QueryDomain.GEOPOLITICAL: [
            "war", "conflict", "military", "defense", "alliance", "diplomatic",
            "tension", "border", "nuclear", "weapons", "sanctions", "coup",
            "invasion", "terrorism", "security", "nato", "china", "russia",
        ],
        QueryDomain.SOCIAL: [
            "protest", "sentiment", "public opinion", "social", "unrest",
            "movement", "civil", "demonstration", "strike", "population",
            "migration", "refugee", "rights", "equality",
        ],
        QueryDomain.CLIMATE: [
            "climate", "weather", "flood", "drought", "fire", "earthquake",
            "hurricane", "monsoon", "temperature", "environment", "pollution",
            "carbon", "emissions", "disaster",
        ],
        QueryDomain.POLICY: [
            "policy", "regulation", "law", "government", "legislation",
            "reform", "scheme", "program", "minister", "election",
            "parliament", "governance",
        ],
        QueryDomain.SIMULATION: [
            "what if", "simulate", "scenario", "forecast", "predict",
            "project", "model", "future", "trend", "projection",
        ],
    }

    # India-specific keywords
    INDIA_KEYWORDS = [
        "india", "indian", "delhi", "mumbai", "modi", "bjp", "congress",
        "rupee", "rbi", "lok sabha", "pradhan mantri", "state",
    ]

    def __init__(
        self,
        enable_debate: bool = True,
        min_agents_for_debate: int = 3,
        debate_threshold: float = 0.25,  # Min divergence to trigger debate
        max_parallel_agents: int = 5,
    ):
        self.enable_debate = enable_debate
        self.min_agents_for_debate = min_agents_for_debate
        self.debate_threshold = debate_threshold
        self.max_parallel_agents = max_parallel_agents

        # Initialize agents
        self._agents: Dict[str, ExpertAgent] = create_all_expert_agents()

        # Debate system
        self._debate_system = agent_debate_system

        # Consensus builder
        self._consensus_builder = consensus_builder

        self.logger = logging.getLogger("orchestrator")

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        force_agents: Optional[List[str]] = None,
    ) -> OrchestratedResponse:
        """
        Process a user query through the multi-agent system.

        Args:
            query: User's natural language query
            context: Optional additional context (data, history, etc.)
            force_agents: Optional list of specific agents to use

        Returns:
            OrchestratedResponse with full analysis
        """
        import time
        start_time = time.time()

        self.logger.info(f"Processing query: {query[:100]}...")

        # Enrich context with real data from all available sources
        context = await self._enrich_context(context or {}, query)
        self.logger.info(f"Context enriched with {len(context)} data sources")

        # Step 1: Parse and understand query
        query_context = self._parse_query(query)
        self.logger.info(f"Query analysis: primary_domain={query_context.primary_domain.value}")

        # Step 2: Select agents
        selected_agents = self._select_agents(query_context, force_agents)
        self.logger.info(f"Selected agents: {[a.name for a in selected_agents]}")

        # Step 3: Run agents in parallel
        assessments = await self._run_agents_parallel(selected_agents, query, context)
        self.logger.info(f"Received {len(assessments)} agent assessments")

        # Step 4: Check for divergence and conduct debate if needed
        debate_summary = None
        if self._should_conduct_debate(assessments):
            self.logger.info("Significant divergence detected - initiating debate")
            debate_summary = await self._debate_system.initiate_debate(
                topic=query_context.primary_domain.value,
                question=query,
                agents=selected_agents,
                initial_assessments={a.agent_id: assessments[a.agent_id]
                                     for a in selected_agents if a.agent_id in assessments},
            )

        # Step 5: Build consensus
        consensus = self._consensus_builder.build_consensus(
            query=query,
            assessments=list(assessments.values()),
            debate_summary=debate_summary,
        )

        # Step 6: Generate final response
        response = self._generate_response(
            query_context=query_context,
            assessments=assessments,
            consensus=consensus,
            debate_summary=debate_summary,
            context=context,
        )

        response.processing_time_ms = (time.time() - start_time) * 1000

        self.logger.info(
            f"Query processed in {response.processing_time_ms:.0f}ms. "
            f"Confidence: {response.overall_confidence}"
        )

        return response

    def _parse_query(self, query: str) -> QueryContext:
        """Parse and analyze the user query."""
        query_lower = query.lower()

        # Domain detection
        domain_scores: Dict[QueryDomain, float] = {}
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                domain_scores[domain] = score

        # Normalize scores
        total = sum(domain_scores.values()) or 1
        domain_confidence = {d.value: s / total for d, s in domain_scores.items()}

        # Determine primary domain
        if domain_scores:
            primary = max(domain_scores, key=domain_scores.get)
            secondary = [d for d, s in domain_scores.items() if d != primary and s > 0]
        else:
            primary = QueryDomain.MULTI_DOMAIN
            secondary = []

        # Query type detection
        is_what_if = any(p in query_lower for p in ["what if", "what happens if", "suppose", "assuming"])
        is_forecast = any(p in query_lower for p in ["predict", "forecast", "future", "will", "expect"])
        is_comparison = any(p in query_lower for p in ["compare", "versus", "vs", "difference between"])
        is_historical = any(p in query_lower for p in ["historical", "past", "previous", "before"])

        # Country/region extraction (simple pattern matching)
        countries = []
        regions = []

        country_patterns = [
            "india", "china", "usa", "russia", "pakistan", "iran", "saudi arabia",
            "united states", "uk", "germany", "japan", "australia", "israel",
        ]
        for country in country_patterns:
            if country in query_lower:
                countries.append(country.title())

        region_patterns = [
            "middle east", "south asia", "east asia", "europe", "africa",
            "indo-pacific", "asia pacific", "central asia", "southeast asia",
        ]
        for region in region_patterns:
            if region in query_lower:
                regions.append(region.title())

        # Extract simulation variables for what-if queries
        simulation_vars = {}
        if is_what_if:
            # Pattern: "X rises/falls by Y%"
            patterns = [
                r"(\w+)\s+(?:rises?|increases?|goes up)\s+(?:by\s+)?(\d+)%?",
                r"(\w+)\s+(?:falls?|decreases?|drops?)\s+(?:by\s+)?(\d+)%?",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                for var, value in matches:
                    simulation_vars[var] = {"change": float(value), "direction": "up" if "rise" in pattern else "down"}

        return QueryContext(
            raw_query=query,
            normalized_query=query.strip(),
            primary_domain=primary,
            secondary_domains=secondary[:3],
            domain_confidence=domain_confidence,
            countries=countries,
            regions=regions,
            is_what_if=is_what_if,
            is_forecast=is_forecast,
            is_comparison=is_comparison,
            is_historical=is_historical,
            simulation_variables=simulation_vars,
        )

    async def _enrich_context(
        self,
        context: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Enrich context with real data from all available sources.

        Fetches data from:
        - Runtime intelligence engine (global/geopolitical data)
        - Data store (domestic/civic data)
        - News feeds
        - Risk indices
        """
        enriched = dict(context)
        query_lower = query.lower()

        try:
            # 1. Import data sources
            from app.services.runtime_intelligence import runtime_engine
            from app.data.store import store

            # 2. Get global overview (always useful)
            try:
                global_overview = runtime_engine.get_global_overview()
                if global_overview:
                    enriched["global_overview"] = global_overview
                    enriched["systemic_stress"] = global_overview.get("systemic_stress", 0)
                    enriched["total_signals"] = global_overview.get("total_signals", 0)
                    self.logger.debug("Fetched global overview data")
            except Exception as e:
                self.logger.warning(f"Could not fetch global overview: {e}")

            # 3. Get country data if query mentions countries
            try:
                countries = runtime_engine.get_enriched_countries()
                if countries:
                    # Find relevant countries based on query
                    relevant_countries = []
                    for country in countries:
                        if country["name"].lower() in query_lower:
                            relevant_countries.append(country)
                            # Also get detailed analysis
                            analysis = runtime_engine.get_country_analysis(country["id"])
                            if analysis:
                                enriched[f"country_{country['id']}"] = analysis

                    enriched["countries"] = countries
                    enriched["relevant_countries"] = relevant_countries
                    self.logger.debug(f"Fetched {len(countries)} countries, {len(relevant_countries)} relevant")
            except Exception as e:
                self.logger.warning(f"Could not fetch country data: {e}")

            # 4. Get active signals
            try:
                signals = runtime_engine.get_all_signals()
                if signals:
                    enriched["active_signals"] = signals[:50]  # Top 50 signals
                    # Categorize signals
                    signal_categories = {}
                    for sig in signals:
                        cat = sig.get("category", "other")
                        if cat not in signal_categories:
                            signal_categories[cat] = []
                        signal_categories[cat].append(sig)
                    enriched["signals_by_category"] = signal_categories
                    self.logger.debug(f"Fetched {len(signals)} intelligence signals")
            except Exception as e:
                self.logger.warning(f"Could not fetch signals: {e}")

            # 5. Get domestic data if relevant
            if any(kw in query_lower for kw in ["india", "domestic", "booth", "constituency", "scheme"]):
                try:
                    enriched["domestic_stats"] = store.get_stats()
                    enriched["constituencies"] = store.get_constituencies()
                    enriched["schemes"] = store.get_schemes()
                    self.logger.debug("Fetched domestic data")
                except Exception as e:
                    self.logger.warning(f"Could not fetch domestic data: {e}")

            # 6. Get economic indicators
            try:
                enriched["economic_indicators"] = {
                    "source": "aggregated",
                    "gdp_growth_trend": "stable",
                    "inflation_outlook": "moderate",
                    "trade_balance": "deficit",
                    "currency_pressure": global_overview.get("systemic_stress", 50) / 100 if global_overview else 0.5,
                }
            except Exception as e:
                self.logger.warning(f"Could not build economic indicators: {e}")

            # 7. Get geopolitical risk indices
            try:
                if countries:
                    high_risk = [c for c in countries if c.get("risk_index", 0) > 70]
                    enriched["risk_indices"] = {
                        "high_risk_countries": [c["name"] for c in high_risk],
                        "average_global_risk": sum(c.get("risk_index", 0) for c in countries) / len(countries) if countries else 0,
                        "risk_hotspots": high_risk[:5],
                    }
            except Exception as e:
                self.logger.warning(f"Could not compute risk indices: {e}")

            # 8. Get corridors/trade routes if relevant
            if any(kw in query_lower for kw in ["trade", "corridor", "route", "shipping", "supply chain"]):
                try:
                    corridors = runtime_engine.get_corridors()
                    if corridors:
                        enriched["trade_corridors"] = corridors
                        self.logger.debug(f"Fetched {len(corridors)} trade corridors")
                except Exception as e:
                    self.logger.warning(f"Could not fetch corridors: {e}")

            # 9. News/feeds if relevant
            try:
                from app.services.feed_aggregator import feed_engine
                feeds = feed_engine.get_feeds()
                if feeds:
                    # Filter relevant news
                    relevant_news = [f for f in feeds if any(kw in f.get("text", "").lower() for kw in query_lower.split()[:5])]
                    enriched["news_feeds"] = relevant_news[:10] if relevant_news else feeds[:10]
                    self.logger.debug(f"Fetched {len(enriched['news_feeds'])} relevant news items")
            except Exception as e:
                self.logger.warning(f"Could not fetch news feeds: {e}")

            self.logger.info(f"Context enriched with {len(enriched)} data points")

        except Exception as e:
            self.logger.error(f"Context enrichment failed: {e}")

        return enriched

    def _select_agents(
        self,
        query_context: QueryContext,
        force_agents: Optional[List[str]] = None
    ) -> List[ExpertAgent]:
        """Select appropriate agents based on query analysis."""
        if force_agents:
            return [self._agents[a] for a in force_agents if a in self._agents]

        selected = []

        # Always include risk assessment
        selected.append(self._agents["risk"])

        # Domain-specific agents
        domain_agent_map = {
            QueryDomain.ECONOMIC: ["economic"],
            QueryDomain.GEOPOLITICAL: ["geopolitical"],
            QueryDomain.SOCIAL: ["social"],
            QueryDomain.CLIMATE: ["climate"],
            QueryDomain.POLICY: ["policy"],
            QueryDomain.SIMULATION: ["simulation"],
        }

        # Add primary domain agent
        if query_context.primary_domain in domain_agent_map:
            for agent_key in domain_agent_map[query_context.primary_domain]:
                if agent_key in self._agents:
                    selected.append(self._agents[agent_key])

        # Add secondary domain agents
        for domain in query_context.secondary_domains[:2]:
            if domain in domain_agent_map:
                for agent_key in domain_agent_map[domain]:
                    if agent_key in self._agents and self._agents[agent_key] not in selected:
                        selected.append(self._agents[agent_key])

        # Add simulation agent for what-if queries
        if query_context.is_what_if or query_context.is_forecast:
            if self._agents["simulation"] not in selected:
                selected.append(self._agents["simulation"])

        # Ensure minimum agents
        if len(selected) < 2:
            for agent in self._agents.values():
                if agent not in selected:
                    selected.append(agent)
                    if len(selected) >= 3:
                        break

        # Limit to max parallel
        return selected[:self.max_parallel_agents]

    async def _run_agents_parallel(
        self,
        agents: List[ExpertAgent],
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, AgentAssessment]:
        """Run multiple agents in parallel."""
        async def run_single_agent(agent: ExpertAgent) -> Tuple[str, AgentAssessment]:
            try:
                assessment = await agent.analyze(query, context)
                return (agent.agent_id, assessment)
            except Exception as e:
                self.logger.error(f"Agent {agent.name} failed: {e}")
                # Return minimal assessment on failure
                return (agent.agent_id, AgentAssessment(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    domain=agent.domain,
                    query_context=query,
                    executive_summary=f"Agent {agent.name} encountered an error",
                    overall_confidence=ConfidenceLevel.INSUFFICIENT,
                    confidence_score=0.0,
                ))

        # Run all agents concurrently
        results = await asyncio.gather(*[run_single_agent(a) for a in agents])

        return dict(results)

    def _should_conduct_debate(
        self,
        assessments: Dict[str, AgentAssessment]
    ) -> bool:
        """Determine if debate is needed based on divergence."""
        if not self.enable_debate:
            return False

        if len(assessments) < self.min_agents_for_debate:
            return False

        # Calculate divergence
        confidences = [a.confidence_score for a in assessments.values()]
        if not confidences:
            return False

        divergence = max(confidences) - min(confidences)

        return divergence >= self.debate_threshold

    def _generate_response(
        self,
        query_context: QueryContext,
        assessments: Dict[str, AgentAssessment],
        consensus: ConsensusResult,
        debate_summary: Optional[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> OrchestratedResponse:
        """Generate the final orchestrated response."""

        # Aggregate all data sources
        all_sources = []
        all_citations = []
        all_findings = []
        all_assumptions = []
        all_uncertainty = []

        for assessment in assessments.values():
            all_sources.extend(assessment.data_sources_used)
            all_findings.extend(assessment.key_findings)
            for claim in assessment.claims:
                all_assumptions.extend(claim.assumptions)
                if claim.probability < 0.5:
                    all_uncertainty.append(claim.statement)

        # Generate executive summary
        executive_summary = self._create_executive_summary(
            query_context, consensus, assessments
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            query_context, consensus, assessments
        )

        # Build causal chain
        causal_chain = self._build_causal_chain(query_context, assessments)

        # Generate timeline
        timeline = self._generate_timeline(query_context, assessments)

        # Generate map layers
        map_layers = self._generate_map_layers(query_context, assessments)

        return OrchestratedResponse(
            query_context=query_context,
            consensus=consensus,
            agent_assessments=assessments,
            debate_conducted=debate_summary is not None,
            debate_summary=debate_summary,
            executive_summary=executive_summary,
            key_findings=list(set(all_findings))[:10],
            recommendations=recommendations,
            overall_confidence=consensus.confidence_level,
            confidence_score=consensus.confidence_score,
            disagreements=[d.to_dict() for d in consensus.disagreements],
            minority_opinions=consensus.minority_opinions,
            data_sources_cited=list(set(all_sources)),
            citations=all_citations,
            uncertainty_factors=consensus.uncertainty_factors,
            key_assumptions=list(set(all_assumptions))[:5],
            scenarios=consensus.scenarios,
            map_layers=map_layers,
            affected_regions=query_context.regions + query_context.countries,
            timeline=timeline,
            causal_chain=causal_chain,
            agents_consulted=[a.agent_name for a in assessments.values()],
        )

    def _create_executive_summary(
        self,
        query_context: QueryContext,
        consensus: ConsensusResult,
        assessments: Dict[str, AgentAssessment]
    ) -> str:
        """Create executive summary of the analysis."""
        parts = []

        # Opening
        parts.append(f"INTELLIGENCE ASSESSMENT: {query_context.raw_query[:100]}")
        parts.append("")

        # Consensus view
        parts.append("CONSENSUS VIEW:")
        parts.append(consensus.consensus_view)
        parts.append("")

        # Confidence
        parts.append(f"CONFIDENCE: {consensus.confidence_level} ({consensus.confidence_score:.0%})")
        parts.append(f"AGREEMENT: {consensus.consensus_strength.value.replace('_', ' ').title()}")
        parts.append("")

        # Key domains
        domains = list(set(a.domain for a in assessments.values()))
        parts.append(f"DOMAINS ANALYZED: {', '.join(domains)}")
        parts.append(f"AGENTS CONSULTED: {len(assessments)}")

        # Disagreements (if any)
        if consensus.disagreements:
            parts.append("")
            parts.append("NOTE: Significant disagreements exist among analysts:")
            for d in consensus.disagreements[:2]:
                parts.append(f"  - {d.topic[:80]}")

        return "\n".join(parts)

    def _generate_recommendations(
        self,
        query_context: QueryContext,
        consensus: ConsensusResult,
        assessments: Dict[str, AgentAssessment]
    ) -> List[str]:
        """Generate strategic recommendations."""
        recommendations = []

        # Based on confidence level
        if consensus.confidence_score >= 0.7:
            recommendations.append(
                "High confidence assessment - consider for immediate strategic planning"
            )
        elif consensus.confidence_score >= 0.5:
            recommendations.append(
                "Moderate confidence - monitor situation and update assessment as new data emerges"
            )
        else:
            recommendations.append(
                "Low confidence assessment - recommend gathering additional intelligence before action"
            )

        # Based on domain
        domain_recs = {
            "economics": "Coordinate with economic policy stakeholders",
            "geopolitics": "Engage diplomatic and security apparatus",
            "social_dynamics": "Monitor public sentiment channels",
            "climate_environment": "Activate disaster preparedness protocols if applicable",
            "policy": "Review relevant policy frameworks",
        }

        for assessment in assessments.values():
            if assessment.domain in domain_recs:
                recommendations.append(domain_recs[assessment.domain])

        # What-if specific
        if query_context.is_what_if:
            recommendations.append("Run additional scenario simulations with varied parameters")

        return list(set(recommendations))[:5]

    def _build_causal_chain(
        self,
        query_context: QueryContext,
        assessments: Dict[str, AgentAssessment]
    ) -> List[str]:
        """Build cause-effect reasoning chain."""
        chain = []

        # Extract reasoning chains from all agents
        for assessment in assessments.values():
            for claim in assessment.claims:
                if claim.reasoning_chain:
                    chain.extend(claim.reasoning_chain[:2])

        # Deduplicate and limit
        seen = set()
        unique_chain = []
        for step in chain:
            if step not in seen:
                seen.add(step)
                unique_chain.append(step)

        return unique_chain[:10]

    def _generate_timeline(
        self,
        query_context: QueryContext,
        assessments: Dict[str, AgentAssessment]
    ) -> List[Dict[str, Any]]:
        """Generate projected timeline of events."""
        timeline = []

        # Short-term (days)
        timeline.append({
            "timeframe": "Immediate (0-7 days)",
            "events": ["Initial market/situation response", "Official statements expected"],
            "confidence": "High",
        })

        # Medium-term (weeks)
        timeline.append({
            "timeframe": "Short-term (1-4 weeks)",
            "events": ["Secondary effects emerge", "Policy responses formulated"],
            "confidence": "Moderate",
        })

        # Long-term (months)
        timeline.append({
            "timeframe": "Medium-term (1-6 months)",
            "events": ["Structural adjustments", "New equilibrium forms"],
            "confidence": "Low",
        })

        return timeline

    def _generate_map_layers(
        self,
        query_context: QueryContext,
        assessments: Dict[str, AgentAssessment]
    ) -> List[Dict[str, Any]]:
        """Generate comprehensive map visualization layers for the analysis."""
        layers = []

        # Get country data for visualization
        try:
            from app.services.runtime_intelligence import runtime_engine
            countries = runtime_engine.get_enriched_countries()

            # Build risk heatmap layer
            if countries:
                country_risks = {}
                for country in countries:
                    # Check if this country is mentioned in query
                    is_relevant = country["name"].lower() in query_context.raw_query.lower()
                    risk_score = country.get("risk_index", 50) / 100

                    if is_relevant or risk_score > 0.6:
                        country_risks[country["id"]] = {
                            "name": country["name"],
                            "risk": risk_score,
                            "signals": country.get("active_signals", 0),
                            "influence": country.get("influence_index", 50),
                            "pressure": country.get("pressure", "normal"),
                            "relevant": is_relevant,
                        }

                if country_risks:
                    layers.append({
                        "type": "risk_heatmap",
                        "name": "Risk Assessment Overlay",
                        "description": "Country risk levels based on analysis",
                        "data": country_risks,
                        "color_scale": "red_gradient",
                        "visible": True,
                    })

                # Highlighted countries layer (ones mentioned in query)
                relevant_country_ids = [cid for cid, data in country_risks.items() if data.get("relevant")]
                if relevant_country_ids:
                    layers.append({
                        "type": "highlight",
                        "name": "Focus Countries",
                        "description": "Countries directly mentioned in analysis",
                        "data": relevant_country_ids,
                        "color": "#3b82f6",
                        "border_width": 3,
                        "visible": True,
                    })

            # Signal density layer
            signals = runtime_engine.get_all_signals() if hasattr(runtime_engine, 'get_all_signals') else []
            if signals:
                signal_density = {}
                for sig in signals[:100]:
                    country_id = sig.get("country_id")
                    if country_id:
                        if country_id not in signal_density:
                            signal_density[country_id] = {"count": 0, "categories": {}}
                        signal_density[country_id]["count"] += 1
                        cat = sig.get("category", "other")
                        signal_density[country_id]["categories"][cat] = signal_density[country_id]["categories"].get(cat, 0) + 1

                if signal_density:
                    layers.append({
                        "type": "signal_density",
                        "name": "Intelligence Signal Density",
                        "description": "Active signals per region",
                        "data": signal_density,
                        "color_scale": "blue_gradient",
                        "visible": False,  # Hidden by default
                    })

            # Trade corridors layer if relevant
            if any(kw in query_context.raw_query.lower() for kw in ["trade", "corridor", "shipping", "supply"]):
                corridors = runtime_engine.get_corridors() if hasattr(runtime_engine, 'get_corridors') else []
                if corridors:
                    layers.append({
                        "type": "route",
                        "name": "Trade Corridors",
                        "description": "Strategic shipping and trade routes",
                        "data": corridors,
                        "color": "#10b981",
                        "line_width": 2,
                        "visible": True,
                    })

        except Exception as e:
            self.logger.warning(f"Could not generate map layers: {e}")

        # Countries layer from query context
        if query_context.countries:
            layers.append({
                "type": "choropleth",
                "name": "Query Focus",
                "description": "Countries mentioned in query",
                "data": {c.lower(): 0.8 for c in query_context.countries},
                "color_scale": "amber",
                "visible": True,
            })

        # Regions layer
        if query_context.regions:
            layers.append({
                "type": "region_highlight",
                "name": "Key Regions",
                "description": "Geographic regions of interest",
                "data": query_context.regions,
                "color": "#f59e0b",
                "visible": True,
            })

        # Agent confidence overlay
        if assessments:
            domain_confidence = {}
            for a in assessments.values():
                domain_confidence[a.domain] = {
                    "confidence": a.confidence_score,
                    "claims": len(a.claims),
                    "agent": a.agent_name,
                }
            layers.append({
                "type": "analysis_overlay",
                "name": "Analysis Confidence",
                "description": "Confidence levels by domain",
                "data": domain_confidence,
                "visible": False,
            })

        return layers

    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get list of available expert agents."""
        return [
            {
                "id": agent.agent_id,
                "name": agent.name,
                "domain": agent.domain,
                "description": agent.expertise_description[:200],
            }
            for agent in self._agents.values()
        ]

    def format_for_display(self, response: OrchestratedResponse) -> str:
        """Format response for terminal/display output."""
        lines = []

        lines.append("=" * 70)
        lines.append("JANGRAPH OS - SOVEREIGN INTELLIGENCE ASSESSMENT")
        lines.append("=" * 70)
        lines.append("")

        lines.append(response.executive_summary)
        lines.append("")

        lines.append("-" * 70)
        lines.append("KEY FINDINGS")
        lines.append("-" * 70)
        for finding in response.key_findings[:5]:
            lines.append(f"  * {finding}")
        lines.append("")

        if response.disagreements:
            lines.append("-" * 70)
            lines.append("AREAS OF DISAGREEMENT")
            lines.append("-" * 70)
            for d in response.disagreements[:3]:
                lines.append(f"  - {d.get('topic', 'Unknown')}: {d.get('severity', 'N/A')}")
            lines.append("")

        lines.append("-" * 70)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)
        for rec in response.recommendations:
            lines.append(f"  > {rec}")
        lines.append("")

        lines.append("-" * 70)
        lines.append("DATA SOURCES")
        lines.append("-" * 70)
        for src in response.data_sources_cited[:8]:
            lines.append(f"  - {src}")
        lines.append("")

        lines.append("-" * 70)
        lines.append("UNCERTAINTY FACTORS")
        lines.append("-" * 70)
        for uf in response.uncertainty_factors[:5]:
            lines.append(f"  ! {uf}")
        lines.append("")

        lines.append("=" * 70)
        lines.append(f"Generated: {response.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Agents: {', '.join(response.agents_consulted)}")
        lines.append(f"Processing: {response.processing_time_ms:.0f}ms")
        lines.append("=" * 70)

        return "\n".join(lines)


# Global orchestrator instance
expert_orchestrator = ExpertAgentOrchestrator()


# Convenience function
async def run_expert_analysis(
    query: str,
    context: Optional[Dict[str, Any]] = None
) -> OrchestratedResponse:
    """
    Run expert analysis on a query.

    This is the main entry point for expert-level reasoning.
    """
    return await expert_orchestrator.process_query(query, context)
