"""
Intent Parser

Parses natural language queries into structured intent for visual intelligence.
Uses rule-based parsing, keyword mapping, and domain ontology.
"""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from app.models.visual_intelligence import (
    ParsedIntent,
    DomainType,
    IntentType,
    ChartType,
    DiagramType,
    MapFeatureType,
    TimeRange,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Geographic Data
# =============================================================================

COUNTRY_ALIASES = {
    # Common names to standardized names
    "india": "India",
    "china": "China",
    "usa": "United States",
    "us": "United States",
    "united states": "United States",
    "america": "United States",
    "uk": "United Kingdom",
    "britain": "United Kingdom",
    "england": "United Kingdom",
    "russia": "Russia",
    "japan": "Japan",
    "germany": "Germany",
    "france": "France",
    "brazil": "Brazil",
    "pakistan": "Pakistan",
    "bangladesh": "Bangladesh",
    "indonesia": "Indonesia",
    "nigeria": "Nigeria",
    "mexico": "Mexico",
    "canada": "Canada",
    "australia": "Australia",
    "south korea": "South Korea",
    "korea": "South Korea",
    "north korea": "North Korea",
    "saudi arabia": "Saudi Arabia",
    "iran": "Iran",
    "turkey": "Turkey",
    "egypt": "Egypt",
    "south africa": "South Africa",
    "vietnam": "Vietnam",
    "thailand": "Thailand",
    "singapore": "Singapore",
    "malaysia": "Malaysia",
    "uae": "United Arab Emirates",
    "israel": "Israel",
    "italy": "Italy",
    "spain": "Spain",
    "poland": "Poland",
    "ukraine": "Ukraine",
    "netherlands": "Netherlands",
    "belgium": "Belgium",
    "sweden": "Sweden",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "switzerland": "Switzerland",
    "austria": "Austria",
    "greece": "Greece",
    "portugal": "Portugal",
    "argentina": "Argentina",
    "chile": "Chile",
    "colombia": "Colombia",
    "peru": "Peru",
    "venezuela": "Venezuela",
    "philippines": "Philippines",
    "taiwan": "Taiwan",
    "sri lanka": "Sri Lanka",
    "nepal": "Nepal",
    "myanmar": "Myanmar",
    "afghanistan": "Afghanistan",
    "iraq": "Iraq",
    "syria": "Syria",
    "yemen": "Yemen",
    "ethiopia": "Ethiopia",
    "kenya": "Kenya",
    "ghana": "Ghana",
    "morocco": "Morocco",
    "algeria": "Algeria",
}

REGION_KEYWORDS = {
    "south asia": ["India", "Pakistan", "Bangladesh", "Sri Lanka", "Nepal"],
    "southeast asia": ["Vietnam", "Thailand", "Indonesia", "Malaysia", "Philippines", "Singapore"],
    "east asia": ["China", "Japan", "South Korea", "Taiwan"],
    "middle east": ["Saudi Arabia", "Iran", "Iraq", "Israel", "UAE", "Turkey"],
    "europe": ["Germany", "France", "UK", "Italy", "Spain"],
    "north america": ["United States", "Canada", "Mexico"],
    "south america": ["Brazil", "Argentina", "Chile", "Colombia"],
    "africa": ["Nigeria", "South Africa", "Egypt", "Kenya", "Ethiopia"],
    "central asia": ["Kazakhstan", "Uzbekistan", "Turkmenistan"],
    "oceania": ["Australia", "New Zealand"],
    "brics": ["Brazil", "Russia", "India", "China", "South Africa"],
    "g7": ["United States", "United Kingdom", "France", "Germany", "Italy", "Canada", "Japan"],
    "g20": ["United States", "China", "Japan", "Germany", "India", "United Kingdom", "France", "Italy", "Brazil", "Canada"],
    "asean": ["Indonesia", "Thailand", "Singapore", "Malaysia", "Philippines", "Vietnam", "Myanmar", "Cambodia", "Laos", "Brunei"],
    "eu": ["Germany", "France", "Italy", "Spain", "Netherlands", "Belgium", "Poland", "Sweden"],
    "nato": ["United States", "United Kingdom", "France", "Germany", "Canada", "Turkey", "Italy", "Poland"],
}


# =============================================================================
# Domain Keywords
# =============================================================================

DOMAIN_KEYWORDS: Dict[DomainType, List[str]] = {
    DomainType.ECONOMICS: [
        "gdp", "economy", "economic", "inflation", "deflation", "growth",
        "recession", "budget", "fiscal", "monetary", "trade balance", "exports",
        "imports", "currency", "forex", "stock market", "investment", "fdi",
        "unemployment", "employment", "labor", "wage", "income", "poverty",
        "debt", "deficit", "surplus", "interest rate", "central bank", "imf",
        "world bank", "financial", "banking", "credit", "loan", "gdp per capita",
    ],
    DomainType.GEOPOLITICS: [
        "conflict", "war", "military", "defense", "alliance", "sanction",
        "treaty", "diplomacy", "diplomatic", "tension", "dispute", "border",
        "territorial", "sovereignty", "political", "government", "regime",
        "election", "democracy", "authoritarian", "coup", "revolution",
        "insurgency", "terrorism", "security", "nato", "un", "united nations",
    ],
    DomainType.CLIMATE: [
        "climate", "temperature", "weather", "rainfall", "precipitation",
        "drought", "flood", "hurricane", "typhoon", "cyclone", "monsoon",
        "global warming", "carbon", "emissions", "greenhouse", "pollution",
        "environment", "environmental", "sustainability", "renewable",
        "fossil fuel", "deforestation", "biodiversity", "ecosystem",
    ],
    DomainType.INFRASTRUCTURE: [
        "infrastructure", "roads", "highways", "railways", "rail", "ports",
        "airports", "bridges", "tunnels", "construction", "urban", "rural",
        "development", "connectivity", "transport", "transportation",
        "logistics", "supply chain", "warehouse", "distribution",
    ],
    DomainType.DEMOGRAPHICS: [
        "population", "demographic", "birth rate", "death rate", "fertility",
        "mortality", "life expectancy", "aging", "youth", "migration",
        "immigration", "emigration", "urbanization", "rural", "literacy",
        "education", "health", "healthcare", "disease", "pandemic",
    ],
    DomainType.DEFENSE: [
        "military", "defense", "army", "navy", "air force", "weapons",
        "missiles", "nuclear", "artillery", "tanks", "aircraft", "ships",
        "submarines", "soldiers", "troops", "war", "conflict", "battle",
        "strategic", "tactical", "intelligence", "cyber", "drone",
    ],
    DomainType.TRADE: [
        "trade", "export", "import", "tariff", "quota", "customs",
        "free trade", "protectionism", "wto", "bilateral", "multilateral",
        "trade agreement", "commerce", "commodity", "goods", "services",
        "trade deficit", "trade surplus", "trading partner",
    ],
    DomainType.TECHNOLOGY: [
        "technology", "tech", "ai", "artificial intelligence", "machine learning",
        "software", "hardware", "semiconductor", "chip", "digital", "internet",
        "cyber", "blockchain", "quantum", "5g", "innovation", "startup",
        "silicon valley", "research", "development", "r&d", "patent",
    ],
    DomainType.ENERGY: [
        "energy", "oil", "gas", "petroleum", "crude", "opec", "fuel",
        "electricity", "power", "nuclear", "solar", "wind", "renewable",
        "coal", "mining", "pipeline", "refinery", "barrel", "energy security",
    ],
    DomainType.AGRICULTURE: [
        "agriculture", "farming", "farm", "crop", "harvest", "yield",
        "wheat", "rice", "corn", "maize", "soybean", "cotton", "fertilizer",
        "irrigation", "livestock", "cattle", "poultry", "fishery", "food",
        "food security", "hunger", "malnutrition", "arable", "cultivated",
    ],
    DomainType.HEALTH: [
        "health", "healthcare", "hospital", "doctor", "medicine", "drug",
        "pharmaceutical", "vaccine", "disease", "pandemic", "epidemic",
        "covid", "cancer", "diabetes", "mortality", "morbidity", "who",
        "public health", "sanitation", "hygiene",
    ],
    DomainType.SPACE: [
        "space", "satellite", "rocket", "launch", "orbit", "moon", "mars",
        "nasa", "isro", "esa", "spacex", "astronaut", "cosmonaut", "mission",
        "rover", "probe", "telescope", "iss", "space station",
    ],
    DomainType.LOGISTICS: [
        "logistics", "supply chain", "shipping", "freight", "cargo", "container",
        "warehouse", "distribution", "courier", "delivery", "port", "customs",
        "import", "export", "transport", "transportation", "trucking",
    ],
    DomainType.DISASTER: [
        "disaster", "earthquake", "tsunami", "volcano", "flood", "hurricane",
        "cyclone", "typhoon", "tornado", "wildfire", "drought", "famine",
        "landslide", "avalanche", "emergency", "relief", "rescue", "aid",
        "humanitarian", "casualty", "damage", "destruction", "recovery",
    ],
}

# =============================================================================
# Intent Keywords
# =============================================================================

INTENT_KEYWORDS: Dict[IntentType, List[str]] = {
    IntentType.COMPARISON: [
        "compare", "comparison", "versus", "vs", "difference", "between",
        "contrast", "relative", "against", "better than", "worse than",
    ],
    IntentType.TREND: [
        "trend", "over time", "historical", "history", "evolution", "change",
        "growth", "decline", "increase", "decrease", "progression", "trajectory",
        "pattern", "year by year", "annual", "monthly", "quarterly",
    ],
    IntentType.FORECAST: [
        "forecast", "predict", "prediction", "future", "projection", "expected",
        "outlook", "estimate", "anticipate", "will", "next year", "coming years",
    ],
    IntentType.WHAT_IF: [
        "what if", "scenario", "hypothetical", "suppose", "assume", "simulate",
        "if", "would happen", "impact if", "effect if", "consequence",
    ],
    IntentType.ANALYSIS: [
        "analyze", "analysis", "explain", "understand", "why", "how", "cause",
        "reason", "factor", "driver", "assess", "evaluate", "examine", "study",
    ],
    IntentType.CORRELATION: [
        "correlation", "relationship", "connection", "link", "associated",
        "related", "influence", "affect", "impact on", "effect on", "depend",
    ],
    IntentType.IMPACT: [
        "impact", "effect", "consequence", "result", "outcome", "influence",
        "affect", "implication", "repercussion", "fallout", "damage",
    ],
    IntentType.SIMULATION: [
        "simulate", "simulation", "model", "scenario", "war game", "exercise",
        "project", "calculate", "compute",
    ],
    IntentType.OVERVIEW: [
        "overview", "summary", "brief", "general", "status", "current",
        "situation", "state of", "landscape", "outlook", "snapshot",
    ],
}

# =============================================================================
# Chart Type Inference
# =============================================================================

CHART_TYPE_PATTERNS: Dict[str, ChartType] = {
    r"trend|over time|historical|year|annual|monthly|growth|decline": ChartType.LINE,
    r"compare|versus|vs|comparison|between|difference": ChartType.BAR,
    r"breakdown|composition|share|percentage|distribution|proportion": ChartType.PIE,
    r"correlation|relationship|scatter|regression": ChartType.SCATTER,
    r"multiple factors|dimensions|criteria|aspects": ChartType.RADAR,
}

DIAGRAM_TYPE_PATTERNS: Dict[str, DiagramType] = {
    r"workflow|process|steps|procedure|flow": DiagramType.WORKFLOW,
    r"cause|effect|impact|consequence|chain|leads to": DiagramType.CAUSE_EFFECT,
    r"pipeline|stages|phases|sequence": DiagramType.PIPELINE,
    r"infrastructure|network|system|architecture": DiagramType.INFRASTRUCTURE,
    r"network|connections|nodes|graph": DiagramType.NETWORK,
    r"hierarchy|organization|structure|levels": DiagramType.HIERARCHY,
}

# =============================================================================
# Indicator Keywords
# =============================================================================

INDICATOR_KEYWORDS: Dict[str, str] = {
    "gdp": "GDP",
    "gdp growth": "GDP Growth",
    "gdp per capita": "GDP Per Capita",
    "inflation": "Inflation Rate",
    "unemployment": "Unemployment Rate",
    "population": "Population",
    "exports": "Exports",
    "imports": "Imports",
    "trade balance": "Trade Balance",
    "fdi": "Foreign Direct Investment",
    "debt": "Government Debt",
    "deficit": "Budget Deficit",
    "interest rate": "Interest Rate",
    "life expectancy": "Life Expectancy",
    "literacy": "Literacy Rate",
    "birth rate": "Birth Rate",
    "death rate": "Death Rate",
    "co2 emissions": "CO2 Emissions",
    "energy consumption": "Energy Consumption",
    "oil production": "Oil Production",
    "military spending": "Military Expenditure",
    "r&d spending": "R&D Expenditure",
    "tourist arrivals": "Tourist Arrivals",
}


# =============================================================================
# Intent Parser Class
# =============================================================================

class IntentParser:
    """
    Multi-strategy intent parser.

    Parses natural language queries into structured intent using:
    1. Rule-based keyword matching
    2. Domain ontology lookup
    3. Pattern-based chart/diagram type inference
    """

    def __init__(self):
        self._country_pattern = self._build_country_pattern()
        self._region_pattern = self._build_region_pattern()
        self._year_pattern = re.compile(
            r'(?:from\s+)?(\d{4})(?:\s*[-–to]+\s*(\d{4}))?|'
            r'(?:last|past)\s+(\d+)\s+years?|'
            r'(?:since|after)\s+(\d{4})'
        )

    def _build_country_pattern(self) -> re.Pattern:
        """Build regex pattern for country matching."""
        countries = list(COUNTRY_ALIASES.keys())
        pattern = r'\b(' + '|'.join(re.escape(c) for c in countries) + r')\b'
        return re.compile(pattern, re.IGNORECASE)

    def _build_region_pattern(self) -> re.Pattern:
        """Build regex pattern for region matching."""
        regions = list(REGION_KEYWORDS.keys())
        pattern = r'\b(' + '|'.join(re.escape(r) for r in regions) + r')\b'
        return re.compile(pattern, re.IGNORECASE)

    async def parse(self, query: str) -> ParsedIntent:
        """
        Parse a natural language query into structured intent.

        Args:
            query: Natural language query string

        Returns:
            ParsedIntent with extracted information
        """
        query_id = str(uuid.uuid4())[:8]
        query_lower = query.lower()

        # Extract geographic entities
        countries = self._extract_countries(query_lower)
        regions, region_countries = self._extract_regions(query_lower)
        countries = list(set(countries + region_countries))
        cities = self._extract_cities(query_lower)

        # Classify domains
        primary_domain, secondary_domains, domain_confidence = self._classify_domains(query_lower)

        # Detect intent type
        intent_type = self._detect_intent_type(query_lower)

        # Extract time range
        time_range = self._extract_time_range(query_lower)

        # Determine required outputs
        requires_chart, chart_type = self._determine_chart_type(query_lower, intent_type)
        requires_diagram, diagram_type = self._determine_diagram_type(query_lower, primary_domain)
        requires_map = self._should_include_map(countries, regions)
        map_features = self._determine_map_features(query_lower, primary_domain)

        # Extract indicators
        indicators = self._extract_indicators(query_lower, primary_domain)

        # Extract comparison entities
        comparison_entities = self._extract_comparison_entities(query_lower, countries)

        # Calculate parse confidence
        parse_confidence = self._calculate_confidence(
            countries, regions, primary_domain, indicators, intent_type
        )

        return ParsedIntent(
            query_id=query_id,
            raw_query=query,
            countries=countries,
            regions=regions,
            cities=cities,
            primary_domain=primary_domain,
            secondary_domains=secondary_domains,
            domain_confidence=domain_confidence,
            intent_type=intent_type,
            time_range=time_range,
            requires_chart=requires_chart,
            chart_type=chart_type,
            requires_diagram=requires_diagram,
            diagram_type=diagram_type,
            requires_map=requires_map,
            map_features=map_features,
            indicators=indicators,
            comparison_entities=comparison_entities,
            parse_confidence=parse_confidence,
        )

    def _extract_countries(self, query: str) -> List[str]:
        """Extract country names from query."""
        matches = self._country_pattern.findall(query)
        countries = []
        for match in matches:
            normalized = COUNTRY_ALIASES.get(match.lower())
            if normalized and normalized not in countries:
                countries.append(normalized)
        return countries

    def _extract_regions(self, query: str) -> Tuple[List[str], List[str]]:
        """Extract region names and their constituent countries."""
        matches = self._region_pattern.findall(query)
        regions = []
        region_countries = []
        for match in matches:
            region_lower = match.lower()
            if region_lower in REGION_KEYWORDS:
                regions.append(region_lower.title())
                normalized_countries = []
                for country in REGION_KEYWORDS[region_lower]:
                    normalized = COUNTRY_ALIASES.get(country.lower(), country)
                    normalized_countries.append(normalized)
                region_countries.extend(normalized_countries)
        return regions, list(set(region_countries))

    def _extract_cities(self, query: str) -> List[str]:
        """Extract city names from query (simplified)."""
        major_cities = {
            "mumbai": "Mumbai",
            "delhi": "Delhi",
            "new delhi": "Delhi",
            "beijing": "Beijing",
            "shanghai": "Shanghai",
            "tokyo": "Tokyo",
            "new york": "New York",
            "london": "London",
            "paris": "Paris",
            "moscow": "Moscow",
            "dubai": "Dubai",
            "singapore": "Singapore",
            "hong kong": "Hong Kong",
            "sydney": "Sydney",
        }
        cities = []
        for city_lower, city_name in major_cities.items():
            if city_lower in query:
                cities.append(city_name)
        return cities

    def _classify_domains(
        self, query: str
    ) -> Tuple[DomainType, List[DomainType], Dict[str, float]]:
        """Classify query into domains with confidence scores."""
        scores: Dict[DomainType, float] = {}

        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in query:
                    # Weight by keyword specificity (longer = more specific)
                    weight = min(len(keyword) / 10, 1.5)
                    score += weight
            if score > 0:
                scores[domain] = score

        if not scores:
            # Default to economics if no domain detected
            return DomainType.ECONOMICS, [], {"economics": 0.5}

        # Sort by score
        sorted_domains = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_domain = sorted_domains[0][0]
        secondary_domains = [d[0] for d in sorted_domains[1:3]]

        # Normalize scores to confidence
        total_score = sum(scores.values())
        domain_confidence = {
            d.value: round(s / total_score, 2) for d, s in scores.items()
        }

        return primary_domain, secondary_domains, domain_confidence

    def _detect_intent_type(self, query: str) -> IntentType:
        """Detect the intent type of the query."""
        for intent_type, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query:
                    return intent_type

        # Default based on query structure
        if "?" in query:
            return IntentType.ANALYSIS
        return IntentType.OVERVIEW

    def _extract_time_range(self, query: str) -> Optional[TimeRange]:
        """Extract time range from query."""
        current_year = datetime.now().year

        match = self._year_pattern.search(query)
        if match:
            groups = match.groups()
            if groups[0]:  # "2018-2023" or just "2018"
                start_year = int(groups[0])
                end_year = int(groups[1]) if groups[1] else current_year
                return TimeRange(start_year, end_year)
            elif groups[2]:  # "last 5 years"
                years = int(groups[2])
                return TimeRange(current_year - years, current_year)
            elif groups[3]:  # "since 2015"
                return TimeRange(int(groups[3]), current_year)

        # Default: last 10 years for trends
        if any(kw in query for kw in ["trend", "over time", "historical", "growth"]):
            return TimeRange(current_year - 10, current_year)

        return None

    def _determine_chart_type(
        self, query: str, intent_type: IntentType
    ) -> Tuple[bool, Optional[ChartType]]:
        """Determine if chart is needed and what type."""
        requires_chart = False
        chart_type = None

        # Check explicit patterns
        for pattern, ctype in CHART_TYPE_PATTERNS.items():
            if re.search(pattern, query):
                requires_chart = True
                chart_type = ctype
                break

        # Infer from intent type
        if not requires_chart:
            if intent_type == IntentType.TREND:
                requires_chart = True
                chart_type = ChartType.LINE
            elif intent_type == IntentType.COMPARISON:
                requires_chart = True
                chart_type = ChartType.BAR
            elif intent_type == IntentType.CORRELATION:
                requires_chart = True
                chart_type = ChartType.SCATTER
            elif intent_type in [IntentType.ANALYSIS, IntentType.OVERVIEW]:
                requires_chart = True
                chart_type = ChartType.BAR

        return requires_chart, chart_type

    def _determine_diagram_type(
        self, query: str, primary_domain: DomainType
    ) -> Tuple[bool, Optional[DiagramType]]:
        """Determine if diagram is needed and what type."""
        requires_diagram = False
        diagram_type = None

        # Check explicit patterns
        for pattern, dtype in DIAGRAM_TYPE_PATTERNS.items():
            if re.search(pattern, query):
                requires_diagram = True
                diagram_type = dtype
                break

        # Infer from domain
        if not requires_diagram:
            domain_diagram_map = {
                DomainType.LOGISTICS: DiagramType.PIPELINE,
                DomainType.INFRASTRUCTURE: DiagramType.INFRASTRUCTURE,
                DomainType.TRADE: DiagramType.WORKFLOW,
                DomainType.DISASTER: DiagramType.CAUSE_EFFECT,
            }
            if primary_domain in domain_diagram_map:
                requires_diagram = True
                diagram_type = domain_diagram_map[primary_domain]

        # Check for causal/impact language
        if not requires_diagram:
            if any(kw in query for kw in ["impact", "effect", "leads to", "causes", "results in"]):
                requires_diagram = True
                diagram_type = DiagramType.CAUSE_EFFECT

        return requires_diagram, diagram_type

    def _should_include_map(self, countries: List[str], regions: List[str]) -> bool:
        """Determine if map visualization should be included."""
        # Include map if geographic entities are mentioned
        return len(countries) > 0 or len(regions) > 0

    def _determine_map_features(
        self, query: str, primary_domain: DomainType
    ) -> List[MapFeatureType]:
        """Determine which map features to include."""
        features = []

        # Always highlight mentioned countries
        features.append(MapFeatureType.HIGHLIGHT)

        # Check for specific feature keywords
        if any(kw in query for kw in ["route", "corridor", "trade route", "supply chain"]):
            features.append(MapFeatureType.ROUTES)

        if any(kw in query for kw in ["distribution", "density", "concentration", "spread"]):
            features.append(MapFeatureType.HEATMAP)

        if any(kw in query for kw in ["location", "site", "point", "place", "city"]):
            features.append(MapFeatureType.MARKERS)

        if any(kw in query for kw in ["zone", "region", "area", "territory"]):
            features.append(MapFeatureType.POLYGONS)

        # Domain-specific features
        if primary_domain == DomainType.TRADE:
            if MapFeatureType.ROUTES not in features:
                features.append(MapFeatureType.ROUTES)
        elif primary_domain == DomainType.DISASTER:
            if MapFeatureType.HEATMAP not in features:
                features.append(MapFeatureType.HEATMAP)

        # Always include focus
        features.append(MapFeatureType.FOCUS)

        return features

    def _extract_indicators(
        self, query: str, primary_domain: DomainType
    ) -> List[str]:
        """Extract economic/data indicators from query."""
        indicators = []

        for keyword, indicator_name in INDICATOR_KEYWORDS.items():
            if keyword in query:
                indicators.append(indicator_name)

        # Add domain-specific default indicators
        if not indicators:
            domain_indicators = {
                DomainType.ECONOMICS: ["GDP", "GDP Growth"],
                DomainType.DEMOGRAPHICS: ["Population"],
                DomainType.TRADE: ["Exports", "Imports"],
                DomainType.DEFENSE: ["Military Expenditure"],
                DomainType.CLIMATE: ["CO2 Emissions"],
                DomainType.ENERGY: ["Energy Consumption"],
            }
            indicators = domain_indicators.get(primary_domain, ["GDP"])

        return indicators

    def _extract_comparison_entities(
        self, query: str, countries: List[str]
    ) -> List[str]:
        """Extract entities being compared."""
        comparison_entities = []

        # If multiple countries mentioned, they are likely being compared
        if len(countries) >= 2:
            comparison_entities = countries

        # Look for "vs" or "versus" patterns
        vs_match = re.search(r'(\w+)\s+(?:vs|versus|compared to)\s+(\w+)', query)
        if vs_match:
            for group in vs_match.groups():
                normalized = COUNTRY_ALIASES.get(group.lower())
                if normalized and normalized not in comparison_entities:
                    comparison_entities.append(normalized)

        return comparison_entities

    def _calculate_confidence(
        self,
        countries: List[str],
        regions: List[str],
        primary_domain: DomainType,
        indicators: List[str],
        intent_type: IntentType,
    ) -> float:
        """Calculate overall parse confidence score."""
        score = 0.5  # Base score

        # Boost for geographic entities
        if countries:
            score += 0.1 * min(len(countries), 3)
        if regions:
            score += 0.1 * min(len(regions), 2)

        # Boost for specific domain
        if primary_domain != DomainType.ECONOMICS:  # Not default
            score += 0.1

        # Boost for specific indicators
        if indicators:
            score += 0.05 * min(len(indicators), 3)

        # Boost for clear intent
        if intent_type != IntentType.OVERVIEW:  # Not default
            score += 0.1

        return min(round(score, 2), 1.0)


# =============================================================================
# Singleton Instance
# =============================================================================

_intent_parser: Optional[IntentParser] = None


def get_intent_parser() -> IntentParser:
    """Get singleton IntentParser instance."""
    global _intent_parser
    if _intent_parser is None:
        _intent_parser = IntentParser()
    return _intent_parser
