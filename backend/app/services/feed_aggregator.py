
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
    {"name": "NDTV", "url": "https://feeds.ndtv.com/top-stories", "category": "Geopolitics"},
    {"name": "The Hindu", "url": "https://www.thehindu.com/feeder/default.rss", "category": "Geopolitics"},
    {"name": "Reuters World", "url": "https://feeds.reuters.com/reuters/worldNews", "category": "Geopolitics"},
    {"name": "Defense News", "url": "https://www.defensenews.com/arc/outboundfeeds/rss/", "category": "Defense"},
    {"name": "Economic Times", "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms", "category": "Economics"},
    {"name": "PIB India", "url": "https://pib.gov.in/PressReleaseRss.aspx", "category": "Governance"},
    {"name": "India Meteorological Department", "url": "http://www.imd.gov.in/press_release/rss.xml", "category": "Climate"},
]

# How often to refresh (seconds)
REFRESH_INTERVAL = 300  # 5 minutes
MAX_BRIEFS_STORED = 200  # keep more than 50 for analysis

class FeedAggregator:
    def __init__(self):
        self._running = False
        self.last_updated: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._feed_urls: Set[str] = {f["url"] for f in FEEDS}

    async def _fetch_one_feed(self, session: aiohttp.ClientSession, feed_info: Dict) -> List[Dict]:
        """Fetch a single RSS feed and return list of briefs."""
        url = feed_info["url"]
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    logger.warning(f"Feed {feed_info['name']} returned {resp.status}")
                    return []
                text = await resp.text()
        except asyncio.TimeoutError:
            logger.warning(f"Timeout fetching {feed_info['name']}")
            return []
        except Exception as e:
            logger.exception(f"Error fetching {feed_info['name']}: {e}")
            return []

        # Parse the RSS in a thread to avoid blocking
        try:
            feed = await asyncio.to_thread(feedparser.parse, text)
        except Exception as e:
            logger.exception(f"Error parsing {feed_info['name']} RSS: {e}")
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
        return briefs

    async def fetch_feeds(self):
        """Main loop – fetches all feeds concurrently."""
        logger.info("Starting intelligence feed aggregation loop...")
        self._running = True
        async with aiohttp.ClientSession() as session:
            while self._running:
                start_time = time.time()
                all_briefs = []
                # Fetch all feeds concurrently
                tasks = [self._fetch_one_feed(session, feed) for feed in FEEDS]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"Feed fetch failed: {res}")
                    else:
                        all_briefs.extend(res)

                # --- ⚡ OSINT INJECTION ⚡ ---
                try:
                    from app.services.osint_aggregator import osint_engine
                    osint_reports = [
                        {"tool": "X (Twitter)", "data": osint_engine.get_twitter_trends(), "cat": "Geopolitics"},
                        {"tool": "OpenSky", "data": osint_engine.get_opensky_data(), "cat": "Defense"},
                        {"tool": "FRED", "data": osint_engine.get_fred_economic_data(), "cat": "Economics"},
                        {"tool": "NASA", "data": osint_engine.get_nasa_firms(), "cat": "Climate"},
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

    # ------------------------------------------------------------------
    # Classification helpers (same as before)
    # ------------------------------------------------------------------
    @staticmethod
    def _classify_category(text: str) -> str:
        text = text.lower()
        if any(w in text for w in ["border", "troop", "defense", "military", "war", "weapon", "navy", "army"]):
            return "Defense"
        if any(w in text for w in ["market", "economy", "finance", "bank", "subsidy", "trade", "rupee", "inflation"]):
            return "Economics"
        if any(w in text for w in ["weather", "climate", "rain", "storm", "emission", "monsoon", "flood", "heat"]):
            return "Climate"
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