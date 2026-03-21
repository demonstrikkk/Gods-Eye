# import logging
# from typing import TypedDict, Optional, Dict, Any
# from langgraph.graph import StateGraph, END
# from langchain_core.prompts import PromptTemplate
# from app.services.llm_provider import get_enterprise_llm
# from app.schemas.domain import ActionRecommendation

# logger = logging.getLogger("langgraph_intelligence")

# # 1. Define the Graph State Graph Type
# class ProcessingState(TypedDict):
#     input_text: str
#     source_id: str # The document, tweet, or CRM report ID
#     entities: Optional[Dict[str, Any]]
#     sentiment_payload: Optional[Dict[str, Any]]
#     action_plan: Optional[ActionRecommendation]
#     error: Optional[str]

# # 2. Node Implementation Functions
# def extract_entities_node(state: ProcessingState) -> ProcessingState:
#     logger.info("LangGraph Node: Extracting Entities via Main LLM...")
#     llm = get_enterprise_llm()
#     prompt = PromptTemplate.from_template("""
#         You are an elite government intelligence parsing AI.
#         Extract the key entities, primarily 'priority_issue' and 'affected_segment' from the text.
#         Return strictly valid JSON string without markdown blocks.
        
#         Text: {text}
#         Format: {{"priority_issue": "string", "affected_segment": "string"}}
#     """)
#     chain = prompt | llm
    
#     try:
#         # Langchain provides str directly when not explicitly parsed unless using with_structured_output
#         # To strictly enforce schema, we instruct json.
#         raw_result = chain.invoke({"text": state["input_text"]})
#         # Assuming we just need to pass the raw objects down via JSON ast eval
#         import json
        
#         content = raw_result.content
#         if "```json" in content:
#             content = content.split("```json")[1].split("```")[0].strip()
            
#         state["entities"] = json.loads(content)
#     except Exception as e:
#         state["error"] = f"Extraction Failed: {e}"
#         logger.error(state["error"])
        
#     return state

# def analyze_sentiment_node(state: ProcessingState) -> ProcessingState:
#     logger.info("LangGraph Node: Analyzing Sentiment Score and Urgency...")
#     if state.get("error"):
#         return state # Short circuit
        
#     llm = get_enterprise_llm()
#     prompt = PromptTemplate.from_template("""
#         As a political intelligence analyst, score the following text from 0 to 100 on sentiment 
#         (where 0 is deeply negative/urgent, 100 is highly positive). Determine an urgency score 1-10.
        
#         Text: {text}
#         Format: {{"sentiment": int, "urgency": int}}
#     """)
#     chain = prompt | llm
    
#     try:
#         import json
#         raw_result = chain.invoke({"text": state["input_text"]})
#         content = raw_result.content
#         if "```json" in content:
#             content = content.split("```json")[1].split("```")[0].strip()
#         state["sentiment_payload"] = json.loads(content)
#     except Exception as e:
#         state["error"] = f"Sentiment Failure: {e}"
        
#     return state

# def recommend_action_node(state: ProcessingState) -> ProcessingState:
#     logger.info("LangGraph Node: Generating Recommended Direct Action...")
#     if state.get("error"):
#         return state
        
#     llm = get_enterprise_llm()
    
#     # Langchain structured output natively ensures Pydantic validation (Requires highly capable models like Groq's LLaMa3 or Gemini)
#     structured_llm = llm.with_structured_output(ActionRecommendation)
    
#     prompt = PromptTemplate.from_template("""
#         Based on the data collected:
#         Issue: {issue}
#         Segment: {segment}
#         Sentiment: {sentiment}
#         Urgency: {urgency}
        
#         Generate a strictly valid ActionRecommendation for the field operation team.
#         Target region id is: unknown_require_gps_link
#     """)
#     try:
#         entities = state["entities"] or {}
#         sentiment_data = state["sentiment_payload"] or {}
        
#         action_plan = structured_llm.invoke(prompt.format(
#             issue=entities.get("priority_issue", "Unknown"),
#             segment=entities.get("affected_segment", "General Citizenry"),
#             sentiment=sentiment_data.get("sentiment", 50),
#             urgency=sentiment_data.get("urgency", 5)
#         ))
#         state["action_plan"] = action_plan
#     except Exception as e:
#         logger.error(f"Action Recommendation Error: {e}")
#         state["error"] = "Failed to compile action recommendation."
        
#     return state

# # 3. Build the actual LangGraph Engine
# workflow = StateGraph(ProcessingState)

# workflow.add_node("extract_entities", extract_entities_node)
# workflow.add_node("analyze_sentiment", analyze_sentiment_node)
# workflow.add_node("recommend_action", recommend_action_node)

# # Linear execution for this specific processing pipeline
# workflow.add_edge("extract_entities", "analyze_sentiment")
# workflow.add_edge("analyze_sentiment", "recommend_action")
# workflow.add_edge("recommend_action", END)

# workflow.set_entry_point("extract_entities")

# # Compile the LangGraph App
# civic_intelligence_agent = workflow.compile()

# async def process_unstructured_civic_text(text: str, source_id: str) -> ProcessingState:
#     """ API-facing function to trigger the LangGraph orchestration """
#     initial_state = ProcessingState(
#         input_text=text,
#         source_id=source_id,
#         entities=None,
#         sentiment_payload=None,
#         action_plan=None,
#         error=None
#     )
#     # App.invoke relies on async/sync mapping
#     final_state = await civic_intelligence_agent.ainvoke(initial_state)
#     return final_state






import logging
import json
import asyncio
from typing import TypedDict, Optional, Dict, Any, List
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig

from app.services.llm_provider import get_enterprise_llm, get_llm, MODEL_REGISTRY
from app.schemas.domain import ActionRecommendation
from app.data.store import store  # assuming this is your civic data store
from app.services.osint_aggregator import osint_engine  # if needed for additional context

logger = logging.getLogger("langgraph_intelligence")

# ----------------------------------------------------------------------
# 1. Define the Graph State (enriched for hackathon)
# ----------------------------------------------------------------------
class ProcessingState(TypedDict):
    input_text: str
    source_id: str                     # e.g., tweet ID, document ID, channel name
    source_type: str                   # "twitter", "telegram", "reddit", etc.
    language: Optional[str]            # detected language (for multilingual models)
    entities: Optional[Dict[str, Any]]
    sentiment_payload: Optional[Dict[str, Any]]
    action_plan: Optional[ActionRecommendation]
    error: Optional[str]
    # New fields for hyper-local mapping
    location: Optional[str]            # extracted location (constituency/booth)
    worker_assigned: Optional[Dict[str, Any]]  # worker info if needed
    scheme_recommendations: Optional[List[Dict[str, Any]]]  # relevant schemes

# ----------------------------------------------------------------------
# 2. Helper: safe JSON parsing
# ----------------------------------------------------------------------
def _safe_json_parse(content: str) -> Dict:
    """Robust JSON extraction from LLM output."""
    content = content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    start = content.find("{")
    end = content.rfind("}") + 1
    if start >= 0 and end > start:
        content = content[start:end]
    return json.loads(content)

# ----------------------------------------------------------------------
# 3. Node Implementations (async, with fallbacks)
# ----------------------------------------------------------------------
async def extract_entities_node(state: ProcessingState, config: RunnableConfig) -> ProcessingState:
    logger.info(f"LangGraph Node: Extracting Entities from source {state['source_id']}...")
    if state.get("error"):
        return state

    # Use a model good at extraction – maybe a smaller fast model
    llm = get_llm(MODEL_REGISTRY["reasoning_fast"], temperature=0.1)
    if not llm:
        llm = get_enterprise_llm(temperature=0.1)  # fallback

    prompt = PromptTemplate.from_template("""
You are an elite government intelligence parsing AI.
Extract key entities from the following text. Pay special attention to:
- priority_issue (what is the main concern/complaint)
- affected_segment (which demographic or group – e.g., farmers, youth, women, etc.)
- location (if mentioned, e.g., constituency, city, booth)
- language (detect the language, e.g., Hindi, English, Tamil)

Return strictly valid JSON without markdown blocks.
Text: {text}
Format: {{
    "priority_issue": "string",
    "affected_segment": "string",
    "location": "string or null",
    "language": "string"
}}
""")
    chain = prompt | llm
    try:
        raw_result = await chain.ainvoke({"text": state["input_text"]})
        entities = _safe_json_parse(raw_result.content)
        state["entities"] = entities
        state["language"] = entities.get("language")
        state["location"] = entities.get("location")
        logger.debug(f"Extracted entities: {entities}")
    except Exception as e:
        state["error"] = f"Extraction Failed: {e}"
        logger.error(state["error"])
    return state

async def analyze_sentiment_node(state: ProcessingState, config: RunnableConfig) -> ProcessingState:
    logger.info("LangGraph Node: Analyzing Sentiment Score and Urgency...")
    if state.get("error"):
        return state

    # Use a multilingual model if language is Indian (Hindi, etc.)
    if state.get("language") in ["Hindi", "Bengali", "Tamil", "Telugu", "Marathi"]:
        llm = get_llm(MODEL_REGISTRY["multilingual"], temperature=0.1) or get_enterprise_llm(temperature=0.1)
    else:
        llm = get_enterprise_llm(temperature=0.1)

    prompt = PromptTemplate.from_template("""
As a political intelligence analyst, score the following text on sentiment (0-100) and urgency (1-10).
Sentiment: 0 = very negative, 100 = very positive.
Urgency: 1 = no immediate action, 10 = require immediate intervention.
Text: {text}
Return valid JSON: {{"sentiment": int, "urgency": int}}
""")
    chain = prompt | llm
    try:
        raw_result = await chain.ainvoke({"text": state["input_text"]})
        sentiment = _safe_json_parse(raw_result.content)
        state["sentiment_payload"] = sentiment
        logger.debug(f"Sentiment: {sentiment}")
    except Exception as e:
        state["error"] = f"Sentiment Failure: {e}"
        logger.error(state["error"])
    return state

async def enrich_with_geography_node(state: ProcessingState, config: RunnableConfig) -> ProcessingState:
    """Map location to constituency/booth and find relevant workers/schemes."""
    logger.info("LangGraph Node: Enriching with geography...")
    if state.get("error") or not state.get("location"):
        return state

    location = state["location"].lower()
    # Simple lookup: you could use geocoding or a local map
    # For hackathon, we'll simulate: try to find matching constituency
    constituencies = store.get_constituencies()
    matched = None
    for c in constituencies:
        if location in c["name"].lower() or c["name"].lower() in location:
            matched = c
            break
    if matched:
        # Get workers assigned to this constituency
        workers = store.get_workers()
        assigned_workers = [w for w in workers if w.get("constituency_id") == matched["id"]]
        state["worker_assigned"] = {
            "constituency": matched["name"],
            "workers": assigned_workers[:3]  # top few
        }
        # Get relevant schemes for this constituency (e.g., based on demographics)
        # In real app, you'd query schemes relevant to the priority_issue
        schemes = store.get_schemes()
        issue = state["entities"].get("priority_issue", "")
        relevant = [s for s in schemes if issue.lower() in s["target_segment"].lower() or issue.lower() in s["benefit"].lower()]
        state["scheme_recommendations"] = relevant[:3]
    else:
        logger.warning(f"No constituency match for location '{location}'")
    return state

async def recommend_action_node(state: ProcessingState, config: RunnableConfig) -> ProcessingState:
    logger.info("LangGraph Node: Generating Recommended Direct Action...")
    if state.get("error"):
        return state

    # Use a model that supports structured output (function calling)
    llm = get_llm(MODEL_REGISTRY["function_calling"], temperature=0.1)
    if not llm:
        llm = get_enterprise_llm(temperature=0.1)

    structured_llm = llm.with_structured_output(ActionRecommendation)

    entities = state["entities"] or {}
    sentiment = state["sentiment_payload"] or {}

    # Build context: include worker and scheme info if available
    worker_info = ""
    if state.get("worker_assigned"):
        worker_names = [w["name"] for w in state["worker_assigned"]["workers"]]
        worker_info = f"Available workers in {state['worker_assigned']['constituency']}: {', '.join(worker_names)}."
    scheme_info = ""
    if state.get("scheme_recommendations"):
        scheme_names = [s["name"] for s in state["scheme_recommendations"]]
        scheme_info = f"Relevant government schemes: {', '.join(scheme_names)}."

    prompt = PromptTemplate.from_template("""
You are a field operations coordinator for the government.
Based on the intelligence gathered:

- Issue: {issue}
- Segment: {segment}
- Location: {location}
- Sentiment: {sentiment}
- Urgency: {urgency}
{worker_info}
{scheme_info}

Generate a strictly valid ActionRecommendation for the field operation team.
The recommendation should include:
- recommended_action (what to do)
- assigned_worker (if there is a suitable worker, otherwise leave empty)
- priority (high/medium/low)
- expected_outcome (brief)
- tags (list of relevant keywords)
""")
    try:
        formatted_prompt = prompt.format(
            issue=entities.get("priority_issue", "Unknown"),
            segment=entities.get("affected_segment", "General Citizenry"),
            location=entities.get("location", "Unknown"),
            sentiment=sentiment.get("sentiment", 50),
            urgency=sentiment.get("urgency", 5),
            worker_info=worker_info,
            scheme_info=scheme_info
        )
        action_plan = await structured_llm.ainvoke(formatted_prompt)
        state["action_plan"] = action_plan
    except Exception as e:
        logger.error(f"Action Recommendation Error: {e}")
        state["error"] = "Failed to compile action recommendation."
    return state

# ----------------------------------------------------------------------
# 4. Build the LangGraph Workflow
# ----------------------------------------------------------------------
workflow = StateGraph(ProcessingState)

workflow.add_node("extract_entities", extract_entities_node)
workflow.add_node("analyze_sentiment", analyze_sentiment_node)
workflow.add_node("enrich_geography", enrich_with_geography_node)
workflow.add_node("recommend_action", recommend_action_node)

# Define edges (linear flow)
workflow.add_edge("extract_entities", "analyze_sentiment")
workflow.add_edge("analyze_sentiment", "enrich_geography")
workflow.add_edge("enrich_geography", "recommend_action")
workflow.add_edge("recommend_action", END)

workflow.set_entry_point("extract_entities")

# Compile
civic_intelligence_agent = workflow.compile()

# ----------------------------------------------------------------------
# 5. Public API function
# ----------------------------------------------------------------------
async def process_unstructured_civic_text(
    text: str,
    source_id: str,
    source_type: str = "unknown"
) -> ProcessingState:
    """
    [MOCK MODE ACTIVE] 
    Original LangGraph pipeline commented out to conserve API tokens.
    Returns simulated analysis results immediately.
    """
    # ------------------------------------------------------------
    # (Commented out original LangGraph heavy processing)
    # ------------------------------------------------------------
    # initial_state: ProcessingState = {
    #     "input_text": text,
    #     "source_id": source_id,
    #     "source_type": source_type,
    #     "language": None,
    #     "entities": None,
    #     "sentiment_payload": None,
    #     "action_plan": None,
    #     "error": None,
    #     "location": None,
    #     "worker_assigned": None,
    #     "scheme_recommendations": None,
    # }
    # try:
    #     final_state = await civic_intelligence_agent.ainvoke(initial_state)
    # except Exception as e:
    #     logger.exception("LangGraph pipeline failed")
    #     final_state = initial_state
    #     final_state["error"] = f"Pipeline error: {e}"
    # return final_state

    # --- Elite Mock Response (Instant, No API Costs) ---
    await asyncio.sleep(0.05) # simulate minor network jitter
    
    mock_state: ProcessingState = {
        "input_text": text,
        "source_id": source_id,
        "source_type": source_type,
        "language": "English (Local Analysis)",
        "entities": {
            "priority_issue": "General Civic Awareness",
            "affected_segment": "Citizens",
            "location": "Detected via metadata",
            "language": "English"
        },
        "sentiment_payload": {"sentiment": 65, "urgency": 3},
        "action_plan": ActionRecommendation(
            action_type="DISPATCH_WORKER",
            target_region_id="booth_001",
            urgency=3,
            justification_summary="Local processing active. Manual intelligence routing enabled.",
            suggested_message="Intelligence ingestion acknowledged. Analysis cached locally."
        ),
        "error": None,
        "location": "Regional monitoring",
        "worker_assigned": None,
        "scheme_recommendations": None,
    }
    return mock_state

async def process_batch(
    items: List[Dict[str, str]],
    source_type: str = "batch"
) -> List[ProcessingState]:
    """Process multiple texts in parallel (useful for bulk social media analysis)."""
    tasks = []
    for item in items:
        text = item.get("text", "")
        source_id = item.get("id", "unknown")
        tasks.append(process_unstructured_civic_text(text, source_id, source_type))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # If any result is an exception, convert to error state
    final = []
    for res in results:
        if isinstance(res, Exception):
            final.append({
                "input_text": "",
                "source_id": "error",
                "source_type": source_type,
                "error": str(res),
                # other fields default to None
            })
        else:
            final.append(res)
    return final