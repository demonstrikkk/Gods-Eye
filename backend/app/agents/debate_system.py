"""
Multi-Agent Debate System
=========================

Structured debate framework for expert agents:
- Position formulation
- Argument construction
- Rebuttal handling
- Evidence-based counter-arguments
- Convergence detection
- Debate moderator
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .expert_base import ExpertAgent, AgentAssessment

logger = logging.getLogger(__name__)


class DebatePhase(str, Enum):
    """Phases of a structured debate."""

    OPENING = "opening"           # Initial position statements
    EVIDENCE = "evidence"         # Evidence presentation
    CROSS_EXAMINATION = "cross_examination"  # Questioning
    REBUTTAL = "rebuttal"         # Counter-arguments
    CLOSING = "closing"           # Final statements
    DELIBERATION = "deliberation" # Convergence phase


class Stance(str, Enum):
    """Possible stances in a debate."""

    STRONGLY_AGREE = "strongly_agree"
    AGREE = "agree"
    PARTIALLY_AGREE = "partially_agree"
    NEUTRAL = "neutral"
    PARTIALLY_DISAGREE = "partially_disagree"
    DISAGREE = "disagree"
    STRONGLY_DISAGREE = "strongly_disagree"

    def compatibility_score(self, other: "Stance") -> float:
        """Calculate compatibility score between two stances."""
        order = list(Stance)
        self_idx = order.index(self)
        other_idx = order.index(other)
        max_dist = len(order) - 1
        distance = abs(self_idx - other_idx)
        return 1.0 - (distance / max_dist)


@dataclass
class Position:
    """
    A position held by an agent in a debate.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_id: str = ""
    agent_name: str = ""

    # Core position
    statement: str = ""
    stance: Stance = Stance.NEUTRAL
    probability: float = 0.5  # Probability the agent assigns

    # Evidence basis
    supporting_evidence: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)

    # Reasoning
    reasoning_chain: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    caveats: List[str] = field(default_factory=list)

    # Confidence
    confidence: float = 0.7
    uncertainty_factors: List[str] = field(default_factory=list)

    # Meta
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    phase: DebatePhase = DebatePhase.OPENING
    version: int = 1  # Increments if position is updated

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "statement": self.statement,
            "stance": self.stance.value if isinstance(self.stance, Stance) else self.stance,
            "probability": self.probability,
            "supporting_evidence": self.supporting_evidence,
            "data_sources": self.data_sources,
            "citations": self.citations,
            "reasoning_chain": self.reasoning_chain,
            "assumptions": self.assumptions,
            "caveats": self.caveats,
            "confidence": self.confidence,
            "uncertainty_factors": self.uncertainty_factors,
            "timestamp": self.timestamp.isoformat(),
            "phase": self.phase.value if isinstance(self.phase, DebatePhase) else self.phase,
            "version": self.version,
        }


@dataclass
class Argument:
    """
    A structured argument in support of or against a position.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_id: str = ""
    agent_name: str = ""

    # Argument structure
    claim: str = ""
    premises: List[str] = field(default_factory=list)
    conclusion: str = ""
    argument_type: str = "deductive"  # deductive, inductive, abductive

    # Target
    target_position_id: Optional[str] = None
    supports_position: bool = True  # False if counter-argument

    # Evidence
    evidence: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)

    # Strength assessment
    logical_validity: float = 0.8
    empirical_strength: float = 0.7
    overall_strength: float = 0.75

    # Meta
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "claim": self.claim,
            "premises": self.premises,
            "conclusion": self.conclusion,
            "argument_type": self.argument_type,
            "target_position_id": self.target_position_id,
            "supports_position": self.supports_position,
            "evidence": self.evidence,
            "citations": self.citations,
            "logical_validity": self.logical_validity,
            "empirical_strength": self.empirical_strength,
            "overall_strength": self.overall_strength,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Rebuttal:
    """
    A rebuttal to an argument.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_id: str = ""
    agent_name: str = ""

    # Target
    target_argument_id: str = ""
    target_agent_id: str = ""

    # Rebuttal content
    rebuttal_type: str = "direct"  # direct, undermining, outweighing
    counter_claim: str = ""
    counter_evidence: List[str] = field(default_factory=list)
    logical_flaws_identified: List[str] = field(default_factory=list)

    # Effectiveness
    effectiveness_score: float = 0.5

    # Impact on original argument
    reduces_strength_by: float = 0.0

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "target_argument_id": self.target_argument_id,
            "rebuttal_type": self.rebuttal_type,
            "counter_claim": self.counter_claim,
            "counter_evidence": self.counter_evidence,
            "logical_flaws_identified": self.logical_flaws_identified,
            "effectiveness_score": self.effectiveness_score,
            "reduces_strength_by": self.reduces_strength_by,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DebateRound:
    """
    A single round of debate between agents.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    round_number: int = 1
    phase: DebatePhase = DebatePhase.OPENING
    topic: str = ""

    # Participants
    participants: List[str] = field(default_factory=list)  # agent_ids

    # Content
    positions: List[Position] = field(default_factory=list)
    arguments: List[Argument] = field(default_factory=list)
    rebuttals: List[Rebuttal] = field(default_factory=list)

    # Outcomes
    convergence_score: float = 0.0
    key_disagreements: List[str] = field(default_factory=list)
    emerging_consensus: Optional[str] = None

    # Timing
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "round_number": self.round_number,
            "phase": self.phase.value if isinstance(self.phase, DebatePhase) else self.phase,
            "topic": self.topic,
            "participants": self.participants,
            "positions": [p.to_dict() for p in self.positions],
            "arguments": [a.to_dict() for a in self.arguments],
            "rebuttals": [r.to_dict() for r in self.rebuttals],
            "convergence_score": self.convergence_score,
            "key_disagreements": self.key_disagreements,
            "emerging_consensus": self.emerging_consensus,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class AgentDebateSystem:
    """
    Orchestrates structured debates between expert agents.

    Responsibilities:
    - Manage debate rounds
    - Moderate discussions
    - Track positions and arguments
    - Detect convergence/divergence
    - Generate debate summaries
    """

    def __init__(self, max_rounds: int = 3, convergence_threshold: float = 0.75):
        self.max_rounds = max_rounds
        self.convergence_threshold = convergence_threshold
        self.logger = logging.getLogger("debate_system")

        # State
        self._current_debate: Optional[Dict[str, Any]] = None
        self._rounds: List[DebateRound] = []
        self._positions: Dict[str, Position] = {}  # agent_id -> latest position
        self._arguments: Dict[str, List[Argument]] = {}  # agent_id -> arguments
        self._rebuttals: List[Rebuttal] = []

    async def initiate_debate(
        self,
        topic: str,
        question: str,
        agents: List["ExpertAgent"],
        initial_assessments: Dict[str, "AgentAssessment"]
    ) -> Dict[str, Any]:
        """
        Initiate a structured debate among agents.

        Args:
            topic: Main topic of debate
            question: Specific question being debated
            agents: List of participating agents
            initial_assessments: Each agent's initial assessment

        Returns:
            Complete debate record with consensus/disagreements
        """
        self.logger.info(f"Initiating debate on: {topic}")
        self.logger.info(f"Participants: {[a.name for a in agents]}")

        # Initialize debate state
        self._current_debate = {
            "id": str(uuid4())[:8],
            "topic": topic,
            "question": question,
            "start_time": datetime.now(timezone.utc),
            "participants": [a.agent_id for a in agents],
        }
        self._rounds = []
        self._positions = {}
        self._arguments = {}
        self._rebuttals = []

        # Phase 1: Opening - Extract initial positions
        opening_round = await self._run_opening_phase(agents, initial_assessments, question)
        self._rounds.append(opening_round)

        # Check for immediate convergence
        if opening_round.convergence_score >= self.convergence_threshold:
            self.logger.info("Immediate convergence detected - skipping further debate")
        else:
            # Phase 2: Evidence & Arguments
            evidence_round = await self._run_evidence_phase(agents, question)
            self._rounds.append(evidence_round)

            # Phase 3: Rebuttal
            rebuttal_round = await self._run_rebuttal_phase(agents)
            self._rounds.append(rebuttal_round)

            # Phase 4: Deliberation (if still divergent)
            if rebuttal_round.convergence_score < self.convergence_threshold:
                deliberation_round = await self._run_deliberation_phase(agents, question)
                self._rounds.append(deliberation_round)

        # Generate debate summary
        summary = self._generate_debate_summary(topic, question)

        self._current_debate["end_time"] = datetime.now(timezone.utc)
        self._current_debate["summary"] = summary

        return self._current_debate

    async def _run_opening_phase(
        self,
        agents: List["ExpertAgent"],
        assessments: Dict[str, "AgentAssessment"],
        question: str
    ) -> DebateRound:
        """Run opening phase - agents state their positions."""
        self.logger.info("Running opening phase...")

        round_obj = DebateRound(
            round_number=1,
            phase=DebatePhase.OPENING,
            topic=question,
            participants=[a.agent_id for a in agents],
        )

        # Extract positions from assessments
        for agent in agents:
            assessment = assessments.get(agent.agent_id)
            if not assessment:
                continue

            # Determine stance from confidence and claims
            probability = assessment.confidence_score
            stance = self._probability_to_stance(probability)

            position = Position(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                statement=assessment.executive_summary,
                stance=stance,
                probability=probability,
                supporting_evidence=[f.statement for f in assessment.claims[:3]],
                data_sources=assessment.data_sources_used,
                reasoning_chain=[f.statement for f in assessment.claims],
                assumptions=[c.assumptions[0] for c in assessment.claims if c.assumptions],
                caveats=assessment.uncertainty_factors[:3],
                confidence=assessment.confidence_score,
                uncertainty_factors=assessment.data_gaps,
                phase=DebatePhase.OPENING,
            )

            self._positions[agent.agent_id] = position
            round_obj.positions.append(position)

        # Calculate initial convergence
        round_obj.convergence_score = self._calculate_convergence(round_obj.positions)
        round_obj.key_disagreements = self._identify_disagreements(round_obj.positions)

        round_obj.end_time = datetime.now(timezone.utc)
        return round_obj

    async def _run_evidence_phase(
        self,
        agents: List["ExpertAgent"],
        question: str
    ) -> DebateRound:
        """Run evidence phase - agents present supporting arguments."""
        self.logger.info("Running evidence phase...")

        round_obj = DebateRound(
            round_number=2,
            phase=DebatePhase.EVIDENCE,
            topic=question,
            participants=[a.agent_id for a in agents],
        )

        # Each agent constructs arguments for their position
        for agent in agents:
            position = self._positions.get(agent.agent_id)
            if not position:
                continue

            # Generate arguments
            arguments = await self._generate_arguments(agent, position)
            self._arguments[agent.agent_id] = arguments
            round_obj.arguments.extend(arguments)

        round_obj.convergence_score = self._calculate_convergence(
            list(self._positions.values())
        )
        round_obj.end_time = datetime.now(timezone.utc)
        return round_obj

    async def _run_rebuttal_phase(
        self,
        agents: List["ExpertAgent"]
    ) -> DebateRound:
        """Run rebuttal phase - agents respond to other arguments."""
        self.logger.info("Running rebuttal phase...")

        round_obj = DebateRound(
            round_number=3,
            phase=DebatePhase.REBUTTAL,
            topic=self._current_debate.get("question", ""),
            participants=[a.agent_id for a in agents],
        )

        # Each agent reviews arguments from others
        for agent in agents:
            other_arguments = []
            for other_id, args in self._arguments.items():
                if other_id != agent.agent_id:
                    other_arguments.extend(args)

            # Generate rebuttals
            rebuttals = await self._generate_rebuttals(agent, other_arguments)
            self._rebuttals.extend(rebuttals)
            round_obj.rebuttals.extend(rebuttals)

        # Update positions based on rebuttals
        self._update_positions_from_rebuttals()

        round_obj.convergence_score = self._calculate_convergence(
            list(self._positions.values())
        )
        round_obj.key_disagreements = self._identify_disagreements(
            list(self._positions.values())
        )
        round_obj.end_time = datetime.now(timezone.utc)
        return round_obj

    async def _run_deliberation_phase(
        self,
        agents: List["ExpertAgent"],
        question: str
    ) -> DebateRound:
        """Run deliberation phase - agents seek common ground."""
        self.logger.info("Running deliberation phase...")

        round_obj = DebateRound(
            round_number=4,
            phase=DebatePhase.DELIBERATION,
            topic=question,
            participants=[a.agent_id for a in agents],
        )

        # Find common ground
        positions = list(self._positions.values())
        common_ground = self._find_common_ground(positions)

        # Update each agent's position toward consensus
        for agent in agents:
            position = self._positions.get(agent.agent_id)
            if position:
                updated_position = self._move_toward_consensus(position, common_ground)
                self._positions[agent.agent_id] = updated_position
                round_obj.positions.append(updated_position)

        round_obj.convergence_score = self._calculate_convergence(
            list(self._positions.values())
        )
        round_obj.emerging_consensus = common_ground.get("consensus_statement")
        round_obj.key_disagreements = self._identify_disagreements(
            list(self._positions.values())
        )
        round_obj.end_time = datetime.now(timezone.utc)
        return round_obj

    async def _generate_arguments(
        self,
        agent: "ExpertAgent",
        position: Position
    ) -> List[Argument]:
        """Generate arguments supporting an agent's position."""
        arguments = []

        # Main argument
        main_arg = Argument(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            claim=position.statement,
            premises=position.reasoning_chain[:3],
            conclusion=f"Therefore, {position.statement.lower()[:100]}",
            argument_type="deductive",
            target_position_id=position.id,
            supports_position=True,
            evidence=position.supporting_evidence,
            citations=position.citations,
            logical_validity=0.8,
            empirical_strength=position.confidence,
            overall_strength=(0.8 + position.confidence) / 2,
        )
        arguments.append(main_arg)

        # Supporting argument from evidence
        if position.supporting_evidence:
            supporting = Argument(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                claim=position.supporting_evidence[0] if position.supporting_evidence else "",
                premises=position.supporting_evidence[1:3],
                conclusion="This evidence supports the main position",
                argument_type="inductive",
                target_position_id=position.id,
                supports_position=True,
                evidence=position.data_sources[:2],
                logical_validity=0.7,
                empirical_strength=0.75,
                overall_strength=0.72,
            )
            arguments.append(supporting)

        return arguments

    async def _generate_rebuttals(
        self,
        agent: "ExpertAgent",
        arguments: List[Argument]
    ) -> List[Rebuttal]:
        """Generate rebuttals to opposing arguments."""
        rebuttals = []

        agent_position = self._positions.get(agent.agent_id)
        if not agent_position:
            return rebuttals

        for arg in arguments:
            if arg.agent_id == agent.agent_id:
                continue

            # Check if argument conflicts with this agent's position
            compatibility = self._assess_argument_compatibility(arg, agent_position)

            if compatibility < 0.5:  # Significant disagreement
                rebuttal = Rebuttal(
                    agent_id=agent.agent_id,
                    agent_name=agent.name,
                    target_argument_id=arg.id,
                    target_agent_id=arg.agent_id,
                    rebuttal_type="direct" if compatibility < 0.3 else "undermining",
                    counter_claim=self._generate_counter_claim(arg, agent_position),
                    counter_evidence=agent_position.supporting_evidence[:2],
                    logical_flaws_identified=self._identify_logical_flaws(arg),
                    effectiveness_score=1 - compatibility,
                    reduces_strength_by=(1 - compatibility) * 0.3,
                )
                rebuttals.append(rebuttal)

        return rebuttals

    def _calculate_convergence(self, positions: List[Position]) -> float:
        """Calculate convergence score among positions."""
        if len(positions) < 2:
            return 1.0

        # Compare all pairs of positions
        compatibilities = []
        for i, pos1 in enumerate(positions):
            for pos2 in positions[i + 1:]:
                # Stance compatibility
                stance_compat = pos1.stance.compatibility_score(pos2.stance)

                # Probability similarity
                prob_diff = abs(pos1.probability - pos2.probability)
                prob_compat = 1 - prob_diff

                # Combined
                compat = 0.6 * stance_compat + 0.4 * prob_compat
                compatibilities.append(compat)

        return sum(compatibilities) / len(compatibilities) if compatibilities else 0.0

    def _identify_disagreements(self, positions: List[Position]) -> List[str]:
        """Identify key disagreements among positions."""
        disagreements = []

        stances = [p.stance for p in positions]
        stance_set = set(stances)

        # Major stance splits
        if len(stance_set) > 2:
            disagreements.append(
                f"Agents hold {len(stance_set)} different positions"
            )

        # Probability divergence
        probs = [p.probability for p in positions]
        if max(probs) - min(probs) > 0.3:
            high_agent = positions[probs.index(max(probs))]
            low_agent = positions[probs.index(min(probs))]
            disagreements.append(
                f"{high_agent.agent_name} estimates {max(probs):.0%} vs "
                f"{low_agent.agent_name} estimates {min(probs):.0%}"
            )

        # Conflicting assumptions
        all_assumptions = []
        for p in positions:
            all_assumptions.extend(p.assumptions)
        if len(all_assumptions) > len(set(all_assumptions)):
            disagreements.append("Some agents rely on conflicting assumptions")

        return disagreements

    def _find_common_ground(self, positions: List[Position]) -> Dict[str, Any]:
        """Find consensus elements among positions."""
        common_ground = {
            "agreed_evidence": [],
            "shared_assumptions": [],
            "consensus_probability": 0.5,
            "consensus_statement": None,
        }

        if not positions:
            return common_ground

        # Find evidence cited by multiple agents
        evidence_counts: Dict[str, int] = {}
        for p in positions:
            for e in p.supporting_evidence:
                evidence_counts[e] = evidence_counts.get(e, 0) + 1

        common_ground["agreed_evidence"] = [
            e for e, count in evidence_counts.items()
            if count >= len(positions) / 2
        ]

        # Average probability
        common_ground["consensus_probability"] = sum(
            p.probability for p in positions
        ) / len(positions)

        # Generate consensus statement
        if self._calculate_convergence(positions) >= 0.6:
            median_idx = len(positions) // 2
            sorted_positions = sorted(positions, key=lambda p: p.probability)
            common_ground["consensus_statement"] = sorted_positions[median_idx].statement

        return common_ground

    def _move_toward_consensus(
        self,
        position: Position,
        common_ground: Dict[str, Any]
    ) -> Position:
        """Update a position to move toward consensus."""
        updated = Position(
            id=position.id,
            agent_id=position.agent_id,
            agent_name=position.agent_name,
            statement=position.statement,
            stance=position.stance,
            probability=position.probability,
            supporting_evidence=position.supporting_evidence,
            data_sources=position.data_sources,
            citations=position.citations,
            reasoning_chain=position.reasoning_chain,
            assumptions=position.assumptions,
            caveats=position.caveats,
            confidence=position.confidence,
            uncertainty_factors=position.uncertainty_factors,
            phase=DebatePhase.DELIBERATION,
            version=position.version + 1,
        )

        # Adjust probability toward consensus
        consensus_prob = common_ground.get("consensus_probability", 0.5)
        updated.probability = 0.7 * position.probability + 0.3 * consensus_prob

        # Update stance based on new probability
        updated.stance = self._probability_to_stance(updated.probability)

        return updated

    def _update_positions_from_rebuttals(self):
        """Update positions based on effective rebuttals."""
        for rebuttal in self._rebuttals:
            target_agent = rebuttal.target_agent_id
            if target_agent in self._positions:
                position = self._positions[target_agent]
                # Reduce confidence based on rebuttal effectiveness
                reduction = rebuttal.reduces_strength_by
                position.confidence *= (1 - reduction)
                position.probability *= (1 - reduction * 0.5)
                position.caveats.append(f"Contested by {rebuttal.agent_name}")

    def _probability_to_stance(self, probability: float) -> Stance:
        """Convert probability to stance."""
        if probability >= 0.85:
            return Stance.STRONGLY_AGREE
        elif probability >= 0.70:
            return Stance.AGREE
        elif probability >= 0.55:
            return Stance.PARTIALLY_AGREE
        elif probability >= 0.45:
            return Stance.NEUTRAL
        elif probability >= 0.30:
            return Stance.PARTIALLY_DISAGREE
        elif probability >= 0.15:
            return Stance.DISAGREE
        else:
            return Stance.STRONGLY_DISAGREE

    def _assess_argument_compatibility(
        self,
        argument: Argument,
        position: Position
    ) -> float:
        """Assess how compatible an argument is with a position."""
        # Simple heuristic based on keywords and stance
        arg_words = set(argument.claim.lower().split())
        pos_words = set(position.statement.lower().split())

        overlap = len(arg_words & pos_words) / max(len(arg_words | pos_words), 1)

        return overlap

    def _generate_counter_claim(
        self,
        argument: Argument,
        position: Position
    ) -> str:
        """Generate a counter-claim to an argument."""
        return f"Based on {position.data_sources[0] if position.data_sources else 'available evidence'}, an alternative interpretation is that {position.statement.lower()[:150]}"

    def _identify_logical_flaws(self, argument: Argument) -> List[str]:
        """Identify potential logical flaws in an argument."""
        flaws = []

        # Check for weak premises
        if len(argument.premises) < 2:
            flaws.append("Insufficient premises to support conclusion")

        # Check for low empirical strength
        if argument.empirical_strength < 0.5:
            flaws.append("Limited empirical support for claims")

        # Check for assumption gaps
        if argument.logical_validity < 0.7:
            flaws.append("Logical chain has potential gaps")

        return flaws

    def _generate_debate_summary(
        self,
        topic: str,
        question: str
    ) -> Dict[str, Any]:
        """Generate a comprehensive debate summary."""
        positions = list(self._positions.values())

        # Final convergence
        final_convergence = self._calculate_convergence(positions)

        # Consensus view (if achieved)
        consensus_view = None
        if final_convergence >= 0.6:
            sorted_positions = sorted(positions, key=lambda p: -p.confidence)
            consensus_view = {
                "statement": sorted_positions[0].statement if sorted_positions else None,
                "probability": sum(p.probability for p in positions) / len(positions),
                "confidence": final_convergence,
            }

        # Remaining disagreements
        remaining_disagreements = self._identify_disagreements(positions)

        # Agent positions summary
        position_summary = []
        for p in positions:
            position_summary.append({
                "agent": p.agent_name,
                "stance": p.stance.value if isinstance(p.stance, Stance) else p.stance,
                "probability": p.probability,
                "confidence": p.confidence,
                "key_evidence": p.supporting_evidence[:2],
            })

        return {
            "topic": topic,
            "question": question,
            "rounds_conducted": len(self._rounds),
            "final_convergence": final_convergence,
            "convergence_achieved": final_convergence >= self.convergence_threshold,
            "consensus_view": consensus_view,
            "disagreements": remaining_disagreements,
            "position_summary": position_summary,
            "total_arguments": sum(len(args) for args in self._arguments.values()),
            "total_rebuttals": len(self._rebuttals),
            "rounds": [r.to_dict() for r in self._rounds],
        }


# Global debate system instance
agent_debate_system = AgentDebateSystem()
