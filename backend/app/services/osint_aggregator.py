import logging
import hashlib
import json
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.llm_provider import get_enterprise_llm, get_llm, MODEL_REGISTRY
from app.core.config import settings

logger = logging.getLogger("nlp_query_engine")

# Optional: Use Redis for caching (if available)
try:
    from app.cache.redis_client import redis_client
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

class CivicIntelligenceQA:
    """
    Natural Language to Graph Query Engine.
    Translates user questions into Cypher queries and returns natural language answers.
    """
    def __init__(self):
        self.graph = None
        self.last_schema_refresh = None
        self.schema_refresh_interval = timedelta(minutes=30)  # Refresh every 30 min
        self._init_graph()

    def _init_graph(self):
        """Initialize Neo4j connection and schema."""
        try:
            self.graph = Neo4jGraph(
                url=settings.NEO4J_URI,
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
                database=settings.NEO4J_DATABASE  # if needed
            )
            self._refresh_schema()
            logger.info("Neo4j graph connected and schema loaded.")
        except Exception as e:
            logger.warning(f"Neo4j integration unavailable: {e}")
            self.graph = None

    def _refresh_schema(self):
        """Refresh the graph schema from Neo4j."""
        if not self.graph:
            return
        try:
            self.graph.refresh_schema()
            self.last_schema_refresh = datetime.now()
            logger.debug("Graph schema refreshed.")
        except Exception as e:
            logger.error(f"Schema refresh failed: {e}")

    def _ensure_fresh_schema(self):
        """Refresh schema if it's stale."""
        if not self.graph:
            return
        if (self.last_schema_refresh is None or
            datetime.now() - self.last_schema_refresh > self.schema_refresh_interval):
            self._refresh_schema()

    def _generate_cache_key(self, question: str) -> str:
        """Generate a unique cache key for a question."""
        return f"qa:query:{hashlib.md5(question.encode()).hexdigest()}"

    def _get_cached_result(self, question: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached result from Redis."""
        if not CACHE_AVAILABLE:
            return None
        key = self._generate_cache_key(question)
        cached = redis_client.get(key)
        if cached:
            try:
                return json.loads(cached)
            except:
                return None
        return None

    def _cache_result(self, question: str, result: Dict[str, Any], ttl_seconds: int = 300):
        """Store result in Redis with TTL."""
        if not CACHE_AVAILABLE:
            return
        key = self._generate_cache_key(question)
        redis_client.setex(key, ttl_seconds, json.dumps(result))

    def _generate_cypher_query(self, question: str, schema: str) -> str:
        """Use LLM to generate a Cypher query from the question."""
        llm = get_enterprise_llm(temperature=0)  # low temp for deterministic output
        # Use a model good at code generation (like Llama 3.1 70B)
        # We can also use a smaller model if speed matters
        # But we'll use the enterprise LLM for now.

        cypher_prompt = PromptTemplate(
            template="""
You are a principal intelligence analyst querying a Civic Knowledge Graph.
Translate the user's natural language question into a strictly valid Cypher query for Neo4j.

Schema:
{schema}

Rules:
- Only use the node types and properties provided in the schema.
- Do not map PM Kisan to random properties unless it exists as a Scheme node.
- Ensure relationships like (Citizen)-[:LIVES_IN]->(Booth) are respected.
- If the question involves sentiment or coverage, assume there are properties like `avg_sentiment` on Booth nodes, and `coverage` on Scheme nodes.
- Return ONLY the Cypher query, no extra text.

Question: {question}
Cypher Query:""",
            input_variables=["schema", "question"],
        )
        chain = cypher_prompt | llm | StrOutputParser()
        try:
            cypher = chain.invoke({"schema": schema, "question": question})
            # Cleanup: remove markdown code blocks if present
            if "```cypher" in cypher:
                cypher = cypher.split("```cypher")[1].split("```")[0].strip()
            elif "```" in cypher:
                cypher = cypher.split("```")[1].split("```")[0].strip()
            return cypher
        except Exception as e:
            logger.error(f"Cypher generation failed: {e}")
            raise

    def _validate_cypher(self, cypher: str) -> bool:
        """Basic safety check: disallow destructive operations."""
        # Simple check: reject if contains 'DELETE', 'DROP', 'CREATE' (unless you want to allow)
        # But for a query engine, we only want READ queries.
        forbidden = ["DELETE", "DROP", "CREATE", "MERGE", "SET", "REMOVE"]
        upper = cypher.upper()
        for f in forbidden:
            if f in upper:
                logger.warning(f"Potentially destructive Cypher blocked: {cypher}")
                return False
        return True

    def _execute_cypher(self, cypher: str) -> list:
        """Execute a Cypher query against the graph."""
        if not self.graph:
            raise Exception("Graph not connected")
        try:
            result = self.graph.query(cypher)
            return result
        except Exception as e:
            logger.error(f"Cypher execution failed: {e}")
            raise

    def _format_answer(self, question: str, cypher: str, data: list) -> Dict[str, Any]:
        """Use LLM to turn Cypher result into a natural language answer."""
        llm = get_enterprise_llm(temperature=0.3)
        # If no data, return simple message
        if not data:
            return {
                "answer": "No results found matching your query.",
                "cypher": cypher,
                "data": []
            }
        # Convert data to string (truncate if too long)
        data_str = json.dumps(data, indent=2)[:4000]
        prompt = PromptTemplate(
            template="""
You are a strategic intelligence analyst. Based on the data retrieved from the knowledge graph, answer the user's question in a concise, insightful manner.

User question: {question}
Cypher used: {cypher}
Data retrieved:
{data}

Provide a natural language answer that directly addresses the question. If the data shows trends or anomalies, highlight them. Keep it under 150 words.
Answer:""",
            input_variables=["question", "cypher", "data"],
        )
        chain = prompt | llm | StrOutputParser()
        try:
            answer = chain.invoke({"question": question, "cypher": cypher, "data": data_str})
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            answer = "I was unable to formulate an answer, but here is the raw data."
        return {
            "answer": answer.strip(),
            "cypher": cypher,
            "data": data
        }

    def execute_query(self, user_question: str, use_cache: bool = True) -> Union[str, Dict[str, Any]]:
        """
        Execute a natural language query.
        Returns either a string answer (legacy) or a dict with answer, cypher, and data.
        """
        if not self.graph:
            return "Air-gap security mode: Graph DB unreachable. Ensure containers are running."

        # Optionally refresh schema
        self._ensure_fresh_schema()

        # Check cache
        if use_cache:
            cached = self._get_cached_result(user_question)
            if cached:
                logger.info(f"Cache hit for query: {user_question[:50]}")
                # For backward compatibility, if cached is a string, return it.
                if isinstance(cached, str):
                    return cached
                # Otherwise return dict
                return cached

        try:
            # Generate Cypher
            cypher = self._generate_cypher_query(user_question, self.graph.schema)
            logger.info(f"Generated Cypher: {cypher}")

            # Validate
            if not self._validate_cypher(cypher):
                return "I cannot execute queries that modify the data. Please ask a question about existing information."

            # Execute
            data = self._execute_cypher(cypher)

            # Format answer
            result = self._format_answer(user_question, cypher, data)

            # Cache
            self._cache_result(user_question, result)

            # For backward compatibility, if caller expects string, they can take result['answer']
            return result

        except Exception as e:
            logger.exception(f"Query execution failed: {e}")
            return f"An error occurred while processing your query: {str(e)}"

    def raw_cypher_query(self, cypher: str) -> list:
        """Execute a raw Cypher query (admin use only)."""
        if not self.graph:
            raise Exception("Graph not connected")
        if not self._validate_cypher(cypher):
            raise ValueError("Query contains potentially destructive operations.")
        return self._execute_cypher(cypher)

class OSINTAggregator:
    @staticmethod
    def get_gdelt_data() -> Dict[str, Any]:
        return {
            "source": "GDELT Project",
            "global_tension_index": 68.4,
            "recent_events": [
                {"id": "ev1", "title": "Border Stability Exercise reported", "lat": 28.61, "lng": 77.21, "type": "Military", "source": "GDELT", "date": "2026-03-21 14:30"},
                {"id": "ev2", "title": "Large-scale farmer mobilization", "lat": 30.73, "lng": 76.77, "type": "Civil", "source": "Reuters", "date": "2026-03-21 15:45"},
                {"id": "ev3", "title": "Tech Corridor expansion protest", "lat": 12.97, "lng": 77.59, "type": "Civil", "source": "Local Feed", "date": "2026-03-21 16:10"},
            ]
        }

    @staticmethod
    def get_opensky_data() -> Dict[str, Any]:
        return {"source": "OpenSky Network (ADS-B)", "airspace_status": "Normal", "commercial_flights_active": 14205}

    @staticmethod
    def get_fred_economic_data() -> Dict[str, Any]:
        return {"source": "FRED API", "indicators": {"US_10YR_TREASURY": 4.25, "FED_FUNDS_RATE": 5.25}}

    @staticmethod
    def get_polymarket_data() -> Dict[str, Any]:
        return {"source": "Polymarket via API", "active_markets": []}

    @staticmethod
    def get_usgs_earthquakes() -> Dict[str, Any]:
        return {
            "source": "USGS Earthquake API",
            "recent_significant": [
                {"id": "q1", "lat": 15.1, "lng": 80.2, "magnitude": 4.2, "location": "Andhra Coastal", "depth": 10},
                {"id": "q2", "lat": 34.2, "lng": 74.8, "magnitude": 3.8, "location": "Kashmir Region", "depth": 25},
            ]
        }

    @staticmethod
    def get_nasa_firms() -> Dict[str, Any]:
        return {
            "source": "NASA FIRMS",
            "fire_hotspots_detected": 412,
            "hotspots": [
                {"lat": 30.1, "lng": 75.2, "confidence": 88, "intensity": 42.5},
                {"lat": 30.3, "lng": 75.8, "confidence": 92, "intensity": 51.2},
                {"lat": 19.1, "lng": 73.1, "confidence": 76, "intensity": 22.1},
            ]
        }

    @staticmethod
    def get_tabularis_sentiment(text: str) -> Dict[str, Any]:
        return {"source": "Tabularis AI Multilingual Model", "language_detected": "Hindi/Mixed", "sentiment_score": 0.5}

    @staticmethod
    def get_twitter_trends() -> Dict[str, Any]:
        return {"source": "TwitterAPI.io", "top_hashtags": ["#FarmersProtest", "#Budget2026"], "viral_sentiment": "Polarized"}

    @staticmethod
    def get_reddit_discourse() -> Dict[str, Any]:
        return {"source": "Reddit API", "active_discussions": [], "grassroots_consensus": "High anxiety"}

    @staticmethod
    def get_youtube_sentiment() -> Dict[str, Any]:
        return {"source": "YouTube Comments Analysis", "overall_sentiment": 0.12, "key_extracted_themes": []}

    @staticmethod
    def get_telegram_hyperlocal() -> Dict[str, Any]:
        return {"source": "Telegram Bot API", "monitored_channels": 15, "emerging_alerts": []}

    @staticmethod
    def get_bewgle_insights() -> Dict[str, Any]:
        return {"source": "Bewgle AI Insights", "customer_personas": ["Rural Farmer", "Urban Middle Class"], "topic_ratings": {}, "market_trend": "Shift"}

# Singleton instances
qa_engine = CivicIntelligenceQA()
osint_engine = OSINTAggregator()