import asyncio
import logging
import uuid
import sys
import os
from datetime import datetime

# Adjust path so we can import app modules directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.domain import User, Region, RoleType
from app.core.graph import get_graph_driver, close_graph_driver
from app.models.graph_schema import initialize_neo4j_constraints
from app.core.config import settings
from passlib.hash import bcrypt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataSeeder")

async def init_rdbms():
    logger.info("Initializing Postgres/PostGIS tables...")
    async with engine.begin() as conn:
        # Warning: For prototype demo, we drop-all to start clean. Do not use in prod.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with AsyncSessionLocal() as session:
        # Base Admin User
        admin = User(
            email="admin@Gods-Eye.gov",
            full_name="National Admin",
            hashed_password=bcrypt.hash("admin123"),
            role=RoleType.SUPER_ADMIN
        )
        # Base Strategy User
        strategist = User(
            email="strategist@Gods-Eye.gov",
            full_name="Alpha Strategist",
            hashed_password=bcrypt.hash("strat123"),
            role=RoleType.STRATEGIST
        )
        session.add_all([admin, strategist])
        
        # Base Hierarchy (Map to our mock map coordinates)
        state_id = uuid.uuid4()
        delhi_state = Region(
            id=state_id,
            name="Delhi NCT",
            type="STATE",
            center_point="SRID=4326;POINT(77.2090 28.6139)"
        )
        session.add(delhi_state)
        
        # Flush to get IDs
        await session.flush()
        
        dist_id = uuid.uuid4()
        district = Region(
            id=dist_id,
            name="District 4",
            type="DISTRICT",
            parent_id=state_id,
            center_point="SRID=4326;POINT(77.1025 28.7041)",
            demographics={"youth": 250000, "farmers": 1000},
            sentiment_score=68
        )
        session.add(district)
        
        await session.commit()
    logger.info("RDBMS initialization complete.")

async def init_graph():
    logger.info("Initializing Neo4j Graph DB...")
    graph_driver = await get_graph_driver()
    await initialize_neo4j_constraints(graph_driver)

    # Pre-seed Neo4j graph with parameterized writes.
    create_records_query = """
    MERGE (c1:Citizen {id: $citizen1_id})
    SET c1.segment = $citizen1_segment, c1.sentiment = $citizen1_sentiment
    MERGE (b1:Booth {id: $booth1_id})
    SET b1.name = $booth1_name
    MERGE (c1)-[:LIVES_IN]->(b1)
    MERGE (i1:Issue {name: $issue1_name})
    SET i1.urgency = $issue1_urgency
    MERGE (c1)-[:COMPLAINED_ABOUT]->(i1)

    MERGE (c2:Citizen {id: $citizen2_id})
    SET c2.segment = $citizen2_segment, c2.sentiment = $citizen2_sentiment
    MERGE (b2:Booth {id: $booth2_id})
    SET b2.name = $booth2_name
    MERGE (c2)-[:LIVES_IN]->(b2)
    MERGE (i2:Issue {name: $issue2_name})
    SET i2.urgency = $issue2_urgency
    MERGE (c2)-[:COMPLAINED_ABOUT]->(i2)
    """
    create_summary = (
        await graph_driver.execute_query(
            create_records_query,
            citizen1_id="CIT-001",
            citizen1_segment="Youth",
            citizen1_sentiment=22,
            booth1_id="R2",
            booth1_name="Ward 8",
            issue1_name="Road completion awareness low",
            issue1_urgency=5,
            citizen2_id="CIT-002",
            citizen2_segment="Daily Wage",
            citizen2_sentiment=45,
            booth2_id="R1",
            booth2_name="Constituency A",
            issue2_name="Water Supply Deterioration",
            issue2_urgency=9,
            database_=settings.NEO4J_DATABASE,
        )
    ).summary

    logger.info(
        "Neo4j seed write complete: nodes created=%s, relationships created=%s, latency_ms=%s",
        create_summary.counters.nodes_created,
        create_summary.counters.relationships_created,
        create_summary.result_available_after,
    )

    records, summary, _ = await graph_driver.execute_query(
        """
        MATCH (p:Citizen)-[:LIVES_IN]->(:Booth)
        RETURN p.id AS citizen_id
        ORDER BY citizen_id
        """,
        database_=settings.NEO4J_DATABASE,
    )
    logger.info(
        "Neo4j verification query returned %s records in %s ms",
        len(records),
        summary.result_available_after,
    )
    logger.info("Neo4j Data Seeded successfully.")

async def main():
    try:
        await init_graph()
        await init_rdbms()
        logger.info("Data Seeder executed without errors.")
    except Exception as e:
        logger.error(f"Seeder failed: {e}")
    finally:
        await close_graph_driver()

if __name__ == "__main__":
    asyncio.run(main())
