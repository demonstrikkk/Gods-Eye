"""
Gods-Eye OS — Government Officials Database
============================================

Data schema and seed data for government officials,
political figures, and electoral tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class OfficialRole(str, Enum):
    HEAD_OF_STATE = "head_of_state"
    HEAD_OF_GOVERNMENT = "head_of_government"
    MINISTER = "minister"
    DEPUTY_MINISTER = "deputy_minister"
    LEGISLATOR = "legislator"
    MILITARY_LEADER = "military_leader"
    DIPLOMAT = "diplomat"
    INTELLIGENCE_CHIEF = "intelligence_chief"
    CENTRAL_BANKER = "central_banker"
    PARTY_LEADER = "party_leader"


class PoliticalAlignment(str, Enum):
    FAR_LEFT = "far_left"
    LEFT = "left"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    RIGHT = "right"
    FAR_RIGHT = "far_right"
    NATIONALIST = "nationalist"
    TECHNOCRAT = "technocrat"


class RelationshipStance(str, Enum):
    STRONG_ALLY = "strong_ally"
    ALLY = "ally"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    CAUTIOUS = "cautious"
    ADVERSARIAL = "adversarial"
    HOSTILE = "hostile"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Official:
    """Government official or political figure."""
    id: str
    name: str
    country_id: str
    role: OfficialRole
    title: str
    ministry: Optional[str] = None
    party: Optional[str] = None
    alignment: Optional[PoliticalAlignment] = None
    in_office_since: Optional[str] = None
    term_ends: Optional[str] = None
    age: Optional[int] = None
    education: Optional[str] = None
    prior_roles: List[str] = field(default_factory=list)
    key_policies: List[str] = field(default_factory=list)
    stance_on_india: Optional[RelationshipStance] = None
    influence_score: float = 0.5  # 0-1
    stability_risk: float = 0.3  # 0-1 (risk of removal/change)
    notes: str = ""
    image_url: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "country_id": self.country_id,
            "role": self.role.value if isinstance(self.role, OfficialRole) else self.role,
            "title": self.title,
            "ministry": self.ministry,
            "party": self.party,
            "alignment": self.alignment.value if isinstance(self.alignment, PoliticalAlignment) else self.alignment,
            "in_office_since": self.in_office_since,
            "term_ends": self.term_ends,
            "age": self.age,
            "education": self.education,
            "prior_roles": self.prior_roles,
            "key_policies": self.key_policies,
            "stance_on_india": self.stance_on_india.value if isinstance(self.stance_on_india, RelationshipStance) else self.stance_on_india,
            "influence_score": self.influence_score,
            "stability_risk": self.stability_risk,
            "notes": self.notes,
            "image_url": self.image_url,
            "lat": self.lat,
            "lng": self.lng,
        }


@dataclass
class PoliticalParty:
    """Political party information."""
    id: str
    name: str
    country_id: str
    abbreviation: str
    alignment: PoliticalAlignment
    founded: Optional[int] = None
    seats_parliament: int = 0
    total_seats: int = 0
    governing: bool = False
    coalition_partners: List[str] = field(default_factory=list)
    key_policies: List[str] = field(default_factory=list)
    leader_id: Optional[str] = None
    support_pct: float = 0.0  # Current polling

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "country_id": self.country_id,
            "abbreviation": self.abbreviation,
            "alignment": self.alignment.value if isinstance(self.alignment, PoliticalAlignment) else self.alignment,
            "founded": self.founded,
            "seats_parliament": self.seats_parliament,
            "total_seats": self.total_seats,
            "governing": self.governing,
            "seat_share_pct": round((self.seats_parliament / max(self.total_seats, 1)) * 100, 1),
            "coalition_partners": self.coalition_partners,
            "key_policies": self.key_policies,
            "leader_id": self.leader_id,
            "support_pct": self.support_pct,
        }


@dataclass
class Election:
    """Upcoming or recent election."""
    id: str
    country_id: str
    election_type: str  # "presidential", "parliamentary", "local"
    date: str
    status: str  # "upcoming", "ongoing", "completed"
    turnout_pct: Optional[float] = None
    leading_candidate: Optional[str] = None
    leading_party: Optional[str] = None
    projected_winner: Optional[str] = None
    confidence: float = 0.0
    key_issues: List[str] = field(default_factory=list)
    international_observers: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "country_id": self.country_id,
            "election_type": self.election_type,
            "date": self.date,
            "status": self.status,
            "turnout_pct": self.turnout_pct,
            "leading_candidate": self.leading_candidate,
            "leading_party": self.leading_party,
            "projected_winner": self.projected_winner,
            "confidence": self.confidence,
            "key_issues": self.key_issues,
            "international_observers": self.international_observers,
            "notes": self.notes,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SEED DATA - MAJOR WORLD LEADERS
# ═══════════════════════════════════════════════════════════════════════════════

OFFICIALS: List[Dict[str, Any]] = [
    # UNITED STATES
    {
        "id": "OFF-USA-001",
        "name": "Joe Biden",
        "country_id": "CTR-USA",
        "role": "head_of_state",
        "title": "President of the United States",
        "party": "Democratic Party",
        "alignment": "center_left",
        "in_office_since": "2021-01-20",
        "term_ends": "2025-01-20",
        "age": 81,
        "education": "Syracuse University Law",
        "prior_roles": ["Vice President", "Senator (Delaware)"],
        "key_policies": ["Infrastructure investment", "Climate action", "NATO strengthening"],
        "stance_on_india": "strong_ally",
        "influence_score": 0.95,
        "stability_risk": 0.3,
        "lat": 38.8977,
        "lng": -77.0365,
    },
    {
        "id": "OFF-USA-002",
        "name": "Antony Blinken",
        "country_id": "CTR-USA",
        "role": "minister",
        "title": "Secretary of State",
        "ministry": "State Department",
        "party": "Democratic Party",
        "alignment": "center_left",
        "in_office_since": "2021-01-26",
        "prior_roles": ["Deputy Secretary of State", "Deputy NSA"],
        "key_policies": ["Democracy promotion", "Alliance management", "China competition"],
        "stance_on_india": "ally",
        "influence_score": 0.85,
        "stability_risk": 0.2,
        "lat": 38.8951,
        "lng": -77.0484,
    },
    {
        "id": "OFF-USA-003",
        "name": "Lloyd Austin",
        "country_id": "CTR-USA",
        "role": "minister",
        "title": "Secretary of Defense",
        "ministry": "Department of Defense",
        "party": "Independent",
        "alignment": "center",
        "in_office_since": "2021-01-22",
        "prior_roles": ["CENTCOM Commander", "US Army General"],
        "key_policies": ["Indo-Pacific focus", "Modernization", "Allied interoperability"],
        "stance_on_india": "strong_ally",
        "influence_score": 0.88,
        "stability_risk": 0.15,
        "lat": 38.8719,
        "lng": -77.0563,
    },

    # RUSSIA
    {
        "id": "OFF-RUS-001",
        "name": "Vladimir Putin",
        "country_id": "CTR-RUS",
        "role": "head_of_state",
        "title": "President of Russia",
        "party": "United Russia",
        "alignment": "nationalist",
        "in_office_since": "2012-05-07",
        "term_ends": "2030-05-07",
        "age": 71,
        "education": "Leningrad State University Law",
        "prior_roles": ["Prime Minister", "FSB Director"],
        "key_policies": ["Eurasian integration", "Military modernization", "Energy leverage"],
        "stance_on_india": "ally",
        "influence_score": 0.92,
        "stability_risk": 0.25,
        "lat": 55.7558,
        "lng": 37.6173,
    },
    {
        "id": "OFF-RUS-002",
        "name": "Sergei Lavrov",
        "country_id": "CTR-RUS",
        "role": "minister",
        "title": "Foreign Minister",
        "ministry": "Ministry of Foreign Affairs",
        "party": "United Russia",
        "alignment": "nationalist",
        "in_office_since": "2004-03-09",
        "prior_roles": ["UN Ambassador"],
        "key_policies": ["Multipolar world order", "Anti-NATO expansion"],
        "stance_on_india": "ally",
        "influence_score": 0.75,
        "stability_risk": 0.2,
        "lat": 55.7520,
        "lng": 37.6175,
    },
    {
        "id": "OFF-RUS-003",
        "name": "Sergei Shoigu",
        "country_id": "CTR-RUS",
        "role": "minister",
        "title": "Defense Minister",
        "ministry": "Ministry of Defence",
        "party": "United Russia",
        "alignment": "nationalist",
        "in_office_since": "2012-11-06",
        "prior_roles": ["Emergency Minister"],
        "key_policies": ["Military modernization", "Arctic presence"],
        "stance_on_india": "friendly",
        "influence_score": 0.78,
        "stability_risk": 0.35,
        "lat": 55.7415,
        "lng": 37.5882,
    },

    # CHINA
    {
        "id": "OFF-CHN-001",
        "name": "Xi Jinping",
        "country_id": "CTR-CHN",
        "role": "head_of_state",
        "title": "President of China / General Secretary CPC",
        "party": "Communist Party of China",
        "alignment": "nationalist",
        "in_office_since": "2012-11-15",
        "age": 70,
        "education": "Tsinghua University",
        "prior_roles": ["Vice President", "Shanghai Party Secretary"],
        "key_policies": ["Belt and Road", "Common prosperity", "Taiwan reunification"],
        "stance_on_india": "cautious",
        "influence_score": 0.98,
        "stability_risk": 0.1,
        "lat": 39.9042,
        "lng": 116.4074,
    },
    {
        "id": "OFF-CHN-002",
        "name": "Wang Yi",
        "country_id": "CTR-CHN",
        "role": "minister",
        "title": "Foreign Minister",
        "ministry": "Ministry of Foreign Affairs",
        "party": "Communist Party of China",
        "alignment": "technocrat",
        "in_office_since": "2023-07-25",
        "prior_roles": ["State Councilor", "Taiwan Affairs Director"],
        "key_policies": ["Wolf warrior diplomacy", "Global South engagement"],
        "stance_on_india": "cautious",
        "influence_score": 0.72,
        "stability_risk": 0.15,
        "lat": 39.9087,
        "lng": 116.3913,
    },

    # INDIA
    {
        "id": "OFF-IND-001",
        "name": "Narendra Modi",
        "country_id": "CTR-IND",
        "role": "head_of_government",
        "title": "Prime Minister of India",
        "party": "Bharatiya Janata Party",
        "alignment": "center_right",
        "in_office_since": "2014-05-26",
        "age": 73,
        "education": "Gujarat University",
        "prior_roles": ["Chief Minister of Gujarat"],
        "key_policies": ["Digital India", "Make in India", "Multi-alignment foreign policy"],
        "stance_on_india": "strong_ally",
        "influence_score": 0.95,
        "stability_risk": 0.15,
        "lat": 28.6139,
        "lng": 77.2090,
    },
    {
        "id": "OFF-IND-002",
        "name": "S. Jaishankar",
        "country_id": "CTR-IND",
        "role": "minister",
        "title": "External Affairs Minister",
        "ministry": "Ministry of External Affairs",
        "party": "Bharatiya Janata Party",
        "alignment": "center_right",
        "in_office_since": "2019-05-31",
        "prior_roles": ["Foreign Secretary", "Ambassador to US/China"],
        "key_policies": ["Strategic autonomy", "Neighborhood first", "Act East"],
        "stance_on_india": "strong_ally",
        "influence_score": 0.82,
        "stability_risk": 0.1,
        "lat": 28.6015,
        "lng": 77.2167,
    },
    {
        "id": "OFF-IND-003",
        "name": "Rajnath Singh",
        "country_id": "CTR-IND",
        "role": "minister",
        "title": "Defence Minister",
        "ministry": "Ministry of Defence",
        "party": "Bharatiya Janata Party",
        "alignment": "center_right",
        "in_office_since": "2019-05-31",
        "prior_roles": ["Home Minister", "BJP President"],
        "key_policies": ["Defense indigenization", "Border infrastructure"],
        "stance_on_india": "strong_ally",
        "influence_score": 0.78,
        "stability_risk": 0.1,
        "lat": 28.6123,
        "lng": 77.2290,
    },

    # UNITED KINGDOM
    {
        "id": "OFF-GBR-001",
        "name": "Keir Starmer",
        "country_id": "CTR-GBR",
        "role": "head_of_government",
        "title": "Prime Minister",
        "party": "Labour Party",
        "alignment": "center_left",
        "in_office_since": "2024-07-05",
        "age": 61,
        "education": "Oxford University / Leeds University",
        "prior_roles": ["Leader of Opposition", "Director of Public Prosecutions"],
        "key_policies": ["NHS reform", "Green energy transition", "EU proximity"],
        "stance_on_india": "ally",
        "influence_score": 0.82,
        "stability_risk": 0.25,
        "lat": 51.5033,
        "lng": -0.1276,
    },

    # FRANCE
    {
        "id": "OFF-FRA-001",
        "name": "Emmanuel Macron",
        "country_id": "CTR-FRA",
        "role": "head_of_state",
        "title": "President of France",
        "party": "Renaissance",
        "alignment": "center",
        "in_office_since": "2017-05-14",
        "term_ends": "2027-05-13",
        "age": 46,
        "education": "ENA / Sciences Po",
        "prior_roles": ["Economy Minister", "Investment banker"],
        "key_policies": ["EU integration", "Strategic autonomy", "Indo-Pacific engagement"],
        "stance_on_india": "ally",
        "influence_score": 0.85,
        "stability_risk": 0.3,
        "lat": 48.8566,
        "lng": 2.3522,
    },

    # GERMANY
    {
        "id": "OFF-DEU-001",
        "name": "Olaf Scholz",
        "country_id": "CTR-DEU",
        "role": "head_of_government",
        "title": "Chancellor of Germany",
        "party": "Social Democratic Party",
        "alignment": "center_left",
        "in_office_since": "2021-12-08",
        "age": 65,
        "education": "University of Hamburg Law",
        "prior_roles": ["Finance Minister", "Hamburg Mayor"],
        "key_policies": ["Zeitenwende defense policy", "Energy transition", "EU leadership"],
        "stance_on_india": "friendly",
        "influence_score": 0.80,
        "stability_risk": 0.35,
        "lat": 52.5200,
        "lng": 13.4050,
    },

    # JAPAN
    {
        "id": "OFF-JPN-001",
        "name": "Fumio Kishida",
        "country_id": "CTR-JPN",
        "role": "head_of_government",
        "title": "Prime Minister of Japan",
        "party": "Liberal Democratic Party",
        "alignment": "center_right",
        "in_office_since": "2021-10-04",
        "age": 66,
        "education": "Waseda University",
        "prior_roles": ["Foreign Minister"],
        "key_policies": ["Free and Open Indo-Pacific", "Defense doubling", "Quad engagement"],
        "stance_on_india": "strong_ally",
        "influence_score": 0.78,
        "stability_risk": 0.35,
        "lat": 35.6762,
        "lng": 139.6503,
    },

    # PAKISTAN
    {
        "id": "OFF-PAK-001",
        "name": "Shehbaz Sharif",
        "country_id": "CTR-PAK",
        "role": "head_of_government",
        "title": "Prime Minister of Pakistan",
        "party": "Pakistan Muslim League (N)",
        "alignment": "center_right",
        "in_office_since": "2024-03-03",
        "age": 72,
        "education": "Government College Lahore",
        "prior_roles": ["Chief Minister Punjab", "Opposition Leader"],
        "key_policies": ["Economic stabilization", "CPEC", "Relations normalization"],
        "stance_on_india": "cautious",
        "influence_score": 0.65,
        "stability_risk": 0.55,
        "lat": 33.6844,
        "lng": 73.0479,
    },

    # IRAN
    {
        "id": "OFF-IRN-001",
        "name": "Ebrahim Raisi",
        "country_id": "CTR-IRN",
        "role": "head_of_state",
        "title": "President of Iran",
        "party": "Principlists",
        "alignment": "right",
        "in_office_since": "2021-08-03",
        "age": 63,
        "education": "Seminary education",
        "prior_roles": ["Chief Justice", "Prosecutor General"],
        "key_policies": ["Resistance economy", "Regional influence", "Nuclear program"],
        "stance_on_india": "friendly",
        "influence_score": 0.72,
        "stability_risk": 0.4,
        "lat": 35.6892,
        "lng": 51.3890,
    },

    # ISRAEL
    {
        "id": "OFF-ISR-001",
        "name": "Benjamin Netanyahu",
        "country_id": "CTR-ISR",
        "role": "head_of_government",
        "title": "Prime Minister of Israel",
        "party": "Likud",
        "alignment": "right",
        "in_office_since": "2022-12-29",
        "age": 74,
        "education": "MIT",
        "prior_roles": ["Finance Minister", "UN Ambassador"],
        "key_policies": ["Security first", "Abraham Accords expansion", "Iran containment"],
        "stance_on_india": "strong_ally",
        "influence_score": 0.82,
        "stability_risk": 0.45,
        "lat": 31.7683,
        "lng": 35.2137,
    },

    # UKRAINE
    {
        "id": "OFF-UKR-001",
        "name": "Volodymyr Zelenskyy",
        "country_id": "CTR-UKR",
        "role": "head_of_state",
        "title": "President of Ukraine",
        "party": "Servant of the People",
        "alignment": "center",
        "in_office_since": "2019-05-20",
        "age": 46,
        "education": "Kyiv National Economic University",
        "prior_roles": ["Actor", "Producer"],
        "key_policies": ["NATO membership", "EU integration", "Territorial integrity"],
        "stance_on_india": "neutral",
        "influence_score": 0.85,
        "stability_risk": 0.5,
        "lat": 50.4501,
        "lng": 30.5234,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# POLITICAL PARTIES
# ═══════════════════════════════════════════════════════════════════════════════

PARTIES: List[Dict[str, Any]] = [
    {
        "id": "PTY-USA-DEM",
        "name": "Democratic Party",
        "country_id": "CTR-USA",
        "abbreviation": "DEM",
        "alignment": "center_left",
        "founded": 1828,
        "seats_parliament": 212,
        "total_seats": 435,
        "governing": True,
        "key_policies": ["Healthcare expansion", "Climate action", "Social programs"],
        "leader_id": "OFF-USA-001",
        "support_pct": 47.5,
    },
    {
        "id": "PTY-USA-GOP",
        "name": "Republican Party",
        "country_id": "CTR-USA",
        "abbreviation": "GOP",
        "alignment": "center_right",
        "founded": 1854,
        "seats_parliament": 220,
        "total_seats": 435,
        "governing": False,
        "key_policies": ["Tax cuts", "Border security", "Deregulation"],
        "support_pct": 46.8,
    },
    {
        "id": "PTY-IND-BJP",
        "name": "Bharatiya Janata Party",
        "country_id": "CTR-IND",
        "abbreviation": "BJP",
        "alignment": "center_right",
        "founded": 1980,
        "seats_parliament": 303,
        "total_seats": 543,
        "governing": True,
        "coalition_partners": ["PTY-IND-NDA"],
        "key_policies": ["Hindutva", "Economic development", "Strong defense"],
        "leader_id": "OFF-IND-001",
        "support_pct": 37.4,
    },
    {
        "id": "PTY-IND-INC",
        "name": "Indian National Congress",
        "country_id": "CTR-IND",
        "abbreviation": "INC",
        "alignment": "center_left",
        "founded": 1885,
        "seats_parliament": 52,
        "total_seats": 543,
        "governing": False,
        "key_policies": ["Secularism", "Social welfare", "Federalism"],
        "support_pct": 21.8,
    },
    {
        "id": "PTY-RUS-UR",
        "name": "United Russia",
        "country_id": "CTR-RUS",
        "abbreviation": "UR",
        "alignment": "nationalist",
        "founded": 2001,
        "seats_parliament": 324,
        "total_seats": 450,
        "governing": True,
        "key_policies": ["Strong state", "Traditional values", "Eurasian integration"],
        "leader_id": "OFF-RUS-001",
        "support_pct": 49.8,
    },
    {
        "id": "PTY-CHN-CPC",
        "name": "Communist Party of China",
        "country_id": "CTR-CHN",
        "abbreviation": "CPC",
        "alignment": "left",
        "founded": 1921,
        "seats_parliament": 2977,
        "total_seats": 2977,
        "governing": True,
        "key_policies": ["Socialism with Chinese characteristics", "Common prosperity"],
        "leader_id": "OFF-CHN-001",
        "support_pct": 100.0,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# ELECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

ELECTIONS: List[Dict[str, Any]] = [
    {
        "id": "ELC-USA-2024",
        "country_id": "CTR-USA",
        "election_type": "presidential",
        "date": "2024-11-05",
        "status": "completed",
        "turnout_pct": 66.2,
        "leading_party": "Republican Party",
        "projected_winner": "Donald Trump",
        "confidence": 0.98,
        "key_issues": ["Economy", "Immigration", "Democracy"],
        "international_observers": True,
    },
    {
        "id": "ELC-IND-2024",
        "country_id": "CTR-IND",
        "election_type": "parliamentary",
        "date": "2024-06-04",
        "status": "completed",
        "turnout_pct": 65.8,
        "leading_party": "BJP",
        "projected_winner": "NDA Coalition",
        "confidence": 0.95,
        "key_issues": ["Economy", "Employment", "Development"],
        "international_observers": False,
    },
    {
        "id": "ELC-GBR-2024",
        "country_id": "CTR-GBR",
        "election_type": "parliamentary",
        "date": "2024-07-04",
        "status": "completed",
        "turnout_pct": 59.9,
        "leading_party": "Labour Party",
        "projected_winner": "Keir Starmer",
        "confidence": 0.99,
        "key_issues": ["NHS", "Cost of living", "Immigration"],
        "international_observers": False,
    },
    {
        "id": "ELC-FRA-2027",
        "country_id": "CTR-FRA",
        "election_type": "presidential",
        "date": "2027-04-10",
        "status": "upcoming",
        "leading_candidate": "TBD",
        "confidence": 0.0,
        "key_issues": ["Economy", "Immigration", "EU relations"],
        "international_observers": True,
        "notes": "Macron ineligible for third term",
    },
    {
        "id": "ELC-DEU-2025",
        "country_id": "CTR-DEU",
        "election_type": "parliamentary",
        "date": "2025-09-28",
        "status": "upcoming",
        "leading_party": "CDU/CSU",
        "confidence": 0.65,
        "key_issues": ["Economy", "Migration", "Energy"],
        "international_observers": False,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# OFFICIALS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class OfficialsEngine:
    """Engine for managing government officials data."""

    def __init__(self):
        self._officials = {o["id"]: o for o in OFFICIALS}
        self._parties = {p["id"]: p for p in PARTIES}
        self._elections = {e["id"]: e for e in ELECTIONS}

    def get_all_officials(self) -> List[Dict[str, Any]]:
        """Get all officials."""
        return list(self._officials.values())

    def get_official(self, official_id: str) -> Optional[Dict[str, Any]]:
        """Get official by ID."""
        return self._officials.get(official_id)

    def get_officials_by_country(self, country_id: str) -> List[Dict[str, Any]]:
        """Get all officials for a country."""
        return [o for o in self._officials.values() if o["country_id"] == country_id]

    def get_officials_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get officials by role type."""
        return [o for o in self._officials.values() if o["role"] == role]

    def get_heads_of_state(self) -> List[Dict[str, Any]]:
        """Get all heads of state."""
        return [o for o in self._officials.values() if o["role"] in ("head_of_state", "head_of_government")]

    def get_all_parties(self) -> List[Dict[str, Any]]:
        """Get all political parties."""
        return list(self._parties.values())

    def get_parties_by_country(self, country_id: str) -> List[Dict[str, Any]]:
        """Get parties for a country."""
        return [p for p in self._parties.values() if p["country_id"] == country_id]

    def get_governing_parties(self) -> List[Dict[str, Any]]:
        """Get currently governing parties."""
        return [p for p in self._parties.values() if p.get("governing")]

    def get_all_elections(self) -> List[Dict[str, Any]]:
        """Get all elections."""
        return list(self._elections.values())

    def get_election(self, election_id: str) -> Optional[Dict[str, Any]]:
        """Get election by ID."""
        return self._elections.get(election_id)

    def get_elections_by_country(self, country_id: str) -> List[Dict[str, Any]]:
        """Get elections for a country."""
        return [e for e in self._elections.values() if e["country_id"] == country_id]

    def get_upcoming_elections(self) -> List[Dict[str, Any]]:
        """Get upcoming elections."""
        return [e for e in self._elections.values() if e["status"] == "upcoming"]

    def search_officials(self, query: str) -> List[Dict[str, Any]]:
        """Search officials by name or title."""
        query_lower = query.lower()
        return [
            o for o in self._officials.values()
            if query_lower in o["name"].lower() or query_lower in o.get("title", "").lower()
        ]

    def get_india_relations_summary(self) -> Dict[str, Any]:
        """Get summary of world leaders' stances on India."""
        stances = {}
        for official in self._officials.values():
            stance = official.get("stance_on_india")
            if stance:
                stances[stance] = stances.get(stance, 0) + 1

        return {
            "total_officials": len(self._officials),
            "stance_distribution": stances,
            "strong_allies": [o for o in self._officials.values() if o.get("stance_on_india") == "strong_ally"],
            "adversarial": [o for o in self._officials.values() if o.get("stance_on_india") in ("adversarial", "hostile")],
        }


# Global instance
officials_engine = OfficialsEngine()
