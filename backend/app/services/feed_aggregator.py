
import asyncio
import aiohttp
import logging
import time
from typing import List, Dict, Optional, Set
from datetime import datetime
import feedparser  # still used for parsing, but we'll wrap it in a thread
from app.core.config import settings
from app.data.store import store
from app.services.intelligence_engine import process_unstructured_civic_text

logger = logging.getLogger("feed_aggregator")

# ----------------------------------------------------------------------
# Feed configuration – you can move this to environment variables later
# ----------------------------------------------------------------------
FEEDS = [
    {
        "name": "Reuters World",
        "url": "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
        "fallback_urls": [
            "https://news.google.com/rss/search?q=reuters+world+news&hl=en-IN&gl=IN&ceid=IN:en",
        ],
        "category": "Geopolitics",
    },
    {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml", "category": "Geopolitics"},
    {
        "name": "Al Jazeera",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "fallback_urls": [
            "https://news.google.com/rss/search?q=al+jazeera+world&hl=en-IN&gl=IN&ceid=IN:en",
        ],
        "category": "Geopolitics",
    },
    {"name": "DW World", "url": "https://rss.dw.com/rdf/rss-en-all", "category": "Geopolitics"},
    {"name": "France24", "url": "https://www.france24.com/en/rss", "category": "Geopolitics"},
    {"name": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/", "category": "Defense"},
    {"name": "The Diplomat", "url": "https://thediplomat.com/feed/", "category": "Geopolitics"},
    {"name": "Economic Times", "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms", "category": "Economics"},
    {
        "name": "PIB India",
        "url": "https://pib.gov.in/RssMain.aspx",
        "fallback_urls": [
            "https://news.google.com/rss/search?q=Press+Information+Bureau+India&hl=en-IN&gl=IN&ceid=IN:en",
        ],
        "category": "Governance",
    },
    {
        "name": "India Meteorological Department",
        "url": "https://news.google.com/rss/search?q=India+Meteorological+Department+weather+alert&hl=en-IN&gl=IN&ceid=IN:en",
        "category": "Climate",
    },
    {"name": "Global Conflict Watch", "url": "https://news.google.com/rss/search?q=global+conflict+protest+military&hl=en-IN&gl=IN&ceid=IN:en", "category": "Conflict"},
    {"name": "Cyber Threat Watch", "url": "https://news.google.com/rss/search?q=cyber+attack+ransomware+cisa&hl=en-IN&gl=IN&ceid=IN:en", "category": "Cyber"},
    {"name": "Climate Extremes Watch", "url": "https://news.google.com/rss/search?q=wildfire+heatwave+flood+weather+alert&hl=en-IN&gl=IN&ceid=IN:en", "category": "Climate"},
    {"name": "Trade Route Watch", "url": "https://news.google.com/rss/search?q=shipping+red+sea+suez+trade+route&hl=en-IN&gl=IN&ceid=IN:en", "category": "Mobility"},
    {"name": "AI Infrastructure Watch", "url": "https://news.google.com/rss/search?q=AI+data+center+semiconductor+compute+infrastructure&hl=en-IN&gl=IN&ceid=IN:en", "category": "Infrastructure"},
    {"name": "Internet Outage Watch", "url": "https://news.google.com/rss/search?q=internet+outage+network+disruption&hl=en-IN&gl=IN&ceid=IN:en", "category": "Cyber"},
]

# How often to refresh (seconds)
REFRESH_INTERVAL = 300  # 5 minutes
MAX_BRIEFS_STORED = 200  # keep more than 50 for analysis
MAX_CONCURRENT_FEEDS = 6
PER_FEED_TIMEOUT_SECONDS = 18
PER_FEED_RETRY_ATTEMPTS = 2
REQUEST_HEADERS = {
    "User-Agent": "Gods-Eye-OS/1.0 (+https://localhost)",
    "Accept": "application/rss+xml, application/xml;q=0.9, text/xml;q=0.9, */*;q=0.5",
}

class FeedAggregator:
    def __init__(self):
        self._running = False
        self.last_updated: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._feed_urls: Set[str] = {f["url"] for f in FEEDS}
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_FEEDS)
        self._source_health: Dict[str, Dict] = {}

    @staticmethod
    def _candidate_urls(feed_info: Dict) -> List[str]:
        urls = [feed_info["url"]]
        urls.extend(feed_info.get("fallback_urls", []))
        return [url for url in urls if url]

    async def _fetch_one_feed(self, session: aiohttp.ClientSession, feed_info: Dict) -> List[Dict]:
        """Fetch a single RSS feed and return list of briefs."""
        text = ""
        used_url = ""
        failed_attempts: List[str] = []
        async with self._semaphore:
            for candidate_url in self._candidate_urls(feed_info):
                for attempt in range(PER_FEED_RETRY_ATTEMPTS):
                    try:
                        async with session.get(
                            candidate_url,
                            timeout=aiohttp.ClientTimeout(total=PER_FEED_TIMEOUT_SECONDS, connect=6, sock_read=12),
                            allow_redirects=True,
                        ) as resp:
                            if resp.status != 200:
                                failed_attempts.append(f"{candidate_url} -> HTTP {resp.status}")
                                continue
                            text = await resp.text(errors="ignore")
                            used_url = candidate_url
                            break
                    except asyncio.TimeoutError:
                        failed_attempts.append(f"{candidate_url} -> timeout")
                    except aiohttp.ClientError as e:
                        failed_attempts.append(f"{candidate_url} -> network error: {e}")
                    except Exception as e:
                        failed_attempts.append(f"{candidate_url} -> unexpected error: {e}")

                    # Short backoff avoids hammering sources that are rate-limited.
                    if attempt + 1 < PER_FEED_RETRY_ATTEMPTS:
                        await asyncio.sleep(0.25 * (attempt + 1))

                if text:
                    break

        if not text:
            if failed_attempts:
                logger.warning(f"Feed {feed_info['name']} unavailable after retries: {'; '.join(failed_attempts[:3])}")
            self._source_health[feed_info["name"]] = {
                "id": f"feed-{feed_info['name'].lower().replace(' ', '-')}",
                "label": feed_info["name"],
                "mode": "rss",
                "status": "unavailable",
                "item_count": 0,
                "message": "; ".join(failed_attempts[:2]) if failed_attempts else "Feed unavailable",
                "last_updated": datetime.utcnow().isoformat(),
            }
            return []

        # Parse the RSS in a thread to avoid blocking
        try:
            feed = await asyncio.to_thread(feedparser.parse, text)
        except Exception as e:
            logger.warning(f"Error parsing {feed_info['name']} RSS from {used_url}: {e}")
            return []

        briefs = []
        for entry in feed.entries[:5]:  # take top 5 per feed
            title = entry.get("title", "")
            if not title:
                continue
            # Optional: use the feed's own category, or fallback to generic
            category = feed_info.get("category", self._classify_category(title))
            urgency = self._determine_urgency(title)
            briefs.append({
                "id": f"{int(time.time()*1000)}-{hash(title) & 0xFFFFFF}",
                "source": feed_info["name"],
                "category": category,
                "text": f"[{feed_info['name']}] {title}",
                "summary": entry.get("summary", entry.get("description", "No detailed summary available.")),
                "urgency": urgency,
                "time": "LIVE",
                "url": entry.get("link", ""),
                "published": entry.get("published", ""),
            })

        self._source_health[feed_info["name"]] = {
            "id": f"feed-{feed_info['name'].lower().replace(' ', '-')}",
            "label": feed_info["name"],
            "mode": "rss",
            "status": "live" if briefs else "limited",
            "item_count": len(briefs),
            "message": f"Fetched via {used_url}" if used_url else "Feed parsed with limited entries",
            "last_updated": datetime.utcnow().isoformat(),
        }
        return briefs

    async def _fetch_newsapi(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Optional NewsAPI fetch using the user's free dev key if configured."""
        if not settings.NEWS_API_KEY:
            return []
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "language": "en",
            "pageSize": 8,
            "category": "general",
        }
        headers = {
            "X-Api-Key": settings.NEWS_API_KEY,
        }
        try:
            async with session.get(url, params=params, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    logger.warning(f"NewsAPI returned {resp.status}")
                    return []
                payload = await resp.json()
        except Exception as e:
            logger.warning(f"NewsAPI fetch failed: {e}")
            self._source_health["NewsAPI"] = {
                "id": "feed-newsapi",
                "label": "NewsAPI",
                "mode": "api",
                "status": "unavailable",
                "item_count": 0,
                "message": str(e),
                "last_updated": datetime.utcnow().isoformat(),
            }
            return []

        briefs = []
        for article in payload.get("articles", [])[:8]:
            title = article.get("title")
            if not title:
                continue
            briefs.append(
                {
                    "id": f"newsapi-{int(time.time()*1000)}-{hash(title) & 0xFFFFFF}",
                    "source": article.get("source", {}).get("name", "NewsAPI"),
                    "category": self._classify_category(title),
                    "text": f"[NewsAPI] {title}",
                    "summary": article.get("description") or title,
                    "urgency": self._determine_urgency(title),
                    "time": "LIVE",
                    "url": article.get("url", ""),
                    "published": article.get("publishedAt", ""),
                }
            )

        self._source_health["NewsAPI"] = {
            "id": "feed-newsapi",
            "label": "NewsAPI",
            "mode": "api",
            "status": "live" if briefs else "limited",
            "item_count": len(briefs),
            "message": "Top-headlines fetch completed",
            "last_updated": datetime.utcnow().isoformat(),
        }
        return briefs

    async def fetch_feeds(self):
        """Main loop – fetches all feeds concurrently."""
        logger.info("Starting intelligence feed aggregation loop...")
        self._running = True
        timeout = aiohttp.ClientTimeout(total=15, connect=6, sock_read=10)
        connector = aiohttp.TCPConnector(limit=40, ttl_dns_cache=300)
        async with aiohttp.ClientSession(headers=REQUEST_HEADERS, timeout=timeout, connector=connector, trust_env=True) as session:
            while self._running:
                start_time = time.time()
                all_briefs = []
                # Fetch all feeds concurrently
                tasks = [self._fetch_one_feed(session, feed) for feed in FEEDS]
                tasks.append(self._fetch_newsapi(session))
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"Feed fetch failed: {res}")
                    else:
                        all_briefs.extend(res)

                deduped_briefs = []
                seen_briefs = set()
                for brief in all_briefs:
                    fingerprint = (brief.get("url") or brief.get("text") or "").strip().lower()
                    if not fingerprint or fingerprint in seen_briefs:
                        continue
                    seen_briefs.add(fingerprint)
                    deduped_briefs.append(brief)
                all_briefs = deduped_briefs

                # --- ⚡ OSINT INJECTION ⚡ ---
                try:
                    from app.services.osint_aggregator import osint_engine
                    osint_reports = [
                        {"tool": "X (Twitter)", "data": osint_engine.get_twitter_trends(), "cat": "Geopolitics"},
                        {"tool": "OpenSky", "data": osint_engine.get_opensky_data(), "cat": "Defense"},
                        {"tool": "FRED", "data": osint_engine.get_fred_economic_data(), "cat": "Economics"},
                        {"tool": "NASA", "data": osint_engine.get_nasa_firms(), "cat": "Climate"},
                        {"tool": "Yahoo Search", "data": osint_engine.get_yahoo_search_results(), "cat": "Geopolitics"},
                        {"tool": "DuckDuckGo", "data": osint_engine.get_duckduckgo_search_results(), "cat": "Geopolitics"},
                        {"tool": "SerpAPI", "data": osint_engine.get_serpapi_search_results(), "cat": "Geopolitics"},
                    ]
                    for report in osint_reports:
                        tool_name = report["tool"]
                        data = report["data"]
                        # Turn tool data into a readable ticker brief
                        text = ""
                        if tool_name == "X (Twitter)":
                            text = f"[INTEL] Trending: {', '.join(data.get('top_hashtags', [])[:3])} | Sentiment: {data.get('viral_sentiment')}"
                        elif tool_name == "OpenSky":
                            text = f"[DEFENSE] Airspace Status: {data.get('airspace_status')} | Active Flights: {data.get('commercial_flights_active')}"
                        elif tool_name == "FRED":
                            rates = data.get("indicators", {})
                            text = f"[ECON] Fed Rate: {rates.get('FED_FUNDS_RATE')}% | 10YR Treasury: {rates.get('US_10YR_TREASURY')}%"
                        elif tool_name == "NASA":
                            text = f"[CLIMATE] NASA FIRMS Alert: {data.get('fire_hotspots_detected')} hotspots detected globally."
                        elif tool_name == "Yahoo Search":
                            top = (data.get("results") or [{}])[0]
                            if top.get("title"):
                                text = f"[SEARCH] Yahoo pulse: {top.get('title')}"
                        elif tool_name == "DuckDuckGo":
                            top = (data.get("results") or [{}])[0]
                            if top.get("title"):
                                text = f"[SEARCH] DuckDuckGo pulse: {top.get('title')}"
                        elif tool_name == "SerpAPI":
                            top = (data.get("results") or [{}])[0]
                            if top.get("title"):
                                text = f"[SEARCH] SerpAPI pulse: {top.get('title')}"

                        if text:
                            all_briefs.append({
                                "id": f"osint-{tool_name.lower()}-{int(time.time())}",
                                "source": f"{tool_name} Intelligence",
                                "category": report["cat"],
                                "text": text,
                                "summary": f"Automated OSINT Intel signal from {tool_name}. Data indicates current status as: {text}. High-fidelity extraction active.",
                                "urgency": "High" if "Alert" in text or "Critical" in text else "Medium",
                                "time": "LIVE",
                                "url": ""
                            })
                except Exception as osint_err:
                    logger.error(f"OSINT Injection failed: {osint_err}")

                if all_briefs:
                    # Store briefs in the central store (persistent)
                    store.add_feed_briefs(all_briefs)

                    # Send each new brief through the LangGraph pipeline for deeper processing
                    # This will extract entities, sentiment, and even trigger actions.
                    for brief in all_briefs:
                        try:
                            # Process asynchronously; don't wait for completion to keep loop fast
                            asyncio.create_task(
                                process_unstructured_civic_text(
                                    text=brief["text"],
                                    source_id=brief["id"],
                                    source_type="rss"
                                )
                            )
                        except Exception as e:
                            logger.error(f"Error feeding brief to LangGraph: {e}")

                self.last_updated = datetime.now()
                logger.info(f"Aggregated {len(all_briefs)} new intelligence briefs from {len(FEEDS)} sources.")
                elapsed = time.time() - start_time
                sleep_time = max(0, REFRESH_INTERVAL - elapsed)
                await asyncio.sleep(sleep_time)

    def start(self):
        """Start the background task."""
        asyncio.create_task(self.fetch_feeds())

    def stop(self):
        """Graceful stop."""
        self._running = False

    def get_feeds(self) -> List[Dict]:
        """Return recent briefs from the store."""
        return store.get_recent_feed_briefs(limit=MAX_BRIEFS_STORED)

    def get_source_health(self) -> List[Dict]:
        """Expose per-source feed availability for UI health panels."""
        return list(self._source_health.values())

    # ------------------------------------------------------------------
    # Classification helpers (same as before)
    # ------------------------------------------------------------------
    @staticmethod
    def _classify_category(text: str) -> str:
        text = text.lower()
        if any(w in text for w in ["border", "troop", "defense", "military", "war", "weapon", "navy", "army"]):
            return "Defense"
        if any(w in text for w in ["conflict", "protest", "attack", "clash", "iran", "missile"]):
            return "Conflict"
        if any(w in text for w in ["market", "economy", "finance", "bank", "subsidy", "trade", "rupee", "inflation"]):
            return "Economics"
        if any(w in text for w in ["weather", "climate", "rain", "storm", "emission", "monsoon", "flood", "heat"]):
            return "Climate"
        if any(w in text for w in ["ship", "port", "aviation", "flight", "canal", "logistics", "route", "maritime"]):
            return "Mobility"
        if any(w in text for w in ["grid", "pipeline", "cable", "data center", "spaceport", "compute"]):
            return "Infrastructure"
        if any(w in text for w in ["cyber", "ransomware", "malware", "internet outage", "vulnerability"]):
            return "Cyber"
        if any(w in text for w in ["tech", "broadband", "cyber", "digital", "data", "ai", "isro"]):
            return "Tech"
        if any(w in text for w in ["election", "minister", "foreign", "treaty", "geopolitics", "modi", "biden", "china", "pakistan"]):
            return "Geopolitics"
        return "Society"

    @staticmethod
    def _determine_urgency(text: str) -> str:
        text = text.lower()
        if any(w in text for w in ["alert", "warning", "critical", "attack", "crisis", "spike", "danger", "urgent", "clash"]):
            return "High"
        if any(w in text for w in ["expected", "agreement", "update", "new", "plans", "meets"]):
            return "Medium"
        return "Low"

# Singleton instance
feed_engine = FeedAggregator()
