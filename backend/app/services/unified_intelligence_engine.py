import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from app.models.unified_intelligence import (
    UnifiedIntelligenceRequest,
    UnifiedIntelligenceResult,
    QueryAssessment,
    QueryComplexity,
    CapabilitySet,
    CapabilityType,
    ReasoningResult,
    ToolsResult,
    VisualsResult,
    MapIntelligenceResult,
    CapabilityExecutionStatus,
    AssistantResponsePayload,
    AssistantResponseSection,
)
from app.services.expert_strategic_agent import run_expert_strategic_analysis
from app.services.strategic_agent import run_strategic_analysis
from app.services.visual_intelligence_engine import get_visual_intelligence_engine
from app.services.map_intelligence_layer import get_map_intelligence_layer
from app.services.llm_provider import get_enterprise_llm

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    role: str
    content: str
    timestamp: str


@dataclass
class ConversationSession:
    conversation_id: str
    title: str = "Unified Intelligence Session"
    memory_summary: str = ""
    turns: List[ConversationTurn] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    last_capabilities: List[str] = field(default_factory=list)
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())


class QueryAssessor:
    REASONING_KEYWORDS = [
        "analyze", "assess", "evaluate", "explain", "why", "how", "compare",
        "contrast", "debate", "consensus", "opinion", "perspective", "impact",
        "consequence", "risk", "opportunity", "strategy", "complex", "multi-faceted",
    ]
    TOOLS_KEYWORDS = [
        "latest", "current", "recent", "news", "social media", "twitter",
        "reddit", "trending", "sentiment", "real-time", "osint", "intelligence",
        "what's happening", "update", "status", "monitor",
    ]
    VISUALS_KEYWORDS = [
        "chart", "graph", "diagram", "visualize", "show", "plot", "compare",
        "trend", "over time", "growth", "decline", "statistics", "data",
        "numbers", "metrics", "indicators", "gdp", "inflation", "population",
    ]
    GEOGRAPHIC_KEYWORDS = [
        "india", "china", "usa", "europe", "asia", "middle east", "country",
        "region", "global", "international", "world", "map", "location",
        "geographic", "spatial", "territory", "border", "zone",
    ]

    async def assess_query(self, query: str, context: Dict[str, Any] = None) -> QueryAssessment:
        query_lower = query.lower()
        context = context or {}
        reasoning_score = self._count_keywords(query_lower, self.REASONING_KEYWORDS)
        tools_score = self._count_keywords(query_lower, self.TOOLS_KEYWORDS)
        visuals_score = self._count_keywords(query_lower, self.VISUALS_KEYWORDS)
        geographic_score = self._count_keywords(query_lower, self.GEOGRAPHIC_KEYWORDS)

        has_geographic = geographic_score > 0
        has_data_indicators = any(
            kw in query_lower for kw in ["gdp", "inflation", "population", "trade", "growth", "rate", "index"]
        )
        has_time_dimension = any(
            kw in query_lower for kw in ["trend", "over time", "historical", "forecast", "future", "past", "year"]
        )
        requires_external = tools_score > 0 or any(
            kw in query_lower for kw in ["latest", "current", "recent", "real-time"]
        )
        requires_multi_perspective = reasoning_score >= 2 or any(
            kw in query_lower for kw in ["compare", "contrast", "debate", "multiple", "various"]
        )

        complexity = self._assess_complexity(
            query_length=len(query.split()),
            reasoning_score=reasoning_score,
            requires_multi_perspective=requires_multi_perspective,
            has_data_indicators=has_data_indicators,
        )

        capabilities = CapabilitySet()
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX] or reasoning_score >= 2:
            capabilities.reasoning = True
        if requires_external or tools_score > 0 or (has_data_indicators and not visuals_score):
            capabilities.tools = True
        if visuals_score > 0 or (has_data_indicators and has_time_dimension):
            capabilities.visuals = True
        if has_geographic:
            capabilities.map_intelligence = True
        if capabilities.count() == 0:
            capabilities.reasoning = True
        if context.get("conversation_memory"):
            capabilities.reasoning = True

        return QueryAssessment(
            complexity=complexity,
            domains=self._identify_domains(query_lower),
            has_geographic_entities=has_geographic,
            has_data_indicators=has_data_indicators,
            has_time_dimension=has_time_dimension,
            requires_external_data=requires_external,
            requires_multi_perspective=requires_multi_perspective,
            confidence=0.85,
            suggested_capabilities=capabilities,
        )

    def _count_keywords(self, text: str, keywords: List[str]) -> int:
        return sum(1 for kw in keywords if kw in text)

    def _assess_complexity(
        self,
        query_length: int,
        reasoning_score: int,
        requires_multi_perspective: bool,
        has_data_indicators: bool,
    ) -> QueryComplexity:
        score = 0
        if query_length > 20:
            score += 2
        elif query_length > 10:
            score += 1
        score += min(reasoning_score, 3)
        if requires_multi_perspective:
            score += 2
        if has_data_indicators:
            score += 1
        if score >= 7:
            return QueryComplexity.VERY_COMPLEX
        if score >= 5:
            return QueryComplexity.COMPLEX
        if score >= 3:
            return QueryComplexity.MODERATE
        return QueryComplexity.SIMPLE

    def _identify_domains(self, text: str) -> List[str]:
        domains = []
        domain_keywords = {
            "economics": ["gdp", "economy", "trade", "inflation", "growth", "fiscal", "monetary"],
            "geopolitics": ["conflict", "war", "alliance", "diplomacy", "sanction", "security"],
            "climate": ["climate", "weather", "emissions", "environment", "carbon", "renewable"],
            "infrastructure": ["infrastructure", "roads", "transport", "logistics", "connectivity"],
            "defense": ["military", "defense", "army", "weapons", "strategic"],
            "technology": ["tech", "ai", "software", "digital", "cyber", "innovation"],
            "space": ["space", "satellite", "rocket", "orbit", "mission", "aerospace"],
        }
        for domain, keywords in domain_keywords.items():
            if any(kw in text for kw in keywords):
                domains.append(domain)
        return domains or ["general"]


class UnifiedIntelligenceEngine:
    def __init__(self):
        self._assessor = QueryAssessor()
        self._expert_orchestrator = None
        self._visual_engine = None
        self._map_intelligence = None
        self._sessions: Dict[str, ConversationSession] = {}
        self._max_turns = 12
        try:
            self._llm = get_enterprise_llm(temperature=0.3)
        except RuntimeError:
            logger.warning("Unified intelligence LLM synthesis unavailable; using deterministic synthesis.")
            self._llm = None

    async def analyze(self, request: UnifiedIntelligenceRequest) -> UnifiedIntelligenceResult:
        start_time = time.time()
        query_id = str(uuid.uuid4())[:8]
        conversation_id = request.conversation_id or str(uuid.uuid4())[:12]
        session = self._get_or_create_session(conversation_id)
        context = self._build_enriched_context(request, session)
        assessment = await self._assessor.assess_query(request.query, context)
        capabilities = self._resolve_capabilities(assessment, request)
        results, statuses = await self._execute_capabilities(
            query_id=query_id,
            query=request.query,
            context=context,
            capabilities=capabilities,
            max_time=request.max_processing_time or 30.0,
        )
        unified_summary = await self._synthesize_unified_summary(request.query, results)
        assistant_response = await self._build_assistant_response(
            query=request.query,
            assessment=assessment,
            results=results,
            statuses=statuses,
            unified_summary=unified_summary,
            session=session,
        )
        data_sources = self._collect_data_sources(results)
        capability_statuses = [status.to_dict() for status in statuses]
        capabilities_activated = [status.capability.value for status in statuses if status.success]
        confidence_score = self._calculate_overall_confidence(results, statuses)
        total_time = (time.time() - start_time) * 1000

        self._remember_turn(session, request.query, assistant_response, assessment, capabilities_activated)

        return UnifiedIntelligenceResult(
            query_id=query_id,
            conversation_id=conversation_id,
            query=request.query,
            assessment=assessment,
            reasoning=results.get("reasoning"),
            tools=results.get("tools"),
            visuals=results.get("visuals"),
            map_intelligence=results.get("map_intelligence"),
            unified_summary=unified_summary,
            assistant_response=assistant_response,
            confidence_score=confidence_score,
            data_sources_used=data_sources,
            capabilities_activated=capabilities_activated,
            capability_statuses=capability_statuses,
            total_processing_time_ms=round(total_time, 2),
            timestamp=datetime.now().isoformat(),
        )

    def _get_or_create_session(self, conversation_id: str) -> ConversationSession:
        if conversation_id not in self._sessions:
            self._sessions[conversation_id] = ConversationSession(conversation_id=conversation_id)
        return self._sessions[conversation_id]

    def _build_enriched_context(self, request: UnifiedIntelligenceRequest, session: ConversationSession) -> Dict[str, Any]:
        context = dict(request.context or {})
        context["conversation_memory"] = {
            "conversation_id": session.conversation_id,
            "title": session.title,
            "memory_summary": session.memory_summary,
            "recent_turns": [turn.__dict__ for turn in session.turns[-6:]],
            "client_history": [message.model_dump() for message in request.conversation_history[-6:]],
            "previous_domains": session.domains,
            "last_capabilities": session.last_capabilities,
        }
        return context

    def _resolve_capabilities(self, assessment: QueryAssessment, request: UnifiedIntelligenceRequest) -> CapabilitySet:
        capabilities = assessment.suggested_capabilities
        if request.forced_capabilities:
            capabilities = CapabilitySet()
            for cap in request.forced_capabilities:
                if cap == CapabilityType.REASONING:
                    capabilities.reasoning = True
                elif cap == CapabilityType.TOOLS:
                    capabilities.tools = True
                elif cap == CapabilityType.VISUALS:
                    capabilities.visuals = True
                elif cap == CapabilityType.MAP_INTELLIGENCE:
                    capabilities.map_intelligence = True
        return capabilities

    def _capability_result_key(self, capability: CapabilityType) -> str:
        return "map_intelligence" if capability == CapabilityType.MAP_INTELLIGENCE else capability.value

    async def _execute_capabilities(
        self,
        query_id: str,
        query: str,
        context: Dict[str, Any],
        capabilities: CapabilitySet,
        max_time: float,
    ) -> Tuple[Dict[str, Any], List[CapabilityExecutionStatus]]:
        tasks = []
        capability_types: List[CapabilityType] = []
        if capabilities.reasoning:
            tasks.append(self._execute_reasoning(query_id, query, context))
            capability_types.append(CapabilityType.REASONING)
        if capabilities.tools:
            tasks.append(self._execute_tools(query_id, query, context))
            capability_types.append(CapabilityType.TOOLS)
        if capabilities.visuals:
            tasks.append(self._execute_visuals(query_id, query, context))
            capability_types.append(CapabilityType.VISUALS)
        if capabilities.map_intelligence:
            tasks.append(self._execute_map_intelligence(query_id, query, context))
            capability_types.append(CapabilityType.MAP_INTELLIGENCE)

        try:
            results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=max_time)
        except asyncio.TimeoutError:
            logger.warning(f"[{query_id}] Timeout after {max_time}s")
            results = [Exception("Timeout") for _ in tasks]

        results_dict: Dict[str, Any] = {}
        statuses: List[CapabilityExecutionStatus] = []
        for result, cap_type in zip(results, capability_types):
            if isinstance(result, Exception):
                statuses.append(CapabilityExecutionStatus(capability=cap_type, success=False, error_message=str(result)))
                continue
            if result is not None:
                results_dict[self._capability_result_key(cap_type)] = result
                statuses.append(
                    CapabilityExecutionStatus(
                        capability=cap_type,
                        success=True,
                        execution_time_ms=result.processing_time_ms if hasattr(result, "processing_time_ms") else 0.0,
                    )
                )
        return results_dict, statuses

    async def _execute_reasoning(self, query_id: str, query: str, context: Dict[str, Any]) -> Optional[ReasoningResult]:
        try:
            start = time.time()
            response = await run_expert_strategic_analysis(query=query, context=context)
            uncertainty = response.get("uncertainty_quantification", {})
            return ReasoningResult(
                executive_summary=response.get("executive_summary", ""),
                analysis=response.get("situation_analysis", response.get("executive_summary", "")),
                key_findings=response.get("key_findings", response.get("strategic_recommendations", [])[:5]),
                confidence=response.get("expert_assessment", {}).get("confidence", {}).get("score", 0.7),
                expert_agents_used=response.get("_meta", {}).get("expert_agents_consulted", []),
                consensus_achieved=response.get("_meta", {}).get("consensus_strength") not in ["weak", "divergent"],
                processing_time_ms=round((time.time() - start) * 1000, 2),
                risk_factors=response.get("key_risk_factors", [])[:4],
                strategic_recommendations=response.get("strategic_recommendations", [])[:5],
                uncertainty_factors=uncertainty.get("uncertainty_factors", [])[:4],
                timeline=response.get("timeline", [])[:4],
            )
        except Exception as e:
            logger.error(f"[{query_id}] Reasoning failed: {e}", exc_info=True)
            return None

    async def _execute_tools(self, query_id: str, query: str, context: Dict[str, Any]) -> Optional[ToolsResult]:
        try:
            start = time.time()
            memory_summary = context.get("conversation_memory", {}).get("memory_summary", "")
            tool_query = query if not memory_summary else f"{query}\n\nConversation memory:\n{memory_summary}"
            response = await run_strategic_analysis(tool_query)
            meta = response.get("_meta", {})
            tools_used = meta.get("tools_used", [])
            unavailable_tools = meta.get("unavailable_tools", {})
            tool_outputs = {key: value for key, value in response.items() if not key.startswith("_")}
            insights = []
            if response.get("executive_summary"):
                insights.append(response["executive_summary"])
            for factor in response.get("key_risk_factors", [])[:3]:
                if isinstance(factor, dict):
                    insights.append(f"{factor.get('factor', 'Signal')}: {factor.get('description', '')}".strip())
            for recommendation in response.get("strategic_recommendations", [])[:2]:
                insights.append(f"Action: {recommendation}")
            return ToolsResult(
                tools_executed=tools_used,
                data_sources=[tool.replace("_", " ").title() for tool in tools_used],
                tool_outputs=tool_outputs,
                insights=insights[:6],
                processing_time_ms=round((time.time() - start) * 1000, 2),
                unavailable_tools=unavailable_tools,
            )
        except Exception as e:
            logger.error(f"[{query_id}] Tools execution failed: {e}", exc_info=True)
            return None

    async def _execute_visuals(self, query_id: str, query: str, context: Dict[str, Any]) -> Optional[VisualsResult]:
        try:
            start = time.time()
            if self._visual_engine is None:
                self._visual_engine = get_visual_intelligence_engine()
            result = await self._visual_engine.process_query(query, context)
            charts = [chart.to_dict() for chart in result.charts]
            diagrams = [diagram.to_dict() for diagram in result.diagrams]
            return VisualsResult(
                charts=charts,
                diagrams=diagrams,
                chart_insights=[chart.get("insight", "") for chart in charts if chart.get("insight")],
                diagram_insights=[diagram.get("description", "") for diagram in diagrams if diagram.get("description")],
                processing_time_ms=round((time.time() - start) * 1000, 2),
            )
        except Exception as e:
            logger.error(f"[{query_id}] Visuals generation failed: {e}", exc_info=True)
            return None

    async def _execute_map_intelligence(self, query_id: str, query: str, context: Dict[str, Any]) -> Optional[MapIntelligenceResult]:
        try:
            start = time.time()
            if self._visual_engine is None:
                self._visual_engine = get_visual_intelligence_engine()
            if self._map_intelligence is None:
                self._map_intelligence = get_map_intelligence_layer()
            intent = await self._visual_engine.parse_intent(query)
            from app.models.visual_intelligence import DataFetchResult
            data_result = DataFetchResult(
                datasets={},
                sources_used=[],
                sources_failed=[],
                data_quality_score=0.5,
                time_coverage=None,
                geo_coverage=intent.countries,
            )
            map_output = await self._map_intelligence.generate_map_intelligence(intent, data_result)
            return MapIntelligenceResult(
                commands=map_output.commands,
                affected_regions=map_output.affected_regions,
                markers=[marker.to_dict() for marker in map_output.markers],
                routes=[route.to_dict() for route in map_output.routes],
                heatmap_data=map_output.heatmap_data,
                processing_time_ms=round((time.time() - start) * 1000, 2),
            )
        except Exception as e:
            logger.error(f"[{query_id}] Map intelligence failed: {e}", exc_info=True)
            return None

    async def _synthesize_unified_summary(self, query: str, results: Dict[str, Any]) -> str:
        parts: List[str] = []
        if results.get("reasoning"):
            parts.append(results["reasoning"].executive_summary)
        if results.get("tools") and results["tools"].insights:
            parts.append("Live evidence: " + " ".join(results["tools"].insights[:2]))
        if results.get("visuals"):
            artifact_bits = []
            if results["visuals"].charts:
                artifact_bits.append(f"{len(results['visuals'].charts)} chart(s)")
            if results["visuals"].diagrams:
                artifact_bits.append(f"{len(results['visuals'].diagrams)} diagram(s)")
            if artifact_bits:
                parts.append("Generated " + " and ".join(artifact_bits) + " to support the answer.")
        if results.get("map_intelligence") and results["map_intelligence"].affected_regions:
            parts.append(f"Spatial layer covers {', '.join(results['map_intelligence'].affected_regions[:3])}.")
        if not parts:
            parts.append(f"Analysis for '{query}' completed, but the capability outputs were limited.")
        return " ".join(parts)

    async def _build_assistant_response(
        self,
        query: str,
        assessment: QueryAssessment,
        results: Dict[str, Any],
        statuses: List[CapabilityExecutionStatus],
        unified_summary: str,
        session: ConversationSession,
    ) -> AssistantResponsePayload:
        if self._llm is not None:
            llm_payload = await self._try_llm_assistant_response(
                query=query,
                assessment=assessment,
                results=results,
                statuses=statuses,
                unified_summary=unified_summary,
                session=session,
            )
            if llm_payload is not None:
                return llm_payload
        return self._build_deterministic_response(query, assessment, results, statuses, unified_summary, session)

    async def _try_llm_assistant_response(
        self,
        query: str,
        assessment: QueryAssessment,
        results: Dict[str, Any],
        statuses: List[CapabilityExecutionStatus],
        unified_summary: str,
        session: ConversationSession,
    ) -> Optional[AssistantResponsePayload]:
        try:
            compact = {
                "assessment": assessment.to_dict(),
                "summary": unified_summary,
                "reasoning": results.get("reasoning").to_dict() if results.get("reasoning") else None,
                "tools": results.get("tools").to_dict() if results.get("tools") else None,
                "visuals": {
                    "chart_count": len(results["visuals"].charts),
                    "diagram_count": len(results["visuals"].diagrams),
                    "chart_insights": results["visuals"].chart_insights[:3],
                    "diagram_insights": results["visuals"].diagram_insights[:2],
                } if results.get("visuals") else None,
                "map_intelligence": results.get("map_intelligence").to_dict() if results.get("map_intelligence") else None,
                "statuses": [status.to_dict() for status in statuses],
                "memory_summary": session.memory_summary,
            }
            prompt = (
                "You are a unified intelligence assistant. Produce a sharp, practical answer like an elite AI analyst assistant. "
                "Keep uncertainty explicit and avoid hype. Return ONLY valid JSON with keys "
                "title, executive_brief, key_takeaways, next_actions, suggested_follow_ups, memory_summary, response_blocks. "
                "Each response_blocks item must contain title, content, tone.\n\n"
                f"User query: {query}\nPayload: {json.dumps(compact, default=str)[:12000]}"
            )
            response = await self._llm.ainvoke(prompt)
            payload = self._parse_json_blob(getattr(response, "content", str(response)))
            return AssistantResponsePayload(
                title=payload.get("title", self._derive_title(query, assessment)),
                executive_brief=payload.get("executive_brief", unified_summary),
                key_takeaways=payload.get("key_takeaways", [])[:5],
                next_actions=payload.get("next_actions", [])[:4],
                suggested_follow_ups=payload.get("suggested_follow_ups", [])[:4],
                memory_summary=payload.get("memory_summary", self._build_memory_summary(session, query, [])),
                response_blocks=[
                    AssistantResponseSection(
                        title=block.get("title", "Analysis"),
                        content=block.get("content", ""),
                        tone=block.get("tone", "default"),
                    )
                    for block in payload.get("response_blocks", [])[:4]
                    if block.get("content")
                ],
                artifact_overview=self._build_artifact_overview(results, statuses),
            )
        except Exception as e:
            logger.warning(f"LLM assistant synthesis failed, using deterministic fallback: {e}")
            return None

    def _build_deterministic_response(
        self,
        query: str,
        assessment: QueryAssessment,
        results: Dict[str, Any],
        statuses: List[CapabilityExecutionStatus],
        unified_summary: str,
        session: ConversationSession,
    ) -> AssistantResponsePayload:
        reasoning = results.get("reasoning")
        tools = results.get("tools")
        visuals = results.get("visuals")
        map_data = results.get("map_intelligence")
        takeaways: List[str] = []
        actions: List[str] = []
        if reasoning and reasoning.key_findings:
            takeaways.extend(reasoning.key_findings[:3])
            actions.extend(reasoning.strategic_recommendations[:3])
        if tools and tools.insights:
            takeaways.extend([item for item in tools.insights[:2] if item not in takeaways])
        if visuals and visuals.charts:
            actions.append("Use the generated charts to brief stakeholders on trend direction and divergence.")
        if map_data and map_data.affected_regions:
            actions.append(f"Validate geographic exposure in {', '.join(map_data.affected_regions[:3])}.")
        if not takeaways:
            takeaways.append(unified_summary)
        blocks = [AssistantResponseSection(title="What matters now", content=unified_summary, tone="priority")]
        evidence_parts = []
        if tools and tools.data_sources:
            evidence_parts.append("Sources used: " + ", ".join(tools.data_sources[:6]))
        if tools and tools.unavailable_tools:
            evidence_parts.append("Unavailable connectors: " + ", ".join(list(tools.unavailable_tools.keys())[:4]))
        if reasoning and reasoning.uncertainty_factors:
            evidence_parts.append("Uncertainty: " + "; ".join(reasoning.uncertainty_factors[:3]))
        if evidence_parts:
            blocks.append(AssistantResponseSection(title="Evidence and caveats", content=" ".join(evidence_parts), tone="evidence"))
        if actions:
            blocks.append(AssistantResponseSection(title="Recommended next moves", content=" ".join(f"{idx + 1}. {item}" for idx, item in enumerate(actions[:3])), tone="action"))
        return AssistantResponsePayload(
            title=self._derive_title(query, assessment),
            executive_brief=unified_summary,
            key_takeaways=takeaways[:5],
            next_actions=actions[:4],
            suggested_follow_ups=[
                f"What changed versus the prior context for {assessment.domains[0]}?",
                "Which risks are most likely over the next 30 days?",
                "Turn this into an executive briefing with sharper recommendations.",
                "Show the strongest evidence and the weakest assumptions.",
            ],
            memory_summary=self._build_memory_summary(session, query, takeaways),
            response_blocks=blocks,
            artifact_overview=self._build_artifact_overview(results, statuses),
        )

    def _build_artifact_overview(self, results: Dict[str, Any], statuses: List[CapabilityExecutionStatus]) -> Dict[str, Any]:
        visuals = results.get("visuals")
        map_data = results.get("map_intelligence")
        return {
            "charts": len(visuals.charts) if visuals else 0,
            "diagrams": len(visuals.diagrams) if visuals else 0,
            "map_markers": len(map_data.markers) if map_data else 0,
            "map_routes": len(map_data.routes) if map_data else 0,
            "successful_capabilities": sum(1 for status in statuses if status.success),
            "failed_capabilities": sum(1 for status in statuses if not status.success),
        }

    def _build_memory_summary(self, session: ConversationSession, query: str, takeaways: List[str]) -> str:
        latest = "; ".join(takeaways[:3]) if takeaways else query
        if session.memory_summary:
            return f"{session.memory_summary} Latest focus: {query}. Current takeaways: {latest}."
        return f"Conversation focus: {query}. Current takeaways: {latest}."

    def _derive_title(self, query: str, assessment: QueryAssessment) -> str:
        domain = assessment.domains[0].replace("_", " ").title() if assessment.domains else "General"
        return f"{domain} Brief: {' '.join(query.strip().split())[:48]}"

    def _remember_turn(
        self,
        session: ConversationSession,
        query: str,
        assistant_response: AssistantResponsePayload,
        assessment: QueryAssessment,
        capabilities_activated: List[str],
    ) -> None:
        now = datetime.now().isoformat()
        session.turns.append(ConversationTurn(role="user", content=query, timestamp=now))
        session.turns.append(ConversationTurn(role="assistant", content=assistant_response.executive_brief, timestamp=now))
        session.turns = session.turns[-self._max_turns:]
        session.memory_summary = assistant_response.memory_summary
        session.last_capabilities = capabilities_activated
        session.domains = list(dict.fromkeys([*session.domains, *assessment.domains]))[-6:]
        if session.title == "Unified Intelligence Session":
            session.title = self._derive_title(query, assessment)
        session.last_updated = now

    def _collect_data_sources(self, results: Dict[str, Any]) -> List[str]:
        sources: List[str] = []
        if results.get("tools"):
            sources.extend(results["tools"].data_sources)
        if results.get("visuals"):
            sources.extend(["World Bank", "Data Commons", "QuickChart"])
        if results.get("reasoning"):
            sources.append("Expert Analysis System")
        return list(dict.fromkeys(sources))

    def _calculate_overall_confidence(self, results: Dict[str, Any], statuses: List[CapabilityExecutionStatus]) -> float:
        total_score = 0.0
        count = 0
        if results.get("reasoning"):
            total_score += results["reasoning"].confidence
            count += 1
        if statuses:
            total_score += sum(1 for status in statuses if status.success) / len(statuses)
            count += 1
        return round(total_score / count, 2) if count else 0.7

    def _parse_json_blob(self, content: str) -> Dict[str, Any]:
        text = content.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= start:
            text = text[start:end + 1]
        return json.loads(text)


_unified_intelligence_engine: Optional[UnifiedIntelligenceEngine] = None


def get_unified_intelligence_engine() -> UnifiedIntelligenceEngine:
    global _unified_intelligence_engine
    if _unified_intelligence_engine is None:
        _unified_intelligence_engine = UnifiedIntelligenceEngine()
    return _unified_intelligence_engine
