"""
Gods-Eye OS — Virtual Battleground Engine
==========================================

Strategic simulation engine for geopolitical scenario modeling:
- Military strength comparison
- Ally/adversary network graphs
- Force deployment visualization
- Conflict outcome modeling
- Trade route disruption analysis
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("battleground_engine")


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS & TYPES
# ═══════════════════════════════════════════════════════════════════════════════

class RelationType(str, Enum):
    ALLY = "ally"
    ADVERSARY = "adversary"
    NEUTRAL = "neutral"
    STRATEGIC_PARTNER = "strategic_partner"
    RIVAL = "rival"
    DEFENSE_PACT = "defense_pact"


class ForceType(str, Enum):
    GROUND = "ground"
    AIR = "air"
    NAVAL = "naval"
    NUCLEAR = "nuclear"
    CYBER = "cyber"
    SPACE = "space"


class ConflictPhase(str, Enum):
    TENSION = "tension"
    ESCALATION = "escalation"
    LIMITED_CONFLICT = "limited_conflict"
    FULL_WAR = "full_war"
    DE_ESCALATION = "de_escalation"
    CEASEFIRE = "ceasefire"
    RESOLUTION = "resolution"


# ═══════════════════════════════════════════════════════════════════════════════
# MILITARY STRENGTH DATA
# ═══════════════════════════════════════════════════════════════════════════════

# Global military power index data (approximate, for simulation)
MILITARY_STRENGTH: Dict[str, Dict[str, Any]] = {
    "CTR-USA": {
        "name": "United States",
        "power_index": 0.0712,  # Lower is better (GlobalFirepower style)
        "active_personnel": 1_390_000,
        "reserve_personnel": 845_000,
        "aircraft": 13247,
        "fighters": 1957,
        "attack_helicopters": 983,
        "tanks": 5500,
        "naval_vessels": 484,
        "aircraft_carriers": 11,
        "submarines": 68,
        "nuclear_warheads": 5550,
        "defense_budget_usd": 886_000_000_000,
        "gdp_usd": 25_460_000_000_000,
        "tech_level": 10,
        "projection_capability": 10,
        "nato_member": True,
        "nuclear_power": True,
    },
    "CTR-RUS": {
        "name": "Russia",
        "power_index": 0.0714,
        "active_personnel": 1_330_000,
        "reserve_personnel": 2_000_000,
        "aircraft": 4173,
        "fighters": 772,
        "attack_helicopters": 544,
        "tanks": 12420,
        "naval_vessels": 605,
        "aircraft_carriers": 1,
        "submarines": 70,
        "nuclear_warheads": 6257,
        "defense_budget_usd": 86_400_000_000,
        "gdp_usd": 1_778_000_000_000,
        "tech_level": 8,
        "projection_capability": 7,
        "nato_member": False,
        "nuclear_power": True,
    },
    "CTR-CHN": {
        "name": "China",
        "power_index": 0.0722,
        "active_personnel": 2_035_000,
        "reserve_personnel": 510_000,
        "aircraft": 3285,
        "fighters": 1200,
        "attack_helicopters": 281,
        "tanks": 5250,
        "naval_vessels": 777,
        "aircraft_carriers": 3,
        "submarines": 78,
        "nuclear_warheads": 500,
        "defense_budget_usd": 292_000_000_000,
        "gdp_usd": 17_960_000_000_000,
        "tech_level": 9,
        "projection_capability": 6,
        "nato_member": False,
        "nuclear_power": True,
    },
    "CTR-IND": {
        "name": "India",
        "power_index": 0.1025,
        "active_personnel": 1_455_550,
        "reserve_personnel": 1_155_000,
        "aircraft": 2182,
        "fighters": 564,
        "attack_helicopters": 37,
        "tanks": 4614,
        "naval_vessels": 295,
        "aircraft_carriers": 2,
        "submarines": 18,
        "nuclear_warheads": 172,
        "defense_budget_usd": 83_600_000_000,
        "gdp_usd": 3_530_000_000_000,
        "tech_level": 7,
        "projection_capability": 5,
        "nato_member": False,
        "nuclear_power": True,
    },
    "CTR-GBR": {
        "name": "United Kingdom",
        "power_index": 0.1435,
        "active_personnel": 148_500,
        "reserve_personnel": 78_600,
        "aircraft": 664,
        "fighters": 119,
        "attack_helicopters": 48,
        "tanks": 227,
        "naval_vessels": 75,
        "aircraft_carriers": 2,
        "submarines": 11,
        "nuclear_warheads": 225,
        "defense_budget_usd": 68_000_000_000,
        "gdp_usd": 3_070_000_000_000,
        "tech_level": 9,
        "projection_capability": 7,
        "nato_member": True,
        "nuclear_power": True,
    },
    "CTR-FRA": {
        "name": "France",
        "power_index": 0.1848,
        "active_personnel": 203_250,
        "reserve_personnel": 35_000,
        "aircraft": 1004,
        "fighters": 266,
        "attack_helicopters": 69,
        "tanks": 406,
        "naval_vessels": 180,
        "aircraft_carriers": 1,
        "submarines": 10,
        "nuclear_warheads": 290,
        "defense_budget_usd": 53_600_000_000,
        "gdp_usd": 2_780_000_000_000,
        "tech_level": 9,
        "projection_capability": 6,
        "nato_member": True,
        "nuclear_power": True,
    },
    "CTR-PAK": {
        "name": "Pakistan",
        "power_index": 0.1711,
        "active_personnel": 654_000,
        "reserve_personnel": 550_000,
        "aircraft": 1372,
        "fighters": 357,
        "attack_helicopters": 52,
        "tanks": 3742,
        "naval_vessels": 114,
        "aircraft_carriers": 0,
        "submarines": 9,
        "nuclear_warheads": 170,
        "defense_budget_usd": 10_300_000_000,
        "gdp_usd": 376_000_000_000,
        "tech_level": 5,
        "projection_capability": 3,
        "nato_member": False,
        "nuclear_power": True,
    },
    "CTR-IRN": {
        "name": "Iran",
        "power_index": 0.2269,
        "active_personnel": 610_000,
        "reserve_personnel": 350_000,
        "aircraft": 551,
        "fighters": 186,
        "attack_helicopters": 12,
        "tanks": 1634,
        "naval_vessels": 101,
        "aircraft_carriers": 0,
        "submarines": 19,
        "nuclear_warheads": 0,
        "defense_budget_usd": 6_800_000_000,
        "gdp_usd": 388_000_000_000,
        "tech_level": 5,
        "projection_capability": 3,
        "nato_member": False,
        "nuclear_power": False,
    },
    "CTR-ISR": {
        "name": "Israel",
        "power_index": 0.2596,
        "active_personnel": 169_500,
        "reserve_personnel": 465_000,
        "aircraft": 601,
        "fighters": 241,
        "attack_helicopters": 48,
        "tanks": 1370,
        "naval_vessels": 67,
        "aircraft_carriers": 0,
        "submarines": 5,
        "nuclear_warheads": 90,
        "defense_budget_usd": 23_400_000_000,
        "gdp_usd": 522_000_000_000,
        "tech_level": 9,
        "projection_capability": 4,
        "nato_member": False,
        "nuclear_power": True,
    },
    "CTR-JPN": {
        "name": "Japan",
        "power_index": 0.1711,
        "active_personnel": 247_150,
        "reserve_personnel": 56_000,
        "aircraft": 1459,
        "fighters": 261,
        "attack_helicopters": 119,
        "tanks": 1004,
        "naval_vessels": 155,
        "aircraft_carriers": 0,
        "submarines": 23,
        "nuclear_warheads": 0,
        "defense_budget_usd": 54_100_000_000,
        "gdp_usd": 4_230_000_000_000,
        "tech_level": 9,
        "projection_capability": 4,
        "nato_member": False,
        "nuclear_power": False,
    },
    "CTR-DEU": {
        "name": "Germany",
        "power_index": 0.2322,
        "active_personnel": 184_000,
        "reserve_personnel": 30_000,
        "aircraft": 617,
        "fighters": 130,
        "attack_helicopters": 47,
        "tanks": 266,
        "naval_vessels": 80,
        "aircraft_carriers": 0,
        "submarines": 6,
        "nuclear_warheads": 0,
        "defense_budget_usd": 55_800_000_000,
        "gdp_usd": 4_070_000_000_000,
        "tech_level": 9,
        "projection_capability": 4,
        "nato_member": True,
        "nuclear_power": False,
    },
    "CTR-UKR": {
        "name": "Ukraine",
        "power_index": 0.2516,
        "active_personnel": 900_000,
        "reserve_personnel": 250_000,
        "aircraft": 318,
        "fighters": 69,
        "attack_helicopters": 34,
        "tanks": 1890,
        "naval_vessels": 15,
        "aircraft_carriers": 0,
        "submarines": 0,
        "nuclear_warheads": 0,
        "defense_budget_usd": 44_000_000_000,
        "gdp_usd": 160_000_000_000,
        "tech_level": 6,
        "projection_capability": 2,
        "nato_member": False,
        "nuclear_power": False,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ALLIANCE & ADVERSARY RELATIONSHIPS
# ═══════════════════════════════════════════════════════════════════════════════

RELATIONSHIPS: Dict[Tuple[str, str], Dict[str, Any]] = {
    # NATO Alliances
    ("CTR-USA", "CTR-GBR"): {"type": RelationType.DEFENSE_PACT, "strength": 0.95, "alliance": "NATO/Five Eyes"},
    ("CTR-USA", "CTR-FRA"): {"type": RelationType.DEFENSE_PACT, "strength": 0.85, "alliance": "NATO"},
    ("CTR-USA", "CTR-DEU"): {"type": RelationType.DEFENSE_PACT, "strength": 0.85, "alliance": "NATO"},
    ("CTR-USA", "CTR-JPN"): {"type": RelationType.DEFENSE_PACT, "strength": 0.90, "alliance": "US-Japan Security"},
    ("CTR-USA", "CTR-ISR"): {"type": RelationType.STRATEGIC_PARTNER, "strength": 0.92, "alliance": "Strategic Partner"},
    ("CTR-USA", "CTR-IND"): {"type": RelationType.STRATEGIC_PARTNER, "strength": 0.70, "alliance": "Quad"},
    ("CTR-GBR", "CTR-FRA"): {"type": RelationType.DEFENSE_PACT, "strength": 0.80, "alliance": "NATO"},

    # Russia Sphere
    ("CTR-RUS", "CTR-CHN"): {"type": RelationType.STRATEGIC_PARTNER, "strength": 0.75, "alliance": "SCO"},
    ("CTR-RUS", "CTR-IRN"): {"type": RelationType.STRATEGIC_PARTNER, "strength": 0.65, "alliance": "Strategic Alignment"},

    # China Relationships
    ("CTR-CHN", "CTR-PAK"): {"type": RelationType.STRATEGIC_PARTNER, "strength": 0.85, "alliance": "All-Weather Partner"},

    # Adversarial Relationships
    ("CTR-USA", "CTR-RUS"): {"type": RelationType.ADVERSARY, "strength": -0.70, "tension": "High"},
    ("CTR-USA", "CTR-CHN"): {"type": RelationType.RIVAL, "strength": -0.55, "tension": "Elevated"},
    ("CTR-USA", "CTR-IRN"): {"type": RelationType.ADVERSARY, "strength": -0.80, "tension": "High"},
    ("CTR-IND", "CTR-PAK"): {"type": RelationType.ADVERSARY, "strength": -0.85, "tension": "Critical"},
    ("CTR-IND", "CTR-CHN"): {"type": RelationType.RIVAL, "strength": -0.50, "tension": "Elevated"},
    ("CTR-ISR", "CTR-IRN"): {"type": RelationType.ADVERSARY, "strength": -0.90, "tension": "Critical"},
    ("CTR-RUS", "CTR-UKR"): {"type": RelationType.ADVERSARY, "strength": -0.95, "tension": "Active Conflict"},
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ForceDeployment:
    """Represents a military force deployment."""
    country_id: str
    force_type: ForceType
    location: Tuple[float, float]  # lat, lng
    strength: int  # Personnel or unit count
    status: str  # "deployed", "standby", "mobilizing"
    description: str = ""


@dataclass
class ConflictScenario:
    """A simulated conflict scenario."""
    id: str
    name: str
    phase: ConflictPhase
    primary_actors: List[str]
    secondary_actors: List[str]
    trigger: str
    probability: float
    timeline_days: int
    casualties_estimate: Tuple[int, int]  # min, max
    economic_impact_usd: float
    global_stability_impact: float  # -1.0 to 1.0
    affected_trade_routes: List[str]


@dataclass
class BattlegroundState:
    """Current state of a virtual battleground."""
    scenario_id: str
    phase: ConflictPhase
    day: int
    force_deployments: List[ForceDeployment]
    active_fronts: List[Dict[str, Any]]
    supply_routes: List[Dict[str, Any]]
    casualties: Dict[str, int]
    territory_changes: List[Dict[str, Any]]
    international_response: Dict[str, str]


# ═══════════════════════════════════════════════════════════════════════════════
# BATTLEGROUND ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class BattlegroundEngine:
    """
    Virtual Battleground Engine for strategic scenario simulation.

    Capabilities:
    - Military strength comparison
    - Alliance/adversary network analysis
    - Conflict outcome modeling
    - Force deployment visualization
    - Economic impact assessment
    """

    def __init__(self):
        self.logger = logging.getLogger("battleground_engine")
        self._scenarios: Dict[str, ConflictScenario] = {}

    def get_military_strength(self, country_id: str) -> Dict[str, Any]:
        """Get military strength data for a country."""
        if country_id in MILITARY_STRENGTH:
            data = MILITARY_STRENGTH[country_id].copy()
            data["country_id"] = country_id
            data["rank"] = self._calculate_rank(country_id)
            return data
        return {"country_id": country_id, "error": "Data not available"}

    def compare_forces(
        self,
        country_a: str,
        country_b: str,
        include_allies: bool = False
    ) -> Dict[str, Any]:
        """
        Compare military forces between two countries.
        Optionally includes allied forces.
        """
        force_a = self.get_military_strength(country_a)
        force_b = self.get_military_strength(country_b)

        if "error" in force_a or "error" in force_b:
            return {"error": "Insufficient data for comparison"}

        # Calculate weighted comparison
        comparison = {
            "country_a": {
                "id": country_a,
                "name": force_a.get("name", country_a),
                "power_index": force_a.get("power_index", 1.0),
                "total_personnel": force_a.get("active_personnel", 0) + force_a.get("reserve_personnel", 0),
                "aircraft": force_a.get("aircraft", 0),
                "tanks": force_a.get("tanks", 0),
                "naval_vessels": force_a.get("naval_vessels", 0),
                "nuclear_capable": force_a.get("nuclear_power", False),
                "tech_level": force_a.get("tech_level", 5),
                "projection": force_a.get("projection_capability", 5),
            },
            "country_b": {
                "id": country_b,
                "name": force_b.get("name", country_b),
                "power_index": force_b.get("power_index", 1.0),
                "total_personnel": force_b.get("active_personnel", 0) + force_b.get("reserve_personnel", 0),
                "aircraft": force_b.get("aircraft", 0),
                "tanks": force_b.get("tanks", 0),
                "naval_vessels": force_b.get("naval_vessels", 0),
                "nuclear_capable": force_b.get("nuclear_power", False),
                "tech_level": force_b.get("tech_level", 5),
                "projection": force_b.get("projection_capability", 5),
            },
        }

        # Calculate advantage scores
        comparison["analysis"] = self._analyze_force_balance(comparison)

        # Include allies if requested
        if include_allies:
            comparison["country_a"]["allies"] = self._get_allies(country_a)
            comparison["country_b"]["allies"] = self._get_allies(country_b)
            comparison["alliance_analysis"] = self._analyze_alliance_balance(
                country_a, country_b
            )

        return comparison

    def get_alliance_network(self) -> Dict[str, Any]:
        """Get the full alliance/adversary network graph."""
        nodes = []
        edges = []

        # Create nodes for all countries with military data
        for country_id, data in MILITARY_STRENGTH.items():
            nodes.append({
                "id": country_id,
                "name": data.get("name", country_id),
                "power_index": data.get("power_index", 1.0),
                "nuclear_power": data.get("nuclear_power", False),
                "nato_member": data.get("nato_member", False),
            })

        # Create edges for relationships
        for (a, b), rel in RELATIONSHIPS.items():
            edges.append({
                "source": a,
                "target": b,
                "type": rel["type"].value if isinstance(rel["type"], RelationType) else rel["type"],
                "strength": rel.get("strength", 0),
                "alliance": rel.get("alliance", ""),
                "tension": rel.get("tension", ""),
            })

        return {
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_countries": len(nodes),
                "alliances": len([e for e in edges if e["strength"] > 0]),
                "adversarial": len([e for e in edges if e["strength"] < 0]),
            },
        }

    def _get_allies(self, country_id: str) -> List[Dict[str, Any]]:
        """Get list of allies for a country."""
        allies = []
        for (a, b), rel in RELATIONSHIPS.items():
            if rel.get("strength", 0) > 0:
                if a == country_id:
                    allies.append({"id": b, "alliance": rel.get("alliance", ""), "strength": rel["strength"]})
                elif b == country_id:
                    allies.append({"id": a, "alliance": rel.get("alliance", ""), "strength": rel["strength"]})
        return allies

    def simulate_conflict(
        self,
        country_a: str,
        country_b: str,
        scenario_type: str = "conventional",
        duration_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Simulate a conflict scenario between two countries.

        Returns:
        - Probability outcomes
        - Casualty estimates
        - Economic impact
        - Global stability effects
        - Map visualization data
        """
        comparison = self.compare_forces(country_a, country_b, include_allies=True)

        if "error" in comparison:
            return comparison

        # Get relationship context
        relationship = self._get_relationship(country_a, country_b)

        # Calculate outcome probabilities
        outcomes = self._calculate_outcome_probabilities(
            comparison, scenario_type, duration_days
        )

        # Generate timeline
        timeline = self._generate_conflict_timeline(
            country_a, country_b, duration_days, outcomes
        )

        # Calculate impacts
        impacts = self._calculate_impacts(country_a, country_b, outcomes, duration_days)

        # Generate map visualization data
        map_layers = self._generate_conflict_map_layers(
            country_a, country_b, outcomes, timeline
        )

        return {
            "scenario": {
                "type": scenario_type,
                "duration_days": duration_days,
                "actors": [country_a, country_b],
                "relationship_context": relationship,
            },
            "force_comparison": comparison,
            "outcome_probabilities": outcomes,
            "timeline": timeline,
            "impacts": impacts,
            "map_visualization": map_layers,
            "warnings": self._generate_warnings(country_a, country_b, comparison),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_rank(self, country_id: str) -> int:
        """Calculate global military rank."""
        sorted_countries = sorted(
            MILITARY_STRENGTH.items(),
            key=lambda x: x[1].get("power_index", float("inf"))
        )
        for rank, (cid, _) in enumerate(sorted_countries, 1):
            if cid == country_id:
                return rank
        return 999

    def _analyze_force_balance(self, comparison: Dict) -> Dict[str, Any]:
        """Analyze force balance between two countries."""
        a = comparison["country_a"]
        b = comparison["country_b"]

        # Lower power index is stronger
        power_ratio = (1 / a["power_index"]) / (1 / b["power_index"]) if b["power_index"] > 0 else 1

        # Determine advantage
        if power_ratio > 1.3:
            advantage = a["name"]
            advantage_level = "significant"
        elif power_ratio > 1.1:
            advantage = a["name"]
            advantage_level = "moderate"
        elif power_ratio < 0.77:
            advantage = b["name"]
            advantage_level = "significant"
        elif power_ratio < 0.91:
            advantage = b["name"]
            advantage_level = "moderate"
        else:
            advantage = "Neither (contested)"
            advantage_level = "balanced"

        return {
            "power_ratio": round(power_ratio, 2),
            "advantage": advantage,
            "advantage_level": advantage_level,
            "personnel_ratio": round(a["total_personnel"] / max(b["total_personnel"], 1), 2),
            "air_superiority": a["name"] if a["aircraft"] > b["aircraft"] else b["name"],
            "naval_superiority": a["name"] if a["naval_vessels"] > b["naval_vessels"] else b["name"],
            "tech_advantage": a["name"] if a["tech_level"] > b["tech_level"] else b["name"],
            "nuclear_parity": a["nuclear_capable"] and b["nuclear_capable"],
        }

    def _analyze_alliance_balance(self, country_a: str, country_b: str) -> Dict[str, Any]:
        """Analyze alliance strength for both sides."""
        allies_a = self._get_allies(country_a)
        allies_b = self._get_allies(country_b)

        # Calculate combined strength
        strength_a = 1.0  # Base country
        for ally in allies_a:
            if ally["id"] in MILITARY_STRENGTH:
                # Inverse power index (lower is stronger)
                strength_a += (1 / MILITARY_STRENGTH[ally["id"]].get("power_index", 1)) * ally["strength"]

        strength_b = 1.0
        for ally in allies_b:
            if ally["id"] in MILITARY_STRENGTH:
                strength_b += (1 / MILITARY_STRENGTH[ally["id"]].get("power_index", 1)) * ally["strength"]

        return {
            "alliance_count_a": len(allies_a),
            "alliance_count_b": len(allies_b),
            "combined_strength_a": round(strength_a, 2),
            "combined_strength_b": round(strength_b, 2),
            "alliance_advantage": country_a if strength_a > strength_b else country_b,
        }

    def _get_relationship(self, country_a: str, country_b: str) -> Dict[str, Any]:
        """Get relationship context between two countries."""
        key = (country_a, country_b)
        key_rev = (country_b, country_a)

        if key in RELATIONSHIPS:
            rel = RELATIONSHIPS[key]
            return {
                "type": rel["type"].value if isinstance(rel["type"], RelationType) else rel["type"],
                "strength": rel.get("strength", 0),
                "context": rel.get("alliance", rel.get("tension", "Unknown")),
            }
        elif key_rev in RELATIONSHIPS:
            rel = RELATIONSHIPS[key_rev]
            return {
                "type": rel["type"].value if isinstance(rel["type"], RelationType) else rel["type"],
                "strength": rel.get("strength", 0),
                "context": rel.get("alliance", rel.get("tension", "Unknown")),
            }
        return {"type": "neutral", "strength": 0, "context": "No direct relationship"}

    def _calculate_outcome_probabilities(
        self,
        comparison: Dict,
        scenario_type: str,
        duration_days: int
    ) -> Dict[str, Any]:
        """Calculate probability of various conflict outcomes."""
        analysis = comparison.get("analysis", {})
        power_ratio = analysis.get("power_ratio", 1.0)

        # Base probabilities modified by power ratio
        if power_ratio > 1.5:
            decisive_a = 0.55
            limited_a = 0.25
            stalemate = 0.12
            limited_b = 0.05
            decisive_b = 0.03
        elif power_ratio > 1.2:
            decisive_a = 0.35
            limited_a = 0.30
            stalemate = 0.20
            limited_b = 0.10
            decisive_b = 0.05
        elif power_ratio > 0.8:
            decisive_a = 0.15
            limited_a = 0.25
            stalemate = 0.35
            limited_b = 0.15
            decisive_b = 0.10
        else:
            decisive_a = 0.05
            limited_a = 0.10
            stalemate = 0.20
            limited_b = 0.30
            decisive_b = 0.35

        # Nuclear factor - increases stalemate probability
        if analysis.get("nuclear_parity"):
            stalemate += 0.25
            decisive_a *= 0.5
            decisive_b *= 0.5
            # Normalize
            total = decisive_a + limited_a + stalemate + limited_b + decisive_b
            decisive_a /= total
            limited_a /= total
            stalemate /= total
            limited_b /= total
            decisive_b /= total

        country_a = comparison["country_a"]["name"]
        country_b = comparison["country_b"]["name"]

        return {
            f"decisive_victory_{country_a}": round(decisive_a, 3),
            f"limited_victory_{country_a}": round(limited_a, 3),
            "stalemate": round(stalemate, 3),
            f"limited_victory_{country_b}": round(limited_b, 3),
            f"decisive_victory_{country_b}": round(decisive_b, 3),
            "nuclear_escalation_risk": 0.05 if analysis.get("nuclear_parity") else 0.01,
            "international_intervention_probability": 0.65,
        }

    def _generate_conflict_timeline(
        self,
        country_a: str,
        country_b: str,
        duration_days: int,
        outcomes: Dict
    ) -> List[Dict[str, Any]]:
        """Generate projected conflict timeline."""
        name_a = MILITARY_STRENGTH.get(country_a, {}).get("name", country_a)
        name_b = MILITARY_STRENGTH.get(country_b, {}).get("name", country_b)

        timeline = [
            {
                "day": 1,
                "phase": "Escalation",
                "event": "Initial hostilities begin",
                "description": f"Military confrontation escalates between {name_a} and {name_b}",
                "impact": "High",
            },
            {
                "day": 3,
                "phase": "Initial Combat",
                "event": "Air and missile strikes",
                "description": "Both sides engage in strategic strikes on military infrastructure",
                "impact": "High",
            },
            {
                "day": 7,
                "phase": "Ground Operations",
                "event": "Ground forces engage",
                "description": "Initial territorial battles begin along borders",
                "impact": "High",
            },
            {
                "day": 14,
                "phase": "Sustained Conflict",
                "event": "International response",
                "description": "UN/NATO/Regional bodies respond with diplomatic pressure",
                "impact": "Medium",
            },
        ]

        if duration_days > 21:
            timeline.append({
                "day": 21,
                "phase": "Attrition",
                "event": "Resource depletion begins",
                "description": "Both sides face logistical challenges and supply constraints",
                "impact": "Medium",
            })

        if duration_days > 30:
            timeline.append({
                "day": 30,
                "phase": "De-escalation Pressure",
                "event": "Ceasefire negotiations",
                "description": "International mediation efforts intensify",
                "impact": "Medium",
            })

        return timeline

    def _calculate_impacts(
        self,
        country_a: str,
        country_b: str,
        outcomes: Dict,
        duration_days: int
    ) -> Dict[str, Any]:
        """Calculate economic and humanitarian impacts."""
        gdp_a = MILITARY_STRENGTH.get(country_a, {}).get("gdp_usd", 1_000_000_000_000)
        gdp_b = MILITARY_STRENGTH.get(country_b, {}).get("gdp_usd", 1_000_000_000_000)

        # Estimate daily GDP loss during conflict (2-5% of daily GDP)
        daily_loss_rate = 0.03 / 365
        economic_cost = (gdp_a + gdp_b) * daily_loss_rate * duration_days

        # Casualty estimates based on duration and force sizes
        personnel_a = MILITARY_STRENGTH.get(country_a, {}).get("active_personnel", 100000)
        personnel_b = MILITARY_STRENGTH.get(country_b, {}).get("active_personnel", 100000)
        base_casualties = int((personnel_a + personnel_b) * 0.001 * (duration_days / 7))

        return {
            "economic_impact_usd": round(economic_cost, 2),
            "estimated_military_casualties": {
                "low": int(base_casualties * 0.5),
                "high": int(base_casualties * 2.5),
            },
            "estimated_civilian_casualties": {
                "low": int(base_casualties * 0.2),
                "high": int(base_casualties * 1.5),
            },
            "displaced_persons_estimate": int(base_casualties * 10),
            "global_trade_disruption_pct": min(15, duration_days * 0.3),
            "energy_price_impact_pct": min(40, duration_days * 1.0),
            "global_stability_score_change": -0.1 * (duration_days / 30),
        }

    def _generate_conflict_map_layers(
        self,
        country_a: str,
        country_b: str,
        outcomes: Dict,
        timeline: List
    ) -> List[Dict[str, Any]]:
        """Generate map visualization layers for conflict scenario."""
        layers = []

        # Get country coordinates (approximate capitals)
        country_coords = {
            "CTR-USA": (38.9, -77.0),
            "CTR-RUS": (55.75, 37.6),
            "CTR-CHN": (39.9, 116.4),
            "CTR-IND": (28.6, 77.2),
            "CTR-PAK": (33.7, 73.1),
            "CTR-UKR": (50.45, 30.5),
            "CTR-IRN": (35.7, 51.4),
            "CTR-ISR": (31.8, 35.2),
            "CTR-GBR": (51.5, -0.13),
            "CTR-FRA": (48.9, 2.35),
            "CTR-DEU": (52.5, 13.4),
            "CTR-JPN": (35.7, 139.7),
        }

        coord_a = country_coords.get(country_a, (0, 0))
        coord_b = country_coords.get(country_b, (0, 0))

        # Conflict zone layer
        layers.append({
            "type": "conflict_zone",
            "name": "Conflict Zone",
            "description": "Active conflict area between belligerents",
            "data": {
                "actors": [country_a, country_b],
                "center": ((coord_a[0] + coord_b[0]) / 2, (coord_a[1] + coord_b[1]) / 2),
                "radius_km": 500,
                "intensity": "high",
            },
            "color": "#ef4444",
            "visible": True,
        })

        # Force deployment markers
        layers.append({
            "type": "force_deployment",
            "name": "Force Deployments",
            "description": "Military force positions",
            "data": [
                {"country_id": country_a, "lat": coord_a[0], "lng": coord_a[1], "type": "ground", "strength": "heavy"},
                {"country_id": country_b, "lat": coord_b[0], "lng": coord_b[1], "type": "ground", "strength": "heavy"},
            ],
            "color": "#f59e0b",
            "visible": True,
        })

        # Front line (approximation)
        layers.append({
            "type": "frontline",
            "name": "Front Lines",
            "description": "Active combat fronts",
            "data": {
                "start": coord_a,
                "end": coord_b,
                "status": "contested",
            },
            "color": "#dc2626",
            "visible": True,
        })

        return layers

    def _generate_warnings(
        self,
        country_a: str,
        country_b: str,
        comparison: Dict
    ) -> List[str]:
        """Generate strategic warnings for the scenario."""
        warnings = []
        analysis = comparison.get("analysis", {})

        if analysis.get("nuclear_parity"):
            warnings.append("CRITICAL: Both nations possess nuclear weapons - escalation risk is severe")

        if MILITARY_STRENGTH.get(country_a, {}).get("nato_member") or MILITARY_STRENGTH.get(country_b, {}).get("nato_member"):
            warnings.append("WARNING: NATO involvement possible - potential for wider conflict")

        allies_a = comparison.get("country_a", {}).get("allies", [])
        allies_b = comparison.get("country_b", {}).get("allies", [])
        if len(allies_a) > 2 or len(allies_b) > 2:
            warnings.append("CAUTION: Multiple alliance commitments could trigger cascade effect")

        return warnings


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL ENGINE INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

battleground_engine = BattlegroundEngine()
