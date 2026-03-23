"""
Agent Debate Engine for JanGraph OS

This module implements a structured debate system where multiple expert agents:
1. Present their initial positions with supporting evidence
2. Challenge each other's claims and methodology
3. Respond to challenges with counter-arguments
4. Revise positions based on debate outcomes
5. Converge toward consensus or document disagreements

The debate process ensures:
- Rigorous examination of all claims
- Explicit uncertainty about contested points
- Clear documentation of minority views
- Higher quality final assessments
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import json

from .framework import (
    AgentPosition,
    ConfidenceLevel,
    DebateRound,
    DisagreementType,
    Evidence,
    ExpertAgent,
    ExpertInsight,
    agent_registry,
)

logger = logging.getLogger(__name__)


@dataclass
class Challenge:
    """A challenge issued by one agent to another."""
    challenger_id: str
    challenger_name: str
    target_id: str
    target_name: str
    challenge_type: DisagreementType
    claim_challenged: str
    challenge_statement: str
    counter_evidence: List[Evidence]
    severity: str  # "minor", "moderate", "major"
    suggested_revision: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "challenger_id": self.challenger_id,
            "challenger_name": self.challenger_name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "challenge_type": self.challenge_type.value,
            "claim_challenged": self.claim_challenged,
            "challenge_statement": self.challenge_statement,
            "counter_evidence": [e.to_dict() for e in self.counter_evidence],
            "severity": self.severity,
            "suggested_revision": self.suggested_revision,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ChallengeResponse:
    """A response to a challenge."""
    responder_id: str
    challenge: Challenge
    accepted: bool
    response_statement: str
    position_revised: bool
    new_position: Optional[str] = None
    additional_evidence: List[Evidence] = field(default_factory=list)
    concession_made: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "responder_id": self.responder_id,
            "challenge": self.challenge.to_dict(),
            "accepted": self.accepted,
            "response_statement": self.response_statement,
            "position_revised": self.position_revised,
            "new_position": self.new_position,
            "additional_evidence": [e.to_dict() for e in self.additional_evidence],
            "concession_made": self.concession_made,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DebateConfig:
    """Configuration for the debate process."""
    max_rounds: int = 3
    challenge_threshold: float = 0.15  # Min probability diff to trigger challenge
    convergence_threshold: float = 0.85  # Agreement level to end early
    timeout_per_round_seconds: float = 30.0
    require_evidence_for_challenges: bool = True
    allow_position_revision: bool = True
    min_agents_for_consensus: int = 2


class DebateEngine:
    """
    Orchestrates structured debates between expert agents.

    The debate process:
    1. Collect initial positions from all agents
    2. Identify disagreements and potential challenges
    3. Execute challenge rounds
    4. Process responses and position revisions
    5. Calculate convergence and document remaining disagreements
    """

    def __init__(self, config: Optional[DebateConfig] = None):
        self.config = config or DebateConfig()
        self.logger = logging.getLogger(__name__)

    async def conduct_debate(
        self,
        topic: str,
        agents: List[ExpertAgent],
        initial_insights: List[ExpertInsight],
        context: Dict[str, Any],
    ) -> Tuple[List[DebateRound], List[AgentPosition], float]:
        """
        Conduct a full debate between agents.

        Returns:
            - List of debate rounds
            - Final positions of all agents
            - Convergence score (0-1)
        """
        start_time = datetime.utcnow()
        self.logger.info(f"Starting debate on: {topic} with {len(agents)} agents")

        # Step 1: Form initial positions from insights
        positions = self._form_initial_positions(agents, initial_insights)

        if len(positions) < 2:
            self.logger.info("Fewer than 2 positions, skipping debate")
            return [], positions, 1.0

        debate_rounds: List[DebateRound] = []
        convergence = self._calculate_convergence(positions)

        # Step 2: Execute debate rounds
        for round_num in range(1, self.config.max_rounds + 1):
            self.logger.info(f"Debate round {round_num}, current convergence: {convergence:.3f}")

            # Early termination if consensus reached
            if convergence >= self.config.convergence_threshold:
                self.logger.info(f"Early consensus reached at round {round_num}")
                break

            # Execute one debate round
            round_result = await self._execute_round(
                round_num,
                topic,
                agents,
                positions,
                context,
            )

            debate_rounds.append(round_result)
            positions = self._apply_revisions(positions, round_result.position_revisions)
            convergence = self._calculate_convergence(positions)

        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        self.logger.info(f"Debate completed in {elapsed_ms:.1f}ms, final convergence: {convergence:.3f}")

        return debate_rounds, positions, convergence

    def _form_initial_positions(
        self,
        agents: List[ExpertAgent],
        insights: List[ExpertInsight],
    ) -> List[AgentPosition]:
        """Convert insights to formal debate positions."""
        positions = []

        for agent, insight in zip(agents, insights):
            # Extract main probability estimate from probabilistic outputs
            main_prob = 0.5
            if insight.probabilistic_outputs:
                main_prob = insight.probabilistic_outputs[0].probability

            # Determine willingness to revise based on confidence
            revision_willingness = {
                ConfidenceLevel.VERY_LOW: 0.9,
                ConfidenceLevel.LOW: 0.75,
                ConfidenceLevel.MODERATE: 0.5,
                ConfidenceLevel.HIGH: 0.3,
                ConfidenceLevel.VERY_HIGH: 0.15,
                ConfidenceLevel.NEAR_CERTAIN: 0.05,
            }.get(insight.confidence_overall, 0.5)

            position = AgentPosition(
                agent_id=agent.agent_id,
                agent_name=agent.agent_name,
                stance=insight.assessment,
                probability_estimate=main_prob,
                confidence=insight.confidence_overall,
                key_arguments=insight.key_findings[:5],
                supporting_evidence=insight.evidence_base[:5],
                counterarguments_addressed=[],
                willingness_to_revise=revision_willingness,
                revision_conditions=insight.caveats[:3],
            )
            positions.append(position)

        return positions

    async def _execute_round(
        self,
        round_num: int,
        topic: str,
        agents: List[ExpertAgent],
        positions: List[AgentPosition],
        context: Dict[str, Any],
    ) -> DebateRound:
        """Execute a single debate round."""
        challenges_raised: List[Challenge] = []
        challenges_addressed: List[ChallengeResponse] = []
        position_revisions: List[Dict[str, Any]] = []

        # Identify potential challenges
        for i, challenger_pos in enumerate(positions):
            for j, target_pos in enumerate(positions):
                if i == j:
                    continue

                challenge = await self._identify_challenge(
                    agents[i],
                    challenger_pos,
                    target_pos,
                    context,
                )

                if challenge:
                    challenges_raised.append(challenge)

        # Process challenges (respond and potentially revise)
        for challenge in challenges_raised:
            target_agent = next(
                (a for a in agents if a.agent_id == challenge.target_id),
                None
            )
            target_pos = next(
                (p for p in positions if p.agent_id == challenge.target_id),
                None
            )

            if target_agent and target_pos:
                response = await self._process_challenge(
                    target_agent,
                    target_pos,
                    challenge,
                    context,
                )
                challenges_addressed.append(response)

                if response.position_revised and response.new_position:
                    position_revisions.append({
                        "agent_id": target_agent.agent_id,
                        "old_position": target_pos.stance,
                        "new_position": response.new_position,
                        "reason": response.concession_made or "Revised based on challenge",
                    })

        convergence = self._calculate_convergence(positions)

        return DebateRound(
            round_number=round_num,
            topic=topic,
            positions=positions,
            challenges_raised=[c.to_dict() for c in challenges_raised],
            challenges_addressed=[c.to_dict() for c in challenges_addressed],
            position_revisions=position_revisions,
            convergence_score=convergence,
        )

    async def _identify_challenge(
        self,
        challenger: ExpertAgent,
        challenger_pos: AgentPosition,
        target_pos: AgentPosition,
        context: Dict[str, Any],
    ) -> Optional[Challenge]:
        """
        Identify if challenger should challenge target's position.

        Uses the agent's challenge() method to generate challenges.
        """
        # Check if probability difference exceeds threshold
        prob_diff = abs(challenger_pos.probability_estimate - target_pos.probability_estimate)

        if prob_diff < self.config.challenge_threshold:
            return None

        try:
            challenge_result = await asyncio.wait_for(
                challenger.challenge(target_pos),
                timeout=self.config.timeout_per_round_seconds / 2,
            )

            if not challenge_result or not challenge_result.get("challenge_statement"):
                return None

            # Parse challenge type
            challenge_type_str = challenge_result.get("challenge_type", "factual")
            try:
                challenge_type = DisagreementType(challenge_type_str)
            except ValueError:
                challenge_type = DisagreementType.FACTUAL

            # Parse counter evidence
            counter_evidence = challenge_result.get("counter_evidence", [])
            if counter_evidence and isinstance(counter_evidence[0], dict):
                # Convert dicts to Evidence objects if needed
                counter_evidence = []

            return Challenge(
                challenger_id=challenger.agent_id,
                challenger_name=challenger.agent_name,
                target_id=target_pos.agent_id,
                target_name=target_pos.agent_name,
                challenge_type=challenge_type,
                claim_challenged=target_pos.stance[:200],
                challenge_statement=challenge_result.get("challenge_statement", ""),
                counter_evidence=counter_evidence,
                severity=challenge_result.get("severity", "moderate"),
                suggested_revision=challenge_result.get("suggested_revision"),
            )

        except asyncio.TimeoutError:
            self.logger.warning(f"Challenge timeout for {challenger.agent_name}")
            return None
        except Exception as e:
            self.logger.error(f"Challenge error: {e}")
            return None

    async def _process_challenge(
        self,
        target_agent: ExpertAgent,
        target_pos: AgentPosition,
        challenge: Challenge,
        context: Dict[str, Any],
    ) -> ChallengeResponse:
        """
        Process a challenge to an agent's position.

        The agent may:
        - Accept the challenge and revise their position
        - Reject the challenge with counter-arguments
        - Partially accept with caveats
        """
        try:
            # Use agent's revise method
            challenges_list = [{
                "challenger_id": challenge.challenger_id,
                "challenge_type": challenge.challenge_type.value,
                "challenge_statement": challenge.challenge_statement,
                "suggested_revision": challenge.suggested_revision,
            }]

            revised_position = await asyncio.wait_for(
                target_agent.revise(
                    target_pos,
                    challenges_list,
                    challenge.counter_evidence,
                ),
                timeout=self.config.timeout_per_round_seconds / 2,
            )

            # Determine if position was meaningfully revised
            prob_changed = abs(revised_position.probability_estimate - target_pos.probability_estimate) > 0.05
            stance_changed = revised_position.stance != target_pos.stance

            return ChallengeResponse(
                responder_id=target_agent.agent_id,
                challenge=challenge,
                accepted=prob_changed or stance_changed,
                response_statement=f"Position {'revised' if prob_changed or stance_changed else 'maintained'} after considering challenge",
                position_revised=prob_changed or stance_changed,
                new_position=revised_position.stance if stance_changed else None,
                additional_evidence=revised_position.supporting_evidence[:2],
                concession_made="Adjusted probability estimate" if prob_changed else None,
            )

        except asyncio.TimeoutError:
            self.logger.warning(f"Response timeout for {target_agent.agent_name}")
            return ChallengeResponse(
                responder_id=target_agent.agent_id,
                challenge=challenge,
                accepted=False,
                response_statement="Challenge could not be processed in time",
                position_revised=False,
            )
        except Exception as e:
            self.logger.error(f"Challenge processing error: {e}")
            return ChallengeResponse(
                responder_id=target_agent.agent_id,
                challenge=challenge,
                accepted=False,
                response_statement=f"Error processing challenge: {str(e)[:100]}",
                position_revised=False,
            )

    def _calculate_convergence(self, positions: List[AgentPosition]) -> float:
        """
        Calculate convergence score among agent positions.

        Uses both probability alignment and qualitative stance similarity.
        """
        if len(positions) < 2:
            return 1.0

        # Probability-based convergence
        probs = [p.probability_estimate for p in positions]
        prob_range = max(probs) - min(probs)
        prob_convergence = 1.0 - prob_range

        # Confidence-weighted convergence
        total_confidence = sum(
            {
                ConfidenceLevel.VERY_LOW: 0.2,
                ConfidenceLevel.LOW: 0.4,
                ConfidenceLevel.MODERATE: 0.6,
                ConfidenceLevel.HIGH: 0.8,
                ConfidenceLevel.VERY_HIGH: 0.9,
                ConfidenceLevel.NEAR_CERTAIN: 0.95,
            }.get(p.confidence, 0.5)
            for p in positions
        )
        avg_confidence = total_confidence / len(positions)

        # Combined convergence score
        return (prob_convergence * 0.6) + (avg_confidence * 0.4)

    def _apply_revisions(
        self,
        positions: List[AgentPosition],
        revisions: List[Dict[str, Any]],
    ) -> List[AgentPosition]:
        """Apply position revisions from a debate round."""
        for revision in revisions:
            agent_id = revision.get("agent_id")
            new_stance = revision.get("new_position")

            for i, pos in enumerate(positions):
                if pos.agent_id == agent_id and new_stance:
                    # Create updated position
                    positions[i] = AgentPosition(
                        agent_id=pos.agent_id,
                        agent_name=pos.agent_name,
                        stance=new_stance,
                        probability_estimate=pos.probability_estimate,  # May be updated separately
                        confidence=pos.confidence,
                        key_arguments=pos.key_arguments,
                        supporting_evidence=pos.supporting_evidence,
                        counterarguments_addressed=pos.counterarguments_addressed + [revision.get("reason", "")],
                        willingness_to_revise=pos.willingness_to_revise,
                        revision_conditions=pos.revision_conditions,
                    )
                    break

        return positions

    def identify_disagreements(
        self,
        positions: List[AgentPosition],
    ) -> List[Dict[str, Any]]:
        """
        Identify and categorize remaining disagreements between agents.

        Returns structured disagreement records for the consensus report.
        """
        disagreements = []

        for i, pos_a in enumerate(positions):
            for j, pos_b in enumerate(positions):
                if i >= j:
                    continue

                prob_diff = abs(pos_a.probability_estimate - pos_b.probability_estimate)

                if prob_diff > 0.1:  # Significant probability disagreement
                    disagreement_type = self._categorize_disagreement(pos_a, pos_b)

                    disagreements.append({
                        "agents": [pos_a.agent_name, pos_b.agent_name],
                        "type": disagreement_type.value,
                        "description": f"{pos_a.agent_name} estimates {pos_a.probability_estimate:.0%} while {pos_b.agent_name} estimates {pos_b.probability_estimate:.0%}",
                        "probability_difference": round(prob_diff, 4),
                        "position_a": pos_a.stance[:200],
                        "position_b": pos_b.stance[:200],
                        "unresolved": True,
                    })

        return disagreements

    def _categorize_disagreement(
        self,
        pos_a: AgentPosition,
        pos_b: AgentPosition,
    ) -> DisagreementType:
        """Categorize the type of disagreement between two positions."""
        prob_diff = abs(pos_a.probability_estimate - pos_b.probability_estimate)

        # Check confidence levels
        confidence_diff = abs(
            list(ConfidenceLevel).index(pos_a.confidence) -
            list(ConfidenceLevel).index(pos_b.confidence)
        )

        if prob_diff > 0.3:
            return DisagreementType.PROBABILISTIC
        elif confidence_diff > 2:
            return DisagreementType.METHODOLOGICAL
        elif len(set(pos_a.key_arguments) & set(pos_b.key_arguments)) == 0:
            return DisagreementType.FACTUAL
        else:
            return DisagreementType.SEVERITY

    def extract_minority_views(
        self,
        positions: List[AgentPosition],
    ) -> List[Dict[str, Any]]:
        """
        Extract minority views that differ significantly from consensus.

        Minority views are important for documenting alternative interpretations.
        """
        if len(positions) < 3:
            return []

        # Calculate median probability
        probs = sorted(p.probability_estimate for p in positions)
        median_prob = probs[len(probs) // 2]

        minority_views = []

        for pos in positions:
            deviation = abs(pos.probability_estimate - median_prob)

            if deviation > 0.2:  # 20% deviation from median
                minority_views.append({
                    "agent": pos.agent_name,
                    "position": pos.stance,
                    "probability": pos.probability_estimate,
                    "deviation_from_median": round(deviation, 4),
                    "confidence": pos.confidence.value,
                    "key_arguments": pos.key_arguments[:3],
                    "rationale": "This view represents a significant departure from the consensus estimate",
                })

        return minority_views
