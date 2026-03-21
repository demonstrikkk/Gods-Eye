"""
JanGraph OS - Global Ontology Seed
Creates a world-scale intelligence dataset that can coexist with the civic demo
dataset without changing the local governance model.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

COUNTRIES: List[Dict] = [
    {
        "id": "CTR-IND",
        "name": "India",
        "region": "South Asia",
        "lat": 20.5937,
        "lng": 78.9629,
        "risk_index": 54,
        "influence_index": 88,
        "sentiment": 63,
        "stability": "Watch",
        "pressure": "Border posture, energy prices, monsoon volatility",
        "top_domains": ["Geopolitics", "Climate", "Technology"],
        "key_entities": ["BRICS", "ISRO", "Indian Ocean", "Digital Public Infrastructure"],
    },
    {
        "id": "CTR-USA",
        "name": "United States",
        "region": "North America",
        "lat": 38.9072,
        "lng": -77.0369,
        "risk_index": 58,
        "influence_index": 96,
        "sentiment": 57,
        "stability": "Watch",
        "pressure": "Rates, elections, alliance posture",
        "top_domains": ["Economics", "Defense", "Technology"],
        "key_entities": ["Federal Reserve", "NATO", "Silicon Valley", "Pacific Command"],
    },
    {
        "id": "CTR-CHN",
        "name": "China",
        "region": "East Asia",
        "lat": 39.9042,
        "lng": 116.4074,
        "risk_index": 66,
        "influence_index": 94,
        "sentiment": 51,
        "stability": "Elevated",
        "pressure": "Trade decoupling, maritime tension, industrial slowdown",
        "top_domains": ["Geopolitics", "Trade", "Technology"],
        "key_entities": ["Belt and Road", "South China Sea", "Semiconductors", "PLA Navy"],
    },
    {
        "id": "CTR-GBR",
        "name": "United Kingdom",
        "region": "Europe",
        "lat": 51.5072,
        "lng": -0.1276,
        "risk_index": 43,
        "influence_index": 77,
        "sentiment": 59,
        "stability": "Stable",
        "pressure": "Inflation persistence, maritime security",
        "top_domains": ["Finance", "Defense", "Society"],
        "key_entities": ["City of London", "North Sea", "Royal Navy"],
    },
    {
        "id": "CTR-DEU",
        "name": "Germany",
        "region": "Europe",
        "lat": 52.52,
        "lng": 13.405,
        "risk_index": 47,
        "influence_index": 80,
        "sentiment": 61,
        "stability": "Stable",
        "pressure": "Manufacturing demand, energy transition",
        "top_domains": ["Industry", "Energy", "Trade"],
        "key_entities": ["EU", "Rhine corridor", "Industrial exports"],
    },
    {
        "id": "CTR-UKR",
        "name": "Ukraine",
        "region": "Eastern Europe",
        "lat": 50.4501,
        "lng": 30.5234,
        "risk_index": 86,
        "influence_index": 69,
        "sentiment": 39,
        "stability": "Critical",
        "pressure": "Conflict persistence, infrastructure strain",
        "top_domains": ["Defense", "Logistics", "Humanitarian"],
        "key_entities": ["Black Sea", "Air defense", "Grain exports"],
    },
    {
        "id": "CTR-RUS",
        "name": "Russia",
        "region": "Eurasia",
        "lat": 55.7558,
        "lng": 37.6173,
        "risk_index": 78,
        "influence_index": 85,
        "sentiment": 41,
        "stability": "Critical",
        "pressure": "Conflict economy, sanctions adaptation",
        "top_domains": ["Defense", "Energy", "Geopolitics"],
        "key_entities": ["Arctic", "Sanctions", "Energy exports"],
    },
    {
        "id": "CTR-ARE",
        "name": "United Arab Emirates",
        "region": "Middle East",
        "lat": 24.4539,
        "lng": 54.3773,
        "risk_index": 39,
        "influence_index": 73,
        "sentiment": 67,
        "stability": "Stable",
        "pressure": "Shipping lanes, capital flows",
        "top_domains": ["Energy", "Trade", "Logistics"],
        "key_entities": ["Gulf shipping", "Sovereign wealth", "Aviation"],
    },
    {
        "id": "CTR-SAU",
        "name": "Saudi Arabia",
        "region": "Middle East",
        "lat": 24.7136,
        "lng": 46.6753,
        "risk_index": 52,
        "influence_index": 79,
        "sentiment": 62,
        "stability": "Watch",
        "pressure": "Oil balancing, Red Sea routing",
        "top_domains": ["Energy", "Defense", "Infrastructure"],
        "key_entities": ["OPEC+", "Red Sea", "Vision 2030"],
    },
    {
        "id": "CTR-ZAF",
        "name": "South Africa",
        "region": "Africa",
        "lat": -25.7479,
        "lng": 28.2293,
        "risk_index": 57,
        "influence_index": 63,
        "sentiment": 49,
        "stability": "Watch",
        "pressure": "Power reliability, logistics bottlenecks",
        "top_domains": ["Energy", "Society", "Trade"],
        "key_entities": ["BRICS", "Ports", "Grid stability"],
    },
    {
        "id": "CTR-BRA",
        "name": "Brazil",
        "region": "Latin America",
        "lat": -15.7939,
        "lng": -47.8828,
        "risk_index": 48,
        "influence_index": 74,
        "sentiment": 58,
        "stability": "Stable",
        "pressure": "Climate pressure, commodity swings",
        "top_domains": ["Climate", "Agriculture", "Trade"],
        "key_entities": ["Amazon", "Soy corridors", "BRICS"],
    },
    {
        "id": "CTR-SGP",
        "name": "Singapore",
        "region": "Southeast Asia",
        "lat": 1.3521,
        "lng": 103.8198,
        "risk_index": 28,
        "influence_index": 71,
        "sentiment": 71,
        "stability": "Stable",
        "pressure": "Maritime exposure, trade sensitivity",
        "top_domains": ["Trade", "Technology", "Finance"],
        "key_entities": ["Malacca Strait", "Port logistics", "Semiconductor routing"],
    },
]

SIGNALS: List[Dict] = [
    {
        "id": "SIG-001",
        "country_id": "CTR-UKR",
        "title": "Black Sea insurance costs climb again",
        "summary": "Shipping risk premiums are rising around grain routes and secondary ports.",
        "category": "Geopolitics",
        "severity": "High",
        "source": "Maritime Monitor",
        "time": "LIVE",
        "lat": 46.4825,
        "lng": 30.7233,
    },
    {
        "id": "SIG-002",
        "country_id": "CTR-SAU",
        "title": "Oil balancing posture tightens across Gulf producers",
        "summary": "Energy markets remain sensitive to output coordination and Red Sea disruptions.",
        "category": "Economics",
        "severity": "Medium",
        "source": "Energy Desk",
        "time": "LIVE",
        "lat": 24.7136,
        "lng": 46.6753,
    },
    {
        "id": "SIG-003",
        "country_id": "CTR-IND",
        "title": "Heatwave pressure building ahead of pre-monsoon cycle",
        "summary": "Climate volatility is increasing stress on power demand and agriculture planning.",
        "category": "Climate",
        "severity": "High",
        "source": "Climate Grid",
        "time": "LIVE",
        "lat": 28.6139,
        "lng": 77.209,
    },
    {
        "id": "SIG-004",
        "country_id": "CTR-CHN",
        "title": "Industrial export routing shifts toward alternate maritime lanes",
        "summary": "Trade actors are diversifying flows as tariff and security conditions shift.",
        "category": "Trade",
        "severity": "Medium",
        "source": "Supply Chain Wire",
        "time": "LIVE",
        "lat": 31.2304,
        "lng": 121.4737,
    },
    {
        "id": "SIG-005",
        "country_id": "CTR-USA",
        "title": "Higher-for-longer rate narrative strengthens dollar pressure",
        "summary": "Emerging market financing risk remains sensitive to US policy guidance.",
        "category": "Economics",
        "severity": "Medium",
        "source": "Macro Desk",
        "time": "LIVE",
        "lat": 38.8977,
        "lng": -77.0365,
    },
    {
        "id": "SIG-006",
        "country_id": "CTR-BRA",
        "title": "Amazon fire clusters widen into export logistics concern",
        "summary": "Climate stress is no longer isolated to ecology; it is now a transport and supply issue.",
        "category": "Climate",
        "severity": "High",
        "source": "Geo Ecology Watch",
        "time": "LIVE",
        "lat": -3.119,
        "lng": -60.0217,
    },
    {
        "id": "SIG-007",
        "country_id": "CTR-ZAF",
        "title": "Grid unreliability re-enters mining throughput calculations",
        "summary": "Infrastructure fragility is bleeding into export confidence.",
        "category": "Infrastructure",
        "severity": "Medium",
        "source": "Africa Infra Monitor",
        "time": "LIVE",
        "lat": -26.2041,
        "lng": 28.0473,
    },
    {
        "id": "SIG-008",
        "country_id": "CTR-SGP",
        "title": "Semiconductor logistics cluster sees rerouting demand",
        "summary": "Trade and chip-supply resilience planning are tightening across Southeast Asia.",
        "category": "Technology",
        "severity": "Low",
        "source": "Tech Flow",
        "time": "LIVE",
        "lat": 1.2903,
        "lng": 103.8519,
    },
    {
        "id": "SIG-009",
        "country_id": "CTR-DEU",
        "title": "Manufacturing softness persists despite energy stabilization",
        "summary": "Industrial demand recovery remains uneven across the core European engine.",
        "category": "Industry",
        "severity": "Medium",
        "source": "Euro Industrial Watch",
        "time": "LIVE",
        "lat": 52.52,
        "lng": 13.405,
    },
    {
        "id": "SIG-010",
        "country_id": "CTR-RUS",
        "title": "Arctic energy shipping draws added strategic scrutiny",
        "summary": "Northern routing now intersects sanctions adaptation and defense posture.",
        "category": "Defense",
        "severity": "High",
        "source": "Polar Security Desk",
        "time": "LIVE",
        "lat": 69.3558,
        "lng": 88.1893,
    },
    {
        "id": "SIG-011",
        "country_id": "CTR-ARE",
        "title": "Gulf logistics hubs absorb spillover from disrupted sea lanes",
        "summary": "Regional ports are acting as shock absorbers for rerouted cargo networks.",
        "category": "Trade",
        "severity": "Medium",
        "source": "Port Intelligence",
        "time": "LIVE",
        "lat": 25.2048,
        "lng": 55.2708,
    },
    {
        "id": "SIG-012",
        "country_id": "CTR-GBR",
        "title": "Defense procurement cycle lengthens under budget stress",
        "summary": "Capability planning remains active but timelines are stretching.",
        "category": "Defense",
        "severity": "Low",
        "source": "Allied Readiness Monitor",
        "time": "LIVE",
        "lat": 51.5072,
        "lng": -0.1276,
    },
]

CORRIDORS: List[Dict] = [
    {
        "id": "COR-IND-SGP",
        "label": "Indo-Pacific Tech Spine",
        "category": "Technology",
        "status": "Growing",
        "weight": 82,
        "from_country": "CTR-IND",
        "to_country": "CTR-SGP",
    },
    {
        "id": "COR-SAU-IND",
        "label": "Energy Security Arc",
        "category": "Energy",
        "status": "Stressed",
        "weight": 77,
        "from_country": "CTR-SAU",
        "to_country": "CTR-IND",
    },
    {
        "id": "COR-USA-GBR",
        "label": "Atlantic Security Bridge",
        "category": "Defense",
        "status": "Stable",
        "weight": 74,
        "from_country": "CTR-USA",
        "to_country": "CTR-GBR",
    },
    {
        "id": "COR-CHN-ARE",
        "label": "Maritime Capital Route",
        "category": "Trade",
        "status": "Elevated",
        "weight": 69,
        "from_country": "CTR-CHN",
        "to_country": "CTR-ARE",
    },
    {
        "id": "COR-BRA-ZAF",
        "label": "South Atlantic Commodity Link",
        "category": "Agriculture",
        "status": "Stable",
        "weight": 58,
        "from_country": "CTR-BRA",
        "to_country": "CTR-ZAF",
    },
    {
        "id": "COR-DEU-UKR",
        "label": "European Resilience Corridor",
        "category": "Logistics",
        "status": "Critical",
        "weight": 84,
        "from_country": "CTR-DEU",
        "to_country": "CTR-UKR",
    },
]


def build_global_ontology_dataset() -> Dict:
    country_map = {country["id"]: dict(country) for country in COUNTRIES}

    for country in country_map.values():
        country["active_signals"] = 0

    for signal in SIGNALS:
        country = country_map.get(signal["country_id"])
        if country:
            country["active_signals"] += 1

    countries = list(country_map.values())
    high_risk = [country for country in countries if country["risk_index"] >= 70]

    nodes = []
    links = []

    domain_ids = set()
    for country in countries:
        nodes.append(
            {
                "id": country["id"],
                "group": "Country",
                "label": country["name"],
                "val": max(6, round(country["influence_index"] / 12)),
                "color": "#ef4444" if country["risk_index"] >= 70 else "#3b82f6" if country["risk_index"] >= 50 else "#10b981",
            }
        )
        for domain in country["top_domains"]:
            domain_id = f"DOMAIN-{domain.upper()}"
            if domain_id not in domain_ids:
                nodes.append(
                    {
                        "id": domain_id,
                        "group": "Domain",
                        "label": domain,
                        "val": 7,
                        "color": "#a855f7",
                    }
                )
                domain_ids.add(domain_id)
            links.append({"source": country["id"], "target": domain_id, "label": "SHAPED_BY"})

    for signal in SIGNALS:
        node_id = f"SIGNAL-{signal['id']}"
        nodes.append(
            {
                "id": node_id,
                "group": "Signal",
                "label": signal["title"],
                "val": 4,
                "color": "#f59e0b" if signal["severity"] == "High" else "#38bdf8",
            }
        )
        links.append({"source": signal["country_id"], "target": node_id, "label": "EMITS"})

    for corridor in CORRIDORS:
        links.append(
            {
                "source": corridor["from_country"],
                "target": corridor["to_country"],
                "label": corridor["category"].upper(),
            }
        )

    return {
        "overview": {
            "total_countries": len(countries),
            "total_signals": len(SIGNALS),
            "critical_zones": len(high_risk),
            "active_corridors": len(CORRIDORS),
            "systemic_stress": round(sum(country["risk_index"] for country in countries) / len(countries), 1),
            "updated_at": datetime.now().isoformat(),
        },
        "countries": countries,
        "signals": SIGNALS,
        "corridors": CORRIDORS,
        "graph": {"nodes": nodes, "links": links},
    }
