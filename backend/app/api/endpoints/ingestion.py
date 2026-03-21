from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging

from app.services.intelligence_engine import process_unstructured_civic_text
from app.core.graph import get_graph_session
from app.models.graph_schema import GraphQueries
from neo4j import AsyncSession as GraphSession

logger = logging.getLogger("ingestion_api")
router = APIRouter()

class IngestionPayload(BaseModel):
    source_id: str
    citizen_id: str
    text: str
    urgency_override: int = None

async def bg_process_and_store(payload: IngestionPayload, graph_session: GraphSession):
    """
    Background worker function that runs the LangGraph engine natively.
    """
    try:
        logger.info(f"Initiating LangGraph pipeline for source: {payload.source_id}")
        
        # 1. Run Intelligence Pipeline
        final_state = await process_unstructured_civic_text(payload.text, payload.source_id)
        
        if final_state.get("error"):
            logger.error(f"Graph Pipeline Error: {final_state['error']}")
            return
            
        # 2. Extract Data
        entities = final_state.get("entities", {})
        sentiment = final_state.get("sentiment_payload", {})
        action_plan = final_state.get("action_plan")

        issue_name = entities.get("priority_issue", "General Feedback")
        urgency = payload.urgency_override or sentiment.get("urgency", 5)

        # 3. Write securely to Neo4j Graph
        await GraphQueries.register_citizen_complaint(
            session=graph_session,
            citizen_id=payload.citizen_id,
            issue_name=issue_name,
            urgency=urgency
        )
        logger.info(f"Successfully processed and stored Graph Action: {action_plan.action_type if action_plan else 'N/A'}")
        
    except Exception as e:
        logger.error(f"Background Ingestion Failure: {e}")

@router.post("/unstructured")
async def ingest_unstructured_data(
    payload: IngestionPayload, 
    background_tasks: BackgroundTasks,
    graph_session: GraphSession = Depends(get_graph_session)
):
    """
    Accepts raw SMS, Tweets, or PDF notes.
    Delegates to LangGraph AI layer via background worker for sentiment/entity extraction.
    """
    # Trigger graph processing in the background to avoid locking the UI/Integration
    background_tasks.add_task(bg_process_and_store, payload, graph_session)
    
    return {
        "status": "processing",
        "message": "Payload queued for LangGraph Intelligence Engine",
        "source": payload.source_id
    }
