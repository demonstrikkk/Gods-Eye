"""
Gods-Eye OS — Counter-Questioning Agent
========================================

Adversarial testing agent that challenges expert analysis conclusions,
identifies assumptions, and generates critical counter-questions to ensure
robust intelligence assessment.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("counter_questioning")


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class QuestionType(str, Enum):
    ASSUMPTION_CHALLENGE = "assumption_challenge"
    EVIDENCE_QUALITY = "evidence_quality"
    ALTERNATIVE_EXPLANATION = "alternative_explanation"
    MISSING_PERSPECTIVE = "missing_perspective"
    BIAS_CHECK = "bias_check"
    TEMPORAL_VALIDITY = "temporal_validity"
    CAUSAL_REVERSAL = "causal_reversal"


class CriticalityLevel(str, Enum):
    FUNDAMENTAL = "fundamental"  # Challenges core conclusion
    SIGNIFICANT = "significant"  # Affects confidence level
    MODERATE = "moderate"  # Refines understanding
    MINOR = "minor"  # Clarification needed


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CounterQuestion:
    """A critical question that challenges an aspect of the analysis."""
    id: str
    question: str
    type: QuestionType
    criticality: CriticalityLevel
    targets: List[str]  # What this questions (e.g., "consensus_view", "evidence_1")
    rationale: str
    alternative_hypothesis: Optional[str] = None
    required_evidence: List[str] = field(default_factory=list)
    impact_if_true: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "type": self.type.value if isinstance(self.type, QuestionType) else self.type,
            "criticality": self.criticality.value if isinstance(self.criticality, CriticalityLevel) else self.criticality,
            "targets": self.targets,
            "rationale": self.rationale,
            "alternative_hypothesis": self.alternative_hypothesis,
            "required_evidence": self.required_evidence,
            "impact_if_true": self.impact_if_true,
        }


@dataclass
class AssumptionChallenge:
    """Challenge to an implicit or explicit assumption."""
    assumption: str
    why_questionable: str
    counter_scenario: str
    probability_if_false: float
    evidence_needed: List[str]


@dataclass
class CounterAnalysis:
    """Complete counter-questioning analysis."""
    original_conclusion: str
    counter_questions: List[CounterQuestion]
    assumption_challenges: List[AssumptionChallenge]
    evidence_gaps: List[str]
    alternative_interpretations: List[Dict[str, str]]
    confidence_adjustment: Dict[str, Any]
    red_team_summary: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_conclusion": self.original_conclusion,
            "counter_questions": [q.to_dict() for q in self.counter_questions],
            "assumption_challenges": [
                {
                    "assumption": a.assumption,
                    "why_questionable": a.why_questionable,
                    "counter_scenario": a.counter_scenario,
                    "probability_if_false": a.probability_if_false,
                    "evidence_needed": a.evidence_needed,
                }
                for a in self.assumption_challenges
            ],
            "evidence_gaps": self.evidence_gaps,
            "alternative_interpretations": self.alternative_interpretations,
            "confidence_adjustment": self.confidence_adjustment,
            "red_team_summary": self.red_team_summary,
            "timestamp": self.timestamp,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# COUNTER-QUESTIONING ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class CounterQuestioningAgent:
    """
    Adversarial agent that red-teams expert analysis by:
    - Challenging assumptions
    - Identifying evidence gaps
    - Proposing alternative explanations
    - Testing logical consistency
    - Checking for cognitive biases
    """

    def __init__(self):
        self.logger = logging.getLogger("counter_questioning")

    def analyze(
        self,
        expert_assessment: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> CounterAnalysis:
        """
        Perform counter-questioning analysis on expert assessment.

        Args:
            expert_assessment: The expert analysis to challenge
            context: Additional context (query, data sources, etc.)

        Returns:
            CounterAnalysis with critical questions and challenges
        """
        self.logger.info("Starting counter-questioning analysis")

        # Extract key elements
        consensus_view = expert_assessment.get("consensus_view", "")
        confidence = expert_assessment.get("confidence", {})
        key_findings = expert_assessment.get("key_findings", [])
        data_sources = expert_assessment.get("data_sources_cited", [])

        # Generate counter-questions
        counter_questions = self._generate_counter_questions(
            consensus_view, key_findings, confidence, data_sources
        )

        # Challenge assumptions
        assumption_challenges = self._identify_assumptions(
            consensus_view, key_findings, context or {}
        )

        # Identify evidence gaps
        evidence_gaps = self._identify_evidence_gaps(
            data_sources, key_findings, context or {}
        )

        # Generate alternative interpretations
        alternatives = self._generate_alternatives(
            consensus_view, key_findings, counter_questions
        )

        # Assess confidence adjustment
        confidence_adjustment = self._assess_confidence_adjustment(
            counter_questions, assumption_challenges, evidence_gaps
        )

        # Generate red team summary
        red_team_summary = self._generate_red_team_summary(
            counter_questions, assumption_challenges, confidence_adjustment
        )

        return CounterAnalysis(
            original_conclusion=consensus_view,
            counter_questions=counter_questions,
            assumption_challenges=assumption_challenges,
            evidence_gaps=evidence_gaps,
            alternative_interpretations=alternatives,
            confidence_adjustment=confidence_adjustment,
            red_team_summary=red_team_summary,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def _generate_counter_questions(
        self,
        consensus: str,
        findings: List[str],
        confidence: Dict,
        sources: List[str]
    ) -> List[CounterQuestion]:
        """Generate critical counter-questions."""
        questions = []
        q_id = 0

        # Challenge evidence quality
        if sources:
            q_id += 1
            questions.append(CounterQuestion(
                id=f"CQ-{q_id:03d}",
                question="Are the data sources sufficiently diverse and independent to avoid correlated errors?",
                type=QuestionType.EVIDENCE_QUALITY,
                criticality=CriticalityLevel.SIGNIFICANT,
                targets=["data_sources"],
                rationale="Multiple sources citing the same underlying data could create false confidence",
                required_evidence=["Source methodology verification", "Original data provenance"],
                impact_if_true="Confidence should be downgraded if sources are not truly independent",
            ))

        # Challenge temporal assumptions
        q_id += 1
        questions.append(CounterQuestion(
            id=f"CQ-{q_id:03d}",
            question="How rapidly could the situation change, invalidating this assessment?",
            type=QuestionType.TEMPORAL_VALIDITY,
            criticality=CriticalityLevel.SIGNIFICANT,
            targets=["consensus_view"],
            rationale="Geopolitical situations can shift quickly; static assessments may have short validity windows",
            required_evidence=["Historical volatility analysis", "Leading indicators"],
            impact_if_true="Assessment may need time-bounded validity statement",
        ))

        # Challenge causal direction
        if "because" in consensus.lower() or "due to" in consensus.lower():
            q_id += 1
            questions.append(CounterQuestion(
                id=f"CQ-{q_id:03d}",
                question="Could the causal relationship be reversed or bidirectional rather than unidirectional?",
                type=QuestionType.CAUSAL_REVERSAL,
                criticality=CriticalityLevel.FUNDAMENTAL,
                targets=["causal_reasoning"],
                rationale="Correlation does not imply causation; reverse causality is common in complex systems",
                alternative_hypothesis="The observed effect may be causing the presumed cause",
                required_evidence=["Time-series analysis", "Controlled comparison"],
                impact_if_true="Would fundamentally change the policy implications of this assessment",
            ))

        # Check for missing perspectives
        q_id += 1
        questions.append(CounterQuestion(
            id=f"CQ-{q_id:03d}",
            question="What perspectives from adversarial or neutral parties are missing from this analysis?",
            type=QuestionType.MISSING_PERSPECTIVE,
            criticality=CriticalityLevel.MODERATE,
            targets=["expert_agents", "evidence_base"],
            rationale="Analysis may reflect Western/allied bias if adversary viewpoints not considered",
            required_evidence=["Russian/Chinese media analysis", "Non-aligned nation perspectives"],
            impact_if_true="May reveal blind spots or misunderstandings of adversary intentions",
        ))

        # Challenge assumptions in findings
        for i, finding in enumerate(findings[:3]):
            if any(word in finding.lower() for word in ["likely", "probably", "suggests", "indicates"]):
                q_id += 1
                questions.append(CounterQuestion(
                    id=f"CQ-{q_id:03d}",
                    question=f"What alternative explanation could account for: '{finding[:80]}...'?",
                    type=QuestionType.ALTERNATIVE_EXPLANATION,
                    criticality=CriticalityLevel.MODERATE,
                    targets=[f"finding_{i+1}"],
                    rationale="Probabilistic language indicates uncertainty; alternative explanations should be explored",
                    alternative_hypothesis="Observed pattern may be coincidental or caused by unobserved factors",
                    impact_if_true="Reduces confidence in this specific finding",
                ))

        # Confidence calibration check
        confidence_score = confidence.get("score", 0.5)
        if confidence_score > 0.75:
            q_id += 1
            questions.append(CounterQuestion(
                id=f"CQ-{q_id:03d}",
                question="Is the high confidence level justified given the inherent uncertainty in geopolitical forecasting?",
                type=QuestionType.BIAS_CHECK,
                criticality=CriticalityLevel.SIGNIFICANT,
                targets=["confidence_assessment"],
                rationale="Overconfidence is a common cognitive bias; geopolitical events are inherently hard to predict",
                required_evidence=["Historical accuracy of similar predictions", "Epistemic uncertainty assessment"],
                impact_if_true="Confidence should potentially be reduced by 10-20%",
            ))

        return questions

    def _identify_assumptions(
        self,
        consensus: str,
        findings: List[str],
        context: Dict
    ) -> List[AssumptionChallenge]:
        """Identify and challenge implicit assumptions."""
        challenges = []

        # Common geopolitical assumptions to challenge
        common_assumptions = [
            {
                "assumption": "Actors behave rationally according to their stated interests",
                "why_questionable": "Leaders may have hidden agendas, misperceive threats, or act emotionally",
                "counter_scenario": "Key decision-maker acts irrationally due to domestic pressure or personal factors",
                "probability_if_false": 0.25,
                "evidence_needed": ["Psychological profile of leaders", "Internal political pressures"],
            },
            {
                "assumption": "Recent trends will continue into the near future",
                "why_questionable": "Non-linear tipping points and black swan events can disrupt trends suddenly",
                "counter_scenario": "Unexpected crisis or technological breakthrough changes the dynamic completely",
                "probability_if_false": 0.15,
                "evidence_needed": ["Leading indicators of trend reversal", "Fragility analysis"],
            },
            {
                "assumption": "Information from allied intelligence services is accurate",
                "why_questionable": "Allies may have political reasons to shade intelligence or may themselves be deceived",
                "counter_scenario": "Provided intelligence serves ally's agenda rather than objective truth",
                "probability_if_false": 0.20,
                "evidence_needed": ["Independent verification", "Motive analysis"],
            },
        ]

        # Convert to AssumptionChallenge objects
        for assumption_dict in common_assumptions:
            challenges.append(AssumptionChallenge(**assumption_dict))

        # Add context-specific assumptions
        if "economic" in consensus.lower() or any("economic" in f.lower() for f in findings):
            challenges.append(AssumptionChallenge(
                assumption="Economic indicators accurately reflect real economic health",
                why_questionable="Official statistics may be manipulated; informal economy may be large",
                counter_scenario="Real economic situation is significantly worse/better than official data suggests",
                probability_if_false=0.30,
                evidence_needed=["Independent economic surveys", "Satellite imagery analysis", "Power consumption data"],
            ))

        return challenges

    def _identify_evidence_gaps(
        self,
        sources: List[str],
        findings: List[str],
        context: Dict
    ) -> List[str]:
        """Identify critical evidence gaps."""
        gaps = []

        # Check for source diversity
        if len(set(sources)) < 3:
            gaps.append("Limited source diversity - fewer than 3 independent data sources")

        # Check for on-the-ground perspective
        has_human = any(word in " ".join(sources).lower() for word in ["interview", "survey", "field", "eyewitness"])
        if not has_human:
            gaps.append("No human intelligence or ground-truth validation - relying entirely on remote assessment")

        # Check for adversary perspective
        has_adversary = any(word in " ".join(sources).lower() for word in ["russian", "chinese", "iranian"])
        if not has_adversary:
            gaps.append("Missing adversary perspective - analysis may reflect allied bias")

        # Check for historical context
        has_historical = any(word in " ".join(sources).lower() for word in ["historical", "precedent", "past"])
        if not has_historical:
            gaps.append("Insufficient historical context - may be treating situation as unprecedented when it's not")

        # Check for quantitative data
        has_quantitative = any(word in " ".join(sources).lower() for word in ["data", "statistics", "measurement", "indicator"])
        if not has_quantitative:
            gaps.append("Lacks quantitative validation - purely qualitative assessment may miss objective indicators")

        return gaps

    def _generate_alternatives(
        self,
        consensus: str,
        findings: List[str],
        counter_questions: List[CounterQuestion]
    ) -> List[Dict[str, str]]:
        """Generate alternative interpretations."""
        alternatives = []

        # Generate alternatives based on counter-questions
        for cq in counter_questions:
            if cq.alternative_hypothesis:
                alternatives.append({
                    "interpretation": cq.alternative_hypothesis,
                    "rationale": cq.rationale,
                    "probability": "15-30%",
                    "implications": cq.impact_if_true,
                })

        # Add generic alternative scenarios
        alternatives.append({
            "interpretation": "Situation is fundamentally misunderstood due to deception operations",
            "rationale": "Adversaries may be deliberately creating false signals to mislead analysis",
            "probability": "5-15%",
            "implications": "Would require complete reassessment with focus on adversary deception capabilities",
        })

        alternatives.append({
            "interpretation": "Observed pattern is temporary noise rather than meaningful signal",
            "rationale": "Random fluctuations can appear as patterns; requires longer time series to validate",
            "probability": "20-35%",
            "implications": "Current assessment may be premature; recommend continued monitoring before action",
        })

        return alternatives

    def _assess_confidence_adjustment(
        self,
        counter_questions: List[CounterQuestion],
        assumption_challenges: List[AssumptionChallenge],
        evidence_gaps: List[str]
    ) -> Dict[str, Any]:
        """Assess whether confidence should be adjusted based on red-teaming."""
        # Count critical issues
        fundamental_questions = sum(1 for q in counter_questions if q.criticality == CriticalityLevel.FUNDAMENTAL)
        significant_questions = sum(1 for q in counter_questions if q.criticality == CriticalityLevel.SIGNIFICANT)
        risky_assumptions = sum(1 for a in assumption_challenges if a.probability_if_false > 0.2)
        critical_gaps = len(evidence_gaps)

        # Calculate adjustment
        adjustment_score = 0
        if fundamental_questions > 0:
            adjustment_score -= 0.15 * fundamental_questions
        if significant_questions > 1:
            adjustment_score -= 0.05 * (significant_questions - 1)
        if risky_assumptions > 1:
            adjustment_score -= 0.08 * (risky_assumptions - 1)
        if critical_gaps > 2:
            adjustment_score -= 0.05 * (critical_gaps - 2)

        # Cap adjustment
        adjustment_score = max(adjustment_score, -0.30)

        recommendation = "maintain" if adjustment_score > -0.05 else "reduce" if adjustment_score > -0.15 else "significantly reduce"

        return {
            "recommended_adjustment": adjustment_score,
            "recommendation": recommendation,
            "fundamental_challenges": fundamental_questions,
            "significant_challenges": significant_questions,
            "risky_assumptions": risky_assumptions,
            "critical_gaps": critical_gaps,
            "reasoning": self._generate_adjustment_reasoning(
                adjustment_score, fundamental_questions, significant_questions, risky_assumptions, critical_gaps
            ),
        }

    def _generate_adjustment_reasoning(
        self,
        score: float,
        fundamental: int,
        significant: int,
        risky_assumptions: int,
        gaps: int
    ) -> str:
        """Generate human-readable reasoning for confidence adjustment."""
        if score > -0.05:
            return "Red team analysis found no major concerns. Original confidence assessment appears well-calibrated."

        issues = []
        if fundamental > 0:
            issues.append(f"{fundamental} fundamental challenge(s) to core conclusions")
        if significant > 0:
            issues.append(f"{significant} significant question(s) about evidence or reasoning")
        if risky_assumptions > 0:
            issues.append(f"{risky_assumptions} questionable assumption(s) with >20% false probability")
        if gaps > 2:
            issues.append(f"{gaps} critical evidence gaps")

        return f"Red team identified: {'; '.join(issues)}. Recommend confidence reduction of {abs(score)*100:.0f} percentage points."

    def _generate_red_team_summary(
        self,
        counter_questions: List[CounterQuestion],
        assumption_challenges: List[AssumptionChallenge],
        confidence_adjustment: Dict[str, Any]
    ) -> str:
        """Generate executive summary of red team findings."""
        recommendation = confidence_adjustment.get("recommendation", "maintain")
        reasoning = confidence_adjustment.get("reasoning", "")

        summary = f"**Red Team Assessment**: {recommendation.upper()} confidence level\n\n"
        summary += f"{reasoning}\n\n"

        summary += f"**Key Challenges**:\n"
        for i, cq in enumerate(counter_questions[:3], 1):
            summary += f"{i}. [{cq.criticality.value.upper()}] {cq.question}\n"

        if assumption_challenges:
            summary += f"\n**Most Questionable Assumption**: {assumption_challenges[0].assumption}\n"
            summary += f"   → {assumption_challenges[0].why_questionable}\n"

        summary += f"\n**Bottom Line**: This assessment should be treated as {self._get_confidence_descriptor(recommendation)} "
        summary += "and validated with additional evidence before informing high-stakes decisions."

        return summary

    def _get_confidence_descriptor(self, recommendation: str) -> str:
        """Get human-readable confidence descriptor."""
        descriptors = {
            "maintain": "reasonably robust",
            "reduce": "tentative",
            "significantly reduce": "highly uncertain",
        }
        return descriptors.get(recommendation, "preliminary")


# Global instance
counter_questioning_agent = CounterQuestioningAgent()
