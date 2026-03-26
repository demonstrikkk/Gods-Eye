import logging
import hashlib
import json
import re
import html
from typing import Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
import urllib.parse
import urllib.request
import urllib.error
import base64
import time
from pathlib import Path

from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
try:
    from langchain_neo4j import Neo4jGraph
except Exception:
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
    redis_client = None
    CACHE_AVAILABLE = False


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _json_get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 12,
    auth: Optional[tuple[str, str]] = None,
    retries: int = 2,
    retry_delay: float = 0.7,
) -> Any:
    req_headers = headers or {}
    if "User-Agent" not in req_headers:
        req_headers = {**req_headers, "User-Agent": OSINTAggregator.USER_AGENT}

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=req_headers)
            if auth:
                token = base64.b64encode(f"{auth[0]}:{auth[1]}".encode("utf-8")).decode("ascii")
                req.add_header("Authorization", f"Basic {token}")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_error = e
            is_transient = e.code in {408, 409, 425, 429, 500, 502, 503, 504}
            if not is_transient or attempt >= retries:
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            last_error = e
            if attempt >= retries:
                raise
        except Exception as e:
            last_error = e
            if attempt >= retries:
                raise

        time.sleep(retry_delay * (2**attempt))

    if last_error:
        raise last_error
    raise RuntimeError("Request failed without error context")

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
        if not CACHE_AVAILABLE or redis_client is None:
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
        if not CACHE_AVAILABLE or redis_client is None:
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
    USER_AGENT = "Gods-EyeOS/0.1 (student-dev intelligence cockpit)"
    _CACHE_TTL_SECONDS = 180
    _cache: Dict[str, Dict[str, Any]] = {}
    DATA_GOV_DEFAULT_QUERIES = [
        "air quality",
        "power generation",
        "rainfall",
        "public health",
        "agriculture",
    ]
    DATA_GOV_SEARCH_URLS = (
        "https://www.data.gov.in/search/site/{query}",
        "https://www.data.gov.in/catalogs?title={query}",
        "https://www.data.gov.in/catalog?title={query}",
    )
    DATA_GOV_RESOURCE_LINK_RE = re.compile(r"/resource/([A-Za-z0-9][A-Za-z0-9-]{5,})", re.IGNORECASE)
    DATA_GOV_API_LINK_RE = re.compile(r"/apis/([0-9a-fA-F-]{36})", re.IGNORECASE)
    DATA_GOV_TITLE_RE = re.compile(r"<title>([^<]{6,180})</title>", re.IGNORECASE | re.DOTALL)

    @classmethod
    def _cache_get(cls, key: str, ttl_seconds: Optional[int] = None) -> Optional[Dict[str, Any]]:
        cached = cls._cache.get(key)
        if not cached:
            return None
        ttl = ttl_seconds if ttl_seconds is not None else cls._CACHE_TTL_SECONDS
        if time.time() - cached.get("ts", 0) > ttl:
            return None
        return cached.get("value")

    @classmethod
    def _cache_set(cls, key: str, value: Dict[str, Any]) -> None:
        cls._cache[key] = {"ts": time.time(), "value": value}

    @classmethod
    def _data_gov_cache_path(cls) -> Path:
        return Path(__file__).resolve().parent.parent / "data" / "data_gov_catalog_cache.json"

    @classmethod
    def _read_data_gov_cache(cls) -> Dict[str, Any]:
        path = cls._data_gov_cache_path()
        if not path.exists():
            return {"last_synced": None, "resources": []}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Failed to read data.gov.in cache: {e}")
            return {"last_synced": None, "resources": []}

    @classmethod
    def _write_data_gov_cache(cls, cache: Dict[str, Any]) -> None:
        path = cls._data_gov_cache_path()
        try:
            path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to write data.gov.in cache: {e}")

    @classmethod
    def _data_gov_queries(cls) -> List[str]:
        raw = settings.DATA_GOV_IN_QUERY_TERMS.strip()
        if raw:
            return [item.strip() for item in raw.split(",") if item.strip()]
        return list(cls.DATA_GOV_DEFAULT_QUERIES)

    @staticmethod
    def _score_data_gov_entry(entry: Dict[str, Any], queries: List[str]) -> int:
        haystack = " ".join(
            str(entry.get(field, "")).lower()
            for field in ("title", "description", "source_query")
        )
        score = 0
        for query in queries:
            tokens = [token for token in re.split(r"\W+", query.lower()) if token]
            if not tokens:
                continue
            matched = sum(token in haystack for token in tokens)
            score += matched * 5
            if query.lower() in haystack:
                score += 8
        return score

    @classmethod
    def _extract_data_gov_entries(cls, html: str, query: str) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        seen: set[str] = set()
        page_title_match = cls.DATA_GOV_TITLE_RE.search(html)
        page_title = page_title_match.group(1).strip() if page_title_match else ""

        def add_entry(resource_id: str, context: str, discovered_from: str) -> None:
            if resource_id in seen:
                return
            seen.add(resource_id)
            title_match = re.search(r'title="([^"]{6,180})"', context, flags=re.IGNORECASE)
            entries.append(
                {
                    "resource_id": resource_id,
                    "title": title_match.group(1).strip() if title_match else page_title or f"Query match for {query}",
                    "description": "",
                    "source_query": query,
                    "discovered_from": discovered_from,
                }
            )

        for match in cls.DATA_GOV_RESOURCE_LINK_RE.finditer(html):
            resource_id = match.group(1)
            context = html[max(0, match.start() - 260): min(len(html), match.end() + 260)]
            api_match = cls.DATA_GOV_API_LINK_RE.search(context)
            if api_match:
                add_entry(api_match.group(1), context, "api_detail")
            else:
                add_entry(resource_id, context, "html_search")

        for match in cls.DATA_GOV_API_LINK_RE.finditer(html):
            resource_id = match.group(1)
            context = html[max(0, match.start() - 260): min(len(html), match.end() + 260)]
            add_entry(resource_id, context, "api_detail")
        return entries

    @classmethod
    def _discover_data_gov_resources(cls, queries: List[str]) -> Dict[str, Any]:
        cache = cls._read_data_gov_cache()
        existing = {item.get("resource_id"): item for item in cache.get("resources", []) if item.get("resource_id")}
        discovered_any = False

        for query in queries:
            encoded = urllib.parse.quote(query)
            for template in cls.DATA_GOV_SEARCH_URLS:
                url = template.format(query=encoded)
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": cls.USER_AGENT})
                    with urllib.request.urlopen(req, timeout=12) as response:
                        html = response.read().decode("utf-8", errors="ignore")
                    matches = cls._extract_data_gov_entries(html, query)
                    for match in matches:
                        resource_id = match["resource_id"]
                        prior = existing.get(resource_id, {})
                        existing[resource_id] = {
                            **prior,
                            **match,
                            "last_seen": datetime.utcnow().isoformat(),
                        }
                    if matches:
                        discovered_any = True
                        break
                except Exception:
                    continue

        resources = sorted(
            existing.values(),
            key=lambda item: cls._score_data_gov_entry(item, queries),
            reverse=True,
        )
        updated_cache = {
            "last_synced": datetime.utcnow().isoformat() if discovered_any else cache.get("last_synced"),
            "resources": resources[:200],
        }
        if discovered_any or updated_cache != cache:
            cls._write_data_gov_cache(updated_cache)
        return {
            "resources": resources,
            "used_cache_only": not discovered_any,
            "last_synced": updated_cache.get("last_synced"),
        }

    @classmethod
    def get_gdelt_data(cls) -> Dict[str, Any]:
        cached = cls._cache_get("gdelt", ttl_seconds=240)
        if cached:
            return cached

        url = (
            "https://api.gdeltproject.org/api/v2/doc/doc?"
            + urllib.parse.urlencode(
                {
                    "query": "(conflict OR protest OR election OR sanctions OR cyclone OR flood)",
                    "mode": "ArtList",
                    "maxrecords": 5,
                    "format": "json",
                    "sort": "datedesc",
                }
            )
        )
        try:
            payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT}, retries=3, retry_delay=1.0)
            articles = payload.get("articles", []) if isinstance(payload, dict) else []
            fallback_coords = [
                (50.4501, 30.5234),
                (24.7136, 46.6753),
                (20.5937, 78.9629),
                (1.3521, 103.8198),
                (38.9072, -77.0369),
                (52.52, 13.405),
            ]
            events = []
            for index, article in enumerate(articles[:6]):
                lat, lng = fallback_coords[index % len(fallback_coords)]
                events.append(
                    {
                        "id": f"gdelt-{index}",
                        "title": article.get("title", "GDELT event"),
                        "lat": lat,
                        "lng": lng,
                        "type": article.get("sourcecountry", "Global"),
                        "source": article.get("domain", "GDELT"),
                        "date": article.get("seendate", ""),
                        "url": article.get("url", ""),
                    }
                )
            result = {
                "source": "GDELT Project",
                "global_tension_index": min(95, 45 + len(events) * 4),
                "recent_events": events,
            }
            cls._cache_set("gdelt", result)
            return result
            
        except Exception as e:
            logger.warning(f"GDELT fetch failed: {e}")
            fallback = {
                "source": "GDELT Project (fallback)",
                "global_tension_index": 68.4,
                "recent_events": [
                    {"id": "ev1", "title": "Black Sea logistics disruption flagged", "lat": 46.4825, "lng": 30.7233, "type": "Logistics", "source": "GDELT", "date": datetime.utcnow().isoformat()},
                    {"id": "ev2", "title": "Heatwave pressure building across South Asia", "lat": 28.6139, "lng": 77.209, "type": "Climate", "source": "GDELT", "date": datetime.utcnow().isoformat()},
                ],
            }
            stale = cls._cache_get("gdelt", ttl_seconds=3600)
            if stale:
                return stale
            cls._cache_set("gdelt", fallback)
            return fallback

    @classmethod
    def get_opensky_data(cls) -> Dict[str, Any]:
        try:
            auth = None
            if settings.OPENSKY_USERNAME and settings.OPENSKY_PASSWORD:
                auth = (settings.OPENSKY_USERNAME, settings.OPENSKY_PASSWORD)
            payload = _json_get(
                "https://opensky-network.org/api/states/all",
                headers={"User-Agent": cls.USER_AGENT},
                auth=auth,
            )
            states = payload.get("states", []) if isinstance(payload, dict) else []
            return {
                "source": "OpenSky Network (ADS-B)",
                "airspace_status": "Elevated" if len(states) > 15000 else "Normal",
                "commercial_flights_active": len(states),
                "sample_flights": [
                    {
                        "callsign": state[1].strip() if len(state) > 1 and state[1] else "UNKNOWN",
                        "country": state[2],
                        "lat": state[6],
                        "lng": state[5],
                    }
                    for state in states[:10]
                ],
            }
        except Exception as e:
            logger.warning(f"OpenSky fetch failed: {e}")
            return {"source": "OpenSky Network (fallback)", "airspace_status": "Normal", "commercial_flights_active": 0, "sample_flights": []}

    @classmethod
    def _fred_series(cls, series_id: str, limit: int = 1) -> List[Dict[str, Any]]:
        if not settings.FRED_API_KEY:
            return []
        url = (
            "https://api.stlouisfed.org/fred/series/observations?"
            + urllib.parse.urlencode(
                {
                    "series_id": series_id,
                    "api_key": settings.FRED_API_KEY,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": limit,
                }
            )
        )
        payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT})
        return payload.get("observations", []) if isinstance(payload, dict) else []

    @classmethod
    def get_fred_economic_data(cls) -> Dict[str, Any]:
        try:
            fed = cls._fred_series("FEDFUNDS")
            treasury = cls._fred_series("DGS10")
            inflation = cls._fred_series("CPIAUCSL")
            return {
                "source": "FRED API",
                "indicators": {
                    "FED_FUNDS_RATE": _safe_float(fed[0]["value"]) if fed else None,
                    "US_10YR_TREASURY": _safe_float(treasury[0]["value"]) if treasury else None,
                    "US_CPI": _safe_float(inflation[0]["value"]) if inflation else None,
                },
            }
        except Exception as e:
            logger.warning(f"FRED fetch failed: {e}")
            return {"source": "FRED API (fallback)", "indicators": {"US_10YR_TREASURY": 4.25, "FED_FUNDS_RATE": 5.25, "US_CPI": 319.8}}

    @classmethod
    def get_polymarket_data(cls) -> Dict[str, Any]:
        try:
            payload = _json_get("https://gamma-api.polymarket.com/markets?limit=8", headers={"User-Agent": cls.USER_AGENT})
            markets = payload if isinstance(payload, list) else []
            return {
                "source": "Polymarket",
                "active_markets": [
                    {
                        "question": market.get("question"),
                        "active": market.get("active"),
                        "volume": market.get("volume"),
                        "endDate": market.get("endDate"),
                    }
                    for market in markets[:6]
                ],
            }
        except Exception as e:
            logger.warning(f"Polymarket fetch failed: {e}")
            return {"source": "Polymarket (fallback)", "active_markets": []}

    @classmethod
    def get_usgs_earthquakes(cls) -> Dict[str, Any]:
        try:
            payload = _json_get(
                "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_week.geojson",
                headers={"User-Agent": cls.USER_AGENT},
            )
            features = payload.get("features", []) if isinstance(payload, dict) else []
            return {
                "source": "USGS Earthquake API",
                "recent_significant": [
                    {
                        "id": feature.get("id"),
                        "lat": feature.get("geometry", {}).get("coordinates", [0, 0, 0])[1],
                        "lng": feature.get("geometry", {}).get("coordinates", [0, 0, 0])[0],
                        "magnitude": feature.get("properties", {}).get("mag"),
                        "location": feature.get("properties", {}).get("place"),
                        "depth": feature.get("geometry", {}).get("coordinates", [0, 0, 0])[2],
                    }
                    for feature in features[:10]
                ],
            }
        except Exception as e:
            logger.warning(f"USGS fetch failed: {e}")
            return {"source": "USGS Earthquake API (fallback)", "recent_significant": []}

    @classmethod
    def get_nasa_firms(cls) -> Dict[str, Any]:
        try:
            payload = _json_get(
                "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&category=wildfires&limit=12",
                headers={"User-Agent": cls.USER_AGENT},
            )
            events = payload.get("events", []) if isinstance(payload, dict) else []
            hotspots = []
            for event in events:
                geometries = event.get("geometry", [])
                if not geometries:
                    continue
                latest = geometries[-1]
                coords = latest.get("coordinates", [0, 0])
                hotspots.append(
                    {
                        "id": event.get("id"),
                        "lat": coords[1],
                        "lng": coords[0],
                        "confidence": 80,
                        "intensity": 35.0,
                        "title": event.get("title"),
                    }
                )
            return {"source": "NASA EONET Wildfires", "fire_hotspots_detected": len(hotspots), "hotspots": hotspots}
        except Exception as e:
            logger.warning(f"NASA wildfire fetch failed: {e}")
            return {"source": "NASA EONET Wildfires (fallback)", "fire_hotspots_detected": 0, "hotspots": []}

    @staticmethod
    def get_tabularis_sentiment(text: str) -> Dict[str, Any]:
        positive_tokens = ["growth", "agreement", "stable", "recovery", "success"]
        negative_tokens = ["war", "crisis", "disruption", "attack", "flood", "fire"]
        lower = text.lower()
        pos = sum(token in lower for token in positive_tokens)
        neg = sum(token in lower for token in negative_tokens)
        score = 0.5 + (pos - neg) * 0.1
        return {"source": "Keyword Sentiment Fallback", "language_detected": "English", "sentiment_score": max(0.0, min(1.0, score))}

    @classmethod
    def get_twitter_trends(cls) -> Dict[str, Any]:
        # Paid providers are optional during student/dev mode. Use GDELT/news fallback when unavailable.
        gdelt = cls.get_gdelt_data()
        titles = [event["title"] for event in gdelt.get("recent_events", [])[:5]]
        hashtags = [f"#{''.join(ch for ch in title.split()[0] if ch.isalnum())}" for title in titles if title]
        return {"source": "Derived Trends Fallback", "top_hashtags": hashtags[:5], "viral_sentiment": "Elevated" if gdelt.get("global_tension_index", 0) > 60 else "Mixed"}

    @classmethod
    def get_reddit_discourse(cls) -> Dict[str, Any]:
        try:
            url = "https://www.reddit.com/search.json?q=geopolitics%20OR%20economy&sort=hot&limit=8"
            payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT})
            posts = payload.get("data", {}).get("children", []) if isinstance(payload, dict) else []
            discussions = []
            for post in posts:
                item = post.get("data", {})
                discussions.append(
                    {
                        "title": item.get("title"),
                        "subreddit": item.get("subreddit"),
                        "score": item.get("score"),
                        "comments": item.get("num_comments"),
                        "url": f"https://reddit.com{item.get('permalink', '')}",
                    }
                )
            return {
                "source": "Reddit Public JSON",
                "active_discussions": discussions,
                "grassroots_consensus": "Anxious" if any((post.get("comments") or 0) > 500 for post in discussions) else "Mixed",
            }
        except Exception as e:
            logger.warning(f"Reddit fetch failed: {e}")
            return {"source": "Reddit Public JSON (fallback)", "active_discussions": [], "grassroots_consensus": "Unknown"}

    @staticmethod
    def _search_queries(country_name: Optional[str] = None) -> List[str]:
        if country_name:
            return [
                f"{country_name} geopolitics risk",
                f"{country_name} economic outlook",
                f"{country_name} climate infrastructure cyber",
            ]
        return [
            "india geopolitics risk",
            "global energy disruption",
            "cybersecurity incident today",
        ]

    @staticmethod
    def _extract_search_results(html_text: str, limit: int = 8) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        seen: set[str] = set()
        pattern = re.compile(r'<a[^>]+href="(https?://[^"#]+)"[^>]*>(.*?)</a>', flags=re.IGNORECASE | re.DOTALL)
        for href, title_raw in pattern.findall(html_text):
            href_lower = href.lower()
            if any(host in href_lower for host in ["duckduckgo.com", "search.yahoo.com", "r.search.yahoo.com"]):
                continue
            if href_lower in seen:
                continue
            title = re.sub(r"<[^>]+>", " ", title_raw)
            title = html.unescape(re.sub(r"\s+", " ", title)).strip()
            if len(title) < 12:
                continue
            seen.add(href_lower)
            results.append({"title": title, "url": href})
            if len(results) >= limit:
                break
        return results

    @classmethod
    def get_duckduckgo_search_results(cls, query: Optional[str] = None) -> Dict[str, Any]:
        query = query or " OR ".join(cls._search_queries())
        cache_key = f"search:ddg:{query.lower()}"
        cached = cls._cache_get(cache_key, ttl_seconds=300)
        if cached:
            return cached
        try:
            url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query, "kl": "in-en"})
            req = urllib.request.Request(url, headers={"User-Agent": cls.USER_AGENT})
            with urllib.request.urlopen(req, timeout=12) as response:
                page = response.read().decode("utf-8", errors="ignore")
            results = cls._extract_search_results(page, limit=8)
            payload = {
                "source": "DuckDuckGo Search",
                "query": query,
                "results": results,
                "status": "live" if results else "fallback",
            }
            cls._cache_set(cache_key, payload)
            return payload
        except Exception as e:
            logger.warning(f"DuckDuckGo search fetch failed: {e}")
            fallback = {
                "source": "DuckDuckGo Search (fallback)",
                "query": query,
                "results": [],
                "status": "error",
            }
            stale = cls._cache_get(cache_key, ttl_seconds=3600)
            return stale or fallback

    @classmethod
    def get_yahoo_search_results(cls, query: Optional[str] = None) -> Dict[str, Any]:
        query = query or " OR ".join(cls._search_queries())
        cache_key = f"search:yahoo:{query.lower()}"
        cached = cls._cache_get(cache_key, ttl_seconds=300)
        if cached:
            return cached
        try:
            url = "https://search.yahoo.com/search?" + urllib.parse.urlencode({"p": query, "ei": "UTF-8"})
            req = urllib.request.Request(url, headers={"User-Agent": cls.USER_AGENT})
            with urllib.request.urlopen(req, timeout=12) as response:
                page = response.read().decode("utf-8", errors="ignore")
            results = cls._extract_search_results(page, limit=8)
            payload = {
                "source": "Yahoo Search",
                "query": query,
                "results": results,
                "status": "live" if results else "fallback",
            }
            cls._cache_set(cache_key, payload)
            return payload
        except Exception as e:
            logger.warning(f"Yahoo search fetch failed: {e}")
            fallback = {
                "source": "Yahoo Search (fallback)",
                "query": query,
                "results": [],
                "status": "error",
            }
            stale = cls._cache_get(cache_key, ttl_seconds=3600)
            return stale or fallback

    @classmethod
    def get_country_search_briefs(cls, country_name: str, region: Optional[str] = None) -> Dict[str, Any]:
        query_terms = cls._search_queries(country_name)
        if region:
            query_terms.append(f"{region} regional stability")
        query = " OR ".join(query_terms)
        ddg = cls.get_duckduckgo_search_results(query=query)
        yahoo = cls.get_yahoo_search_results(query=query)

        merged: List[Dict[str, str]] = []
        seen_urls: set[str] = set()
        for source_name, payload in (("DuckDuckGo", ddg), ("Yahoo", yahoo)):
            for item in payload.get("results", []):
                url = str(item.get("url", "")).strip()
                title = str(item.get("title", "")).strip()
                if not url or not title or url in seen_urls:
                    continue
                seen_urls.add(url)
                merged.append({"title": title, "url": url, "source": source_name})
                if len(merged) >= 8:
                    break
            if len(merged) >= 8:
                break

        status = "live" if merged else "fallback"
        return {
            "source": "Country Search Briefs",
            "country": country_name,
            "query": query,
            "results": merged,
            "status": status,
        }

    @classmethod
    def get_youtube_sentiment(cls) -> Dict[str, Any]:
        try:
            if not settings.YOUTUBE_API_KEY:
                raise ValueError("Missing YouTube API key")
            search_url = (
                "https://www.googleapis.com/youtube/v3/search?"
                + urllib.parse.urlencode(
                    {
                        "part": "snippet",
                        "q": "geopolitics OR economy",
                        "maxResults": 5,
                        "type": "video",
                        "key": settings.YOUTUBE_API_KEY,
                    }
                )
            )
            payload = _json_get(search_url, headers={"User-Agent": cls.USER_AGENT})
            items = payload.get("items", []) if isinstance(payload, dict) else []
            themes = [item.get("snippet", {}).get("title") for item in items[:5]]
            return {"source": "YouTube Data API", "overall_sentiment": 0.5, "key_extracted_themes": themes}
        except Exception as e:
            logger.warning(f"YouTube fetch failed: {e}")
            return {"source": "YouTube Data API (fallback)", "overall_sentiment": 0.0, "key_extracted_themes": []}

    @staticmethod
    def get_telegram_hyperlocal() -> Dict[str, Any]:
        return {"source": "Telegram Public Monitoring", "monitored_channels": 0, "emerging_alerts": []}

    @classmethod
    def get_bewgle_insights(cls) -> Dict[str, Any]:
        signals = cls.get_gdelt_data().get("recent_events", [])
        personas = ["Energy-sensitive importer", "Climate-exposed district", "Trade corridor observer"]
        topic_ratings = {event["title"]: 0.6 for event in signals[:3]}
        return {"source": "Derived Insight Fallback", "customer_personas": personas, "topic_ratings": topic_ratings, "market_trend": "Volatile"}

    @classmethod
    def get_mastodon_public(cls) -> Dict[str, Any]:
        try:
            base = settings.MASTODON_API_BASE_URL.rstrip("/")
            candidate_urls = [
                f"{base}/api/v1/timelines/public?limit=10&local=true",
                f"{base}/api/v1/timelines/public?limit=10",
            ]
            posts = []
            for url in candidate_urls:
                try:
                    payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT}, retries=1)
                    posts = payload if isinstance(payload, list) else []
                    if posts:
                        break
                except Exception:
                    continue
            return {
                "source": "Mastodon Public Timeline",
                "posts": [
                    {
                        "id": post.get("id"),
                        "content": post.get("content", "")[:160],
                        "replies": post.get("replies_count"),
                        "reblogs": post.get("reblogs_count"),
                        "favourites": post.get("favourites_count"),
                    }
                    for post in posts[:8]
                ],
            }
        except Exception as e:
            logger.warning(f"Mastodon fetch failed: {e}")
            return {"source": "Mastodon Public Timeline (fallback)", "posts": []}

    @staticmethod
    def get_bluesky_trends() -> Dict[str, Any]:
        return {"source": "Bluesky Public Fallback", "posts": [], "trend_state": "Unavailable without scraper/runtime token"}

    @classmethod
    def get_acled_data(cls) -> Dict[str, Any]:
        gdelt = cls.get_gdelt_data()
        events = gdelt.get("recent_events", [])
        mapped = [
            {
                "region": event.get("type", "Global"),
                "title": event.get("title"),
                "date": event.get("date"),
                "source": event.get("source"),
                "india_exposure": "Medium",
            }
            for event in events[:6]
        ]
        return {"source": "Conflict Feed via GDELT fallback", "active_conflicts": mapped, "global_conflict_index": gdelt.get("global_tension_index", 0)}

    @classmethod
    def get_energy_markets(cls) -> Dict[str, Any]:
        try:
            indicators = cls.get_fred_economic_data().get("indicators", {})
            wti = cls._fred_series("DCOILWTICO")
            brent = cls._fred_series("DCOILBRENTEU")
            brent_value = _safe_float(brent[0]["value"]) if brent else None
            return {
                "source": "FRED Energy Series",
                "brent_crude_usd": brent_value,
                "wti_crude_usd": _safe_float(wti[0]["value"]) if wti else None,
                "natural_gas_usd": indicators.get("US_10YR_TREASURY"),
                "india_oil_import_dependency": "87%+",
                "risk_assessment": "Elevated" if brent_value is not None and brent_value > 85 else "Moderate",
            }
        except Exception as e:
            logger.warning(f"Energy market fetch failed: {e}")
            return {"source": "Energy Market Fallback", "brent_crude_usd": None, "wti_crude_usd": None, "india_oil_import_dependency": "87%+", "risk_assessment": "Unknown"}

    @classmethod
    def get_defense_posture(cls) -> Dict[str, Any]:
        opensky = cls.get_opensky_data()
        gdelt = cls.get_gdelt_data()
        return {
            "source": "Composite Defense Posture",
            "border_alert_level": "Elevated" if gdelt.get("global_tension_index", 0) >= 60 else "Normal",
            "active_deployments": [event["title"] for event in gdelt.get("recent_events", [])[:3]],
            "cyber_threat_level": "Moderate",
            "aviation_load": opensky.get("commercial_flights_active", 0),
        }

    @classmethod
    def get_world_bank_snapshot(cls) -> Dict[str, Any]:
        countries = ["IND", "USA", "CHN", "BRA", "ZAF"]
        indicators = {
            "gdp_current_usd": "NY.GDP.MKTP.CD",
            "inflation_consumer": "FP.CPI.TOTL.ZG",
            "population_total": "SP.POP.TOTL",
        }
        snapshot: Dict[str, Any] = {"source": "World Bank Open Data", "countries": {}}
        try:
            for code in countries:
                snapshot["countries"][code] = {}
                for label, indicator in indicators.items():
                    url = f"https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?format=json&per_page=2"
                    payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT})
                    rows = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
                    latest = next((row for row in rows if row.get("value") is not None), None)
                    snapshot["countries"][code][label] = {
                        "value": latest.get("value") if latest else None,
                        "date": latest.get("date") if latest else None,
                    }
            return snapshot
        except Exception as e:
            logger.warning(f"World Bank fetch failed: {e}")
            return {"source": "World Bank Open Data (fallback)", "countries": {}}

    @classmethod
    def get_country_catalog(cls) -> Dict[str, Any]:
        try:
            payload = _json_get(
                "https://restcountries.com/v3.1/all?fields=name,cca3,latlng,region,subregion,population,capital,area",
                headers={"User-Agent": cls.USER_AGENT},
            )
            rows = payload if isinstance(payload, list) else []
            countries = []
            for row in rows:
                latlng = row.get("latlng", [])
                if len(latlng) < 2 or not row.get("cca3") or not row.get("name", {}).get("common"):
                    continue
                countries.append(
                    {
                        "id": f"CTR-{row['cca3']}",
                        "iso3": row["cca3"],
                        "name": row["name"]["common"],
                        "region": row.get("subregion") or row.get("region") or "Global",
                        "macro_region": row.get("region") or "Global",
                        "lat": latlng[0],
                        "lng": latlng[1],
                        "population": row.get("population", 0),
                        "capital": (row.get("capital") or [None])[0],
                        "area": row.get("area"),
                    }
                )
            return {"source": "REST Countries", "countries": countries, "status": "live"}
        except Exception as e:
            logger.warning(f"Country catalog fetch failed: {e}")
            return {"source": "REST Countries (fallback)", "countries": [], "status": "error"}

    @classmethod
    def get_cisa_kev_data(cls) -> Dict[str, Any]:
        try:
            payload = _json_get(
                "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
                headers={"User-Agent": cls.USER_AGENT},
            )
            vulns = payload.get("vulnerabilities", []) if isinstance(payload, dict) else []
            return {
                "source": "CISA KEV Catalog",
                "status": "live",
                "vulnerabilities": [
                    {
                        "cve": vuln.get("cveID"),
                        "vendor": vuln.get("vendorProject"),
                        "product": vuln.get("product"),
                        "added": vuln.get("dateAdded"),
                        "required_action": vuln.get("requiredAction"),
                        "description": vuln.get("shortDescription"),
                    }
                    for vuln in vulns[:8]
                ],
            }
        except Exception as e:
            logger.warning(f"CISA KEV fetch failed: {e}")
            return {"source": "CISA KEV Catalog (fallback)", "status": "error", "vulnerabilities": []}

    @classmethod
    def get_open_meteo_weather(cls, lat: float, lng: float) -> Dict[str, Any]:
        try:
            url = (
                "https://api.open-meteo.com/v1/forecast?"
                + urllib.parse.urlencode(
                    {
                        "latitude": lat,
                        "longitude": lng,
                        "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m,weather_code",
                        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                        "forecast_days": 1,
                        "timezone": "auto",
                    }
                )
            )
            payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT})
            current = payload.get("current", {}) if isinstance(payload, dict) else {}
            daily = payload.get("daily", {}) if isinstance(payload, dict) else {}
            return {
                "source": "Open-Meteo",
                "status": "live",
                "current": current,
                "daily": {
                    "temperature_2m_max": (daily.get("temperature_2m_max") or [None])[0],
                    "temperature_2m_min": (daily.get("temperature_2m_min") or [None])[0],
                    "precipitation_sum": (daily.get("precipitation_sum") or [None])[0],
                    "wind_speed_10m_max": (daily.get("wind_speed_10m_max") or [None])[0],
                },
            }
        except Exception as e:
            logger.warning(f"Open-Meteo weather fetch failed: {e}")
            return {"source": "Open-Meteo (fallback)", "status": "error", "current": {}, "daily": {}}

    @classmethod
    def get_eia_energy_data(cls) -> Dict[str, Any]:
        if not settings.EIA_API_KEY:
            return {"source": "EIA API", "series": {}, "status": "missing_key"}
        try:
            series = {
                "brent": "PET.RBRTE.D",
                "wti": "PET.RWTC.D",
            }
            result = {"source": "EIA API", "series": {}}
            for label, series_id in series.items():
                url = (
                    "https://api.eia.gov/v2/seriesid/"
                    + urllib.parse.quote(series_id, safe="")
                    + "?"
                    + urllib.parse.urlencode({"api_key": settings.EIA_API_KEY, "length": 3})
                )
                payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT})
                rows = payload.get("response", {}).get("data", []) if isinstance(payload, dict) else []
                latest = rows[0] if rows else {}
                result["series"][label] = {
                    "value": latest.get("value"),
                    "period": latest.get("period"),
                }
            return result
        except Exception as e:
            logger.warning(f"EIA fetch failed: {e}")
            return {"source": "EIA API (fallback)", "series": {}}

    @classmethod
    def get_data_gov_snapshot(cls) -> Dict[str, Any]:
        data_gov_key = settings.DATA_GOV_IN_KEY or settings.VITE_DATA_GOV_IN_KEY
        resource_ids = [item.strip() for item in settings.DATA_GOV_IN_RESOURCE_IDS.split(",") if item.strip()]
        query_terms = cls._data_gov_queries()
        if not data_gov_key:
            return {
                "source": "data.gov.in",
                "datasets": [],
                "status": "missing_key",
                "strategy": "unconfigured",
                "message": "Missing API key for data.gov.in connector.",
            }

        discovery = {"resources": [], "used_cache_only": False, "last_synced": None}
        strategy = "resource_ids"
        if not resource_ids:
            discovery = cls._discover_data_gov_resources(query_terms)
            ranked = discovery.get("resources", [])
            resource_ids = [item["resource_id"] for item in ranked[:3] if item.get("resource_id")]
            strategy = "cached_query_discovery" if discovery.get("used_cache_only") else "query_discovery"
        if not resource_ids:
            return {
                "source": "data.gov.in",
                "datasets": [],
                "status": "fallback",
                "strategy": strategy,
                "selected_queries": query_terms,
                "catalog_entries": len(discovery.get("resources", [])),
                "message": "No resource ids available yet. Add DATA_GOV_IN_RESOURCE_IDS or allow the cache to warm through query discovery.",
            }

        catalog_by_id = {
            item.get("resource_id"): item
            for item in discovery.get("resources", [])
            if item.get("resource_id")
        }
        datasets = []
        try:
            for resource_id in resource_ids[:3]:
                url = (
                    f"https://api.data.gov.in/resource/{resource_id}?"
                    + urllib.parse.urlencode(
                        {
                            "api-key": data_gov_key,
                            "format": "json",
                            "limit": 5,
                        }
                    )
                )
                payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT})
                records = payload.get("records", []) if isinstance(payload, dict) else []
                metadata = catalog_by_id.get(resource_id, {})
                datasets.append(
                    {
                        "resource_id": resource_id,
                        "title": payload.get("title") or metadata.get("title") or resource_id,
                        "record_count": len(records),
                        "sample": records[:2],
                        "source_query": metadata.get("source_query"),
                    }
                )
            detail = (
                "data.gov.in live via explicit resource ids."
                if strategy == "resource_ids"
                else f"data.gov.in live via {strategy.replace('_', ' ')}."
            )
            return {
                "source": "data.gov.in",
                "datasets": datasets,
                "status": "live",
                "strategy": strategy,
                "selected_queries": query_terms if strategy != "resource_ids" else [],
                "catalog_entries": len(discovery.get("resources", [])),
                "last_catalog_sync": discovery.get("last_synced"),
                "message": detail,
            }
        except Exception as e:
            logger.warning(f"data.gov.in fetch failed: {e}")
            return {
                "source": "data.gov.in (fallback)",
                "datasets": [],
                "status": "error",
                "strategy": strategy,
                "selected_queries": query_terms if strategy != "resource_ids" else [],
                "catalog_entries": len(discovery.get("resources", [])),
                "message": f"data.gov.in fetch failed after {strategy.replace('_', ' ')}.",
            }

    @classmethod
    def get_market_snapshot(cls) -> Dict[str, Any]:
        tickers = {
            "SPY": "S&P 500 ETF",
            "QQQ": "Nasdaq 100 ETF",
            "INDA": "India ETF",
            "GLD": "Gold ETF",
            "BTCUSD": "Bitcoin",
        }
        quotes = []
        if not settings.FINNHUB_API_KEY:
            return {"source": "Finnhub", "quotes": quotes, "status": "missing_key"}
        try:
            for symbol, name in tickers.items():
                url = (
                    "https://finnhub.io/api/v1/quote?"
                    + urllib.parse.urlencode({"symbol": symbol, "token": settings.FINNHUB_API_KEY})
                )
                payload = _json_get(url, headers={"User-Agent": cls.USER_AGENT})
                current = _safe_float(payload.get("c"))
                previous_close = _safe_float(payload.get("pc"))
                change_pct = round(((current - previous_close) / previous_close) * 100, 2) if previous_close else 0.0
                quotes.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "price": current,
                        "change_pct": change_pct,
                        "high": _safe_float(payload.get("h")),
                        "low": _safe_float(payload.get("l")),
                    }
                )
            return {"source": "Finnhub", "quotes": quotes, "status": "live"}
        except Exception as e:
            logger.warning(f"Finnhub fetch failed: {e}")
            return {"source": "Finnhub (fallback)", "quotes": [], "status": "error"}

    @classmethod
    def get_global_alerts(cls) -> list[Dict[str, Any]]:
        alerts: list[Dict[str, Any]] = []
        for event in cls.get_gdelt_data().get("recent_events", [])[:4]:
            alerts.append(
                {
                    "id": event.get("id"),
                    "source": event.get("source", "GDELT"),
                    "category": event.get("type", "Geopolitics"),
                    "text": event.get("title", ""),
                    "urgency": "High" if "war" in event.get("title", "").lower() or "disruption" in event.get("title", "").lower() else "Medium",
                    "time": event.get("date", "LIVE"),
                }
            )
        for quake in cls.get_usgs_earthquakes().get("recent_significant", [])[:2]:
            alerts.append(
                {
                    "id": quake.get("id"),
                    "source": "USGS",
                    "category": "Seismic",
                    "text": f"M{quake.get('magnitude')} earthquake near {quake.get('location')}",
                    "urgency": "High" if _safe_float(quake.get("magnitude")) >= 6 else "Medium",
                    "time": "LIVE",
                }
            )
        for fire in cls.get_nasa_firms().get("hotspots", [])[:2]:
            alerts.append(
                {
                    "id": fire.get("id"),
                    "source": "NASA",
                    "category": "Climate",
                    "text": fire.get("title", "Wildfire hotspot detected"),
                    "urgency": "Medium",
                    "time": "LIVE",
                }
            )
        return alerts

# Singleton instances
qa_engine = CivicIntelligenceQA()
osint_engine = OSINTAggregator()
