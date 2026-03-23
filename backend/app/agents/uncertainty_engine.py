"""
Uncertainty Quantification Engine
=================================

Advanced uncertainty quantification for expert-level reasoning:
- Probabilistic assessments
- Confidence intervals
- Bayesian updating
- Monte Carlo simulations
- Sensitivity analysis
- Epistemic vs aleatory uncertainty
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

logger = logging.getLogger(__name__)


class UncertaintyType(str, Enum):
    """Types of uncertainty in analysis."""

    EPISTEMIC = "epistemic"      # Reducible - due to lack of knowledge
    ALEATORY = "aleatory"        # Irreducible - inherent randomness
    MODEL = "model"              # From model assumptions
    MEASUREMENT = "measurement"  # From data collection
    LINGUISTIC = "linguistic"    # From ambiguous language


class DistributionType(str, Enum):
    """Probability distribution types."""

    NORMAL = "normal"
    LOGNORMAL = "lognormal"
    UNIFORM = "uniform"
    TRIANGULAR = "triangular"
    BETA = "beta"
    DISCRETE = "discrete"
    EMPIRICAL = "empirical"


@dataclass
class ConfidenceInterval:
    """
    Represents a confidence interval for a probabilistic estimate.
    """

    point_estimate: float = 0.0
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    confidence_level: float = 0.90  # 90% CI by default

    # Distribution info
    distribution: DistributionType = DistributionType.NORMAL
    distribution_params: Dict[str, float] = field(default_factory=dict)

    # Metadata
    methodology: str = ""
    sample_size: Optional[int] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def interval_width(self) -> float:
        """Width of the confidence interval."""
        return self.upper_bound - self.lower_bound

    @property
    def relative_uncertainty(self) -> float:
        """Relative uncertainty as fraction of point estimate."""
        if self.point_estimate == 0:
            return float('inf')
        return self.interval_width / (2 * abs(self.point_estimate))

    def contains(self, value: float) -> bool:
        """Check if a value falls within the interval."""
        return self.lower_bound <= value <= self.upper_bound

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_estimate": self.point_estimate,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "confidence_level": self.confidence_level,
            "interval_width": self.interval_width,
            "relative_uncertainty": self.relative_uncertainty if self.point_estimate != 0 else None,
            "distribution": self.distribution.value if isinstance(self.distribution, DistributionType) else self.distribution,
            "methodology": self.methodology,
        }


@dataclass
class ProbabilisticAssessment:
    """
    Complete probabilistic assessment of a claim or scenario.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    claim: str = ""

    # Core probability
    probability: float = 0.5
    confidence_interval: Optional[ConfidenceInterval] = None

    # Probability breakdown
    base_rate: float = 0.5            # Prior probability
    evidence_adjustment: float = 0.0  # Likelihood ratio adjustment
    final_probability: float = 0.5   # Posterior

    # Uncertainty decomposition
    epistemic_uncertainty: float = 0.0
    aleatory_uncertainty: float = 0.0
    model_uncertainty: float = 0.0
    total_uncertainty: float = 0.0

    # Scenarios
    best_case_probability: float = 0.0
    worst_case_probability: float = 0.0
    most_likely_probability: float = 0.0

    # Sensitivity
    key_assumptions: List[str] = field(default_factory=list)
    sensitivity_factors: Dict[str, float] = field(default_factory=dict)

    # Methodology
    methodology: str = ""
    data_points_used: int = 0
    historical_accuracy: Optional[float] = None

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def verbal_probability(self) -> str:
        """Convert probability to verbal expression (IC standard)."""
        p = self.probability
        if p >= 0.99:
            return "Almost certain"
        elif p >= 0.93:
            return "Highly likely"
        elif p >= 0.75:
            return "Likely"
        elif p >= 0.55:
            return "Probable"
        elif p >= 0.45:
            return "Roughly even odds"
        elif p >= 0.25:
            return "Unlikely"
        elif p >= 0.07:
            return "Highly unlikely"
        elif p >= 0.01:
            return "Remote chance"
        else:
            return "Almost no chance"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "claim": self.claim,
            "probability": self.probability,
            "verbal": self.verbal_probability(),
            "confidence_interval": self.confidence_interval.to_dict() if self.confidence_interval else None,
            "base_rate": self.base_rate,
            "evidence_adjustment": self.evidence_adjustment,
            "uncertainty": {
                "epistemic": self.epistemic_uncertainty,
                "aleatory": self.aleatory_uncertainty,
                "model": self.model_uncertainty,
                "total": self.total_uncertainty,
            },
            "scenarios": {
                "best_case": self.best_case_probability,
                "worst_case": self.worst_case_probability,
                "most_likely": self.most_likely_probability,
            },
            "sensitivity_factors": self.sensitivity_factors,
            "methodology": self.methodology,
            "data_points_used": self.data_points_used,
            "timestamp": self.timestamp.isoformat(),
        }


class BayesianUpdater:
    """
    Bayesian inference engine for updating beliefs based on evidence.
    """

    def __init__(self):
        self.logger = logging.getLogger("bayesian_updater")

    def update_probability(
        self,
        prior: float,
        likelihood_ratio: float,
        evidence_quality: float = 1.0
    ) -> float:
        """
        Update probability using Bayes' theorem.

        Args:
            prior: Prior probability P(H)
            likelihood_ratio: P(E|H) / P(E|~H)
            evidence_quality: Weight for evidence (0-1)

        Returns:
            Posterior probability P(H|E)
        """
        # Apply evidence quality adjustment
        adjusted_lr = 1 + (likelihood_ratio - 1) * evidence_quality

        # Bayes update
        prior_odds = prior / (1 - prior) if prior < 1 else float('inf')
        posterior_odds = prior_odds * adjusted_lr

        # Convert back to probability
        posterior = posterior_odds / (1 + posterior_odds)

        return max(0.01, min(0.99, posterior))  # Bound to avoid certainty

    def sequential_update(
        self,
        prior: float,
        evidence_list: List[Dict[str, float]]
    ) -> Tuple[float, List[float]]:
        """
        Sequentially update probability with multiple pieces of evidence.

        Args:
            prior: Initial prior probability
            evidence_list: List of {likelihood_ratio, quality} dicts

        Returns:
            Tuple of (final_posterior, list_of_intermediate_posteriors)
        """
        current = prior
        history = [prior]

        for evidence in evidence_list:
            lr = evidence.get("likelihood_ratio", 1.0)
            quality = evidence.get("quality", 1.0)
            current = self.update_probability(current, lr, quality)
            history.append(current)

        return current, history

    def estimate_likelihood_ratio(
        self,
        evidence_type: str,
        evidence_strength: str,
        source_reliability: float
    ) -> float:
        """
        Estimate likelihood ratio based on evidence characteristics.

        Args:
            evidence_type: Type of evidence (confirming, disconfirming, mixed)
            evidence_strength: Strength (strong, moderate, weak)
            source_reliability: Source reliability (0-1)

        Returns:
            Estimated likelihood ratio
        """
        # Base LR by type
        base_lr = {
            "confirming": {"strong": 5.0, "moderate": 2.0, "weak": 1.3},
            "disconfirming": {"strong": 0.2, "moderate": 0.5, "weak": 0.77},
            "mixed": {"strong": 1.2, "moderate": 1.0, "weak": 1.0},
        }

        lr = base_lr.get(evidence_type, {}).get(evidence_strength, 1.0)

        # Adjust for source reliability
        # Low reliability pulls LR toward 1
        lr = 1 + (lr - 1) * source_reliability

        return lr


class UncertaintyQuantifier:
    """
    Main uncertainty quantification engine.

    Provides:
    - Confidence interval estimation
    - Uncertainty decomposition
    - Monte Carlo simulation
    - Sensitivity analysis
    """

    def __init__(self):
        self.bayesian = BayesianUpdater()
        self.logger = logging.getLogger("uncertainty_quantifier")
        self._rng = np.random.default_rng()

    def quantify_claim_probability(
        self,
        claim: str,
        supporting_evidence: List[Dict[str, Any]],
        base_rate: float = 0.5,
        historical_accuracy: Optional[float] = None
    ) -> ProbabilisticAssessment:
        """
        Generate a complete probabilistic assessment for a claim.

        Args:
            claim: The claim being assessed
            supporting_evidence: List of evidence with quality and type info
            base_rate: Prior probability based on base rates
            historical_accuracy: Past accuracy of similar predictions

        Returns:
            ProbabilisticAssessment with full uncertainty quantification
        """
        # Start with base rate
        current_prob = base_rate

        # Evidence updates
        evidence_adjustments = []
        for evidence in supporting_evidence:
            lr = self.bayesian.estimate_likelihood_ratio(
                evidence.get("type", "mixed"),
                evidence.get("strength", "moderate"),
                evidence.get("reliability", 0.7),
            )
            quality = evidence.get("quality", 0.7)
            current_prob = self.bayesian.update_probability(current_prob, lr, quality)
            evidence_adjustments.append(lr)

        # Calculate uncertainty components
        epistemic = self._estimate_epistemic_uncertainty(supporting_evidence)
        aleatory = self._estimate_aleatory_uncertainty(claim)
        model = self._estimate_model_uncertainty(historical_accuracy)
        total = math.sqrt(epistemic**2 + aleatory**2 + model**2)

        # Build confidence interval
        ci = self._build_confidence_interval(
            current_prob,
            total,
            len(supporting_evidence)
        )

        # Scenario analysis
        best_case = min(current_prob + 2 * total, 0.99)
        worst_case = max(current_prob - 2 * total, 0.01)

        # Sensitivity analysis
        sensitivity = self._perform_sensitivity_analysis(
            base_rate, evidence_adjustments
        )

        assessment = ProbabilisticAssessment(
            claim=claim,
            probability=current_prob,
            confidence_interval=ci,
            base_rate=base_rate,
            evidence_adjustment=sum(evidence_adjustments) / max(len(evidence_adjustments), 1),
            final_probability=current_prob,
            epistemic_uncertainty=epistemic,
            aleatory_uncertainty=aleatory,
            model_uncertainty=model,
            total_uncertainty=total,
            best_case_probability=best_case,
            worst_case_probability=worst_case,
            most_likely_probability=current_prob,
            sensitivity_factors=sensitivity,
            methodology="Bayesian updating with evidence weighting",
            data_points_used=len(supporting_evidence),
            historical_accuracy=historical_accuracy,
        )

        return assessment

    def monte_carlo_simulation(
        self,
        variables: Dict[str, Dict[str, Any]],
        model_function: Callable[..., float],
        n_iterations: int = 10000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for uncertainty propagation.

        Args:
            variables: Dict of variable_name -> {distribution, params}
            model_function: Function that takes variable values and returns output
            n_iterations: Number of simulation iterations

        Returns:
            Dict with simulation results and statistics
        """
        results = []

        for _ in range(n_iterations):
            # Sample each variable
            sampled_values = {}
            for var_name, var_config in variables.items():
                sampled_values[var_name] = self._sample_distribution(
                    var_config.get("distribution", "normal"),
                    var_config.get("params", {})
                )

            # Evaluate model
            try:
                result = model_function(**sampled_values)
                results.append(result)
            except Exception as e:
                self.logger.warning(f"Simulation iteration failed: {e}")

        results = np.array(results)

        return {
            "mean": float(np.mean(results)),
            "median": float(np.median(results)),
            "std": float(np.std(results)),
            "percentiles": {
                "5th": float(np.percentile(results, 5)),
                "25th": float(np.percentile(results, 25)),
                "50th": float(np.percentile(results, 50)),
                "75th": float(np.percentile(results, 75)),
                "95th": float(np.percentile(results, 95)),
            },
            "confidence_interval_90": {
                "lower": float(np.percentile(results, 5)),
                "upper": float(np.percentile(results, 95)),
            },
            "n_iterations": n_iterations,
            "n_successful": len(results),
        }

    def aggregate_agent_uncertainties(
        self,
        agent_assessments: List[Dict[str, Any]],
        aggregation_method: str = "weighted_average"
    ) -> Dict[str, Any]:
        """
        Aggregate uncertainty estimates from multiple agents.

        Args:
            agent_assessments: List of assessments with probabilities and uncertainties
            aggregation_method: Method for aggregation

        Returns:
            Aggregated uncertainty estimate
        """
        if not agent_assessments:
            return {
                "aggregated_probability": 0.5,
                "aggregated_uncertainty": 1.0,
                "method": aggregation_method,
                "agreement_level": "none",
            }

        probabilities = [a.get("probability", 0.5) for a in agent_assessments]
        uncertainties = [a.get("uncertainty", 0.3) for a in agent_assessments]
        confidences = [a.get("confidence_score", 0.5) for a in agent_assessments]

        if aggregation_method == "weighted_average":
            # Weight by inverse uncertainty
            weights = [1 / max(u, 0.01) for u in uncertainties]
            weight_sum = sum(weights)
            normalized_weights = [w / weight_sum for w in weights]

            agg_prob = sum(p * w for p, w in zip(probabilities, normalized_weights))

            # Aggregated uncertainty (reduced due to multiple sources)
            variance_reduction = 1 / math.sqrt(len(agent_assessments))
            agg_uncertainty = np.mean(uncertainties) * variance_reduction

        elif aggregation_method == "median":
            agg_prob = float(np.median(probabilities))
            agg_uncertainty = float(np.median(uncertainties))

        elif aggregation_method == "extrema_bounded":
            # Bounded by most confident assessment
            min_uncertainty_idx = uncertainties.index(min(uncertainties))
            agg_prob = probabilities[min_uncertainty_idx]
            agg_uncertainty = min(uncertainties)

        else:
            # Simple average
            agg_prob = float(np.mean(probabilities))
            agg_uncertainty = float(np.mean(uncertainties))

        # Calculate agreement level
        prob_std = float(np.std(probabilities))
        if prob_std < 0.05:
            agreement = "strong"
        elif prob_std < 0.15:
            agreement = "moderate"
        elif prob_std < 0.25:
            agreement = "weak"
        else:
            agreement = "divergent"

        return {
            "aggregated_probability": agg_prob,
            "aggregated_uncertainty": agg_uncertainty,
            "method": aggregation_method,
            "agreement_level": agreement,
            "probability_std": prob_std,
            "n_agents": len(agent_assessments),
            "individual_probabilities": probabilities,
        }

    def _estimate_epistemic_uncertainty(
        self,
        evidence: List[Dict[str, Any]]
    ) -> float:
        """Estimate epistemic (knowledge) uncertainty."""
        if not evidence:
            return 0.4  # High uncertainty with no evidence

        # Lower uncertainty with more high-quality evidence
        qualities = [e.get("quality", 0.5) for e in evidence]
        avg_quality = sum(qualities) / len(qualities)

        # Diminishing returns on evidence quantity
        quantity_factor = 1 / math.sqrt(len(evidence))

        return (1 - avg_quality) * quantity_factor * 0.5

    def _estimate_aleatory_uncertainty(self, claim: str) -> float:
        """Estimate aleatory (inherent randomness) uncertainty."""
        # Keywords suggesting inherent uncertainty
        high_uncertainty_keywords = [
            "will", "future", "predict", "forecast", "might", "could",
            "election", "war", "crisis", "outbreak"
        ]
        moderate_keywords = [
            "trend", "likely", "expect", "probably"
        ]

        claim_lower = claim.lower()
        high_count = sum(1 for k in high_uncertainty_keywords if k in claim_lower)
        mod_count = sum(1 for k in moderate_keywords if k in claim_lower)

        base_aleatory = 0.1
        adjustment = high_count * 0.08 + mod_count * 0.04

        return min(base_aleatory + adjustment, 0.4)

    def _estimate_model_uncertainty(
        self,
        historical_accuracy: Optional[float]
    ) -> float:
        """Estimate model uncertainty based on past performance."""
        if historical_accuracy is None:
            return 0.15  # Default moderate model uncertainty

        # Lower accuracy = higher model uncertainty
        return (1 - historical_accuracy) * 0.3

    def _build_confidence_interval(
        self,
        point_estimate: float,
        total_uncertainty: float,
        sample_size: int
    ) -> ConfidenceInterval:
        """Build a confidence interval around a probability estimate."""
        # Adjust for sample size
        se_adjustment = 1 / math.sqrt(max(sample_size, 1))
        effective_uncertainty = total_uncertainty * (1 + se_adjustment)

        # 90% CI
        z_90 = 1.645
        margin = z_90 * effective_uncertainty

        return ConfidenceInterval(
            point_estimate=point_estimate,
            lower_bound=max(0.01, point_estimate - margin),
            upper_bound=min(0.99, point_estimate + margin),
            confidence_level=0.90,
            distribution=DistributionType.NORMAL,
            distribution_params={"mean": point_estimate, "std": effective_uncertainty},
            methodology="Normal approximation with uncertainty propagation",
            sample_size=sample_size,
        )

    def _perform_sensitivity_analysis(
        self,
        base_rate: float,
        likelihood_ratios: List[float]
    ) -> Dict[str, float]:
        """Perform sensitivity analysis on inputs."""
        sensitivities = {}

        # Base rate sensitivity
        current = base_rate
        for lr in likelihood_ratios:
            current = self.bayesian.update_probability(current, lr)

        # Perturb base rate
        perturbed_high = base_rate + 0.1
        current_high = perturbed_high
        for lr in likelihood_ratios:
            current_high = self.bayesian.update_probability(current_high, lr)

        sensitivities["base_rate"] = abs(current_high - current) / 0.1

        # Overall LR sensitivity
        if likelihood_ratios:
            avg_lr = sum(likelihood_ratios) / len(likelihood_ratios)
            sensitivities["evidence_strength"] = abs(avg_lr - 1.0)

        return sensitivities

    def _sample_distribution(
        self,
        dist_type: str,
        params: Dict[str, Any]
    ) -> float:
        """Sample from a probability distribution."""
        if dist_type == "normal":
            return float(self._rng.normal(
                params.get("mean", 0),
                params.get("std", 1)
            ))
        elif dist_type == "uniform":
            return float(self._rng.uniform(
                params.get("low", 0),
                params.get("high", 1)
            ))
        elif dist_type == "triangular":
            return float(self._rng.triangular(
                params.get("low", 0),
                params.get("mode", 0.5),
                params.get("high", 1)
            ))
        elif dist_type == "lognormal":
            return float(self._rng.lognormal(
                params.get("mean", 0),
                params.get("sigma", 1)
            ))
        else:
            return float(self._rng.random())


# Global instance
uncertainty_quantifier = UncertaintyQuantifier()
