"""
Gods-Eye OS — Country Workspace Aggregator
===========================================

Aggregates comprehensive data about a specific country for deep-dive analysis.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("country_workspace")


class CountryWorkspaceAggregator:
    """
    Aggregates all available data about a country for comprehensive analysis.

    Provides:
    - Government officials and political structure
    - Military capabilities and comparisons
    - Recent signals and events
    - Electoral data
    - Economic indicators
    - Relationships with other countries
    """

    def __init__(self):
        self.logger = logging.getLogger("country_workspace")

    def get_country_workspace(self, country_id: str) -> Dict[str, Any]:
        """
        Get comprehensive workspace data for a country.

        Args:
            country_id: Country identifier (e.g., "CTR-IND")

        Returns:
            Complete country workspace data
        """
        from app.services.runtime_intelligence import runtime_engine
        from app.data.officials_data import officials_engine
        from app.services.battleground_engine import battleground_engine

        workspace = {
            "country_id": country_id,
            "country_name": self._get_country_name(country_id),
            "last_updated": None,
        }

        # Get core country data
        country_data = runtime_engine.get_country(country_id)
        if country_data:
            workspace["overview"] = {
                "name": country_data.get("name", ""),
                "region": country_data.get("region", ""),
                "macro_region": country_data.get("macro_region", ""),
                "capital": country_data.get("capital", ""),
                "population": country_data.get("population", 0),
                "risk_index": country_data.get("risk_index", 0),
                "influence_index": country_data.get("influence_index", 0),
                "sentiment": country_data.get("sentiment", 0),
                "stability": country_data.get("stability", ""),
                "pressure": country_data.get("pressure", ""),
                "top_domains": country_data.get("top_domains", []),
                "active_signals": country_data.get("active_signals", 0),
                "lat": country_data.get("lat"),
                "lng": country_data.get("lng"),
            }

        # Get government officials
        officials = officials_engine.get_officials_by_country(country_id)
        workspace["government"] = {
            "officials": officials,
            "officials_count": len(officials),
            "head_of_state": next((o for o in officials if o["role"] in ("head_of_state", "head_of_government")), None),
            "ministers": [o for o in officials if o["role"] == "minister"],
        }

        # Get political parties
        parties = officials_engine.get_parties_by_country(country_id)
        workspace["political_landscape"] = {
            "parties": parties,
            "governing_party": next((p for p in parties if p.get("governing")), None),
            "total_parties": len(parties),
        }

        # Get elections
        elections = officials_engine.get_elections_by_country(country_id)
        workspace["electoral_calendar"] = {
            "elections": elections,
            "upcoming": [e for e in elections if e["status"] == "upcoming"],
            "recent": [e for e in elections if e["status"] == "completed"],
        }

        # Get military capabilities
        military = battleground_engine.get_military_strength(country_id)
        workspace["military_capabilities"] = military if not military.get("error") else None

        # Get signals and events
        country_analysis = runtime_engine.get_country_analysis(country_id)
        if country_analysis:
            workspace["intelligence"] = {
                "signals": country_analysis.get("signals", []),
                "assets": country_analysis.get("assets", []),
                "feeds": country_analysis.get("feeds", []),
                "signal_count": len(country_analysis.get("signals", [])),
                "asset_count": len(country_analysis.get("assets", [])),
                "summary": country_analysis.get("summary", ""),
                "risk_factors": country_analysis.get("risk_factors", []),
                "opportunities": country_analysis.get("opportunities", []),
            }

        # Get relationships
        workspace["relationships"] = self._get_country_relationships(country_id, battleground_engine)

        # Get key rivals for comparison
        workspace["key_rivals"] = self._identify_key_rivals(country_id, battleground_engine)

        return workspace

    def get_country_comparison(
        self,
        country_a: str,
        country_b: str,
        include_military: bool = True,
        include_political: bool = True
    ) -> Dict[str, Any]:
        """
        Compare two countries across multiple dimensions.

        Args:
            country_a: First country ID
            country_b: Second country ID
            include_military: Include military comparison
            include_political: Include political comparison

        Returns:
            Comprehensive comparison data
        """
        from app.services.runtime_intelligence import runtime_engine
        from app.data.officials_data import officials_engine
        from app.services.battleground_engine import battleground_engine

        comparison = {
            "country_a": country_a,
            "country_b": country_b,
            "country_a_name": self._get_country_name(country_a),
            "country_b_name": self._get_country_name(country_b),
        }

        # Basic metrics comparison
        data_a = runtime_engine.get_country(country_a)
        data_b = runtime_engine.get_country(country_b)

        if data_a and data_b:
            comparison["overview"] = {
                "risk_index": {
                    "a": data_a.get("risk_index", 0),
                    "b": data_b.get("risk_index", 0),
                    "difference": data_a.get("risk_index", 0) - data_b.get("risk_index", 0),
                },
                "influence_index": {
                    "a": data_a.get("influence_index", 0),
                    "b": data_b.get("influence_index", 0),
                    "difference": data_a.get("influence_index", 0) - data_b.get("influence_index", 0),
                },
                "sentiment": {
                    "a": data_a.get("sentiment", 0),
                    "b": data_b.get("sentiment", 0),
                    "difference": data_a.get("sentiment", 0) - data_b.get("sentiment", 0),
                },
                "active_signals": {
                    "a": data_a.get("active_signals", 0),
                    "b": data_b.get("active_signals", 0),
                },
                "population": {
                    "a": data_a.get("population", 0),
                    "b": data_b.get("population", 0),
                },
            }

        # Military comparison
        if include_military:
            military_comp = battleground_engine.compare_forces(country_a, country_b, include_allies=True)
            comparison["military"] = military_comp if not military_comp.get("error") else None

        # Political comparison
        if include_political:
            officials_a = officials_engine.get_officials_by_country(country_a)
            officials_b = officials_engine.get_officials_by_country(country_b)

            comparison["political"] = {
                "officials_count": {
                    "a": len(officials_a),
                    "b": len(officials_b),
                },
                "head_of_state_a": next((o for o in officials_a if o["role"] in ("head_of_state", "head_of_government")), None),
                "head_of_state_b": next((o for o in officials_b if o["role"] in ("head_of_state", "head_of_government")), None),
            }

        # Relationship status
        relationship = self._get_bilateral_relationship(country_a, country_b, battleground_engine)
        comparison["relationship"] = relationship

        return comparison

    def _get_country_name(self, country_id: str) -> str:
        """Get human-readable country name."""
        from app.services.runtime_intelligence import runtime_engine

        country = runtime_engine.get_country(country_id)
        if country:
            return country.get("name", country_id.replace("CTR-", ""))
        return country_id.replace("CTR-", "")

    def _get_country_relationships(
        self,
        country_id: str,
        battleground_engine: Any
    ) -> Dict[str, Any]:
        """Get country's relationships with other nations."""
        from app.services.battleground_engine import RELATIONSHIPS

        allies = []
        adversaries = []
        neutral = []

        for (a, b), rel in RELATIONSHIPS.items():
            if a == country_id or b == country_id:
                other = b if a == country_id else a
                other_name = self._get_country_name(other)

                rel_data = {
                    "country_id": other,
                    "country_name": other_name,
                    "type": rel["type"].value if hasattr(rel["type"], "value") else rel["type"],
                    "strength": rel.get("strength", 0),
                    "context": rel.get("alliance", rel.get("tension", "")),
                }

                if rel.get("strength", 0) > 0:
                    allies.append(rel_data)
                elif rel.get("strength", 0) < 0:
                    adversaries.append(rel_data)
                else:
                    neutral.append(rel_data)

        return {
            "allies": sorted(allies, key=lambda x: x["strength"], reverse=True),
            "adversaries": sorted(adversaries, key=lambda x: x["strength"]),
            "neutral": neutral,
            "total_allies": len(allies),
            "total_adversaries": len(adversaries),
        }

    def _identify_key_rivals(
        self,
        country_id: str,
        battleground_engine: Any
    ) -> List[str]:
        """Identify key rival countries for comparison."""
        from app.services.battleground_engine import RELATIONSHIPS

        rivals = []
        for (a, b), rel in RELATIONSHIPS.items():
            if (a == country_id or b == country_id) and rel.get("strength", 0) < 0:
                rivals.append(b if a == country_id else a)

        # Limit to top 3 rivals
        return rivals[:3]

    def _get_bilateral_relationship(
        self,
        country_a: str,
        country_b: str,
        battleground_engine: Any
    ) -> Dict[str, Any]:
        """Get relationship status between two countries."""
        from app.services.battleground_engine import RELATIONSHIPS

        key = (country_a, country_b)
        key_rev = (country_b, country_a)

        if key in RELATIONSHIPS:
            rel = RELATIONSHIPS[key]
        elif key_rev in RELATIONSHIPS:
            rel = RELATIONSHIPS[key_rev]
        else:
            return {
                "type": "neutral",
                "strength": 0,
                "context": "No direct relationship data",
            }

        return {
            "type": rel["type"].value if hasattr(rel["type"], "value") else rel["type"],
            "strength": rel.get("strength", 0),
            "context": rel.get("alliance", rel.get("tension", "Unknown")),
        }


# Global instance
country_workspace_aggregator = CountryWorkspaceAggregator()
