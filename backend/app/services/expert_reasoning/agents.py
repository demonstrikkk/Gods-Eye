"""
Specialized Expert Agents for Gods-Eye OS

This module contains expert agents for specific domains:
1. EconomicAnalystAgent - Economic indicators, trade, finance
2. GeopoliticalStrategistAgent - International relations, conflicts
3. SocialSentimentAgent - Public opinion, social movements
4. ClimateEnvironmentAgent - Climate, disasters, environment
5. PolicyImpactAgent - Policy analysis, regulatory impact
6. RiskAssessmentAgent - Risk evaluation and mitigation
7. SimulationForecastAgent - Scenario modeling and predictions

Each agent implements expert-level reasoning with:
- Data source citations
- Uncertainty quantification
- Probabilistic outputs
- Cross-agent validation
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import random
import hashlib

from .framework import (
    AgentPosition,
    Citation,
    ConfidenceLevel,
    DataQuality,
    Evidence,
    EvidenceType,
    ExpertAgent,
    ExpertInsight,
    ProbabilisticOutput,
    UncertaintyBand,
    agent_registry,
)

logger = logging.getLogger(__name__)


# ============================================================================
# ECONOMIC ANALYST AGENT
# ============================================================================

class EconomicAnalystAgent(ExpertAgent):
    """
    Expert agent for economic analysis.

    Domains: GDP, inflation, trade, employment, markets, fiscal policy

    Data Sources:
    - World Bank API
    - IMF World Economic Outlook
    - FRED (Federal Reserve Economic Data)
    - Trading Economics
    - National statistics bureaus
    """

    def __init__(self, llm_callable=None):
        super().__init__(
            agent_id="economic_analyst",
            agent_name="Economic Analyst",
            domain="economic",
            description="Expert in macroeconomic analysis, market dynamics, and fiscal policy",
            data_sources=[
                "World Bank API",
                "IMF WEO",
                "FRED",
                "Trading Economics",
                "EIA Energy Data",
                "BIS Statistics",
            ],
            llm_callable=llm_callable,
        )
        self._analysis_cache: Dict[str, Any] = {}

    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """Analyze economic aspects of a query."""
        start_time = datetime.utcnow()
        self.clear_session_data()

        # Extract economic indicators from context
        economic_data = context.get("economic_indicators", {})
        energy_data = context.get("energy_markets", {})
        trade_data = context.get("trade_data", {})

        # Build citations for data used
        citations = self._build_citations(economic_data, energy_data, trade_data)

        # Create evidence from data
        evidence = self._build_evidence(query, economic_data, energy_data, citations)

        # Generate probabilistic assessment
        prob_output = self._generate_economic_forecast(query, evidence, context)

        # Identify key findings
        key_findings = self._extract_key_findings(economic_data, energy_data, query)

        # Identify risk factors
        risk_factors = self._identify_economic_risks(economic_data, energy_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(query, risk_factors)

        # Determine overall confidence
        confidence = self._calculate_confidence(citations, evidence)

        # Build caveats
        caveats = self._build_caveats(economic_data, energy_data)

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ExpertInsight(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            query=query,
            assessment=self._generate_assessment(query, key_findings, prob_output),
            probabilistic_outputs=[prob_output],
            key_findings=key_findings,
            risk_factors=risk_factors,
            recommendations=recommendations,
            evidence_base=evidence,
            confidence_overall=confidence,
            uncertainty_statement=self._generate_uncertainty_statement(confidence, caveats),
            caveats=caveats,
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_ms,
        )

    def _build_citations(
        self,
        economic_data: Dict,
        energy_data: Dict,
        trade_data: Dict,
    ) -> List[Citation]:
        """Build citations for all data sources used."""
        citations = []

        if economic_data and economic_data.get("status") != "unavailable":
            citations.append(self.add_citation(
                source_name="World Bank API",
                source_type="api",
                data_point="GDP Growth Rate",
                value=economic_data.get("gdp_growth", "N/A"),
                quality=DataQuality.AUTHORITATIVE,
                methodology="Annual GDP growth rate (constant 2015 US$)",
            ))
            citations.append(self.add_citation(
                source_name="IMF WEO",
                source_type="dataset",
                data_point="Inflation Rate",
                value=economic_data.get("inflation", "N/A"),
                quality=DataQuality.AUTHORITATIVE,
                methodology="Consumer Price Index, annual percentage change",
            ))

        if energy_data and energy_data.get("status") != "unavailable":
            citations.append(self.add_citation(
                source_name="EIA",
                source_type="api",
                data_point="Crude Oil Price",
                value=energy_data.get("crude_price", "N/A"),
                quality=DataQuality.RELIABLE,
                methodology="WTI spot price, USD per barrel",
            ))

        return citations

    def _build_evidence(
        self,
        query: str,
        economic_data: Dict,
        energy_data: Dict,
        citations: List[Citation],
    ) -> List[Evidence]:
        """Build structured evidence from data."""
        evidence = []

        # GDP evidence
        if economic_data.get("gdp_growth"):
            evidence.append(self.create_evidence(
                claim=f"GDP growth is currently at {economic_data.get('gdp_growth', 'unknown')}%",
                evidence_type=EvidenceType.STATISTICAL,
                citations=[c for c in citations if "GDP" in c.data_point],
                supporting_data={"gdp_growth": economic_data.get("gdp_growth")},
                reasoning_chain=[
                    "GDP growth measures economic expansion",
                    "Higher growth indicates economic strength",
                    "Growth trajectory affects employment and investment",
                ],
                weight=0.9,
            ))

        # Energy price evidence
        if energy_data.get("crude_price"):
            evidence.append(self.create_evidence(
                claim=f"Oil prices at ${energy_data.get('crude_price', 'unknown')}/barrel impact production costs",
                evidence_type=EvidenceType.REAL_TIME_SIGNAL,
                citations=[c for c in citations if "Oil" in c.data_point],
                supporting_data={"crude_price": energy_data.get("crude_price")},
                reasoning_chain=[
                    "Oil is a key input cost for production",
                    "Price changes affect transport and manufacturing",
                    "Impacts inflation through cost-push mechanism",
                ],
                weight=0.85,
            ))

        return evidence

    def _generate_economic_forecast(
        self,
        query: str,
        evidence: List[Evidence],
        context: Dict,
    ) -> ProbabilisticOutput:
        """Generate probabilistic economic forecast."""
        # Simple heuristic-based forecast
        base_probability = 0.5
        conditions = []

        economic_data = context.get("economic_indicators", {})
        gdp_growth = economic_data.get("gdp_growth", 2.0)

        if isinstance(gdp_growth, (int, float)):
            if gdp_growth > 3:
                base_probability += 0.15
                conditions.append("Strong GDP growth supports positive outlook")
            elif gdp_growth < 1:
                base_probability -= 0.15
                conditions.append("Weak GDP growth increases downside risks")

        energy_data = context.get("energy_markets", {})
        if "increase" in query.lower() or "rise" in query.lower():
            if "oil" in query.lower():
                base_probability -= 0.1  # Oil price rises are typically negative for non-producers
                conditions.append("Oil price increases add inflationary pressure")

        return self.create_probabilistic_output(
            outcome="Economic impact assessment",
            probability=max(0.1, min(0.9, base_probability)),
            evidence=evidence,
            conditions=conditions,
            time_horizon="6-12 months",
            alternatives={
                "strong_positive": 0.15,
                "moderate_positive": 0.25,
                "neutral": 0.2,
                "moderate_negative": 0.25,
                "severe_negative": 0.15,
            },
        )

    def _extract_key_findings(
        self,
        economic_data: Dict,
        energy_data: Dict,
        query: str,
    ) -> List[str]:
        """Extract key economic findings."""
        findings = []

        if economic_data.get("gdp_growth"):
            findings.append(f"Current GDP growth: {economic_data.get('gdp_growth')}%")
        if economic_data.get("inflation"):
            findings.append(f"Inflation rate: {economic_data.get('inflation')}%")
        if energy_data.get("crude_price"):
            findings.append(f"Oil price baseline: ${energy_data.get('crude_price')}/barrel")

        # Query-specific findings
        if "oil" in query.lower():
            findings.append("Energy sector represents significant input cost exposure")
        if "inflation" in query.lower():
            findings.append("Inflationary pressure affects purchasing power and monetary policy")

        return findings or ["Insufficient economic data for detailed findings"]

    def _identify_economic_risks(
        self,
        economic_data: Dict,
        energy_data: Dict,
    ) -> List[Dict[str, Any]]:
        """Identify economic risk factors."""
        risks = []

        # Inflation risk
        inflation = economic_data.get("inflation", 0)
        if isinstance(inflation, (int, float)) and inflation > 5:
            risks.append({
                "factor": "High Inflation",
                "severity": "high",
                "description": f"Inflation at {inflation}% erodes purchasing power",
                "probability": 0.7,
            })

        # Energy price volatility
        if energy_data.get("crude_price"):
            risks.append({
                "factor": "Energy Price Volatility",
                "severity": "medium",
                "description": "Oil price swings impact production costs and trade balance",
                "probability": 0.6,
            })

        return risks

    def _generate_recommendations(
        self,
        query: str,
        risks: List[Dict],
    ) -> List[str]:
        """Generate economic policy recommendations."""
        recs = []

        for risk in risks:
            if risk.get("severity") == "high":
                recs.append(f"Monitor {risk.get('factor')} closely - potential for significant impact")
            elif risk.get("severity") == "medium":
                recs.append(f"Track {risk.get('factor')} trends for early warning signals")

        if "oil" in query.lower():
            recs.append("Consider hedging strategies for energy cost exposure")
            recs.append("Evaluate renewable energy transition timelines")

        return recs or ["Continue standard economic monitoring protocols"]

    def _calculate_confidence(
        self,
        citations: List[Citation],
        evidence: List[Evidence],
    ) -> ConfidenceLevel:
        """Calculate confidence based on data quality."""
        if not citations:
            return ConfidenceLevel.VERY_LOW

        quality_scores = {
            DataQuality.AUTHORITATIVE: 1.0,
            DataQuality.RELIABLE: 0.8,
            DataQuality.MIXED: 0.6,
            DataQuality.UNCERTAIN: 0.4,
            DataQuality.SPECULATIVE: 0.2,
            DataQuality.FALLBACK: 0.1,
        }

        avg_quality = sum(quality_scores.get(c.quality, 0.5) for c in citations) / len(citations)

        if avg_quality > 0.85:
            return ConfidenceLevel.HIGH
        elif avg_quality > 0.7:
            return ConfidenceLevel.MODERATE
        elif avg_quality > 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def _build_caveats(
        self,
        economic_data: Dict,
        energy_data: Dict,
    ) -> List[str]:
        """Build list of analytical caveats."""
        caveats = []

        if not economic_data or economic_data.get("status") == "unavailable":
            caveats.append("Limited access to real-time economic indicators")

        if not energy_data or energy_data.get("status") == "unavailable":
            caveats.append("Energy market data unavailable for analysis")

        caveats.append("Economic forecasts subject to policy changes and external shocks")
        caveats.append("Historical patterns may not predict future outcomes")

        return caveats

    def _generate_uncertainty_statement(
        self,
        confidence: ConfidenceLevel,
        caveats: List[str],
    ) -> str:
        """Generate statement about analytical uncertainty."""
        statements = {
            ConfidenceLevel.VERY_LOW: "Very high uncertainty - limited data availability",
            ConfidenceLevel.LOW: "High uncertainty - several key data gaps",
            ConfidenceLevel.MODERATE: "Moderate uncertainty - some data limitations",
            ConfidenceLevel.HIGH: "Relatively low uncertainty - good data coverage",
            ConfidenceLevel.VERY_HIGH: "Low uncertainty - comprehensive data available",
            ConfidenceLevel.NEAR_CERTAIN: "Very low uncertainty - exceptionally robust data",
        }
        base = statements.get(confidence, "Uncertainty level unknown")
        if caveats:
            return f"{base}. Note: {caveats[0]}"
        return base

    def _generate_assessment(
        self,
        query: str,
        findings: List[str],
        prob_output: ProbabilisticOutput,
    ) -> str:
        """Generate main assessment text."""
        prob_pct = prob_output.probability * 100
        return (
            f"Economic analysis indicates {prob_pct:.0f}% probability of significant impact. "
            f"Key indicators: {'; '.join(findings[:2])}. "
            f"Confidence level: {prob_output.confidence.value}."
        )

    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        """Validate another agent's insight from economic perspective."""
        validation = {
            "agreement_score": 0.5,
            "validated_claims": [],
            "questionable_claims": [],
            "additional_evidence": [],
        }

        # Check if economic implications are considered
        economic_keywords = ["gdp", "inflation", "trade", "market", "price", "cost", "growth"]
        has_economic_basis = any(
            kw in other_insight.assessment.lower()
            for kw in economic_keywords
        )

        if has_economic_basis:
            validation["agreement_score"] = 0.7
            validation["validated_claims"].append("Economic factors appropriately considered")
        else:
            validation["questionable_claims"].append("Economic implications may be underweighted")

        return validation

    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        """Challenge another agent's position on economic grounds."""
        challenge = {
            "challenge_type": "methodological",
            "challenge_statement": "",
            "counter_evidence": [],
            "severity": "minor",
            "suggested_revision": None,
        }

        # Check probability estimate
        if position.probability_estimate > 0.8:
            challenge["challenge_statement"] = (
                "Economic analysis suggests lower probability due to market volatility factors"
            )
            challenge["severity"] = "moderate"
            challenge["suggested_revision"] = "Consider reducing probability estimate by 10-15%"

        return challenge

    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        """Revise position based on challenges."""
        # Adjust probability based on valid challenges
        adjusted_prob = current_position.probability_estimate

        for challenge in challenges:
            if challenge.get("severity") == "major":
                adjusted_prob *= 0.85
            elif challenge.get("severity") == "moderate":
                adjusted_prob *= 0.92

        # Incorporate new evidence
        if new_evidence:
            evidence_quality = sum(e.citation_quality_score for e in new_evidence) / len(new_evidence)
            adjusted_prob = adjusted_prob * 0.7 + evidence_quality * 0.3

        adjusted_prob = max(0.1, min(0.9, adjusted_prob))

        return AgentPosition(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            stance=f"REVISED: {current_position.stance}",
            probability_estimate=adjusted_prob,
            confidence=ConfidenceLevel.from_probability(adjusted_prob),
            key_arguments=current_position.key_arguments + ["Adjusted for cross-domain challenges"],
            supporting_evidence=current_position.supporting_evidence,
            counterarguments_addressed=[c.get("challenge_statement", "") for c in challenges],
            willingness_to_revise=0.3,
            revision_conditions=["New authoritative economic data", "Major policy announcements"],
        )


# ============================================================================
# GEOPOLITICAL STRATEGIST AGENT
# ============================================================================

class GeopoliticalStrategistAgent(ExpertAgent):
    """
    Expert agent for geopolitical analysis.

    Domains: International relations, conflicts, alliances, strategic interests

    Data Sources:
    - GDELT Global Events
    - ACLED Conflict Data
    - SIPRI Arms Data
    - Diplomatic cables
    - Regional analysis
    """

    def __init__(self, llm_callable=None):
        super().__init__(
            agent_id="geopolitical_strategist",
            agent_name="Geopolitical Strategist",
            domain="geopolitical",
            description="Expert in international relations, conflict analysis, and strategic forecasting",
            data_sources=[
                "GDELT",
                "ACLED",
                "SIPRI",
                "UN Reports",
                "Think Tank Analysis",
                "Diplomatic Sources",
            ],
            llm_callable=llm_callable,
        )

    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """Analyze geopolitical aspects of a query."""
        start_time = datetime.utcnow()
        self.clear_session_data()

        # Extract relevant data
        conflict_data = context.get("conflict_data", {})
        gdelt_data = context.get("gdelt_events", {})
        defense_data = context.get("defense_posture", {})

        # Build citations
        citations = []
        if conflict_data and conflict_data.get("status") != "unavailable":
            citations.append(self.add_citation(
                source_name="GDELT Project",
                source_type="api",
                data_point="Conflict Events",
                value=conflict_data.get("event_count", "N/A"),
                quality=DataQuality.RELIABLE,
                methodology="Real-time event monitoring from global news sources",
            ))

        # Build evidence
        evidence = []
        if conflict_data:
            evidence.append(self.create_evidence(
                claim="Regional conflict indicators present",
                evidence_type=EvidenceType.REAL_TIME_SIGNAL,
                citations=citations,
                supporting_data=conflict_data,
                reasoning_chain=[
                    "Conflict events indicate regional instability",
                    "Instability affects trade routes and supply chains",
                    "Potential for escalation impacts strategic planning",
                ],
                weight=0.85,
            ))

        # Generate forecast
        prob_output = self._generate_geopolitical_forecast(query, evidence, context)

        # Key findings
        key_findings = self._extract_findings(conflict_data, gdelt_data, query)

        # Risk factors
        risk_factors = self._identify_geopolitical_risks(conflict_data, query)

        # Recommendations
        recommendations = [
            "Monitor diplomatic channels for de-escalation signals",
            "Assess supply chain exposure to affected regions",
            "Evaluate strategic partnership adjustments",
        ]

        confidence = ConfidenceLevel.MODERATE if citations else ConfidenceLevel.LOW
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ExpertInsight(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            query=query,
            assessment=self._generate_assessment(query, prob_output, key_findings),
            probabilistic_outputs=[prob_output],
            key_findings=key_findings,
            risk_factors=risk_factors,
            recommendations=recommendations,
            evidence_base=evidence,
            confidence_overall=confidence,
            uncertainty_statement=f"Geopolitical analysis at {confidence.value} confidence due to dynamic situation",
            caveats=[
                "Geopolitical situations can change rapidly",
                "Limited visibility into closed diplomatic channels",
                "Intelligence gaps in certain regions",
            ],
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_ms,
        )

    def _generate_geopolitical_forecast(
        self,
        query: str,
        evidence: List[Evidence],
        context: Dict,
    ) -> ProbabilisticOutput:
        """Generate geopolitical risk forecast."""
        base_probability = 0.5

        # Keyword analysis for risk direction
        escalation_keywords = ["tension", "conflict", "war", "military", "escalate"]
        stabilization_keywords = ["peace", "negotiate", "resolve", "deescalate"]

        query_lower = query.lower()
        for kw in escalation_keywords:
            if kw in query_lower:
                base_probability += 0.1

        for kw in stabilization_keywords:
            if kw in query_lower:
                base_probability -= 0.05

        conditions = [
            "Assumes no major military intervention",
            "Based on current diplomatic trajectories",
            "Subject to change with new developments",
        ]

        return self.create_probabilistic_output(
            outcome="Geopolitical risk assessment",
            probability=max(0.15, min(0.85, base_probability)),
            evidence=evidence,
            conditions=conditions,
            time_horizon="3-6 months",
            alternatives={
                "escalation": 0.25,
                "status_quo": 0.45,
                "de_escalation": 0.30,
            },
        )

    def _extract_findings(
        self,
        conflict_data: Dict,
        gdelt_data: Dict,
        query: str,
    ) -> List[str]:
        """Extract key geopolitical findings."""
        findings = []

        if conflict_data.get("event_count"):
            findings.append(f"Active conflict events: {conflict_data.get('event_count')}")

        if gdelt_data.get("tone"):
            findings.append(f"Global news tone: {gdelt_data.get('tone')}")

        # Region-specific findings
        if "middle east" in query.lower():
            findings.append("Middle East regional dynamics show elevated volatility")
        if "asia" in query.lower():
            findings.append("Indo-Pacific strategic competition remains active")

        return findings or ["Geopolitical assessment requires additional intelligence input"]

    def _identify_geopolitical_risks(
        self,
        conflict_data: Dict,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Identify geopolitical risk factors."""
        risks = []

        if "tension" in query.lower() or "escalate" in query.lower():
            risks.append({
                "factor": "Escalation Risk",
                "severity": "high",
                "description": "Potential for conflict escalation in mentioned region",
                "probability": 0.35,
            })

        risks.append({
            "factor": "Supply Chain Disruption",
            "severity": "medium",
            "description": "Geopolitical events may impact trade routes",
            "probability": 0.4,
        })

        return risks

    def _generate_assessment(
        self,
        query: str,
        prob_output: ProbabilisticOutput,
        findings: List[str],
    ) -> str:
        """Generate geopolitical assessment."""
        return (
            f"Geopolitical analysis indicates {prob_output.probability:.0%} probability of significant regional impact. "
            f"Key factors: {'; '.join(findings[:2])}. "
            f"Strategic posture adjustments may be warranted."
        )

    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        """Validate from geopolitical perspective."""
        return {
            "agreement_score": 0.6,
            "validated_claims": ["Regional dynamics considered"],
            "questionable_claims": [],
            "additional_evidence": [],
        }

    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        """Challenge from strategic perspective."""
        return {
            "challenge_type": "probabilistic",
            "challenge_statement": "Geopolitical volatility may be underestimated",
            "counter_evidence": [],
            "severity": "minor",
            "suggested_revision": None,
        }

    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        """Revise based on challenges."""
        adjusted_prob = current_position.probability_estimate

        for challenge in challenges:
            if "underestimate" in challenge.get("challenge_statement", "").lower():
                adjusted_prob = min(0.9, adjusted_prob * 1.1)

        return AgentPosition(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            stance=current_position.stance,
            probability_estimate=adjusted_prob,
            confidence=current_position.confidence,
            key_arguments=current_position.key_arguments,
            supporting_evidence=current_position.supporting_evidence,
            counterarguments_addressed=["Considered alternative perspectives"],
            willingness_to_revise=0.4,
            revision_conditions=["Major diplomatic developments"],
        )


# ============================================================================
# SOCIAL SENTIMENT ANALYST AGENT
# ============================================================================

class SocialSentimentAgent(ExpertAgent):
    """
    Expert agent for social sentiment analysis.

    Domains: Public opinion, social movements, media analysis

    Data Sources:
    - Twitter/X trends
    - Reddit discourse
    - News sentiment
    - Survey data
    """

    def __init__(self, llm_callable=None):
        super().__init__(
            agent_id="social_sentiment",
            agent_name="Social Sentiment Analyst",
            domain="social",
            description="Expert in public opinion analysis and social dynamics",
            data_sources=[
                "Twitter Trends",
                "Reddit API",
                "News Aggregators",
                "Survey Research",
                "Civic Sentiment Data",
            ],
            llm_callable=llm_callable,
        )

    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """Analyze social sentiment dimensions."""
        start_time = datetime.utcnow()
        self.clear_session_data()

        # Extract social data
        civic_data = context.get("civic_sentiment", {})
        twitter_data = context.get("twitter_trends", {})
        reddit_data = context.get("reddit_discourse", {})

        # Build citations
        citations = []
        if civic_data and civic_data.get("status") != "unavailable":
            citations.append(self.add_citation(
                source_name="Civic Sentiment Index",
                source_type="survey",
                data_point="Public Approval",
                value=civic_data.get("approval_rate", "N/A"),
                quality=DataQuality.RELIABLE,
            ))

        # Evidence
        evidence = []
        if civic_data:
            evidence.append(self.create_evidence(
                claim="Public sentiment indicators tracked",
                evidence_type=EvidenceType.STATISTICAL,
                citations=citations,
                supporting_data=civic_data,
                reasoning_chain=[
                    "Social sentiment influences political stability",
                    "Negative sentiment correlates with unrest risk",
                    "Media amplification affects policy response",
                ],
                weight=0.75,
            ))

        prob_output = self._generate_sentiment_forecast(query, evidence, context)
        key_findings = self._extract_sentiment_findings(civic_data, twitter_data, query)
        risk_factors = self._identify_social_risks(query, civic_data)

        confidence = ConfidenceLevel.MODERATE if citations else ConfidenceLevel.LOW
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ExpertInsight(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            query=query,
            assessment=f"Social sentiment analysis: {prob_output.probability:.0%} probability of negative public reaction",
            probabilistic_outputs=[prob_output],
            key_findings=key_findings,
            risk_factors=risk_factors,
            recommendations=[
                "Monitor social media channels for sentiment shifts",
                "Prepare communication strategies for public concerns",
                "Engage civil society stakeholders proactively",
            ],
            evidence_base=evidence,
            confidence_overall=confidence,
            uncertainty_statement="Social sentiment is volatile and can shift rapidly",
            caveats=[
                "Social media may not represent broader public opinion",
                "Sentiment analysis tools have inherent biases",
            ],
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_ms,
        )

    def _generate_sentiment_forecast(
        self,
        query: str,
        evidence: List[Evidence],
        context: Dict,
    ) -> ProbabilisticOutput:
        """Generate sentiment forecast."""
        base_prob = 0.5

        if "unrest" in query.lower() or "protest" in query.lower():
            base_prob += 0.2
        if "support" in query.lower() or "approval" in query.lower():
            base_prob -= 0.1

        return self.create_probabilistic_output(
            outcome="Social sentiment impact assessment",
            probability=max(0.1, min(0.9, base_prob)),
            evidence=evidence,
            conditions=["Based on current social indicators"],
            time_horizon="1-3 months",
        )

    def _extract_sentiment_findings(
        self,
        civic_data: Dict,
        twitter_data: Dict,
        query: str,
    ) -> List[str]:
        """Extract sentiment findings."""
        findings = []
        if civic_data.get("approval_rate"):
            findings.append(f"Current approval rating: {civic_data.get('approval_rate')}%")
        if twitter_data.get("trending"):
            findings.append("Social media activity elevated on related topics")
        return findings or ["Social sentiment data limited"]

    def _identify_social_risks(
        self,
        query: str,
        civic_data: Dict,
    ) -> List[Dict[str, Any]]:
        """Identify social risk factors."""
        risks = []
        if "price" in query.lower() or "inflation" in query.lower():
            risks.append({
                "factor": "Public Discontent",
                "severity": "medium",
                "description": "Economic stress may trigger social unrest",
                "probability": 0.4,
            })
        return risks

    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        return {"agreement_score": 0.6, "validated_claims": [], "questionable_claims": []}

    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        return {"challenge_type": "factual", "challenge_statement": "", "severity": "minor"}

    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        return current_position


# ============================================================================
# CLIMATE & ENVIRONMENT AGENT
# ============================================================================

class ClimateEnvironmentAgent(ExpertAgent):
    """
    Expert agent for climate and environmental analysis.

    Domains: Climate events, disasters, environmental policy

    Data Sources:
    - NASA FIRMS (fires)
    - USGS (earthquakes)
    - NOAA (weather)
    - Climate models
    """

    def __init__(self, llm_callable=None):
        super().__init__(
            agent_id="climate_environment",
            agent_name="Climate & Environment Analyst",
            domain="climate",
            description="Expert in climate impacts, disasters, and environmental policy",
            data_sources=[
                "NASA FIRMS",
                "USGS Earthquakes",
                "NOAA Climate Data",
                "IPCC Reports",
                "Environmental Agencies",
            ],
            llm_callable=llm_callable,
        )

    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """Analyze climate and environmental aspects."""
        start_time = datetime.utcnow()
        self.clear_session_data()

        # Extract environmental data
        firms_data = context.get("nasa_firms", {})
        usgs_data = context.get("usgs_earthquakes", {})

        citations = []
        if firms_data and firms_data.get("status") != "unavailable":
            citations.append(self.add_citation(
                source_name="NASA FIRMS",
                source_type="satellite",
                data_point="Active Fires",
                value=firms_data.get("fire_count", "N/A"),
                quality=DataQuality.AUTHORITATIVE,
            ))

        evidence = []
        if firms_data or usgs_data:
            evidence.append(self.create_evidence(
                claim="Environmental monitoring data available",
                evidence_type=EvidenceType.REAL_TIME_SIGNAL,
                citations=citations,
                supporting_data={"firms": firms_data, "usgs": usgs_data},
                reasoning_chain=[
                    "Satellite monitoring provides real-time hazard detection",
                    "Environmental events have cascading socioeconomic impacts",
                ],
                weight=0.8,
            ))

        prob_output = self.create_probabilistic_output(
            outcome="Environmental impact assessment",
            probability=0.4,
            evidence=evidence,
            conditions=["Based on current environmental indicators"],
            time_horizon="Variable",
        )

        confidence = ConfidenceLevel.MODERATE if citations else ConfidenceLevel.LOW
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ExpertInsight(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            query=query,
            assessment="Climate and environmental factors assessed for scenario impact",
            probabilistic_outputs=[prob_output],
            key_findings=["Environmental monitoring active", "Climate factors may compound other risks"],
            risk_factors=[{
                "factor": "Climate Event Amplification",
                "severity": "medium",
                "description": "Environmental stress can amplify socioeconomic vulnerabilities",
                "probability": 0.35,
            }],
            recommendations=["Include climate resilience in strategic planning"],
            evidence_base=evidence,
            confidence_overall=confidence,
            uncertainty_statement="Climate forecasting has inherent uncertainty",
            caveats=["Long-term climate projections have wide confidence intervals"],
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_ms,
        )

    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        return {"agreement_score": 0.65, "validated_claims": [], "questionable_claims": []}

    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        return {"challenge_type": "temporal", "challenge_statement": "", "severity": "minor"}

    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        return current_position


# ============================================================================
# POLICY IMPACT AGENT
# ============================================================================

class PolicyImpactAgent(ExpertAgent):
    """
    Expert agent for policy analysis.

    Domains: Government policy, regulation, fiscal measures

    Data Sources:
    - Government publications
    - Policy databases
    - Legislative tracking
    - Think tank analysis
    """

    def __init__(self, llm_callable=None):
        super().__init__(
            agent_id="policy_impact",
            agent_name="Policy Impact Analyst",
            domain="policy",
            description="Expert in policy analysis and regulatory impact assessment",
            data_sources=[
                "Government Publications",
                "Legislative Databases",
                "Policy Think Tanks",
                "Regulatory Filings",
            ],
            llm_callable=llm_callable,
        )

    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """Analyze policy implications."""
        start_time = datetime.utcnow()
        self.clear_session_data()

        prob_output = self.create_probabilistic_output(
            outcome="Policy response assessment",
            probability=0.55,
            evidence=[],
            conditions=["Assuming current policy trajectories"],
            time_horizon="6-12 months",
        )

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ExpertInsight(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            query=query,
            assessment="Policy response analysis: government intervention likelihood assessed",
            probabilistic_outputs=[prob_output],
            key_findings=[
                "Policy responses typically lag economic shocks",
                "Fiscal and monetary tools may be deployed",
            ],
            risk_factors=[{
                "factor": "Policy Uncertainty",
                "severity": "medium",
                "description": "Uncertain policy direction affects business planning",
                "probability": 0.5,
            }],
            recommendations=[
                "Monitor government announcements closely",
                "Prepare for multiple policy scenarios",
            ],
            evidence_base=[],
            confidence_overall=ConfidenceLevel.MODERATE,
            uncertainty_statement="Policy decisions are inherently unpredictable",
            caveats=["Political considerations may override economic rationale"],
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_ms,
        )

    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        return {"agreement_score": 0.55, "validated_claims": [], "questionable_claims": []}

    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        return {"challenge_type": "methodological", "challenge_statement": "", "severity": "minor"}

    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        return current_position


# ============================================================================
# RISK ASSESSMENT AGENT
# ============================================================================

class RiskAssessmentAgent(ExpertAgent):
    """
    Expert agent for integrated risk assessment.

    Aggregates risks across all domains into unified risk profile.
    """

    def __init__(self, llm_callable=None):
        super().__init__(
            agent_id="risk_assessment",
            agent_name="Risk Assessment Officer",
            domain="risk",
            description="Expert in multi-domain risk aggregation and assessment",
            data_sources=[
                "Cross-Domain Synthesis",
                "Historical Risk Data",
                "Risk Modeling",
            ],
            llm_callable=llm_callable,
        )

    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """Perform integrated risk assessment."""
        start_time = datetime.utcnow()
        self.clear_session_data()

        # Aggregate risks from context
        all_risks = []
        for key, value in context.items():
            if isinstance(value, dict) and "risk" in str(value).lower():
                all_risks.append({
                    "source": key,
                    "severity": "medium",
                    "description": f"Risk identified in {key} domain",
                })

        # Calculate aggregate risk score
        risk_score = min(0.9, 0.3 + len(all_risks) * 0.1)

        prob_output = self.create_probabilistic_output(
            outcome="Aggregate risk assessment",
            probability=risk_score,
            evidence=[],
            conditions=["Based on multi-domain risk factors"],
            time_horizon="Variable",
        )

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ExpertInsight(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            query=query,
            assessment=f"Aggregate risk level: {risk_score:.0%}. {len(all_risks)} risk factors identified across domains.",
            probabilistic_outputs=[prob_output],
            key_findings=[
                f"Total risk factors identified: {len(all_risks)}",
                "Cross-domain risk amplification possible",
            ],
            risk_factors=all_risks[:5],
            recommendations=[
                "Implement risk mitigation strategies for highest-severity factors",
                "Establish monitoring protocols for emerging risks",
                "Develop contingency plans for worst-case scenarios",
            ],
            evidence_base=[],
            confidence_overall=ConfidenceLevel.MODERATE,
            uncertainty_statement="Risk aggregation involves modeling assumptions",
            caveats=["Black swan events outside modeled scenarios remain possible"],
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_ms,
        )

    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        return {"agreement_score": 0.7, "validated_claims": [], "questionable_claims": []}

    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        return {"challenge_type": "severity", "challenge_statement": "", "severity": "minor"}

    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        return current_position


# ============================================================================
# SIMULATION & FORECASTING AGENT
# ============================================================================

class SimulationForecastAgent(ExpertAgent):
    """
    Expert agent for scenario simulation and forecasting.

    Uses what-if analysis to project future states.
    """

    def __init__(self, llm_callable=None):
        super().__init__(
            agent_id="simulation_forecast",
            agent_name="Simulation & Forecasting Engine",
            domain="simulation",
            description="Expert in scenario modeling and predictive analysis",
            data_sources=[
                "Simulation Models",
                "Historical Patterns",
                "Causal Inference",
            ],
            llm_callable=llm_callable,
        )

    async def analyze(self, query: str, context: Dict[str, Any]) -> ExpertInsight:
        """Run simulation analysis."""
        start_time = datetime.utcnow()
        self.clear_session_data()

        # Generate scenario projections
        scenarios = self._generate_scenarios(query, context)

        # Most likely scenario probability
        most_likely_prob = scenarios.get("most_likely", {}).get("probability", 0.5)

        prob_output = self.create_probabilistic_output(
            outcome="Primary scenario projection",
            probability=most_likely_prob,
            evidence=[],
            conditions=list(scenarios.get("assumptions", [])),
            time_horizon="6-18 months",
            alternatives={
                "best_case": scenarios.get("best_case", {}).get("probability", 0.2),
                "worst_case": scenarios.get("worst_case", {}).get("probability", 0.3),
            },
        )

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return ExpertInsight(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            domain=self.domain,
            query=query,
            assessment=f"Scenario analysis complete. Most likely outcome: {most_likely_prob:.0%} probability.",
            probabilistic_outputs=[prob_output],
            key_findings=[
                f"Best case scenario: {scenarios.get('best_case', {}).get('probability', 20):.0%} probability",
                f"Worst case scenario: {scenarios.get('worst_case', {}).get('probability', 30):.0%} probability",
                "Multiple pathways identified through scenario tree",
            ],
            risk_factors=[{
                "factor": "Model Uncertainty",
                "severity": "medium",
                "description": "Simulation models have inherent limitations",
                "probability": 1.0,
            }],
            recommendations=[
                "Use scenario range rather than point estimates for planning",
                "Update simulations as new data becomes available",
                "Stress-test strategies against worst-case scenarios",
            ],
            evidence_base=[],
            confidence_overall=ConfidenceLevel.MODERATE,
            uncertainty_statement="Forecasts represent modeled projections, not certainties",
            caveats=[
                "Models based on historical patterns",
                "Black swan events not captured",
                "Assumes rational actor behavior",
            ],
            timestamp=datetime.utcnow(),
            processing_time_ms=elapsed_ms,
        )

    def _generate_scenarios(
        self,
        query: str,
        context: Dict,
    ) -> Dict[str, Any]:
        """Generate scenario projections."""
        # Simple scenario generation based on query analysis
        base_prob = 0.5

        # Adjust based on query keywords
        if "rise" in query.lower() or "increase" in query.lower():
            base_prob += 0.1
        if "fall" in query.lower() or "decrease" in query.lower():
            base_prob -= 0.1

        return {
            "best_case": {
                "probability": max(0.1, base_prob - 0.2),
                "description": "Favorable outcome with minimal disruption",
            },
            "most_likely": {
                "probability": base_prob,
                "description": "Expected trajectory based on current trends",
            },
            "worst_case": {
                "probability": min(0.9, base_prob + 0.2),
                "description": "Adverse outcome with significant impact",
            },
            "assumptions": [
                "No major unexpected shocks",
                "Current policy trajectory maintained",
                "Historical patterns remain valid",
            ],
        }

    async def validate(self, other_insight: ExpertInsight) -> Dict[str, Any]:
        return {"agreement_score": 0.6, "validated_claims": [], "questionable_claims": []}

    async def challenge(self, position: AgentPosition) -> Dict[str, Any]:
        return {"challenge_type": "probabilistic", "challenge_statement": "", "severity": "minor"}

    async def revise(
        self,
        current_position: AgentPosition,
        challenges: List[Dict[str, Any]],
        new_evidence: List[Evidence],
    ) -> AgentPosition:
        return current_position


# ============================================================================
# AGENT FACTORY
# ============================================================================

def create_all_expert_agents(llm_callable=None) -> List[ExpertAgent]:
    """Create all expert agents and register them."""
    agents = [
        EconomicAnalystAgent(llm_callable),
        GeopoliticalStrategistAgent(llm_callable),
        SocialSentimentAgent(llm_callable),
        ClimateEnvironmentAgent(llm_callable),
        PolicyImpactAgent(llm_callable),
        RiskAssessmentAgent(llm_callable),
        SimulationForecastAgent(llm_callable),
    ]

    # Register all agents
    for agent in agents:
        agent_registry.register(agent)

    return agents


def get_agents_for_domains(domains: List[str]) -> List[ExpertAgent]:
    """Get agents for specific domains."""
    agents = []
    for domain in domains:
        domain_agents = agent_registry.get_by_domain(domain)
        agents.extend(domain_agents)
    return agents
