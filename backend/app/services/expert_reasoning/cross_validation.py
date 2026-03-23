"""
Cross-Validation and Confidence Scoring Module

This module provides advanced mechanisms for:
1. Cross-agent validation of claims and assessments
2. Multi-dimensional confidence scoring
3. Evidence quality assessment
4. Disagreement analysis and resolution tracking
5. Calibration of probabilistic outputs

These mechanisms ensure expert outputs are rigorous and trustworthy.
"""

from __future__ import annotations

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .framework import (
    Citation,
    ConfidenceLevel,
    DataQuality,
    Evidence,
    EvidenceType,
    ExpertInsight,
    ProbabilisticOutput,
    AgentPosition,
)

logger = logging.getLogger(__name__)


class ValidationResult(Enum):
    """Result of cross-validation check."""
    VALIDATED = "validated"
    PARTIALLY_VALIDATED = "partially_validated"
    UNVALIDATED = "unvalidated"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class ConfidenceScore:
    """
    Multi-dimensional confidence score.

    Breaks down confidence into component factors for transparency.
    """
    overall: float                      # 0-1 composite score
    data_quality_score: float           # Based on citation quality
    evidence_coverage_score: float      # How well covered is the claim
    cross_validation_score: float       # Agreement across agents
    temporal_relevance_score: float     # How recent is the data
    source_diversity_score: float       # Variety of sources
    methodology_score: float            # Quality of analytical approach
    calibration_adjustment: float       # Historical accuracy adjustment

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": round(self.overall, 4),
            "components": {
                "data_quality": round(self.data_quality_score, 4),
                "evidence_coverage": round(self.evidence_coverage_score, 4),
                "cross_validation": round(self.cross_validation_score, 4),
                "temporal_relevance": round(self.temporal_relevance_score, 4),
                "source_diversity": round(self.source_diversity_score, 4),
                "methodology": round(self.methodology_score, 4),
            },
            "calibration_adjustment": round(self.calibration_adjustment, 4),
            "confidence_level": ConfidenceLevel.from_probability(self.overall).value,
        }


@dataclass
class ValidationReport:
    """
    Comprehensive validation report for an insight or claim.
    """
    claim_id: str
    claim_text: str
    result: ValidationResult
    confidence_score: ConfidenceScore
    validating_agents: List[str]
    contradicting_agents: List[str]
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    validation_notes: List[str]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "result": self.result.value,
            "confidence_score": self.confidence_score.to_dict(),
            "validating_agents": self.validating_agents,
            "contradicting_agents": self.contradicting_agents,
            "supporting_evidence_count": len(self.supporting_evidence),
            "contradicting_evidence_count": len(self.contradicting_evidence),
            "validation_notes": self.validation_notes,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


class CrossValidator:
    """
    Cross-validation engine for expert insights.

    Validates claims by:
    - Checking consistency across multiple agents
    - Assessing evidence quality and coverage
    - Identifying contradictions and gaps
    - Generating calibrated confidence scores
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Historical calibration data (would be persisted in production)
        self._calibration_history: List[Tuple[float, bool]] = []

    def validate_insight(
        self,
        insight: ExpertInsight,
        peer_insights: List[ExpertInsight],
    ) -> ValidationReport:
        """
        Validate an insight against peer insights.

        Args:
            insight: The insight to validate
            peer_insights: Insights from other agents on same query

        Returns:
            Comprehensive validation report
        """
        # Calculate component scores
        data_quality = self._calculate_data_quality_score(insight.evidence_base)
        evidence_coverage = self._calculate_evidence_coverage(insight)
        cross_validation = self._calculate_cross_validation_score(insight, peer_insights)
        temporal_relevance = self._calculate_temporal_relevance(insight.evidence_base)
        source_diversity = self._calculate_source_diversity(insight.evidence_base)
        methodology = self._calculate_methodology_score(insight)
        calibration = self._get_calibration_adjustment()

        # Composite score using weighted average
        weights = {
            "data_quality": 0.25,
            "evidence_coverage": 0.15,
            "cross_validation": 0.25,
            "temporal_relevance": 0.10,
            "source_diversity": 0.10,
            "methodology": 0.15,
        }

        overall = (
            data_quality * weights["data_quality"] +
            evidence_coverage * weights["evidence_coverage"] +
            cross_validation * weights["cross_validation"] +
            temporal_relevance * weights["temporal_relevance"] +
            source_diversity * weights["source_diversity"] +
            methodology * weights["methodology"]
        ) * calibration

        confidence_score = ConfidenceScore(
            overall=max(0.05, min(0.95, overall)),
            data_quality_score=data_quality,
            evidence_coverage_score=evidence_coverage,
            cross_validation_score=cross_validation,
            temporal_relevance_score=temporal_relevance,
            source_diversity_score=source_diversity,
            methodology_score=methodology,
            calibration_adjustment=calibration,
        )

        # Determine validation result
        result = self._determine_validation_result(
            cross_validation, confidence_score.overall
        )

        # Identify validating and contradicting agents
        validating, contradicting = self._categorize_peer_positions(
            insight, peer_insights
        )

        # Generate notes and recommendations
        notes = self._generate_validation_notes(
            insight, peer_insights, confidence_score
        )
        recommendations = self._generate_recommendations(
            result, confidence_score
        )

        return ValidationReport(
            claim_id=insight.agent_id + "_" + datetime.utcnow().strftime("%H%M%S"),
            claim_text=insight.assessment[:200],
            result=result,
            confidence_score=confidence_score,
            validating_agents=validating,
            contradicting_agents=contradicting,
            supporting_evidence=insight.evidence_base[:5],
            contradicting_evidence=[],  # Would be populated from peer insights
            validation_notes=notes,
            recommendations=recommendations,
        )

    def _calculate_data_quality_score(self, evidence: List[Evidence]) -> float:
        """Calculate score based on citation quality."""
        if not evidence:
            return 0.2

        quality_weights = {
            DataQuality.AUTHORITATIVE: 1.0,
            DataQuality.RELIABLE: 0.8,
            DataQuality.MIXED: 0.5,
            DataQuality.UNCERTAIN: 0.3,
            DataQuality.SPECULATIVE: 0.15,
            DataQuality.FALLBACK: 0.05,
        }

        scores = []
        for ev in evidence:
            for citation in ev.citations:
                scores.append(quality_weights.get(citation.quality, 0.5))

        if not scores:
            return 0.3

        return statistics.mean(scores)

    def _calculate_evidence_coverage(self, insight: ExpertInsight) -> float:
        """Calculate how well the assessment is covered by evidence."""
        # Simple heuristic: more evidence = better coverage
        evidence_count = len(insight.evidence_base)
        probabilistic_count = len(insight.probabilistic_outputs)

        # Score based on evidence quantity and quality
        base_score = min(1.0, evidence_count / 5)  # Cap at 5 evidence items

        # Bonus for probabilistic outputs
        prob_bonus = min(0.2, probabilistic_count * 0.1)

        # Bonus for reasoning chains
        chain_bonus = 0
        for ev in insight.evidence_base:
            if ev.reasoning_chain and len(ev.reasoning_chain) >= 2:
                chain_bonus += 0.05

        return min(1.0, base_score + prob_bonus + chain_bonus)

    def _calculate_cross_validation_score(
        self,
        insight: ExpertInsight,
        peer_insights: List[ExpertInsight],
    ) -> float:
        """Calculate agreement score across agents."""
        if not peer_insights:
            return 0.5  # Neutral when no peers

        # Extract probability estimates
        insight_prob = 0.5
        if insight.probabilistic_outputs:
            insight_prob = insight.probabilistic_outputs[0].probability

        peer_probs = []
        for peer in peer_insights:
            if peer.probabilistic_outputs:
                peer_probs.append(peer.probabilistic_outputs[0].probability)
            else:
                peer_probs.append(0.5)

        if not peer_probs:
            return 0.5

        # Calculate deviation from peers
        avg_peer_prob = statistics.mean(peer_probs)
        deviation = abs(insight_prob - avg_peer_prob)

        # Score inversely proportional to deviation
        # Max deviation is 1.0, so score = 1 - deviation gives good spread
        agreement_score = 1.0 - deviation

        # Adjust for number of agreeing peers
        agreeing_peers = sum(
            1 for p in peer_probs
            if abs(p - insight_prob) < 0.15
        )
        peer_agreement_bonus = min(0.2, agreeing_peers * 0.05)

        return min(1.0, agreement_score + peer_agreement_bonus)

    def _calculate_temporal_relevance(self, evidence: List[Evidence]) -> float:
        """Calculate score based on data freshness."""
        if not evidence:
            return 0.5

        freshness_scores = []
        for ev in evidence:
            for citation in ev.citations:
                # Score based on freshness (hours since update)
                freshness = citation.freshness_hours
                if freshness <= 1:
                    freshness_scores.append(1.0)
                elif freshness <= 6:
                    freshness_scores.append(0.9)
                elif freshness <= 24:
                    freshness_scores.append(0.75)
                elif freshness <= 72:
                    freshness_scores.append(0.5)
                else:
                    freshness_scores.append(0.3)

        if not freshness_scores:
            return 0.5

        return statistics.mean(freshness_scores)

    def _calculate_source_diversity(self, evidence: List[Evidence]) -> float:
        """Calculate score based on diversity of sources."""
        if not evidence:
            return 0.3

        # Collect unique sources
        sources = set()
        source_types = set()

        for ev in evidence:
            for citation in ev.citations:
                sources.add(citation.source_name)
                source_types.add(citation.source_type)

        # Score based on number of unique sources and types
        source_score = min(1.0, len(sources) / 5)  # Cap at 5 sources
        type_score = min(1.0, len(source_types) / 3)  # Cap at 3 types

        return (source_score * 0.6) + (type_score * 0.4)

    def _calculate_methodology_score(self, insight: ExpertInsight) -> float:
        """Calculate score based on analytical methodology."""
        score = 0.5  # Base score

        # Bonus for explicit caveats
        if insight.caveats:
            score += 0.1

        # Bonus for uncertainty statement
        if insight.uncertainty_statement:
            score += 0.1

        # Bonus for probabilistic outputs
        if insight.probabilistic_outputs:
            for po in insight.probabilistic_outputs:
                if po.alternative_outcomes:
                    score += 0.1
                    break

        # Bonus for evidence with reasoning chains
        has_reasoning = any(
            ev.reasoning_chain and len(ev.reasoning_chain) >= 2
            for ev in insight.evidence_base
        )
        if has_reasoning:
            score += 0.15

        return min(1.0, score)

    def _get_calibration_adjustment(self) -> float:
        """
        Get calibration adjustment based on historical accuracy.

        In production, this would use actual prediction accuracy data.
        """
        if not self._calibration_history:
            return 1.0  # No adjustment without history

        # Calculate historical accuracy
        correct = sum(1 for _, result in self._calibration_history if result)
        total = len(self._calibration_history)

        accuracy = correct / total if total > 0 else 0.5

        # Adjustment factor: slightly penalize overconfidence
        if accuracy < 0.5:
            return 0.85
        elif accuracy < 0.7:
            return 0.95
        else:
            return 1.0

    def _determine_validation_result(
        self,
        cross_validation_score: float,
        overall_score: float,
    ) -> ValidationResult:
        """Determine validation result based on scores."""
        if cross_validation_score >= 0.8 and overall_score >= 0.7:
            return ValidationResult.VALIDATED
        elif cross_validation_score >= 0.5 and overall_score >= 0.5:
            return ValidationResult.PARTIALLY_VALIDATED
        elif cross_validation_score < 0.3:
            return ValidationResult.CONTRADICTED
        elif overall_score < 0.3:
            return ValidationResult.INSUFFICIENT_DATA
        else:
            return ValidationResult.UNVALIDATED

    def _categorize_peer_positions(
        self,
        insight: ExpertInsight,
        peer_insights: List[ExpertInsight],
    ) -> Tuple[List[str], List[str]]:
        """Categorize peers as validating or contradicting."""
        validating = []
        contradicting = []

        insight_prob = 0.5
        if insight.probabilistic_outputs:
            insight_prob = insight.probabilistic_outputs[0].probability

        for peer in peer_insights:
            peer_prob = 0.5
            if peer.probabilistic_outputs:
                peer_prob = peer.probabilistic_outputs[0].probability

            diff = abs(insight_prob - peer_prob)

            if diff < 0.15:
                validating.append(peer.agent_name)
            elif diff > 0.3:
                contradicting.append(peer.agent_name)

        return validating, contradicting

    def _generate_validation_notes(
        self,
        insight: ExpertInsight,
        peer_insights: List[ExpertInsight],
        confidence: ConfidenceScore,
    ) -> List[str]:
        """Generate notes about validation process."""
        notes = []

        # Data quality note
        if confidence.data_quality_score < 0.5:
            notes.append("Data quality is below threshold - consider additional authoritative sources")
        elif confidence.data_quality_score > 0.8:
            notes.append("High-quality data sources support this assessment")

        # Cross-validation note
        if confidence.cross_validation_score < 0.5:
            notes.append("Significant disagreement with peer assessments detected")
        elif confidence.cross_validation_score > 0.8:
            notes.append("Strong consensus across expert agents")

        # Temporal note
        if confidence.temporal_relevance_score < 0.5:
            notes.append("Some data sources may be stale - verify with real-time feeds")

        # Source diversity note
        if confidence.source_diversity_score < 0.5:
            notes.append("Limited source diversity - recommend additional independent sources")

        # Overall assessment
        level = ConfidenceLevel.from_probability(confidence.overall)
        if level in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW]:
            notes.append(f"Overall confidence is {level.value} - treat conclusions with appropriate caution")

        return notes

    def _generate_recommendations(
        self,
        result: ValidationResult,
        confidence: ConfidenceScore,
    ) -> List[str]:
        """Generate actionable recommendations based on validation."""
        recommendations = []

        if result == ValidationResult.CONTRADICTED:
            recommendations.append("Investigate sources of disagreement before acting on this assessment")
            recommendations.append("Conduct additional research to resolve contradictions")

        if result == ValidationResult.INSUFFICIENT_DATA:
            recommendations.append("Gather additional data before relying on this assessment")
            recommendations.append("Consider alternative analytical approaches")

        if confidence.data_quality_score < 0.5:
            recommendations.append("Prioritize acquisition of authoritative data sources")

        if confidence.source_diversity_score < 0.5:
            recommendations.append("Diversify data sources to reduce bias risk")

        if confidence.temporal_relevance_score < 0.5:
            recommendations.append("Update analysis with more recent data")

        if result == ValidationResult.VALIDATED:
            recommendations.append("Assessment validated - suitable for decision support")

        return recommendations[:5]


class ConfidenceCalibrator:
    """
    Calibrates confidence scores based on historical accuracy.

    Tracks predictions and outcomes to improve calibration over time.
    """

    def __init__(self):
        self.predictions: List[Dict[str, Any]] = []
        self.outcomes: Dict[str, bool] = {}
        self.logger = logging.getLogger(__name__)

    def record_prediction(
        self,
        prediction_id: str,
        probability: float,
        confidence_level: ConfidenceLevel,
        timestamp: datetime,
    ) -> None:
        """Record a prediction for later calibration."""
        self.predictions.append({
            "id": prediction_id,
            "probability": probability,
            "confidence": confidence_level.value,
            "timestamp": timestamp.isoformat(),
            "outcome_recorded": False,
        })

    def record_outcome(self, prediction_id: str, occurred: bool) -> None:
        """Record whether a predicted outcome occurred."""
        self.outcomes[prediction_id] = occurred

        # Mark prediction as having outcome
        for pred in self.predictions:
            if pred["id"] == prediction_id:
                pred["outcome_recorded"] = True
                break

    def get_calibration_metrics(self) -> Dict[str, Any]:
        """
        Calculate calibration metrics.

        Returns Brier score and calibration curve data.
        """
        paired_predictions = []

        for pred in self.predictions:
            if pred["id"] in self.outcomes:
                paired_predictions.append({
                    "probability": pred["probability"],
                    "occurred": self.outcomes[pred["id"]],
                })

        if not paired_predictions:
            return {"status": "insufficient_data", "sample_size": 0}

        # Calculate Brier score
        brier_sum = sum(
            (p["probability"] - (1 if p["occurred"] else 0)) ** 2
            for p in paired_predictions
        )
        brier_score = brier_sum / len(paired_predictions)

        # Calculate calibration curve (binned)
        bins = self._calculate_calibration_bins(paired_predictions)

        return {
            "status": "calculated",
            "sample_size": len(paired_predictions),
            "brier_score": round(brier_score, 4),
            "calibration_bins": bins,
            "is_well_calibrated": brier_score < 0.25,
        }

    def _calculate_calibration_bins(
        self,
        predictions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Calculate calibration curve bins."""
        # Create 5 bins: 0-0.2, 0.2-0.4, 0.4-0.6, 0.6-0.8, 0.8-1.0
        bins = []
        bin_edges = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]

        for low, high in bin_edges:
            bin_preds = [
                p for p in predictions
                if low <= p["probability"] < high
            ]

            if bin_preds:
                avg_prob = statistics.mean(p["probability"] for p in bin_preds)
                actual_rate = sum(1 for p in bin_preds if p["occurred"]) / len(bin_preds)

                bins.append({
                    "range": f"{low:.1f}-{high:.1f}",
                    "sample_size": len(bin_preds),
                    "mean_predicted": round(avg_prob, 3),
                    "actual_rate": round(actual_rate, 3),
                    "calibration_error": round(abs(avg_prob - actual_rate), 3),
                })

        return bins

    def get_calibration_adjustment(self) -> float:
        """
        Get recommended adjustment factor based on calibration.

        If overconfident historically, returns < 1.0
        If underconfident, returns > 1.0
        """
        metrics = self.get_calibration_metrics()

        if metrics["status"] == "insufficient_data":
            return 1.0

        # Use Brier score to determine adjustment
        brier = metrics["brier_score"]

        if brier < 0.15:
            return 1.0  # Well calibrated
        elif brier < 0.25:
            return 0.95  # Slightly overconfident
        elif brier < 0.35:
            return 0.9
        else:
            return 0.85  # Significantly overconfident


# Singleton instances
cross_validator = CrossValidator()
confidence_calibrator = ConfidenceCalibrator()
