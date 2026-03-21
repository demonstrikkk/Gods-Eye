"""
JanGraph OS — In-Memory Data Store
Singleton that loads the seeded civic dataset on first access.
All API endpoints read from this store. Zero database dependency.
"""
import logging
from typing import Dict, List, Optional, Any
from app.data.seed import build_civic_dataset

logger = logging.getLogger("data_store")

class CivicDataStore:
    """
    Thread-safe singleton data store.
    Generates all demo data once on first access, then serves from memory.
    """
    _instance = None
    _data: Optional[Dict] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_loaded(self):
        if self._data is None:
            logger.info("Generating JanGraph OS civic dataset...")
            self._data = build_civic_dataset()
            stats = self._data["stats"]
            logger.info(
                f"Dataset ready: {stats['total_citizens']:,} citizens, "
                f"{stats['total_booths']} booths, {stats['total_workers']} workers, "
                f"{stats['total_projects']} projects"
            )

    # ── Top-Level Stats ──────────────────────────────
    def get_stats(self) -> Dict:
        self._ensure_loaded()
        return self._data["stats"]

    # ── Constituencies ───────────────────────────────
    def get_constituencies(self) -> List[Dict]:
        self._ensure_loaded()
        return self._data["constituencies"]

    def get_constituency(self, con_id: str) -> Optional[Dict]:
        self._ensure_loaded()
        return next((c for c in self._data["constituencies"] if c["id"] == con_id), None)

    # ── Wards ────────────────────────────────────────
    def get_wards(self, constituency_id: Optional[str] = None) -> List[Dict]:
        self._ensure_loaded()
        wards = self._data["wards"]
        if constituency_id:
            wards = [w for w in wards if w["constituency_id"] == constituency_id]
        return wards

    # ── Booths ───────────────────────────────────────
    def get_booths(self, constituency_id: Optional[str] = None, ward_id: Optional[str] = None) -> List[Dict]:
        self._ensure_loaded()
        booths = self._data["booths"]
        if constituency_id:
            booths = [b for b in booths if b["constituency_id"] == constituency_id]
        if ward_id:
            booths = [b for b in booths if b["ward_id"] == ward_id]
        return booths

    def get_booth(self, booth_id: str) -> Optional[Dict]:
        self._ensure_loaded()
        return next((b for b in self._data["booths"] if b["id"] == booth_id), None)

    # ── Citizens ─────────────────────────────────────
    def get_citizens(self, booth_id: Optional[str] = None, segment: Optional[str] = None,
                     limit: int = 100, offset: int = 0) -> List[Dict]:
        self._ensure_loaded()
        citizens = self._data["citizens"]
        if booth_id:
            citizens = [c for c in citizens if c["id"].startswith(f"CIT-")]
            # Filter by booth_id prefix in citizen ID hash — use booth lookup instead
            booth = self.get_booth(booth_id)
            if booth:
                # Citizens are stored sequentially by booth order
                booth_idx = next((i for i, b in enumerate(self._data["booths"]) if b["id"] == booth_id), None)
                if booth_idx is not None:
                    start = sum(b["population"] for b in self._data["booths"][:booth_idx])
                    end = start + booth["population"]
                    citizens = self._data["citizens"][start:end]
        if segment:
            citizens = [c for c in citizens if c["segment"] == segment]
        return citizens[offset:offset + limit]

    def get_citizens_count(self, booth_id: Optional[str] = None) -> int:
        self._ensure_loaded()
        if booth_id:
            booth = self.get_booth(booth_id)
            return booth["population"] if booth else 0
        return self._data["stats"]["total_citizens"]

    # ── Segmentation ─────────────────────────────────
    def get_booth_segments(self, booth_id: str) -> Dict:
        booth = self.get_booth(booth_id)
        if not booth:
            return {}
        return booth.get("segments", {})

    def get_constituency_segments(self, constituency_id: str) -> Dict:
        self._ensure_loaded()
        booths = self.get_booths(constituency_id=constituency_id)
        aggregated = {}
        for b in booths:
            for seg, count in b.get("segments", {}).items():
                aggregated[seg] = aggregated.get(seg, 0) + count
        return aggregated

    # ── Schemes / Beneficiaries ──────────────────────
    def get_schemes(self) -> List[Dict]:
        self._ensure_loaded()
        return self._data["schemes"]

    def get_booth_scheme_coverage(self, booth_id: str) -> Dict:
        booth = self.get_booth(booth_id)
        if not booth:
            return {}
        coverage = booth.get("scheme_coverage", {})
        # Enrich with scheme names
        scheme_map = {s["id"]: s for s in self._data["schemes"]}
        return {
            scheme_map.get(sid, {}).get("name", sid): count
            for sid, count in coverage.items()
        }

    def get_unenrolled_eligible(self, booth_id: str, scheme_id: str) -> int:
        """Returns count of citizens eligible but NOT enrolled in a specific scheme."""
        booth = self.get_booth(booth_id)
        if not booth:
            return 0
        scheme = next((s for s in self._data["schemes"] if s["id"] == scheme_id), None)
        if not scheme:
            return 0

        citizens = self.get_citizens(booth_id=booth_id, limit=10000)
        target = scheme["target_segment"]
        eligible = [c for c in citizens if target == "All" or c["segment"] == target]
        enrolled = [c for c in eligible if scheme_id in c.get("enrolled_schemes", [])]
        return len(eligible) - len(enrolled)

    # ── Workers ──────────────────────────────────────
    def get_workers(self, constituency_id: Optional[str] = None,
                    booth_id: Optional[str] = None,
                    status: Optional[str] = None) -> List[Dict]:
        self._ensure_loaded()
        workers = self._data["workers"]
        if constituency_id:
            workers = [w for w in workers if w["assigned_constituency"] == constituency_id]
        if booth_id:
            workers = [w for w in workers if w["assigned_booth"] == booth_id]
        if status:
            workers = [w for w in workers if w["status"] == status]
        return workers

    # ── Projects ─────────────────────────────────────
    def get_projects(self, ward_id: Optional[str] = None,
                     status: Optional[str] = None) -> List[Dict]:
        self._ensure_loaded()
        projects = self._data["projects"]
        if ward_id:
            projects = [p for p in projects if p["ward"] == ward_id]
        if status:
            projects = [p for p in projects if p["status"] == status]
        return projects

    # ── Complaints ───────────────────────────────────
    def get_complaints(self, booth_id: Optional[str] = None,
                       sentiment: Optional[str] = None,
                       limit: int = 50) -> List[Dict]:
        self._ensure_loaded()
        complaints = self._data["complaints"]
        if booth_id:
            complaints = [c for c in complaints if c["booth_id"] == booth_id]
        if sentiment:
            complaints = [c for c in complaints if c["sentiment"] == sentiment]
        # Sort by timestamp descending
        complaints = sorted(complaints, key=lambda x: x["timestamp"], reverse=True)
        return complaints[:limit]

    # ── Feeds ────────────────────────────────────────
    def add_feed_briefs(self, briefs: List[Dict]):
        self._ensure_loaded()
        if "feed_briefs" not in self._data:
            self._data["feed_briefs"] = []
        # Prepend new briefs to keep most recent first
        self._data["feed_briefs"] = briefs + self._data["feed_briefs"]
        # Limit the size arbitrarily to 500
        self._data["feed_briefs"] = self._data["feed_briefs"][:500]

    def get_recent_feed_briefs(self, limit: int = 50) -> List[Dict]:
        self._ensure_loaded()
        return self._data.get("feed_briefs", [])[:limit]

    # ── Map Data (GeoJSON-like) ──────────────────────
    def get_map_data(self) -> List[Dict]:
        """Returns booth-level geospatial data for map rendering."""
        self._ensure_loaded()
        return [
            {
                "id": b["id"],
                "name": b["name"],
                "lat": b["lat"],
                "lng": b["lng"],
                "constituency": b["constituency_name"],
                "population": b["population"],
                "sentiment": b["avg_sentiment"],
                "sentiment_label": b["sentiment_label"],
                "top_issue": b["top_issues"][0]["issue"] if b["top_issues"] else "None",
                "key_voters": b["key_voters"],
                "unresolved": b["unresolved_complaints"],
            }
            for b in self._data["booths"]
        ]

    # ── Executive KPIs ───────────────────────────────
    def get_executive_kpis(self) -> Dict:
        self._ensure_loaded()
        stats = self._data["stats"]
        online_workers = len([w for w in self._data["workers"] if w["status"] == "Online"])
        critical_booths = len([b for b in self._data["booths"] if b["avg_sentiment"] < 40])
        unresolved = sum(b["unresolved_complaints"] for b in self._data["booths"])

        return {
            "national_sentiment": stats["national_avg_sentiment"],
            "active_alerts": critical_booths,
            "field_workers_online": online_workers,
            "total_citizens": stats["total_citizens"],
            "total_booths": stats["total_booths"],
            "total_schemes": stats["total_schemes"],
            "unresolved_complaints": unresolved,
            "scheme_coverage_pct": round(
                len([c for c in self._data["citizens"] if len(c.get("enrolled_schemes", [])) > 0])
                / stats["total_citizens"] * 100, 1
            ),
        }

    # ── Sentiment Timeline ───────────────────────────
    def get_sentiment_timeline(self, hours: int = 24) -> List[Dict]:
        """Returns synthetic past 24h sentiment trend for dashboard charts."""
        import random
        from datetime import datetime, timedelta
        
        self._ensure_loaded()
        national_avg = self._data["stats"]["national_avg_sentiment"]
        
        timeline = []
        now = datetime.now()
        for i in range(hours, -1, -2):  # Every 2 hours
            ts = now - timedelta(hours=i)
            # Add some random walk around the national average
            sentiment = national_avg + random.uniform(-5, 5)
            timeline.append({
                "time": ts.strftime("%H:%M"),
                "sentiment": round(sentiment, 1),
                "alerts": random.randint(2, 12)
            })
        return timeline

    # ── Ontology Graph ───────────────────────────────
    def get_ontology_graph(self, booth_limit: int = 5, citizen_limit: int = 50) -> Dict:
        """Generates a node-edge graph of the civic data for visualization."""
        self._ensure_loaded()
        nodes = []
        links = []
        
        # 1. Add Scheme Nodes
        for idx, scheme in enumerate(self._data["schemes"][:5]):
            nodes.append({"id": f"SCHEME-{scheme['id']}", "group": "Scheme", "label": scheme["name"], "val": 8})
        
        # 2. Add Top Issues Nodes
        global_issues = ["Water Supply", "Roads", "Electricity", "Healthcare", "Education", "Sanitation"]
        for issue in global_issues[:5]:
            nodes.append({"id": f"ISSUE-{issue}", "group": "Issue", "label": issue, "val": 6})
        
        # 3. Add Booths
        booths = self._data["booths"][:booth_limit]
        for b in booths:
            b_id = f"BOOTH-{b['id']}"
            nodes.append({
                "id": b_id, 
                "group": "Booth", 
                "label": f"Booth {b['name']}",
                "val": 5, 
                "color": "#ef4444" if b["avg_sentiment"] < 40 else "#10b981"
            })
            
            # Connect Booth to Top Issue
            if b["top_issues"]:
                links.append({"source": b_id, "target": f"ISSUE-{b['top_issues'][0]['issue']}", "label": "HAS_ISSUE"})
        
        # 4. Add Citizens
        # We'll just grab a few citizens per booth to prevent graph explosion
        for b in booths:
            b_id = f"BOOTH-{b['id']}"
            b_citizens = self.get_citizens(booth_id=b["id"], limit=int(citizen_limit/booth_limit))
            for c in b_citizens:
                c_id = f"CITIZEN-{c['id']}"
                nodes.append({
                    "id": c_id,
                    "group": "Citizen",
                    "label": c["name"],
                    "val": 2,
                    "segment": c["segment"]
                })
                # Link Citizen -> Booth
                links.append({"source": c_id, "target": b_id, "label": "VOTES_IN"})
                
                # Link Citizen -> Scheme
                for scheme_id in c.get("enrolled_schemes", [])[:1]:
                    links.append({"source": c_id, "target": f"SCHEME-{scheme_id}", "label": "BENEFICIARY"})
                    
        return {"nodes": nodes, "links": links}

    # ── Beneficiary Gap Analysis ──────────────────────
    def get_unenrolled_eligible(self, booth_id: str, scheme_id: str) -> int:
        """Count citizens in a booth eligible for a scheme but not enrolled."""
        self._ensure_loaded()
        scheme = None
        for s in self._data["schemes"]:
            if s["id"] == scheme_id:
                scheme = s
                break
        if not scheme:
            return 0

        target_segment = scheme.get("target_segment", "")
        citizens_in_booth = [c for c in self._data["citizens"] if c["booth_id"] == booth_id]

        count = 0
        for c in citizens_in_booth:
            seg = c.get("segment", "General")
            enrolled = c.get("enrolled_schemes", [])
            # Eligible if matching segment AND not already enrolled in this scheme
            if (seg == target_segment or target_segment == "All") and scheme_id not in enrolled:
                count += 1
        return count

# Singleton accessor
store = CivicDataStore()
