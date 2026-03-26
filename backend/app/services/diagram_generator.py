"""
Diagram Generation Engine

Generates visual diagrams using Pollinations API.
Supports workflows, cause-effect chains, pipelines, and infrastructure diagrams.
"""

import urllib.parse
import logging
from typing import List, Dict, Any, Optional

from app.models.visual_intelligence import (
    ParsedIntent,
    DataFetchResult,
    DiagramOutput,
    DiagramType,
    DiagramContext,
    DomainType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Diagram Prompt Templates
# =============================================================================

DIAGRAM_PROMPTS = {
    DiagramType.WORKFLOW: (
        "Professional flowchart diagram showing {description}, "
        "clean minimal design, boxes connected with arrows, "
        "blue and white color scheme, corporate style, "
        "white background, clear labels on each step, "
        "infographic style, high quality"
    ),
    DiagramType.CAUSE_EFFECT: (
        "Cause and effect diagram showing {description}, "
        "fishbone diagram style, professional infographic, "
        "labeled nodes showing causation chain, "
        "arrows showing relationships, business analysis style, "
        "blue gray color palette, white background"
    ),
    DiagramType.PIPELINE: (
        "Pipeline diagram showing {description}, "
        "horizontal flow from left to right, "
        "stages labeled with icons, "
        "professional business infographic style, "
        "gradient colors, clean modern design, white background"
    ),
    DiagramType.INFRASTRUCTURE: (
        "Infrastructure diagram showing {description}, "
        "network topology style with nodes and connections, "
        "technical diagram, icons for different components, "
        "blue and gray colors, professional engineering style, "
        "white background, labeled components"
    ),
    DiagramType.NETWORK: (
        "Network graph diagram showing {description}, "
        "nodes connected by lines, force-directed layout style, "
        "different colors for different node types, "
        "professional data visualization, white background"
    ),
    DiagramType.PROCESS: (
        "Process diagram showing {description}, "
        "step by step workflow, numbered stages, "
        "professional business process style, "
        "arrows showing flow direction, "
        "blue accents, clean white background"
    ),
    DiagramType.HIERARCHY: (
        "Organizational hierarchy diagram showing {description}, "
        "tree structure from top to bottom, "
        "boxes with labels, connecting lines, "
        "corporate style, blue and gray colors, "
        "white background, professional design"
    ),
    DiagramType.COMPARISON: (
        "Side by side comparison diagram showing {description}, "
        "two columns with matching elements, "
        "professional infographic style, "
        "clear labels and icons, "
        "contrasting colors, white background"
    ),
}

# =============================================================================
# Domain-Specific Diagram Contexts
# =============================================================================

DOMAIN_DIAGRAM_TEMPLATES = {
    DomainType.ECONOMICS: {
        "default": "economic factors and their relationships, GDP drivers and economic indicators",
        "trend": "economic growth trajectory showing factors affecting economic development",
        "impact": "cause and effect chain of economic policy impacts",
    },
    DomainType.TRADE: {
        "default": "international trade flow, exports and imports between countries",
        "trend": "trade volume growth over time with key milestones",
        "impact": "trade policy effects on supply chain and markets",
    },
    DomainType.INFRASTRUCTURE: {
        "default": "infrastructure network showing transportation and logistics connections",
        "trend": "infrastructure development phases and progress",
        "impact": "infrastructure investment effects on economic growth",
    },
    DomainType.LOGISTICS: {
        "default": "supply chain pipeline from production to distribution",
        "trend": "logistics efficiency improvements over time",
        "impact": "supply chain disruption effects on delivery",
    },
    DomainType.ENERGY: {
        "default": "energy production and distribution network",
        "trend": "energy transition from fossil to renewable sources",
        "impact": "energy price changes effect on industry",
    },
    DomainType.AGRICULTURE: {
        "default": "farm to market supply chain flow",
        "trend": "agricultural output growth with technology adoption",
        "impact": "climate effects on crop yield and food security",
    },
    DomainType.DISASTER: {
        "default": "disaster impact chain showing affected systems",
        "trend": "disaster recovery phases and timeline",
        "impact": "natural disaster effects on economy and infrastructure",
    },
    DomainType.SPACE: {
        "default": "space mission pipeline from development to launch",
        "trend": "space program evolution and capability growth",
        "impact": "space technology benefits to economy and communication",
    },
    DomainType.DEFENSE: {
        "default": "defense capabilities and strategic assets deployment",
        "trend": "military modernization progress",
        "impact": "defense spending effects on technology and industry",
    },
    DomainType.GEOPOLITICS: {
        "default": "geopolitical relationships and alliances network",
        "trend": "diplomatic relations evolution over time",
        "impact": "sanctions and policy effects on international relations",
    },
}


# =============================================================================
# Diagram Generation Engine
# =============================================================================

class DiagramGenerationEngine:
    """
    Generates visual diagrams using Pollinations API.

    Diagram types:
    - Workflow: Process flows and step sequences
    - Cause-Effect: Fishbone/Ishikawa diagrams
    - Pipeline: Stage-based processing flows
    - Infrastructure: Network and system diagrams
    """

    POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"

    def __init__(self):
        self._default_width = 800
        self._default_height = 600

    async def generate_diagrams_for_intent(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> List[DiagramOutput]:
        """
        Generate diagrams based on intent and data.

        Args:
            intent: Parsed intent
            data_result: Fetched data

        Returns:
            List of DiagramOutput objects
        """
        diagrams = []

        if not intent.requires_diagram:
            return diagrams

        diagram_type = intent.diagram_type or DiagramType.WORKFLOW
        context = self._build_context(intent, data_result)

        # Generate primary diagram
        diagram = await self.generate_diagram(
            diagram_type=diagram_type,
            context=context,
        )
        diagrams.append(diagram)

        # Generate additional diagram for impact analysis
        if intent.intent_type.value in ["impact", "analysis"] and diagram_type != DiagramType.CAUSE_EFFECT:
            impact_context = self._build_impact_context(intent, data_result)
            impact_diagram = await self.generate_diagram(
                diagram_type=DiagramType.CAUSE_EFFECT,
                context=impact_context,
            )
            diagrams.append(impact_diagram)

        return diagrams

    async def generate_diagram(
        self,
        diagram_type: DiagramType,
        context: DiagramContext,
    ) -> DiagramOutput:
        """
        Generate a single diagram.

        Args:
            diagram_type: Type of diagram
            context: Context for diagram generation

        Returns:
            DiagramOutput with image URL
        """
        prompt = self._build_prompt(diagram_type, context)
        image_url = self._generate_pollinations_url(prompt)

        return DiagramOutput(
            image_url=image_url,
            diagram_type=diagram_type,
            prompt_used=prompt,
            description=context.description,
            metadata={
                "elements": context.elements,
                "relationships": context.relationships,
            },
        )

    def _build_context(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> DiagramContext:
        """Build diagram context from intent and data."""
        domain = intent.primary_domain
        intent_type = intent.intent_type.value

        # Get domain-specific template
        domain_templates = DOMAIN_DIAGRAM_TEMPLATES.get(
            domain,
            {"default": "data flow and relationships"}
        )

        # Select appropriate template
        template = domain_templates.get(intent_type, domain_templates.get("default", ""))

        # Build description
        description = template
        if intent.countries:
            countries_str = " and ".join(intent.countries[:2])
            description = f"{countries_str} {template}"

        if intent.indicators:
            indicators_str = ", ".join(intent.indicators[:2])
            description = f"{description} focusing on {indicators_str}"

        # Extract elements from query
        elements = self._extract_elements(intent)

        # Build relationships
        relationships = self._build_relationships(intent, elements)

        return DiagramContext(
            description=description,
            elements=elements,
            relationships=relationships,
            style="professional",
        )

    def _build_impact_context(
        self,
        intent: ParsedIntent,
        data_result: DataFetchResult,
    ) -> DiagramContext:
        """Build context for impact/cause-effect diagrams."""
        # Extract cause and effect from query
        causes = []
        effects = []

        # Domain-specific cause-effect patterns
        domain_patterns = {
            DomainType.ECONOMICS: {
                "causes": ["policy changes", "investment", "trade"],
                "effects": ["GDP growth", "employment", "inflation"],
            },
            DomainType.ENERGY: {
                "causes": ["oil prices", "supply disruption", "demand"],
                "effects": ["fuel costs", "inflation", "industry output"],
            },
            DomainType.CLIMATE: {
                "causes": ["emissions", "deforestation", "industrialization"],
                "effects": ["temperature rise", "extreme weather", "sea level"],
            },
            DomainType.DISASTER: {
                "causes": ["natural event", "infrastructure failure"],
                "effects": ["economic disruption", "displacement", "recovery costs"],
            },
            DomainType.TRADE: {
                "causes": ["tariffs", "trade agreements", "currency"],
                "effects": ["exports", "imports", "supply chain"],
            },
        }

        patterns = domain_patterns.get(
            intent.primary_domain,
            {"causes": ["input factors"], "effects": ["output impacts"]}
        )

        causes = patterns["causes"]
        effects = patterns["effects"]

        # Add indicators as effects
        if intent.indicators:
            effects.extend(intent.indicators[:2])

        description = (
            f"cause and effect analysis showing how "
            f"{', '.join(causes[:2])} lead to changes in "
            f"{', '.join(effects[:2])}"
        )

        if intent.countries:
            description = f"{intent.countries[0]} - {description}"

        return DiagramContext(
            description=description,
            elements=causes + effects,
            relationships=[f"{c} → {e}" for c in causes[:2] for e in effects[:2]],
            style="professional",
        )

    def _extract_elements(self, intent: ParsedIntent) -> List[str]:
        """Extract diagram elements from intent."""
        elements = []

        # Add indicators
        elements.extend(intent.indicators[:4])

        # Add domain-specific elements
        domain_elements = {
            DomainType.LOGISTICS: ["production", "transport", "distribution", "delivery"],
            DomainType.TRADE: ["exports", "imports", "tariffs", "agreements"],
            DomainType.INFRASTRUCTURE: ["roads", "ports", "railways", "airports"],
            DomainType.ENERGY: ["production", "transmission", "distribution", "consumption"],
            DomainType.AGRICULTURE: ["farming", "processing", "transport", "market"],
            DomainType.SPACE: ["research", "development", "manufacturing", "launch", "deployment"],
        }

        if intent.primary_domain in domain_elements:
            elements.extend(domain_elements[intent.primary_domain])

        # Deduplicate
        return list(dict.fromkeys(elements))[:8]

    def _build_relationships(
        self,
        intent: ParsedIntent,
        elements: List[str],
    ) -> List[str]:
        """Build relationships between elements."""
        relationships = []

        # Create sequential relationships for pipeline diagrams
        if intent.diagram_type == DiagramType.PIPELINE and len(elements) >= 2:
            for i in range(len(elements) - 1):
                relationships.append(f"{elements[i]} → {elements[i+1]}")

        # Create impact relationships
        elif intent.intent_type.value in ["impact", "correlation"]:
            if len(elements) >= 2:
                relationships.append(f"{elements[0]} affects {elements[1]}")

        return relationships

    def _build_prompt(
        self,
        diagram_type: DiagramType,
        context: DiagramContext,
    ) -> str:
        """Build prompt for Pollinations API."""
        template = DIAGRAM_PROMPTS.get(
            diagram_type,
            DIAGRAM_PROMPTS[DiagramType.WORKFLOW]
        )

        prompt = template.format(description=context.description)

        # Add elements to prompt
        if context.elements:
            elements_str = ", ".join(context.elements[:5])
            prompt += f", key elements: {elements_str}"

        return prompt

    def _generate_pollinations_url(
        self,
        prompt: str,
        width: int = None,
        height: int = None,
    ) -> str:
        """Generate Pollinations API URL."""
        width = width or self._default_width
        height = height or self._default_height

        # Clean and encode prompt
        clean_prompt = prompt.replace("\n", " ").strip()
        encoded_prompt = urllib.parse.quote(clean_prompt)

        return f"{self.POLLINATIONS_BASE_URL}/{encoded_prompt}?width={width}&height={height}&nologo=true"


# =============================================================================
# Singleton Instance
# =============================================================================

_diagram_engine: Optional[DiagramGenerationEngine] = None


def get_diagram_generator() -> DiagramGenerationEngine:
    """Get singleton DiagramGenerationEngine instance."""
    global _diagram_engine
    if _diagram_engine is None:
        _diagram_engine = DiagramGenerationEngine()
    return _diagram_engine
