"""
JanGraph OS — Data API Endpoints
Serves all civic intelligence data from the in-memory store.
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
from app.data.store import store
from app.schemas.global_api import CountryAnalysisResponse, GlobalOverviewResponse

router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
async def get_global_stats():
    """Returns top-level system statistics."""
    return {"status": "success", "data": store.get_stats()}


@router.get("/global/overview", response_model=GlobalOverviewResponse)
async def get_global_overview():
    """Returns world-scale ontology overview metrics."""
    from app.services.runtime_intelligence import runtime_engine
    return {"status": "success", "data": runtime_engine.get_global_overview()}


@router.get("/global/countries", response_model=Dict[str, Any])
async def get_global_countries(region: Optional[str] = None, min_risk: Optional[int] = None):
    """Returns country nodes used by the global ontology map."""
    from app.services.runtime_intelligence import runtime_engine
    countries = runtime_engine.get_enriched_countries()
    if region:
        countries = [country for country in countries if country["region"] == region]
    if min_risk is not None:
        countries = [country for country in countries if country["risk_index"] >= min_risk]
    return {"status": "success", "count": len(countries), "data": countries}


@router.get("/global/country/{country_id}", response_model=Dict[str, Any])
async def get_global_country(country_id: str):
    from app.services.runtime_intelligence import runtime_engine
    country = runtime_engine.get_country(country_id)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")
    return {"status": "success", "data": country}


@router.get("/global/signals", response_model=Dict[str, Any])
async def get_global_signals(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    country_id: Optional[str] = None,
    layer: Optional[str] = None,
    source_mode: Optional[str] = None,
):
    from app.services.runtime_intelligence import runtime_engine
    if source_mode == "runtime":
        signals = runtime_engine.get_runtime_signals()
    elif source_mode == "seeded":
        signals = runtime_engine.get_seeded_signals()
    else:
        signals = runtime_engine.get_dynamic_signals()
    if category:
        signals = [signal for signal in signals if signal["category"] == category]
    if severity:
        signals = [signal for signal in signals if signal["severity"] == severity]
    if country_id:
        signals = [signal for signal in signals if signal["country_id"] == country_id]
    if layer:
        signals = [signal for signal in signals if signal.get("layer") == layer]
    return {"status": "success", "count": len(signals), "data": signals}


@router.get("/global/assets", response_model=Dict[str, Any])
async def get_global_assets(
    country_id: Optional[str] = None,
    layer: Optional[str] = None,
    source_mode: Optional[str] = None,
):
    from app.services.runtime_intelligence import runtime_engine
    if source_mode == "runtime":
        assets = runtime_engine.get_runtime_assets(country_id=country_id, layer=layer)
    elif source_mode == "seeded":
        assets = runtime_engine.get_seeded_assets(country_id=country_id, layer=layer)
    else:
        assets = runtime_engine.get_structural_assets(country_id=country_id, layer=layer)
    return {"status": "success", "count": len(assets), "data": assets}


@router.get("/global/country-analysis/{country_id}", response_model=CountryAnalysisResponse)
async def get_global_country_analysis(country_id: str):
    from app.services.runtime_intelligence import runtime_engine
    analysis = runtime_engine.get_country_analysis(country_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")
    return {"status": "success", "data": analysis}


@router.get("/global/corridors", response_model=Dict[str, Any])
async def get_global_corridors(source_mode: Optional[str] = None):
    from app.services.runtime_intelligence import runtime_engine
    if source_mode == "runtime":
        corridors = runtime_engine.get_runtime_corridors()
    elif source_mode == "seeded":
        corridors = runtime_engine.get_seeded_corridors()
    else:
        corridors = runtime_engine.get_global_corridors()
    return {"status": "success", "count": len(corridors), "data": corridors}


@router.get("/global/map", response_model=Dict[str, Any])
async def get_global_map():
    from app.services.runtime_intelligence import runtime_engine
    points = runtime_engine.get_enriched_countries()
    return {"status": "success", "count": len(points), "data": points}


@router.get("/global/graph", response_model=Dict[str, Any])
async def get_global_graph():
    from app.services.runtime_intelligence import runtime_engine
    graph = runtime_engine.get_global_graph()
    return {
        "status": "success",
        "nodes": len(graph["nodes"]),
        "edges": len(graph["links"]),
        "data": graph,
    }


@router.get("/sentiment/timeline", response_model=Dict[str, Any])
async def get_sentiment_timeline(hours: int = 24):
    """Returns national sentiment trend data for charts."""
    return {"status": "success", "data": store.get_sentiment_timeline(hours=hours)}


@router.get("/constituencies", response_model=Dict[str, Any])
async def get_constituencies():
    """Returns all constituencies with aggregated stats."""
    cons = store.get_constituencies()
    return {
        "status": "success",
        "count": len(cons),
        "data": [
            {
                "id": c["id"],
                "name": c["name"],
                "state": c["state"],
                "lat": c["lat"],
                "lng": c["lng"],
                "total_population": c["total_population"],
                "avg_sentiment": c["avg_sentiment"],
                "wards": c["wards"],
            }
            for c in cons
        ],
    }


@router.get("/constituency/{con_id}/booths", response_model=Dict[str, Any])
async def get_constituency_booths(con_id: str):
    """Returns all booths in a constituency with sentiment + segmentation data."""
    booths = store.get_booths(constituency_id=con_id)
    if not booths:
        raise HTTPException(status_code=404, detail=f"Constituency {con_id} not found")
    return {
        "status": "success",
        "constituency_id": con_id,
        "count": len(booths),
        "data": booths,
    }


@router.get("/booth/{booth_id}", response_model=Dict[str, Any])
async def get_booth_detail(booth_id: str):
    """Returns complete booth intelligence including segments, issues, schemes."""
    booth = store.get_booth(booth_id)
    if not booth:
        raise HTTPException(status_code=404, detail=f"Booth {booth_id} not found")
    return {"status": "success", "data": booth}


@router.get("/booth/{booth_id}/segments", response_model=Dict[str, Any])
async def get_booth_segments(booth_id: str):
    """Returns voter segmentation breakdown for a booth."""
    segments = store.get_booth_segments(booth_id)
    if not segments:
        raise HTTPException(status_code=404, detail=f"Booth {booth_id} not found")
    total = sum(segments.values())
    return {
        "status": "success",
        "booth_id": booth_id,
        "total_voters": total,
        "segments": [
            {"name": seg, "count": count, "percentage": round(count / total * 100, 1)}
            for seg, count in sorted(segments.items(), key=lambda x: x[1], reverse=True)
        ],
    }


@router.get("/booth/{booth_id}/schemes", response_model=Dict[str, Any])
async def get_booth_schemes(booth_id: str):
    """Returns scheme beneficiary coverage for a booth."""
    coverage = store.get_booth_scheme_coverage(booth_id)
    booth = store.get_booth(booth_id)
    if not booth:
        raise HTTPException(status_code=404, detail=f"Booth {booth_id} not found")
    return {
        "status": "success",
        "booth_id": booth_id,
        "population": booth["population"],
        "schemes": [
            {"name": name, "enrolled": count, "coverage_pct": round(count / booth["population"] * 100, 1)}
            for name, count in sorted(coverage.items(), key=lambda x: x[1], reverse=True)
        ],
    }

@router.get("/booth/{booth_id}/schemes/{scheme_id}/gap", response_model=Dict[str, Any])
async def get_scheme_gap(booth_id: str, scheme_id: str):
    """Returns gap analysis for unenrolled eligible citizens."""
    unenrolled = store.get_unenrolled_eligible(booth_id, scheme_id)
    return {
        "status": "success",
        "booth_id": booth_id,
        "scheme_id": scheme_id,
        "unenrolled_eligible": unenrolled
    }

from app.services.feed_aggregator import feed_engine

@router.get("/feeds", response_model=Dict[str, Any])
async def get_live_feeds():
    """Returns aggregated RSS feeds classified via intelligence engine."""
    feeds = feed_engine.get_feeds()
    return {
        "status": "success",
        "count": len(feeds),
        "data": feeds
    }

@router.get("/booth/{booth_id}/sentiment", response_model=Dict[str, Any])
async def get_booth_sentiment(booth_id: str):
    """Returns sentiment analysis for a booth including issue breakdown."""
    booth = store.get_booth(booth_id)
    if not booth:
        raise HTTPException(status_code=404, detail=f"Booth {booth_id} not found")

    complaints = store.get_complaints(booth_id=booth_id, limit=200)
    sentiment_dist = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for c in complaints:
        sentiment_dist[c["sentiment"]] = sentiment_dist.get(c["sentiment"], 0) + 1

    return {
        "status": "success",
        "booth_id": booth_id,
        "avg_sentiment": booth["avg_sentiment"],
        "sentiment_label": booth["sentiment_label"],
        "distribution": sentiment_dist,
        "top_issues": booth["top_issues"],
        "recent_complaints": complaints[:10],
    }


@router.get("/citizens", response_model=Dict[str, Any])
async def get_citizens(
    booth_id: Optional[str] = None,
    segment: Optional[str] = None,
    limit: int = Query(default=50, le=500),
    offset: int = Query(default=0, ge=0),
):
    """Returns citizen data with filtering options."""
    citizens = store.get_citizens(booth_id=booth_id, segment=segment, limit=limit, offset=offset)
    total = store.get_citizens_count(booth_id=booth_id)
    return {
        "status": "success",
        "total": total,
        "returned": len(citizens),
        "offset": offset,
        "data": citizens,
    }


@router.get("/workers", response_model=Dict[str, Any])
async def get_workers(
    constituency_id: Optional[str] = None,
    booth_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """Returns field worker data with filtering."""
    workers = store.get_workers(constituency_id=constituency_id, booth_id=booth_id, status=status)
    return {
        "status": "success",
        "count": len(workers),
        "online": len([w for w in workers if w["status"] == "Online"]),
        "data": workers,
    }


@router.get("/projects", response_model=Dict[str, Any])
async def get_projects(
    ward_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """Returns infrastructure projects with Before/After data."""
    projects = store.get_projects(ward_id=ward_id, status=status)
    return {
        "status": "success",
        "count": len(projects),
        "data": projects,
    }


@router.get("/complaints", response_model=Dict[str, Any])
async def get_complaints(
    booth_id: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """Returns citizen complaints sorted by recency."""
    complaints = store.get_complaints(booth_id=booth_id, sentiment=sentiment, limit=limit)
    return {
        "status": "success",
        "count": len(complaints),
        "data": complaints,
    }


@router.get("/map", response_model=Dict[str, Any])
async def get_map_data():
    """Returns all booth-level geospatial data for map rendering."""
    points = store.get_map_data()
    return {
        "status": "success",
        "count": len(points),
        "data": points,
    }


@router.get("/schemes", response_model=Dict[str, Any])
async def get_schemes():
    """Returns all government schemes."""
    return {
        "status": "success",
        "data": store.get_schemes(),
    }


@router.get("/segments/{constituency_id}", response_model=Dict[str, Any])
async def get_constituency_segments(constituency_id: str):
    """Returns aggregated segmentation across all booths in a constituency."""
    segments = store.get_constituency_segments(constituency_id)
    if not segments:
        raise HTTPException(status_code=404, detail=f"Constituency {constituency_id} not found")
    total = sum(segments.values())
    return {
        "status": "success",
        "constituency_id": constituency_id,
        "total_voters": total,
        "segments": [
            {"name": seg, "count": count, "percentage": round(count / total * 100, 1)}
            for seg, count in sorted(segments.items(), key=lambda x: x[1], reverse=True)
        ],
    }

@router.get("/graph/ontology", response_model=Dict[str, Any])
async def get_ontology_graph(booths: int = Query(default=5, le=20), citizens: int = Query(default=100, le=500)):
    """Returns force-directed graph data of the civic ontology."""
    from app.services.runtime_intelligence import runtime_engine
    graph_data = runtime_engine.get_global_graph()
    return {
        "status": "success",
        "nodes": len(graph_data["nodes"]),
        "edges": len(graph_data["links"]),
        "data": graph_data
    }


@router.get("/source-health", response_model=Dict[str, Any])
async def get_source_health():
    from app.services.runtime_intelligence import runtime_engine
    health = runtime_engine.get_source_health()
    return {"status": "success", "count": len(health), "data": health}


@router.get("/markets", response_model=Dict[str, Any])
async def get_market_snapshot():
    from app.services.runtime_intelligence import runtime_engine
    snapshot = runtime_engine.get_market_snapshot()
    return {"status": "success", "count": len(snapshot), "data": snapshot}

# ==========================================================
# MANDATED HACKATHON ALIAS ENDPOINTS
# ==========================================================

@router.get("/sentiment/heatmap", response_model=Dict[str, Any])
async def get_heatmap():
    """GeoJSON with constituency-level sentiment (from Telegram, Twitter, Reddit aggregation)."""
    points = store.get_map_data()
    return {"status": "success", "data": points}

@router.get("/booths")
async def get_legacy_booths():
    return {"status": "success", "data": store.get_booths()}

@router.get("/geopolitical/events", response_model=Dict[str, Any])
async def get_geo_events():
    from app.services.osint_aggregator import osint_engine
    data = osint_engine.get_gdelt_data()
    return {"status": "success", "data": data.get("recent_events", [])}

@router.get("/fires", response_model=Dict[str, Any])
async def get_nasa_fires():
    from app.services.osint_aggregator import osint_engine
    data = osint_engine.get_nasa_firms()
    return {"status": "success", "data": data.get("hotspots", [])}

@router.get("/earthquakes", response_model=Dict[str, Any])
async def get_usgs_quakes():
    from app.services.osint_aggregator import osint_engine
    data = osint_engine.get_usgs_earthquakes()
    return {"status": "success", "data": data.get("recent_significant", [])}

@router.get("/news", response_model=Dict[str, Any])
async def get_news_feeds():
    from app.services.feed_aggregator import feed_engine
    feeds = feed_engine.get_feeds()
    return {"status": "success", "data": feeds}

@router.get("/alerts", response_model=Dict[str, Any])
async def get_hyperlocal_alerts():
    from app.services.runtime_intelligence import runtime_engine
    return {"status": "success", "data": runtime_engine.get_alerts()}
