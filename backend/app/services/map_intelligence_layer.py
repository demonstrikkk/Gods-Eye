"""
Map Intelligence Layer

Generates geographic visualizations including markers, heatmaps, routes, and highlights.
Integrates with the existing MapCommandService.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.visual_intelligence import (
    ParsedIntent,
    DataFetchResult,
    MapIntelligenceOutput,
    GeoEntity,
    MapMarker,
    MapRoute,
    MapFeatureType,
    DomainType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Country Coordinates Database
# =============================================================================

COUNTRY_COORDINATES = {
    "India": {"lat": 20.5937, "lng": 78.9629, "iso": "IND"},
    "China": {"lat": 35.8617, "lng": 104.1954, "iso": "CHN"},
    "United States": {"lat": 37.0902, "lng": -95.7129, "iso": "USA"},
    "United Kingdom": {"lat": 55.3781, "lng": -3.4360, "iso": "GBR"},
    "Russia": {"lat": 61.5240, "lng": 105.3188, "iso": "RUS"},
    "Japan": {"lat": 36.2048, "lng": 138.2529, "iso": "JPN"},
    "Germany": {"lat": 51.1657, "lng": 10.4515, "iso": "DEU"},
    "France": {"lat": 46.2276, "lng": 2.2137, "iso": "FRA"},
    "Brazil": {"lat": -14.2350, "lng": -51.9253, "iso": "BRA"},
    "Pakistan": {"lat": 30.3753, "lng": 69.3451, "iso": "PAK"},
    "Bangladesh": {"lat": 23.6850, "lng": 90.3563, "iso": "BGD"},
    "Indonesia": {"lat": -0.7893, "lng": 113.9213, "iso": "IDN"},
    "Nigeria": {"lat": 9.0820, "lng": 8.6753, "iso": "NGA"},
    "Mexico": {"lat": 23.6345, "lng": -102.5528, "iso": "MEX"},
    "Canada": {"lat": 56.1304, "lng": -106.3468, "iso": "CAN"},
    "Australia": {"lat": -25.2744, "lng": 133.7751, "iso": "AUS"},
    "South Korea": {"lat": 35.9078, "lng": 127.7669, "iso": "KOR"},
    "Saudi Arabia": {"lat": 23.8859, "lng": 45.0792, "iso": "SAU"},
    "Iran": {"lat": 32.4279, "lng": 53.6880, "iso": "IRN"},
    "Turkey": {"lat": 38.9637, "lng": 35.2433, "iso": "TUR"},
    "Egypt": {"lat": 26.8206, "lng": 30.8025, "iso": "EGY"},
    "South Africa": {"lat": -30.5595, "lng": 22.9375, "iso": "ZAF"},
    "Vietnam": {"lat": 14.0583, "lng": 108.2772, "iso": "VNM"},
    "Thailand": {"lat": 15.8700, "lng": 100.9925, "iso": "THA"},
    "Singapore": {"lat": 1.3521, "lng": 103.8198, "iso": "SGP"},
    "Malaysia": {"lat": 4.2105, "lng": 101.9758, "iso": "MYS"},
    "United Arab Emirates": {"lat": 23.4241, "lng": 53.8478, "iso": "ARE"},
    "Israel": {"lat": 31.0461, "lng": 34.8516, "iso": "ISR"},
    "Italy": {"lat": 41.8719, "lng": 12.5674, "iso": "ITA"},
    "Spain": {"lat": 40.4637, "lng": -3.7492, "iso": "ESP"},
    "Poland": {"lat": 51.9194, "lng": 19.1451, "iso": "POL"},
    "Ukraine": {"lat": 48.3794, "lng": 31.1656, "iso": "UKR"},
    "Netherlands": {"lat": 52.1326, "lng": 5.2913, "iso": "NLD"},
    "Argentina": {"lat": -38.4161, "lng": -63.6167, "iso": "ARG"},
    "Sri Lanka": {"lat": 7.8731, "lng": 80.7718, "iso": "LKA"},
    "Nepal": {"lat": 28.3949, "lng": 84.1240, "iso": "NPL"},
    "Afghanistan": {"lat": 33.9391, "lng": 67.7100, "iso": "AFG"},
    "Iraq": {"lat": 33.2232, "lng": 43.6793, "iso": "IRQ"},
    "Syria": {"lat": 34.8021, "lng": 38.9968, "iso": "SYR"},
}

CITY_COORDINATES = {
    "Mumbai": {"lat": 19.0760, "lng": 72.8777, "country": "India"},
    "Delhi": {"lat": 28.7041, "lng": 77.1025, "country": "India"},
    "Beijing": {"lat": 39.9042, "lng": 116.4074, "country": "China"},
    "Shanghai": {"lat": 31.2304, "lng": 121.4737, "country": "China"},
    "Tokyo": {"lat": 35.6762, "lng": 139.6503, "country": "Japan"},
    "New York": {"lat": 40.7128, "lng": -74.0060, "country": "United States"},
    "London": {"lat": 51.5074, "lng": -0.1278, "country": "United Kingdom"},
    "Paris": {"lat": 48.8566, "lng": 2.3522, "country": "France"},
    "Moscow": {"lat": 55.7558, "lng": 37.6173, "country": "Russia"},
    "Dubai": {"lat": 25.2048, "lng": 55.2708, "country": "United Arab Emirates"},
    "Singapore": {"lat": 1.3521, "lng": 103.8198, "country": "Singapore"},
    "Hong Kong": {"lat": 22.3193, "lng": 114.1694, "country": "China"},
    "Sydney": {"lat": -33.8688, "lng": 151.2093, "country": "Australia"},
}


# =============================================================================
# Domain Color Mappings
# =============================================================================

DOMAIN_COLORS = {
    DomainType.ECONOMICS: "#22c55e",    # green
    DomainType.GEOPOLITICS: "#ef4444",  # red
    DomainType.CLIMATE: "#06b6d4",      # cyan
    DomainType.DEFENSE: "#6b7280",      # gray
    DomainType.TRADE: "#f59e0b",        # amber
    DomainType.ENERGY: "#f97316",       # orange
    DomainType.INFRASTRUCTURE: "#8b5cf6",  # violet
    DomainType.LOGISTICS: "#3b82f6",    # blue
    DomainType.DISASTER: "#dc2626",     # red-600
    DomainType.SPACE: "#7c3aed",        # violet-600
}


# =============================================================================
# Map Intelligence Layer
# =============================================================================

class MapIntelligenceLayer:
    """
    Geographic visualization intelligence.

    Generates map commands including:
    - Country highlights
    - Markers for points of interest
    - Routes/corridors
    - Heatmaps
    - Focus commands
    """

    def __init__(self):
        self._map_command_service = None

    def _get_map_command_service(self):
        """Lazy load map command service."""
        if self._map_command_service is None:
            try:
                from app.services.map_command_service import get_map_command_service
                self._map_command_service = get_map_command_service()
            except ImportError:
                logger.warning("MapCommandService not available")
        return self._map_command_service

    async def generate_map_intelligence(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> MapIntelligenceOutput:
        """
        Generate comprehensive map visualization.

        Args:
            intent: Parsed intent
            data_result: Fetched data

        Returns:
            MapIntelligenceOutput with commands and data
        """
        commands = []
        markers = []
        routes = []
        geo_entities = []
        heatmap_data = {}

        if not intent.requires_map:
            return MapIntelligenceOutput(
                commands=[],
                affected_regions=[],
                geo_entities=[],
                markers=[],
                routes=[],
            )

        # 1. Extract and validate geo-entities
        geo_entities = self._extract_geo_entities(intent)

        # 2. Generate highlight commands for countries
        if MapFeatureType.HIGHLIGHT in intent.map_features:
            highlight_cmd = self._create_highlight_command(intent, geo_entities)
            if highlight_cmd:
                commands.append(highlight_cmd)

        # 3. Generate focus command
        if MapFeatureType.FOCUS in intent.map_features and geo_entities:
            focus_cmd = self._create_focus_command(geo_entities[0])
            if focus_cmd:
                commands.append(focus_cmd)

        # 4. Generate markers for cities or data points
        if MapFeatureType.MARKERS in intent.map_features:
            markers = self._create_markers(intent, data_result)
            for marker in markers:
                marker_cmd = self._create_marker_command(marker)
                commands.append(marker_cmd)

        # 5. Generate routes for trade/logistics
        if MapFeatureType.ROUTES in intent.map_features:
            routes = self._create_routes(intent)
            for route in routes:
                route_cmd = self._create_route_command(route, intent)
                commands.append(route_cmd)

        # 6. Generate heatmap data
        if MapFeatureType.HEATMAP in intent.map_features:
            heatmap_data = self._create_heatmap_data(intent, data_result)
            if heatmap_data:
                heatmap_cmd = self._create_heatmap_command(heatmap_data, intent)
                commands.append(heatmap_cmd)

        # 7. Determine layer recommendations
        layer_recommendations = self._recommend_layers(intent)

        return MapIntelligenceOutput(
            commands=commands,
            affected_regions=intent.countries + intent.regions,
            geo_entities=geo_entities,
            markers=markers,
            routes=routes,
            heatmap_data=heatmap_data,
            coordinate_data=self._build_coordinate_data(geo_entities),
            layer_recommendations=layer_recommendations,
        )

    def _extract_geo_entities(self, intent: ParsedIntent) -> List[GeoEntity]:
        """Extract GeoEntity objects from intent."""
        entities = []

        # Add countries
        for country in intent.countries:
            coords = COUNTRY_COORDINATES.get(country)
            if coords:
                entities.append(GeoEntity(
                    name=country,
                    entity_type="country",
                    iso_code=coords["iso"],
                    lat=coords["lat"],
                    lng=coords["lng"],
                    confidence=1.0,
                ))

        # Add cities
        for city in intent.cities:
            coords = CITY_COORDINATES.get(city)
            if coords:
                entities.append(GeoEntity(
                    name=city,
                    entity_type="city",
                    lat=coords["lat"],
                    lng=coords["lng"],
                    confidence=1.0,
                ))

        return entities

    def _create_highlight_command(
        self,
        intent: ParsedIntent,
        geo_entities: List[GeoEntity],
    ) -> Optional[Dict[str, Any]]:
        """Create highlight command for countries."""
        country_ids = [e.iso_code for e in geo_entities if e.entity_type == "country"]

        if not country_ids:
            return None

        color = DOMAIN_COLORS.get(intent.primary_domain, "#06b6d4")

        return {
            "type": "highlight",
            "country_ids": country_ids,
            "color": color,
            "pulse": True,
            "description": f"Highlighting: {', '.join(intent.countries[:3])}",
            "source": "visual_intelligence_engine",
            "priority": "high",
            "timestamp": datetime.now().isoformat(),
        }

    def _create_focus_command(self, entity: GeoEntity) -> Optional[Dict[str, Any]]:
        """Create focus command to center map on entity."""
        if not entity.lat or not entity.lng:
            return None

        return {
            "type": "focus",
            "lat": entity.lat,
            "lng": entity.lng,
            "zoom": 4 if entity.entity_type == "country" else 8,
            "duration": 1000,
            "description": f"Focus on {entity.name}",
            "source": "visual_intelligence_engine",
            "timestamp": datetime.now().isoformat(),
        }

    def _create_markers(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> List[MapMarker]:
        """Create markers for data points."""
        markers = []

        # Add markers for cities
        for city in intent.cities:
            coords = CITY_COORDINATES.get(city)
            if coords:
                markers.append(MapMarker(
                    lat=coords["lat"],
                    lng=coords["lng"],
                    label=city,
                    marker_type="city",
                    description=f"City: {city}",
                    color=DOMAIN_COLORS.get(intent.primary_domain, "#06b6d4"),
                ))

        # Add markers for country capitals (for indicators)
        for country in intent.countries[:3]:  # Limit to first 3
            coords = COUNTRY_COORDINATES.get(country)
            if coords:
                # Get indicator value if available
                value_text = ""
                for indicator, dataset in data_result.datasets.items():
                    for v in dataset.values:
                        if v.get("country") == country:
                            value_text = f"{indicator}: {self._format_value(v.get('value', 0))}"
                            break
                    if value_text:
                        break

                markers.append(MapMarker(
                    lat=coords["lat"],
                    lng=coords["lng"],
                    label=country,
                    marker_type="data",
                    description=value_text or f"Country: {country}",
                    color=DOMAIN_COLORS.get(intent.primary_domain, "#06b6d4"),
                ))

        return markers

    def _create_marker_command(self, marker: MapMarker) -> Dict[str, Any]:
        """Create marker command from MapMarker."""
        return {
            "type": "marker",
            "lat": marker.lat,
            "lng": marker.lng,
            "label": marker.label,
            "marker_type": marker.marker_type,
            "color": marker.color,
            "description": marker.description,
            "source": "visual_intelligence_engine",
            "timestamp": datetime.now().isoformat(),
        }

    def _create_routes(self, intent: ParsedIntent) -> List[MapRoute]:
        """Create routes between countries for trade/logistics."""
        routes = []

        # Create routes between compared countries
        if len(intent.countries) >= 2 and intent.primary_domain in [
            DomainType.TRADE, DomainType.LOGISTICS, DomainType.ENERGY
        ]:
            for i in range(len(intent.countries) - 1):
                from_country = intent.countries[i]
                to_country = intent.countries[i + 1]

                from_coords = COUNTRY_COORDINATES.get(from_country)
                to_coords = COUNTRY_COORDINATES.get(to_country)

                if from_coords and to_coords:
                    route_type = "trade" if intent.primary_domain == DomainType.TRADE else "logistics"
                    routes.append(MapRoute(
                        from_lat=from_coords["lat"],
                        from_lng=from_coords["lng"],
                        to_lat=to_coords["lat"],
                        to_lng=to_coords["lng"],
                        route_type=route_type,
                        label=f"{from_country} → {to_country}",
                        color=DOMAIN_COLORS.get(intent.primary_domain, "#f59e0b"),
                    ))

        return routes

    def _create_route_command(
        self,
        route: MapRoute,
        intent: ParsedIntent,
    ) -> Dict[str, Any]:
        """Create route command from MapRoute."""
        return {
            "type": "route",
            "from_lat": route.from_lat,
            "from_lng": route.from_lng,
            "to_lat": route.to_lat,
            "to_lng": route.to_lng,
            "route_type": route.route_type,
            "color": route.color,
            "label": route.label,
            "animated": True,
            "description": f"{route.route_type} route",
            "source": "visual_intelligence_engine",
            "timestamp": datetime.now().isoformat(),
        }

    def _create_heatmap_data(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> Dict[str, float]:
        """Create heatmap data from fetched values."""
        heatmap_data = {}

        # Get first indicator data
        for indicator, dataset in data_result.datasets.items():
            for v in dataset.values:
                country = v.get("country")
                value = v.get("value")
                if country and value is not None:
                    coords = COUNTRY_COORDINATES.get(country)
                    if coords:
                        key = f"{coords['lat']},{coords['lng']}"
                        heatmap_data[key] = float(value)
            break  # Only use first indicator

        return heatmap_data

    def _create_heatmap_command(
        self,
        heatmap_data: Dict[str, float],
        intent: ParsedIntent,
    ) -> Dict[str, Any]:
        """Create heatmap command from data."""
        # Convert to list of points
        points = []
        for coord_key, value in heatmap_data.items():
            lat, lng = map(float, coord_key.split(","))
            points.append({
                "lat": lat,
                "lng": lng,
                "intensity": value,
            })

        return {
            "type": "heatmap",
            "points": points,
            "metric": intent.indicators[0] if intent.indicators else "value",
            "color_scale": "viridis",
            "description": f"Heatmap: {intent.indicators[0] if intent.indicators else 'data'}",
            "source": "visual_intelligence_engine",
            "timestamp": datetime.now().isoformat(),
        }

    def _recommend_layers(self, intent: ParsedIntent) -> List[str]:
        """Recommend map layers based on intent."""
        recommendations = []

        # Domain-specific layer recommendations
        domain_layers = {
            DomainType.ECONOMICS: ["economics", "trade"],
            DomainType.TRADE: ["trade", "logistics"],
            DomainType.INFRASTRUCTURE: ["infrastructure", "logistics"],
            DomainType.CLIMATE: ["climate", "environment"],
            DomainType.DEFENSE: ["defense", "geopolitics"],
            DomainType.ENERGY: ["energy", "infrastructure"],
            DomainType.DISASTER: ["disaster", "infrastructure"],
        }

        recommendations = domain_layers.get(intent.primary_domain, ["economics"])
        return recommendations

    def _build_coordinate_data(
        self,
        geo_entities: List[GeoEntity],
    ) -> Dict[str, Any]:
        """Build coordinate data for frontend."""
        return {
            "entities": [e.to_dict() for e in geo_entities],
            "bounds": self._calculate_bounds(geo_entities),
        }

    def _calculate_bounds(
        self,
        geo_entities: List[GeoEntity],
    ) -> Optional[Dict[str, float]]:
        """Calculate bounding box for entities."""
        if not geo_entities:
            return None

        lats = [e.lat for e in geo_entities if e.lat]
        lngs = [e.lng for e in geo_entities if e.lng]

        if not lats or not lngs:
            return None

        return {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs),
        }

    def _format_value(self, value: float) -> str:
        """Format numeric value for display."""
        if value >= 1e12:
            return f"{value/1e12:.1f}T"
        elif value >= 1e9:
            return f"{value/1e9:.1f}B"
        elif value >= 1e6:
            return f"{value/1e6:.1f}M"
        elif value >= 1e3:
            return f"{value/1e3:.1f}K"
        else:
            return f"{value:.2f}"


# =============================================================================
# Singleton Instance
# =============================================================================

_map_intelligence: Optional[MapIntelligenceLayer] = None


def get_map_intelligence_layer() -> MapIntelligenceLayer:
    """Get singleton MapIntelligenceLayer instance."""
    global _map_intelligence
    if _map_intelligence is None:
        _map_intelligence = MapIntelligenceLayer()
    return _map_intelligence
