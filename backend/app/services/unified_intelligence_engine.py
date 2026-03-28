import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Callable, Awaitable

from app.models.unified_intelligence import (
    UnifiedIntelligenceRequest,
    UnifiedIntelligenceResult,
    QueryAssessment,
    QueryComplexity,
    CapabilitySet,
    CapabilityType,
    UnifiedExecutionMode,
    ReasoningResult,
    ToolsResult,
    VisualsResult,
    MapIntelligenceResult,
    CapabilityExecutionStatus,
    AssistantResponsePayload,
    AssistantResponseSection,
    CockpitState,
    UnifiedExecutionPlan,
    UnifiedExecutionStep,
)
from app.agents.agent_orchestrator import ExpertAgentOrchestrator
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
    VISUAL_TRIGGER_KEYWORDS = [
        "graph", "chart", "plot", "visualize", "visualization", "dashboard", "bar chart", "line chart", "pie chart",
    ]
    EXTERNAL_TRIGGER_KEYWORDS = [
        "latest", "current", "recent", "real-time", "today", "now", "breaking", "live",
    ]

    async def assess_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryAssessment:
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
        requires_external = tools_score > 0 or any(kw in query_lower for kw in self.EXTERNAL_TRIGGER_KEYWORDS)
        requires_multi_perspective = reasoning_score >= 2 or any(
            kw in query_lower for kw in ["compare", "contrast", "debate", "multiple", "various"]
        )
        visual_only_request = any(kw in query_lower for kw in self.VISUAL_TRIGGER_KEYWORDS) and not any(
            kw in query_lower
            for kw in ["latest", "current", "recent", "debate", "consensus", "simulate", "what if", "risk", "live"]
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
        if requires_external or tools_score > 0:
            capabilities.tools = True
        if visuals_score > 0 or (has_data_indicators and has_time_dimension) or visual_only_request:
            capabilities.visuals = True
        if has_geographic:
            capabilities.map_intelligence = True
        if visual_only_request:
            capabilities.reasoning = False
            capabilities.tools = False
            capabilities.map_intelligence = False
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


class UnifiedExecutionPlanner:
    """Query planner that converts a request into an explicit execution blueprint."""

    DOMAIN_AGENT_MAP = {
        "economics": "economic",
        "geopolitics": "geopolitical",
        "defense": "geopolitical",
        "climate": "climate",
        "infrastructure": "policy",
        "technology": "economic",
        "space": "geopolitical",
        "general": "risk",
    }

    def build_plan(
        self,
        query: str,
        assessment: QueryAssessment,
        request: UnifiedIntelligenceRequest,
        capabilities: CapabilitySet,
    ) -> UnifiedExecutionPlan:
        query_lower = query.lower()
        capability_list = capabilities.to_list()
        reasoning_agents = self._select_reasoning_agents(assessment, request.execution_mode, query_lower, bool(capabilities.reasoning))
        selected_tools = self._select_tools(assessment, request.execution_mode, query_lower, bool(capabilities.tools))
        search_queries = self._build_search_queries(query, assessment)
        rationale = self._build_rationale(assessment, request, capability_list, reasoning_agents, selected_tools)
        steps = self._build_steps(capabilities, reasoning_agents, selected_tools)

        if request.execution_mode == UnifiedExecutionMode.FAST:
            response_style = "brief_source_grounded"
        elif request.execution_mode == UnifiedExecutionMode.TOOLS_ONLY:
            response_style = "source_only"
        elif assessment.requires_multi_perspective:
            response_style = "multi_perspective"
        else:
            response_style = "balanced"

        priority = "critical" if assessment.requires_external_data or assessment.complexity in {QueryComplexity.COMPLEX, QueryComplexity.VERY_COMPLEX} else "standard"
        intent_summary = self._intent_summary(query, assessment, capability_list, reasoning_agents, selected_tools)

        return UnifiedExecutionPlan(
            intent_summary=intent_summary,
            priority=priority,
            execution_mode=request.execution_mode.value,
            capabilities=capability_list,
            reasoning_agents=reasoning_agents,
            tools=selected_tools,
            search_queries=search_queries,
            response_style=response_style,
            rationale=rationale,
            steps=steps,
        )

    def _select_reasoning_agents(
        self,
        assessment: QueryAssessment,
        mode: UnifiedExecutionMode,
        query_lower: str,
        enabled: bool,
    ) -> List[str]:
        if not enabled:
            return []

        selected: List[str] = ["risk"]
        for domain in assessment.domains:
            agent = self.DOMAIN_AGENT_MAP.get(domain)
            if agent and agent not in selected:
                selected.append(agent)

        if assessment.requires_multi_perspective:
            for fallback in ["economic", "geopolitical", "policy"]:
                if fallback not in selected:
                    selected.append(fallback)
                if len(selected) >= 4:
                    break

        if any(token in query_lower for token in ["forecast", "future", "scenario", "what if", "simulate"]):
            if "simulation" not in selected:
                selected.append("simulation")

        max_agents = 2 if mode == UnifiedExecutionMode.FAST else 4
        return selected[:max_agents]

    def _select_tools(
        self,
        assessment: QueryAssessment,
        mode: UnifiedExecutionMode,
        query_lower: str,
        enabled: bool,
    ) -> List[str]:
        if not enabled:
            return []

        tools = ["source_health", "recent_briefs", "search_bundle"]
        if assessment.requires_external_data or any(token in query_lower for token in ["latest", "current", "recent", "breaking", "live"]):
            tools.append("alerts")
        if assessment.has_data_indicators or "economics" in assessment.domains:
            tools.append("market_snapshot")
        if assessment.has_geographic_entities or any(token in query_lower for token in ["country", "india", "china", "usa", "region", "border"]):
            tools.append("country_analysis")
        if mode == UnifiedExecutionMode.FAST:
            tools = [tool for tool in tools if tool in {"recent_briefs", "search_bundle", "country_analysis", "source_health"}]
        return list(dict.fromkeys(tools))

    def _build_search_queries(self, query: str, assessment: QueryAssessment) -> List[str]:
        queries = [query]
        if "economics" in assessment.domains:
            queries.append(f"{query} macroeconomic outlook latest")
        if "geopolitics" in assessment.domains or "defense" in assessment.domains:
            queries.append(f"{query} geopolitics conflict diplomacy latest")
        if "climate" in assessment.domains:
            queries.append(f"{query} climate disaster weather latest")
        return list(dict.fromkeys(queries))[:3]

    def _build_rationale(
        self,
        assessment: QueryAssessment,
        request: UnifiedIntelligenceRequest,
        capabilities: List[str],
        reasoning_agents: List[str],
        tools: List[str],
    ) -> List[str]:
        reasons = [
            f"Execution mode '{request.execution_mode.value}' selected with capabilities: {', '.join(capabilities) or 'none'}.",
            f"Query complexity assessed as {assessment.complexity.value} across domains: {', '.join(assessment.domains)}.",
        ]
        if reasoning_agents:
            reasons.append(f"Reasoning lane constrained to agents: {', '.join(reasoning_agents)}.")
        if tools:
            reasons.append(f"Tools lane will run: {', '.join(tools)}.")
        if assessment.requires_external_data:
            reasons.append("External-data triggers were detected, so live or cached source fetch is prioritized.")
        if assessment.requires_multi_perspective:
            reasons.append("Multi-perspective analysis was requested, so cross-domain agents are included.")
        return reasons[:6]

    def _build_steps(
        self,
        capabilities: CapabilitySet,
        reasoning_agents: List[str],
        tools: List[str],
    ) -> List[UnifiedExecutionStep]:
        steps: List[UnifiedExecutionStep] = [
            UnifiedExecutionStep(id="assess", label="Assess query intent and select execution lanes", lane="planner", parallelizable=False),
        ]
        if capabilities.tools:
            steps.append(
                UnifiedExecutionStep(
                    id="tools",
                    label="Fetch live, cached, and search-grounded evidence",
                    lane="tools",
                    parallelizable=True,
                    selected_tools=tools,
                )
            )
        if capabilities.reasoning:
            steps.append(
                UnifiedExecutionStep(
                    id="reasoning",
                    label="Run targeted expert-agent reasoning",
                    lane="reasoning",
                    parallelizable=True,
                    selected_agents=reasoning_agents,
                )
            )
        if capabilities.visuals:
            steps.append(UnifiedExecutionStep(id="visuals", label="Generate visual artifacts only if materially useful", lane="visuals", parallelizable=True))
        if capabilities.map_intelligence:
            steps.append(UnifiedExecutionStep(id="map", label="Generate map overlays and geographic focus payloads", lane="map", parallelizable=True))
        steps.append(UnifiedExecutionStep(id="synthesis", label="Assemble assistant response from completed lanes", lane="synthesis", parallelizable=False))
        return steps

    def _intent_summary(
        self,
        query: str,
        assessment: QueryAssessment,
        capabilities: List[str],
        reasoning_agents: List[str],
        tools: List[str],
    ) -> str:
        parts = [f"Query targets {', '.join(assessment.domains)} analysis"]
        if capabilities:
            parts.append(f"using {', '.join(capabilities)}")
        if reasoning_agents:
            parts.append(f"with agents {', '.join(reasoning_agents)}")
        if tools:
            parts.append(f"and tools {', '.join(tools)}")
        return " ".join(parts) + "."


class UnifiedIntelligenceEngine:
    def __init__(self):
        self._assessor = QueryAssessor()
        self._planner = UnifiedExecutionPlanner()
        self._expert_orchestrator = ExpertAgentOrchestrator()
        self._fast_expert_orchestrator = ExpertAgentOrchestrator(
            enable_debate=False,
            min_agents_for_debate=99,
            debate_threshold=1.0,
            max_parallel_agents=2,
        )
        self._visual_engine = None
        self._map_intelligence = None
        self._sessions: Dict[str, ConversationSession] = {}
        self._max_turns = 12
        try:
            self._llm = get_enterprise_llm(temperature=0.3)
        except RuntimeError:
            logger.warning("Unified intelligence LLM synthesis unavailable; using deterministic synthesis.")
            self._llm = None

    async def _emit_stream_event(
        self,
        stream_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]],
        event_type: str,
        **payload: Any,
    ) -> None:
        """Emit a best-effort stream event when a callback is provided."""
        if stream_callback is None:
            return
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            **payload,
        }
        try:
            await stream_callback(event)
        except Exception as exc:
            logger.debug(f"Stream callback failed for event '{event_type}': {exc}")

    async def analyze(
        self,
        request: UnifiedIntelligenceRequest,
        stream_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None,
    ) -> UnifiedIntelligenceResult:
        start_time = time.time()
        query_id = str(uuid.uuid4())[:8]
        conversation_id = request.conversation_id or str(uuid.uuid4())[:12]
        await self._emit_stream_event(
            stream_callback,
            "phase",
            phase="accepted",
            message="Request accepted. Preparing orchestration context.",
            query_id=query_id,
            conversation_id=conversation_id,
        )

        session = self._get_or_create_session(conversation_id)
        context = self._build_enriched_context(request, session)
        context["execution_mode"] = request.execution_mode.value
        assessment = await self._assessor.assess_query(request.query, context)
        await self._emit_stream_event(
            stream_callback,
            "phase",
            phase="assessment",
            message="Query assessment completed.",
            assessment=assessment.to_dict(),
        )

        capabilities = self._resolve_capabilities(assessment, request)
        execution_plan = self._planner.build_plan(request.query, assessment, request, capabilities)
        context["execution_plan"] = execution_plan.to_dict()
        await self._emit_stream_event(
            stream_callback,
            "phase",
            phase="capabilities_selected",
            message="Capabilities selected for execution.",
            capabilities=capabilities.to_list(),
        )
        await self._emit_stream_event(
            stream_callback,
            "execution_plan",
            message="Execution plan synthesized.",
            execution_plan=execution_plan.to_dict(),
        )

        execution_timeout = request.max_processing_time or 30.0
        if request.execution_mode == UnifiedExecutionMode.FAST:
            execution_timeout = min(execution_timeout, 8.0)

        results, statuses = await self._execute_capabilities(
            query_id=query_id,
            query=request.query,
            context=context,
            capabilities=capabilities,
            max_time=execution_timeout,
        )
        for status in statuses:
            await self._emit_stream_event(
                stream_callback,
                "capability",
                capability=status.capability.value,
                success=status.success,
                execution_time_ms=status.execution_time_ms,
                error_message=status.error_message,
                fallback_used=status.fallback_used,
            )

        map_commands: List[Dict[str, Any]] = []
        visual_markers: List[Dict[str, Any]] = []
        spawned_panels: List[Dict[str, Any]] = []
        map_result = results.get("map_intelligence")
        if map_result:
            map_commands, visual_markers, spawned_panels = self._derive_unified_map_payload(map_result)
            map_result.map_commands = map_commands
            map_result.visual_markers = visual_markers
            map_result.spawned_panels = spawned_panels
            persisted_commands = self._persist_map_commands(map_commands)
            if persisted_commands:
                map_commands = persisted_commands
                map_result.map_commands = persisted_commands
            await self._emit_stream_event(
                stream_callback,
                "map_update",
                message="Map overlays prepared.",
                map_commands=map_commands[:16],
                visual_markers=visual_markers[:32],
                spawned_panels=spawned_panels,
            )

        cockpit_state = self._build_cockpit_state(
            assessment=assessment,
            results=results,
            statuses=statuses,
            map_commands=map_commands,
            visual_markers=visual_markers,
        )
        await self._emit_stream_event(
            stream_callback,
            "cockpit_state",
            message="Cockpit state synthesized.",
            cockpit_state=cockpit_state.to_dict(),
        )

        await self._emit_stream_event(
            stream_callback,
            "thought",
            phase="synthesis",
            message="Synthesizing unified assistant response.",
        )

        allow_cloud_synthesis = (
            request.execution_mode != UnifiedExecutionMode.FAST
            and not self._is_sensitive_local_context(context)
        )
        unified_summary = await self._synthesize_unified_summary(request.query, results)
        assistant_response = await self._build_assistant_response(
            query=request.query,
            assessment=assessment,
            results=results,
            statuses=statuses,
            unified_summary=unified_summary,
            session=session,
            allow_cloud_synthesis=allow_cloud_synthesis,
        )
        data_sources = self._collect_data_sources(results)
        capability_statuses = [status.to_dict() for status in statuses]
        capabilities_activated = [status.capability.value for status in statuses if status.success]
        confidence_score = self._calculate_overall_confidence(results, statuses)
        total_time = (time.time() - start_time) * 1000

        self._remember_turn(session, request.query, assistant_response, assessment, capabilities_activated)

        result = UnifiedIntelligenceResult(
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
            map_commands=map_commands,
            visual_markers=visual_markers,
            cockpit_state=cockpit_state,
            capabilities_activated=capabilities_activated,
            capability_statuses=capability_statuses,
            total_processing_time_ms=round(total_time, 2),
            timestamp=datetime.now().isoformat(),
            execution_plan=execution_plan,
        )

        await self._emit_stream_event(
            stream_callback,
            "phase",
            phase="completed",
            message="Unified analysis completed.",
            query_id=query_id,
            total_processing_time_ms=round(total_time, 2),
        )
        return result

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

    def _is_sensitive_local_context(self, context: Dict[str, Any]) -> bool:
        """Return True when local uploads are marked summary/local-only for cloud transmission safeguards."""
        local_data = context.get("local_data")
        if not isinstance(local_data, dict):
            return False
        transmission_mode = str(local_data.get("transmission_mode") or "").strip().lower()
        return transmission_mode in {"summary_only", "local_only", "local_summary_only"}

    def _resolve_capabilities(self, assessment: QueryAssessment, request: UnifiedIntelligenceRequest) -> CapabilitySet:
        mode = request.execution_mode
        query_lower = request.query.lower()
        capabilities = CapabilitySet(
            reasoning=assessment.suggested_capabilities.reasoning,
            tools=assessment.suggested_capabilities.tools,
            visuals=assessment.suggested_capabilities.visuals,
            map_intelligence=assessment.suggested_capabilities.map_intelligence,
        )

        def from_capability_list(cap_list: Optional[List[CapabilityType]]) -> CapabilitySet:
            selected = CapabilitySet()
            for cap in cap_list or []:
                if cap == CapabilityType.REASONING:
                    selected.reasoning = True
                elif cap == CapabilityType.TOOLS:
                    selected.tools = True
                elif cap == CapabilityType.VISUALS:
                    selected.visuals = True
                elif cap == CapabilityType.MAP_INTELLIGENCE:
                    selected.map_intelligence = True
            return selected

        if request.forced_capabilities:
            return from_capability_list(request.forced_capabilities)

        if mode == UnifiedExecutionMode.MANUAL:
            manual = from_capability_list(request.manual_capabilities)
            return manual if manual.count() > 0 else capabilities
        if mode == UnifiedExecutionMode.VISUAL_ONLY:
            return CapabilitySet(visuals=True)
        if mode == UnifiedExecutionMode.REASONING_ONLY:
            return CapabilitySet(reasoning=True)
        if mode == UnifiedExecutionMode.TOOLS_ONLY:
            return CapabilitySet(tools=True)
        if mode == UnifiedExecutionMode.MAP_ONLY:
            return CapabilitySet(map_intelligence=True)
        if mode == UnifiedExecutionMode.FAST:
            # Fast mode is explicitly data-first and lightweight:
            # fetch live/cached sources plus a 1-2 agent reasoning pass.
            return CapabilitySet(reasoning=True, tools=True)

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
        execution_context = dict(context)
        execution_context["_capabilities"] = capabilities.to_list()
        tasks = []
        capability_types: List[CapabilityType] = []
        if capabilities.reasoning:
            tasks.append(self._execute_reasoning(query_id, query, execution_context))
            capability_types.append(CapabilityType.REASONING)
        if capabilities.tools:
            tasks.append(self._execute_tools(query_id, query, execution_context))
            capability_types.append(CapabilityType.TOOLS)
        if capabilities.visuals:
            tasks.append(self._execute_visuals(query_id, query, execution_context))
            capability_types.append(CapabilityType.VISUALS)
        if capabilities.map_intelligence:
            tasks.append(self._execute_map_intelligence(query_id, query, execution_context))
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
                        execution_time_ms=float(getattr(result, "processing_time_ms", 0.0)),
                    )
                )
        return results_dict, statuses

    def _reasoning_result_from_orchestrated(self, response: Any) -> ReasoningResult:
        disagreement_risks = [
            {
                "factor": str(item.get("topic") or "Analyst disagreement"),
                "severity": str(item.get("severity") or "Medium"),
                "description": ", ".join(item.get("agent_names", [])[:3]) or "Cross-agent variance detected.",
            }
            for item in (response.disagreements or [])[:4]
        ]
        return ReasoningResult(
            executive_summary=response.executive_summary,
            analysis=response.consensus.consensus_view if response.consensus else response.executive_summary,
            key_findings=response.key_findings[:6],
            confidence=response.confidence_score,
            expert_agents_used=response.agents_consulted,
            consensus_achieved=bool(response.consensus and response.consensus.consensus_strength.value not in ["weak", "divergent"]),
            processing_time_ms=round(float(response.processing_time_ms or 0.0), 2),
            risk_factors=disagreement_risks,
            strategic_recommendations=response.recommendations[:5],
            uncertainty_factors=response.uncertainty_factors[:5],
            timeline=response.timeline[:4],
        )

    async def _execute_reasoning(self, query_id: str, query: str, context: Dict[str, Any]) -> Optional[ReasoningResult]:
        try:
            mode = str(context.get("execution_mode") or UnifiedExecutionMode.AUTO.value)
            execution_plan = context.get("execution_plan") if isinstance(context.get("execution_plan"), dict) else {}
            forced_agents = execution_plan.get("reasoning_agents") or None
            if mode == UnifiedExecutionMode.FAST.value:
                response = await self._fast_expert_orchestrator.process_query(
                    query=query,
                    context=context,
                    force_agents=forced_agents[:2] if forced_agents else None,
                )
            else:
                response = await self._expert_orchestrator.process_query(
                    query=query,
                    context=context,
                    force_agents=forced_agents,
                )
            return self._reasoning_result_from_orchestrated(response)
        except Exception as e:
            logger.error(f"[{query_id}] Reasoning failed: {e}", exc_info=True)
            return None

    async def _execute_tools(self, query_id: str, query: str, context: Dict[str, Any]) -> Optional[ToolsResult]:
        try:
            start = time.time()
            from app.services.runtime_intelligence import runtime_engine
            from app.services.feed_aggregator import feed_engine
            from app.services.osint_aggregator import osint_engine

            matched_country = runtime_engine.find_country_by_query(query)
            execution_plan = context.get("execution_plan") if isinstance(context.get("execution_plan"), dict) else {}
            planned_tools = set(execution_plan.get("tools", []))
            planned_search_queries = execution_plan.get("search_queries") or []
            search_query = planned_search_queries[0] if planned_search_queries else (query if not matched_country else f"{matched_country['name']} strategic outlook latest")

            task_builders: Dict[str, Callable[[], Awaitable[Any]]] = {
                "source_health": lambda: asyncio.to_thread(lambda: runtime_engine.get_source_health()[:12]),
                "market_snapshot": lambda: asyncio.to_thread(lambda: runtime_engine.get_market_snapshot()[:6]),
                "recent_briefs": lambda: asyncio.to_thread(lambda: feed_engine.get_recent_briefs(10)),
                "alerts": lambda: asyncio.to_thread(lambda: runtime_engine.get_global_alerts()[:8]),
                "search_bundle": lambda: asyncio.to_thread(lambda: osint_engine.search_query_bundle(search_query, limit=12, max_providers=4)),
            }
            if matched_country:
                task_builders["country_analysis"] = lambda: asyncio.to_thread(lambda: runtime_engine.get_country_analysis(matched_country["id"]))

            selected_tool_names = [name for name in task_builders.keys() if not planned_tools or name in planned_tools]
            task_specs: Dict[str, Awaitable[Any]] = {name: task_builders[name]() for name in selected_tool_names}

            task_names = list(task_specs.keys())
            task_results = await asyncio.gather(*task_specs.values(), return_exceptions=True)

            tool_outputs: Dict[str, Any] = {}
            unavailable_tools: Dict[str, Any] = {}
            tools_used: List[str] = []
            insights: List[str] = []

            for name, result in zip(task_names, task_results):
                if isinstance(result, Exception):
                    unavailable_tools[name] = {"status": "error", "message": str(result)}
                    continue
                if result is None:
                    unavailable_tools[name] = {"status": "unavailable", "message": "No payload returned."}
                    continue
                tool_outputs[name] = result
                tools_used.append(name)

            source_health = tool_outputs.get("source_health", [])
            market_snapshot = tool_outputs.get("market_snapshot", [])
            recent_briefs = tool_outputs.get("recent_briefs", [])
            alerts = tool_outputs.get("alerts", [])
            search_bundle = tool_outputs.get("search_bundle", {})
            country_analysis = tool_outputs.get("country_analysis")

            live_connectors = len([item for item in source_health if item.get("status") == "live"])
            degraded_connectors = len([item for item in source_health if item.get("status") not in {"live", "limited"}])
            insights.append(f"{live_connectors} live source connectors are healthy across the runtime intelligence layer.")
            if degraded_connectors:
                insights.append(f"{degraded_connectors} connectors are degraded, rate-limited, timed out, or otherwise unavailable.")
            if market_snapshot:
                insights.append(f"{len(market_snapshot)} market instruments were included for quick macro context.")
            if recent_briefs:
                insights.append(f"{len(recent_briefs)} recent intelligence briefs were loaded from the feed cache.")
            if alerts:
                insights.append(f"{len(alerts)} active alert items were pulled into the tools layer.")
            if search_bundle:
                provider_names = [
                    provider.get("source")
                    for provider in search_bundle.get("providers", [])
                    if provider.get("status") == "live"
                ]
                result_count = len(search_bundle.get("results", []))
                if result_count:
                    insights.append(
                        f"Open-web search merged {result_count} deduplicated hits from "
                        f"{', '.join(provider_names[:4]) if provider_names else 'cached/open-search providers'}."
                    )
                for provider in search_bundle.get("providers", []):
                    if provider.get("status") not in {"live", "limited"}:
                        unavailable_tools[f"search_provider:{provider.get('source')}"] = {
                            "status": provider.get("status"),
                            "message": provider.get("message") or "Search provider unavailable.",
                        }
            if country_analysis:
                insights.append(
                    f"Country-specific live dossier loaded for {matched_country['name']} with source status and search validation."
                )

            return ToolsResult(
                tools_executed=tools_used,
                data_sources=list(
                    dict.fromkeys(
                        [
                            "Runtime Intelligence",
                            "Feed Aggregator",
                            *[
                                provider.get("source")
                                for provider in search_bundle.get("providers", [])
                                if provider.get("source")
                            ],
                        ]
                    )
                ),
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

    def _normalize_country_id(self, value: Any) -> Optional[str]:
        """Normalize country identifiers to the CTR-XXX format used by frontend data."""
        if value is None:
            return None
        token = str(value).strip().upper()
        if not token:
            return None
        if token.startswith("CTR-"):
            return token
        if len(token) == 3 and token.isalpha():
            return f"CTR-{token}"
        return token

    def _normalize_map_command(self, command: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize command dictionaries into shared map-command schema."""
        raw_type = str(command.get("command_type") or command.get("type") or "").strip().lower()
        if not raw_type:
            return None

        allowed_types = {"highlight", "route", "heatmap", "focus", "marker", "overlay", "clear"}
        if raw_type not in allowed_types:
            return None

        priority = str(command.get("priority") or "medium").strip().lower()
        if priority not in {"low", "medium", "high", "critical"}:
            priority = "medium"

        payload = command.get("data") if isinstance(command.get("data"), dict) else {}
        if not payload:
            payload = {
                key: value
                for key, value in command.items()
                if key not in {"id", "command_type", "type", "priority", "description", "source", "created_at", "timestamp", "metadata", "data"}
            }

        normalized: Dict[str, Any] = {
            "id": str(command.get("id") or f"cmd-{uuid.uuid4().hex[:8]}"),
            "command_type": raw_type,
            "priority": priority,
            "data": dict(payload),
            "description": str(command.get("description") or f"{raw_type.title()} command"),
            "source": str(command.get("source") or "unified_intelligence_engine"),
            "created_at": str(command.get("created_at") or command.get("timestamp") or datetime.utcnow().isoformat()),
            "metadata": command.get("metadata") if isinstance(command.get("metadata"), dict) else {},
        }

        data = normalized["data"]
        if raw_type == "highlight":
            country_ids = data.get("country_ids") or command.get("country_ids") or []
            if isinstance(country_ids, list):
                normalized_ids = []
                for country_id in country_ids:
                    mapped = self._normalize_country_id(country_id)
                    if mapped:
                        normalized_ids.append(mapped)
                data["country_ids"] = normalized_ids
            data.setdefault("color", command.get("color", "#3b82f6"))
            data.setdefault("pulse", command.get("pulse", True))
            data.setdefault("radius", command.get("radius", 400000))

        if raw_type == "focus":
            country_id = data.get("country_id") or command.get("country_id")
            normalized_country_id = self._normalize_country_id(country_id)
            if normalized_country_id:
                data["country_id"] = normalized_country_id
            if "lat" not in data and "lat" in command:
                data["lat"] = command.get("lat")
            if "lng" not in data and "lng" in command:
                data["lng"] = command.get("lng")
            if "zoom_level" not in data and "zoom" in command:
                data["zoom_level"] = command.get("zoom")
            if "duration_ms" not in data and "duration" in command:
                data["duration_ms"] = command.get("duration")

        if raw_type == "route":
            from_country = data.get("from_country") or command.get("from_country")
            to_country = data.get("to_country") or command.get("to_country")
            mapped_from = self._normalize_country_id(from_country)
            mapped_to = self._normalize_country_id(to_country)
            if mapped_from:
                data["from_country"] = mapped_from
            if mapped_to:
                data["to_country"] = mapped_to
            for key in ("from_lat", "from_lng", "to_lat", "to_lng", "start_lat", "start_lng", "end_lat", "end_lng"):
                if key not in data and key in command:
                    data[key] = command.get(key)
            data.setdefault("color", command.get("color", "#10b981"))
            data.setdefault("weight", command.get("weight", 3))

        if raw_type == "marker":
            if "lat" not in data and "lat" in command:
                data["lat"] = command.get("lat")
            if "lng" not in data and "lng" in command:
                data["lng"] = command.get("lng")
            data.setdefault("marker_type", command.get("marker_type", "custom"))
            data.setdefault("label", command.get("label", "Marker"))
            data.setdefault("color", command.get("color", "#f59e0b"))

        if raw_type == "heatmap":
            points = data.get("data_points") or data.get("points") or command.get("data_points") or command.get("points") or []
            normalized_points: List[Dict[str, Any]] = []
            if isinstance(points, list):
                for point in points:
                    if not isinstance(point, dict):
                        continue
                    item: Dict[str, Any] = {}
                    country_id = self._normalize_country_id(point.get("country_id"))
                    if country_id:
                        item["country_id"] = country_id
                    if point.get("lat") is not None:
                        item["lat"] = point.get("lat")
                    if point.get("lng") is not None:
                        item["lng"] = point.get("lng")
                    item["value"] = point.get("value", point.get("intensity", point.get("risk", point.get("score", 0))))
                    if point.get("label"):
                        item["label"] = point.get("label")
                    normalized_points.append(item)
            data["data_points"] = normalized_points
            data.pop("points", None)
            data.setdefault("metric", command.get("metric", "value"))
            data.setdefault("color_scale", command.get("color_scale", "red"))

        if raw_type == "overlay":
            data.setdefault("overlay_type", command.get("overlay_type", "custom"))
            if "overlay_data" not in data and isinstance(command.get("overlay_data"), dict):
                data["overlay_data"] = command.get("overlay_data")

        return normalized

    def _derive_unified_map_payload(
        self,
        map_result: MapIntelligenceResult,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Build normalized map commands, visual markers, and panel hints."""
        normalized_commands: List[Dict[str, Any]] = []

        for raw_command in map_result.commands:
            if isinstance(raw_command, dict):
                command = self._normalize_map_command(raw_command)
                if command:
                    normalized_commands.append(command)

        for marker in map_result.markers:
            if not isinstance(marker, dict):
                continue
            command = self._normalize_map_command(
                {
                    "type": "marker",
                    "lat": marker.get("lat"),
                    "lng": marker.get("lng"),
                    "marker_type": marker.get("marker_type", "signal"),
                    "label": marker.get("label", "Marker"),
                    "color": marker.get("color", "#f59e0b"),
                    "description": marker.get("description", "Map marker"),
                    "source": "unified_intelligence_engine",
                    "priority": "medium",
                }
            )
            if command:
                normalized_commands.append(command)

        for route in map_result.routes:
            if not isinstance(route, dict):
                continue
            command = self._normalize_map_command(
                {
                    "type": "route",
                    "from_lat": route.get("from_lat"),
                    "from_lng": route.get("from_lng"),
                    "to_lat": route.get("to_lat"),
                    "to_lng": route.get("to_lng"),
                    "route_type": route.get("route_type", "route"),
                    "label": route.get("label", "Route"),
                    "color": route.get("color", "#10b981"),
                    "description": route.get("description", "Map route"),
                    "source": "unified_intelligence_engine",
                    "priority": "medium",
                }
            )
            if command:
                normalized_commands.append(command)

        if map_result.heatmap_data:
            points = []
            for key, value in map_result.heatmap_data.items():
                try:
                    lat_str, lng_str = key.split(",", 1)
                    points.append({
                        "lat": float(lat_str),
                        "lng": float(lng_str),
                        "value": value,
                    })
                except Exception:
                    continue
            heatmap_command = self._normalize_map_command(
                {
                    "type": "heatmap",
                    "data_points": points,
                    "metric": "value",
                    "color_scale": "red",
                    "description": "Unified heatmap overlay",
                    "source": "unified_intelligence_engine",
                    "priority": "medium",
                }
            )
            if heatmap_command:
                normalized_commands.append(heatmap_command)

        visual_markers = []
        for index, marker in enumerate(map_result.markers):
            if not isinstance(marker, dict):
                continue
            lat = marker.get("lat")
            lng = marker.get("lng")
            if lat is None or lng is None:
                continue
            visual_markers.append(
                {
                    "id": str(marker.get("id") or f"vm-{index}-{uuid.uuid4().hex[:6]}"),
                    "type": str(marker.get("marker_type") or "signal"),
                    "label": str(marker.get("label") or "Marker"),
                    "coordinates": {"lat": lat, "lng": lng},
                    "color": str(marker.get("color") or "#f59e0b"),
                    "pulse": True,
                }
            )

        spawned_panels = []
        if map_result.affected_regions:
            spawned_panels.append(
                {
                    "id": "regional-focus",
                    "title": "Regional Focus",
                    "kind": "regions",
                    "regions": map_result.affected_regions[:6],
                }
            )
        if map_result.routes:
            spawned_panels.append(
                {
                    "id": "route-watch",
                    "title": "Route Watch",
                    "kind": "routes",
                    "count": len(map_result.routes),
                }
            )

        return normalized_commands, visual_markers, spawned_panels

    def _persist_map_commands(self, commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Persist normalized commands to shared map command service for real-time map polling."""
        if not commands:
            return []
        try:
            from app.services.map_command_service import get_map_command_service

            service = get_map_command_service()
            persisted = []
            for command in commands:
                created = service.create_raw_command(
                    command_type=command["command_type"],
                    data=command["data"],
                    description=command.get("description", "Map command"),
                    source=command.get("source", "unified_intelligence_engine"),
                    priority=command.get("priority", "medium"),
                    metadata=command.get("metadata", {}),
                    command_id=command.get("id"),
                    created_at=command.get("created_at"),
                )
                persisted.append(created.to_dict())
            return persisted
        except Exception as exc:
            logger.warning(f"Failed to persist unified map commands: {exc}")
            return commands

    def _build_cockpit_state(
        self,
        assessment: QueryAssessment,
        results: Dict[str, Any],
        statuses: List[CapabilityExecutionStatus],
        map_commands: List[Dict[str, Any]],
        visual_markers: List[Dict[str, Any]],
    ) -> CockpitState:
        """Build frontend command-center state from unified execution outputs."""
        reasoning = results.get("reasoning")
        tools = results.get("tools")
        visuals = results.get("visuals")
        map_layer = results.get("map_intelligence")

        success_count = sum(1 for status in statuses if status.success)
        total_count = len(statuses) or 1
        success_ratio = success_count / total_count

        threat_score = max(0, min(100, int((1 - success_ratio) * 35 + (assessment.confidence * 65))))
        if threat_score >= 78:
            threat_severity = "critical"
        elif threat_score >= 62:
            threat_severity = "high"
        elif threat_score >= 45:
            threat_severity = "elevated"
        else:
            threat_severity = "stable"

        top_finding = "No high-signal finding was produced."
        if reasoning and reasoning.key_findings:
            top_finding = reasoning.key_findings[0]
        elif tools and tools.insights:
            top_finding = tools.insights[0]

        command_types: Dict[str, int] = {}
        for command in map_commands:
            command_type = str(command.get("command_type") or "unknown")
            command_types[command_type] = command_types.get(command_type, 0) + 1

        active_overlays = [
            {
                "key": key,
                "count": count,
                "delta": max(0, count - 1),
                "color": "#3b82f6" if key in {"focus", "highlight"} else "#f59e0b",
                "icon": key,
            }
            for key, count in sorted(command_types.items(), key=lambda item: item[1], reverse=True)
        ]

        stream_phases = [
            {
                "agent": status.capability.value,
                "phase": "completed" if status.success else "failed",
                "status": "ok" if status.success else "error",
            }
            for status in statuses
        ]

        core_intelligence = []
        if reasoning and reasoning.key_findings:
            core_intelligence.extend(
                {
                    "id": f"core-{index}",
                    "label": finding[:84],
                    "description": finding,
                }
                for index, finding in enumerate(reasoning.key_findings[:3])
            )
        if not core_intelligence and tools and tools.insights:
            core_intelligence.extend(
                {
                    "id": f"tool-{index}",
                    "label": insight[:84],
                    "description": insight,
                }
                for index, insight in enumerate(tools.insights[:3])
            )

        return CockpitState(
            priority_alert={
                "title": "Priority Intelligence Alert",
                "body": top_finding,
                "severity": threat_severity,
                "dismissible": True,
            },
            global_threat_level={
                "label": f"{threat_severity.title()} Watch",
                "score": threat_score,
                "severity": threat_severity,
            },
            ontology_pulse={
                "countries": len(map_layer.affected_regions) if map_layer else 0,
                "signals": len(reasoning.key_findings) if reasoning else 0,
                "sources": len(tools.data_sources) if tools else 0,
            },
            risk_watchlist=[
                {"title": risk, "severity": "elevated"}
                for risk in (reasoning.uncertainty_factors[:4] if reasoning else [])
            ],
            operating_logic={
                "title": "Unified Capability Execution",
                "summary": f"{success_count}/{total_count} capabilities completed successfully.",
            },
            active_overlays=active_overlays,
            subpanels=[
                {
                    "id": "visual-payload",
                    "title": "Visual Payload",
                    "charts": len(visuals.charts) if visuals else 0,
                    "diagrams": len(visuals.diagrams) if visuals else 0,
                    "markers": len(visual_markers),
                }
            ],
            stream_phases=stream_phases,
            core_intelligence=core_intelligence,
            demo_mode=False,
            cache_hit=False,
        )

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
        allow_cloud_synthesis: bool = True,
    ) -> AssistantResponsePayload:
        if allow_cloud_synthesis and self._llm is not None:
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
            llm = self._llm
            if llm is None:
                return None

            reasoning_result = results.get("reasoning")
            tools_result = results.get("tools")
            visuals_result = results.get("visuals")
            map_result = results.get("map_intelligence")

            compact = {
                "assessment": assessment.to_dict(),
                "summary": unified_summary,
                "reasoning": reasoning_result.to_dict() if reasoning_result else None,
                "tools": tools_result.to_dict() if tools_result else None,
                "visuals": {
                    "chart_count": len(visuals_result.charts),
                    "diagram_count": len(visuals_result.diagrams),
                    "chart_insights": visuals_result.chart_insights[:3],
                    "diagram_insights": visuals_result.diagram_insights[:2],
                } if visuals_result else None,
                "map_intelligence": map_result.to_dict() if map_result else None,
                "statuses": [status.to_dict() for status in statuses],
                "memory_summary": session.memory_summary,
            }
            prompt = (
                "You are a unified intelligence assistant. Produce a sharp, practical answer like an elite AI analyst assistant. "
                "Keep uncertainty explicit and avoid hype. Return ONLY valid JSON with keys "
                "title, executive_brief, key_takeaways, next_actions, suggested_follow_ups, memory_summary, response_blocks. "
                "Each response_blocks item must contain title, content, tone.\n"
                "Use a Modular Component framework in response block content:\n"
                "1) Markdown for text sections, with clear ### headers when needed.\n"
                "2) Wrap structured content in custom tags such as <Box title=\"Key Metrics\">...</Box> and <Card type=\"analysis\">...</Card>.\n"
                "3) For trends or statistics, emit <Chart type=\"line|bar|pie\" data={JSON_ARRAY}> where JSON_ARRAY is valid JSON.\n"
                "4) Prioritize progressive disclosure: critical summary first, then details.\n\n"
                f"User query: {query}\nPayload: {json.dumps(compact, default=str)[:12000]}"
            )
            response = await llm.ainvoke(prompt)
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
        capability_chart_data = json.dumps([
            {"metric": "reasoning", "value": 1 if results.get("reasoning") else 0},
            {"metric": "tools", "value": 1 if results.get("tools") else 0},
            {"metric": "visuals", "value": 1 if results.get("visuals") else 0},
            {"metric": "map", "value": 1 if results.get("map_intelligence") else 0},
            {"metric": "confidence", "value": round(self._calculate_overall_confidence(results, statuses) * 100, 2)},
        ])
        blocks = [AssistantResponseSection(title="What matters now", content=unified_summary, tone="priority")]
        evidence_parts = []
        if tools and tools.data_sources:
            evidence_parts.append("Sources used: " + ", ".join(tools.data_sources[:6]))
        if tools and tools.unavailable_tools:
            evidence_parts.append("Unavailable connectors: " + ", ".join(list(tools.unavailable_tools.keys())[:4]))
        if reasoning and reasoning.uncertainty_factors:
            evidence_parts.append("Uncertainty: " + "; ".join(reasoning.uncertainty_factors[:3]))
        if evidence_parts:
            blocks.append(
                AssistantResponseSection(
                    title="Evidence and caveats",
                    content=(
                        f"<Box title=\"Evidence & Caveats\">{' '.join(evidence_parts)}</Box>\n"
                        f"<Card type=\"graph\"><Chart type=\"bar\" data={capability_chart_data}></Chart></Card>"
                    ),
                    tone="evidence",
                )
            )
        if actions:
            blocks.append(
                AssistantResponseSection(
                    title="Recommended next moves",
                    content=(
                        f"<Card type=\"analysis\">{' '.join(f'{idx + 1}. {item}' for idx, item in enumerate(actions[:3]))}</Card>"
                    ),
                    tone="action",
                )
            )
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
