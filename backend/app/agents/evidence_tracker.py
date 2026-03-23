"""
Evidence Tracker & Citation System
===================================

Comprehensive evidence tracking for expert-level reasoning:
- Data source provenance
- Citation chains
- Evidence quality scoring
- Fact verification
- Source reliability tracking
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SourceType(str, Enum):
    """Types of data sources."""

    # Official/Institutional
    GOVERNMENT_OFFICIAL = "government_official"
    INTERNATIONAL_ORG = "international_org"
    ACADEMIC_RESEARCH = "academic_research"
    CENTRAL_BANK = "central_bank"

    # Real-time Intelligence
    NEWS_WIRE = "news_wire"
    OSINT_FEED = "osint_feed"
    SATELLITE_DATA = "satellite_data"
    SENSOR_NETWORK = "sensor_network"

    # Social/Sentiment
    SOCIAL_MEDIA = "social_media"
    PUBLIC_FORUM = "public_forum"
    SURVEY_DATA = "survey_data"

    # Derivative
    MODEL_OUTPUT = "model_output"
    AGENT_INFERENCE = "agent_inference"
    AGGREGATED_INDEX = "aggregated_index"


class ReliabilityRating(str, Enum):
    """Reliability ratings for data sources (NATO-style grading)."""

    A = "A"  # Completely reliable
    B = "B"  # Usually reliable
    C = "C"  # Fairly reliable
    D = "D"  # Not usually reliable
    E = "E"  # Unreliable
    F = "F"  # Cannot be judged


class CredibilityRating(str, Enum):
    """Credibility ratings for information content."""

    ONE = "1"    # Confirmed
    TWO = "2"    # Probably true
    THREE = "3"  # Possibly true
    FOUR = "4"   # Doubtful
    FIVE = "5"   # Improbable
    SIX = "6"    # Cannot be judged


@dataclass
class DataSource:
    """
    Represents a data source used for evidence.

    Uses intelligence community standards for reliability assessment.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = ""
    source_type: SourceType = SourceType.OSINT_FEED
    url: Optional[str] = None
    api_endpoint: Optional[str] = None

    # Reliability assessment
    reliability: ReliabilityRating = ReliabilityRating.C
    track_record_score: float = 0.7  # 0-1 historical accuracy

    # Metadata
    update_frequency: str = "daily"  # realtime, hourly, daily, weekly, monthly
    last_updated: Optional[datetime] = None
    geographic_coverage: List[str] = field(default_factory=list)  # ISO country codes
    temporal_coverage_start: Optional[datetime] = None

    # Quality indicators
    methodology_documented: bool = False
    peer_reviewed: bool = False
    official_source: bool = False

    def reliability_score(self) -> float:
        """Calculate numeric reliability score (0-1)."""
        base_scores = {
            ReliabilityRating.A: 0.95,
            ReliabilityRating.B: 0.80,
            ReliabilityRating.C: 0.60,
            ReliabilityRating.D: 0.40,
            ReliabilityRating.E: 0.20,
            ReliabilityRating.F: 0.30,  # Unknown gets middle-low
        }

        base = base_scores.get(self.reliability, 0.5)

        # Adjustments
        adjustments = 0.0
        if self.official_source:
            adjustments += 0.1
        if self.peer_reviewed:
            adjustments += 0.05
        if self.methodology_documented:
            adjustments += 0.05

        return min(base + adjustments, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type.value,
            "url": self.url,
            "reliability": self.reliability.value,
            "reliability_score": self.reliability_score(),
            "track_record_score": self.track_record_score,
            "update_frequency": self.update_frequency,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "official_source": self.official_source,
        }


@dataclass
class Citation:
    """
    A specific citation of evidence from a data source.

    Includes full provenance chain and quality assessment.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    source: DataSource = field(default_factory=DataSource)

    # Citation details
    title: str = ""
    excerpt: str = ""
    full_reference: str = ""
    access_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Location within source
    page_number: Optional[int] = None
    section: Optional[str] = None
    table_figure_id: Optional[str] = None
    api_query_params: Optional[Dict[str, Any]] = None

    # Quality assessment
    credibility: CredibilityRating = CredibilityRating.THREE
    corroboration_count: int = 0  # How many other sources confirm this

    # Evidence classification
    evidence_type: str = "factual"  # factual, statistical, testimonial, circumstantial
    supports_claim: Optional[str] = None  # claim_id this supports

    def quality_score(self) -> float:
        """Calculate overall citation quality score (0-1)."""
        # Source reliability
        source_score = self.source.reliability_score()

        # Credibility score
        cred_scores = {
            CredibilityRating.ONE: 0.95,
            CredibilityRating.TWO: 0.80,
            CredibilityRating.THREE: 0.60,
            CredibilityRating.FOUR: 0.40,
            CredibilityRating.FIVE: 0.20,
            CredibilityRating.SIX: 0.30,
        }
        cred_score = cred_scores.get(self.credibility, 0.5)

        # Corroboration bonus
        corroboration_bonus = min(self.corroboration_count * 0.05, 0.15)

        # Weighted combination
        return 0.4 * source_score + 0.5 * cred_score + 0.1 + corroboration_bonus

    def format_citation(self) -> str:
        """Format as readable citation string."""
        parts = [self.source.name]

        if self.title:
            parts.append(f'"{self.title}"')
        if self.section:
            parts.append(f"Section: {self.section}")
        if self.page_number:
            parts.append(f"p. {self.page_number}")

        parts.append(f"Accessed: {self.access_date.strftime('%Y-%m-%d')}")
        parts.append(f"[Reliability: {self.source.reliability.value}, Credibility: {self.credibility.value}]")

        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source.to_dict(),
            "title": self.title,
            "excerpt": self.excerpt[:200] if self.excerpt else "",
            "full_reference": self.full_reference,
            "access_date": self.access_date.isoformat(),
            "credibility": self.credibility.value,
            "corroboration_count": self.corroboration_count,
            "evidence_type": self.evidence_type,
            "quality_score": self.quality_score(),
            "formatted": self.format_citation(),
        }


@dataclass
class EvidenceChain:
    """
    Chain of evidence supporting a conclusion.

    Tracks the reasoning path from raw data to conclusion.
    """

    id: str = field(default_factory=lambda: str(uuid4())[:8])
    conclusion: str = ""
    citations: List[Citation] = field(default_factory=list)

    # Reasoning chain
    reasoning_steps: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    inferences: List[str] = field(default_factory=list)

    # Quality metrics
    chain_strength: float = 0.5  # 0-1, strength of logical chain
    weakest_link: Optional[str] = None  # Description of weakest point

    # Alternative interpretations
    alternative_conclusions: List[str] = field(default_factory=list)
    counter_evidence: List[Citation] = field(default_factory=list)

    def calculate_chain_strength(self) -> float:
        """Calculate the strength of the evidence chain."""
        if not self.citations:
            return 0.0

        # Average citation quality
        avg_citation_quality = sum(c.quality_score() for c in self.citations) / len(self.citations)

        # Penalty for many assumptions
        assumption_penalty = min(len(self.assumptions) * 0.05, 0.30)

        # Penalty for counter-evidence
        counter_penalty = min(len(self.counter_evidence) * 0.1, 0.40)

        # Bonus for corroboration
        corroboration_bonus = min(sum(c.corroboration_count for c in self.citations) * 0.02, 0.20)

        strength = avg_citation_quality - assumption_penalty - counter_penalty + corroboration_bonus
        self.chain_strength = max(0.0, min(1.0, strength))

        return self.chain_strength

    def identify_weakest_link(self) -> str:
        """Identify the weakest point in the evidence chain."""
        weakest_citation = min(self.citations, key=lambda c: c.quality_score()) if self.citations else None

        weaknesses = []

        if weakest_citation and weakest_citation.quality_score() < 0.5:
            weaknesses.append(
                f"Low-quality source: {weakest_citation.source.name} "
                f"(reliability: {weakest_citation.quality_score():.2f})"
            )

        if len(self.assumptions) > 2:
            weaknesses.append(f"Chain relies on {len(self.assumptions)} unverified assumptions")

        if self.counter_evidence:
            weaknesses.append(f"{len(self.counter_evidence)} pieces of counter-evidence exist")

        if not weaknesses:
            weaknesses.append("No significant weaknesses identified")

        self.weakest_link = weaknesses[0]
        return self.weakest_link

    def to_dict(self) -> Dict[str, Any]:
        self.calculate_chain_strength()
        self.identify_weakest_link()

        return {
            "id": self.id,
            "conclusion": self.conclusion,
            "citations": [c.to_dict() for c in self.citations],
            "reasoning_steps": self.reasoning_steps,
            "assumptions": self.assumptions,
            "inferences": self.inferences,
            "chain_strength": self.chain_strength,
            "weakest_link": self.weakest_link,
            "alternative_conclusions": self.alternative_conclusions,
            "counter_evidence_count": len(self.counter_evidence),
        }


class EvidenceTracker:
    """
    Central evidence tracking and management system.

    Responsibilities:
    - Register and track data sources
    - Manage citations
    - Build evidence chains
    - Cross-reference and corroborate
    - Generate evidence reports
    """

    # Known data sources registry
    KNOWN_SOURCES: Dict[str, DataSource] = {
        "world_bank": DataSource(
            id="world_bank",
            name="World Bank Open Data",
            source_type=SourceType.INTERNATIONAL_ORG,
            url="https://data.worldbank.org",
            api_endpoint="https://api.worldbank.org/v2",
            reliability=ReliabilityRating.A,
            track_record_score=0.95,
            update_frequency="quarterly",
            official_source=True,
            methodology_documented=True,
        ),
        "imf_weo": DataSource(
            id="imf_weo",
            name="IMF World Economic Outlook",
            source_type=SourceType.INTERNATIONAL_ORG,
            url="https://www.imf.org/en/Publications/WEO",
            reliability=ReliabilityRating.A,
            track_record_score=0.90,
            update_frequency="biannual",
            official_source=True,
            peer_reviewed=True,
            methodology_documented=True,
        ),
        "sipri": DataSource(
            id="sipri",
            name="SIPRI Arms Transfers Database",
            source_type=SourceType.ACADEMIC_RESEARCH,
            url="https://www.sipri.org/databases/armstransfers",
            reliability=ReliabilityRating.A,
            track_record_score=0.92,
            update_frequency="annual",
            peer_reviewed=True,
            methodology_documented=True,
        ),
        "gdelt": DataSource(
            id="gdelt",
            name="GDELT Project",
            source_type=SourceType.OSINT_FEED,
            url="https://www.gdeltproject.org",
            api_endpoint="https://api.gdeltproject.org/api/v2",
            reliability=ReliabilityRating.B,
            track_record_score=0.75,
            update_frequency="realtime",
        ),
        "acled": DataSource(
            id="acled",
            name="ACLED Conflict Data",
            source_type=SourceType.ACADEMIC_RESEARCH,
            url="https://acleddata.com",
            reliability=ReliabilityRating.A,
            track_record_score=0.88,
            update_frequency="weekly",
            peer_reviewed=True,
            methodology_documented=True,
        ),
        "nasa_firms": DataSource(
            id="nasa_firms",
            name="NASA FIRMS Fire Data",
            source_type=SourceType.SATELLITE_DATA,
            url="https://firms.modaps.eosdis.nasa.gov",
            reliability=ReliabilityRating.A,
            track_record_score=0.95,
            update_frequency="realtime",
            official_source=True,
            methodology_documented=True,
        ),
        "usgs_earthquake": DataSource(
            id="usgs_earthquake",
            name="USGS Earthquake Catalog",
            source_type=SourceType.SENSOR_NETWORK,
            url="https://earthquake.usgs.gov",
            api_endpoint="https://earthquake.usgs.gov/fdsnws/event/1",
            reliability=ReliabilityRating.A,
            track_record_score=0.98,
            update_frequency="realtime",
            official_source=True,
            methodology_documented=True,
        ),
        "data_gov_in": DataSource(
            id="data_gov_in",
            name="data.gov.in - Government of India",
            source_type=SourceType.GOVERNMENT_OFFICIAL,
            url="https://data.gov.in",
            reliability=ReliabilityRating.B,
            track_record_score=0.80,
            update_frequency="varies",
            official_source=True,
            geographic_coverage=["IND"],
        ),
        "twitter_trends": DataSource(
            id="twitter_trends",
            name="X/Twitter Trends",
            source_type=SourceType.SOCIAL_MEDIA,
            url="https://twitter.com",
            reliability=ReliabilityRating.D,
            track_record_score=0.40,
            update_frequency="realtime",
        ),
        "reddit_discourse": DataSource(
            id="reddit_discourse",
            name="Reddit Public Discourse",
            source_type=SourceType.PUBLIC_FORUM,
            url="https://reddit.com",
            reliability=ReliabilityRating.D,
            track_record_score=0.35,
            update_frequency="realtime",
        ),
        "polymarket": DataSource(
            id="polymarket",
            name="Polymarket Prediction Markets",
            source_type=SourceType.AGGREGATED_INDEX,
            url="https://polymarket.com",
            reliability=ReliabilityRating.C,
            track_record_score=0.65,
            update_frequency="realtime",
        ),
        "rbi": DataSource(
            id="rbi",
            name="Reserve Bank of India",
            source_type=SourceType.CENTRAL_BANK,
            url="https://rbi.org.in",
            reliability=ReliabilityRating.A,
            track_record_score=0.92,
            update_frequency="monthly",
            official_source=True,
            geographic_coverage=["IND"],
        ),
    }

    def __init__(self):
        self._sources: Dict[str, DataSource] = dict(self.KNOWN_SOURCES)
        self._citations: Dict[str, Citation] = {}
        self._evidence_chains: Dict[str, EvidenceChain] = {}
        self._corroboration_map: Dict[str, Set[str]] = {}  # claim_hash -> citation_ids
        self.logger = logging.getLogger("evidence_tracker")

    def register_source(self, source: DataSource) -> str:
        """Register a new data source."""
        self._sources[source.id] = source
        self.logger.info(f"Registered source: {source.name} ({source.id})")
        return source.id

    def get_source(self, source_id: str) -> Optional[DataSource]:
        """Get a data source by ID."""
        return self._sources.get(source_id)

    def create_citation(
        self,
        source_id: str,
        title: str,
        excerpt: str,
        credibility: CredibilityRating = CredibilityRating.THREE,
        evidence_type: str = "factual",
        **kwargs
    ) -> Citation:
        """Create a new citation from a registered source."""
        source = self._sources.get(source_id)
        if not source:
            # Create placeholder source
            source = DataSource(
                id=source_id,
                name=source_id.replace("_", " ").title(),
                reliability=ReliabilityRating.C,
            )
            self._sources[source_id] = source

        citation = Citation(
            source=source,
            title=title,
            excerpt=excerpt,
            credibility=credibility,
            evidence_type=evidence_type,
            **kwargs
        )

        self._citations[citation.id] = citation
        return citation

    def create_evidence_chain(
        self,
        conclusion: str,
        citations: List[Citation],
        reasoning_steps: List[str],
        assumptions: Optional[List[str]] = None
    ) -> EvidenceChain:
        """Create an evidence chain supporting a conclusion."""
        chain = EvidenceChain(
            conclusion=conclusion,
            citations=citations,
            reasoning_steps=reasoning_steps,
            assumptions=assumptions or [],
        )

        chain.calculate_chain_strength()
        chain.identify_weakest_link()

        self._evidence_chains[chain.id] = chain

        # Update corroboration map
        claim_hash = self._hash_claim(conclusion)
        if claim_hash not in self._corroboration_map:
            self._corroboration_map[claim_hash] = set()
        for c in citations:
            self._corroboration_map[claim_hash].add(c.id)

        return chain

    def find_corroborating_evidence(self, claim: str) -> List[Citation]:
        """Find citations that corroborate a claim."""
        claim_hash = self._hash_claim(claim)
        citation_ids = self._corroboration_map.get(claim_hash, set())
        return [self._citations[cid] for cid in citation_ids if cid in self._citations]

    def check_contradictions(
        self,
        claim: str,
        new_citation: Citation
    ) -> List[Tuple[Citation, str]]:
        """Check if new evidence contradicts existing claims."""
        contradictions = []

        # Simple keyword-based contradiction detection
        claim_lower = claim.lower()
        excerpt_lower = new_citation.excerpt.lower()

        contradiction_patterns = [
            ("increase", "decrease"),
            ("rise", "fall"),
            ("growth", "decline"),
            ("positive", "negative"),
            ("stable", "volatile"),
            ("strengthen", "weaken"),
        ]

        for pos, neg in contradiction_patterns:
            if pos in claim_lower and neg in excerpt_lower:
                contradictions.append((new_citation, f"Claim mentions '{pos}' but evidence suggests '{neg}'"))
            if neg in claim_lower and pos in excerpt_lower:
                contradictions.append((new_citation, f"Claim mentions '{neg}' but evidence suggests '{pos}'"))

        return contradictions

    def generate_evidence_report(
        self,
        chain_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive evidence report."""
        chains = [self._evidence_chains[cid] for cid in (chain_ids or self._evidence_chains.keys())
                  if cid in self._evidence_chains]

        if not chains:
            return {"error": "No evidence chains found"}

        # Aggregate metrics
        all_citations = []
        for chain in chains:
            all_citations.extend(chain.citations)

        unique_sources = list(set(c.source.id for c in all_citations))
        avg_chain_strength = sum(c.chain_strength for c in chains) / len(chains)

        # Source breakdown
        source_breakdown = {}
        for citation in all_citations:
            src_id = citation.source.id
            if src_id not in source_breakdown:
                source_breakdown[src_id] = {
                    "name": citation.source.name,
                    "type": citation.source.source_type.value,
                    "reliability": citation.source.reliability.value,
                    "citation_count": 0,
                    "avg_credibility_score": 0,
                }
            source_breakdown[src_id]["citation_count"] += 1

        return {
            "summary": {
                "total_evidence_chains": len(chains),
                "total_citations": len(all_citations),
                "unique_sources": len(unique_sources),
                "average_chain_strength": round(avg_chain_strength, 3),
            },
            "chains": [c.to_dict() for c in chains],
            "source_breakdown": source_breakdown,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _hash_claim(self, claim: str) -> str:
        """Create a hash for claim matching."""
        normalized = " ".join(claim.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def get_source_reliability_tier(self, source_id: str) -> str:
        """Get human-readable reliability tier for a source."""
        source = self._sources.get(source_id)
        if not source:
            return "Unknown"

        score = source.reliability_score()
        if score >= 0.85:
            return "Highly Reliable (Tier 1)"
        elif score >= 0.70:
            return "Reliable (Tier 2)"
        elif score >= 0.50:
            return "Moderately Reliable (Tier 3)"
        elif score >= 0.30:
            return "Low Reliability (Tier 4)"
        else:
            return "Unreliable (Tier 5)"

    def format_citations_for_response(
        self,
        citations: List[Citation],
        style: str = "inline"
    ) -> str:
        """Format citations for inclusion in agent responses."""
        if style == "inline":
            return " ".join(f"[{c.source.name}]" for c in citations)
        elif style == "footnote":
            lines = []
            for i, c in enumerate(citations, 1):
                lines.append(f"[{i}] {c.format_citation()}")
            return "\n".join(lines)
        elif style == "academic":
            return "; ".join(c.format_citation() for c in citations)
        else:
            return str([c.id for c in citations])


# Global evidence tracker instance
evidence_tracker = EvidenceTracker()
