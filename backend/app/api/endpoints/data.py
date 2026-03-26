"""
Gods-Eye OS — Data API Endpoints
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


# ═══════════════════════════════════════════════════════════════════════════════
# GOVERNMENT OFFICIALS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/officials", response_model=Dict[str, Any])
async def get_all_officials():
    """Get all government officials and political figures."""
    from app.data.officials_data import officials_engine

    officials = officials_engine.get_all_officials()
    return {"status": "success", "count": len(officials), "data": officials}


@router.get("/officials/heads-of-state", response_model=Dict[str, Any])
async def get_heads_of_state():
    """Get all heads of state and government."""
    from app.data.officials_data import officials_engine

    heads = officials_engine.get_heads_of_state()
    return {"status": "success", "count": len(heads), "data": heads}


@router.get("/officials/country/{country_id}", response_model=Dict[str, Any])
async def get_officials_by_country(country_id: str):
    """Get officials for a specific country."""
    from app.data.officials_data import officials_engine

    officials = officials_engine.get_officials_by_country(country_id)
    return {"status": "success", "count": len(officials), "data": officials}


@router.get("/officials/{official_id}", response_model=Dict[str, Any])
async def get_official(official_id: str):
    """Get a specific official by ID."""
    from app.data.officials_data import officials_engine

    official = officials_engine.get_official(official_id)
    if not official:
        return {"status": "error", "message": "Official not found"}
    return {"status": "success", "data": official}


@router.get("/officials/search/{query}", response_model=Dict[str, Any])
async def search_officials(query: str):
    """Search officials by name or title."""
    from app.data.officials_data import officials_engine

    results = officials_engine.search_officials(query)
    return {"status": "success", "count": len(results), "data": results}


@router.get("/officials/india-relations", response_model=Dict[str, Any])
async def get_india_relations():
    """Get summary of world leaders' stances on India."""
    from app.data.officials_data import officials_engine

    summary = officials_engine.get_india_relations_summary()
    return {"status": "success", "data": summary}


# ═══════════════════════════════════════════════════════════════════════════════
# POLITICAL PARTIES ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/parties", response_model=Dict[str, Any])
async def get_all_parties():
    """Get all political parties."""
    from app.data.officials_data import officials_engine

    parties = officials_engine.get_all_parties()
    return {"status": "success", "count": len(parties), "data": parties}


@router.get("/parties/country/{country_id}", response_model=Dict[str, Any])
async def get_parties_by_country(country_id: str):
    """Get parties for a specific country."""
    from app.data.officials_data import officials_engine

    parties = officials_engine.get_parties_by_country(country_id)
    return {"status": "success", "count": len(parties), "data": parties}


@router.get("/parties/governing", response_model=Dict[str, Any])
async def get_governing_parties():
    """Get currently governing parties worldwide."""
    from app.data.officials_data import officials_engine

    parties = officials_engine.get_governing_parties()
    return {"status": "success", "count": len(parties), "data": parties}


# ═══════════════════════════════════════════════════════════════════════════════
# ELECTIONS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/elections", response_model=Dict[str, Any])
async def get_all_elections():
    """Get all elections (past, ongoing, upcoming)."""
    from app.data.officials_data import officials_engine

    elections = officials_engine.get_all_elections()
    return {"status": "success", "count": len(elections), "data": elections}


@router.get("/elections/upcoming", response_model=Dict[str, Any])
async def get_upcoming_elections():
    """Get upcoming elections worldwide."""
    from app.data.officials_data import officials_engine

    elections = officials_engine.get_upcoming_elections()
    return {"status": "success", "count": len(elections), "data": elections}


@router.get("/elections/country/{country_id}", response_model=Dict[str, Any])
async def get_elections_by_country(country_id: str):
    """Get elections for a specific country."""
    from app.data.officials_data import officials_engine

    elections = officials_engine.get_elections_by_country(country_id)
    return {"status": "success", "count": len(elections), "data": elections}


@router.get("/elections/{election_id}", response_model=Dict[str, Any])
async def get_election(election_id: str):
    """Get a specific election by ID."""
    from app.data.officials_data import officials_engine

    election = officials_engine.get_election(election_id)
    if not election:
        return {"status": "error", "message": "Election not found"}
    return {"status": "success", "data": election}


# ═══════════════════════════════════════════════════════════════════════════════
# COUNTRY WORKSPACE ENDPOINTS
# Comprehensive country analysis and comparison
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/country-workspace/{country_id}", response_model=Dict[str, Any])
async def get_country_workspace(country_id: str):
    """
    Get comprehensive workspace data for a country.

    Aggregates:
    - Country overview (risk, influence, sentiment)
    - Government officials and political structure
    - Military capabilities
    - Recent signals and events
    - Electoral calendar
    - Relationships with other countries
    - Key rivals for comparison
    """
    from app.services.country_workspace import country_workspace_aggregator

    try:
        workspace = country_workspace_aggregator.get_country_workspace(country_id)
        return {"status": "success", "data": workspace}
    except Exception as e:
        logger.error(f"Country workspace generation failed: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country-compare/{country_a}/{country_b}", response_model=Dict[str, Any])
async def compare_countries(
    country_a: str,
    country_b: str,
    include_military: bool = Query(default=True),
    include_political: bool = Query(default=True)
):
    """
    Compare two countries across multiple dimensions.

    Includes:
    - Overview metrics (risk, influence, sentiment, population)
    - Military capabilities comparison
    - Political structure comparison
    - Relationship status
    """
    from app.services.country_workspace import country_workspace_aggregator

    try:
        comparison = country_workspace_aggregator.get_country_comparison(
            country_a=country_a,
            country_b=country_b,
            include_military=include_military,
            include_political=include_political,
        )
        return {"status": "success", "data": comparison}
    except Exception as e:
        logger.error(f"Country comparison failed: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
