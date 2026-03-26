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
    
    # Pre-seed Neo4j Graph for Demo Map Nodes
    query = """
    MERGE (c1:Citizen {id: 'CIT-001', segment: 'Youth', sentiment: 22})
    MERGE (b1:Booth {id: 'R2', name: 'Ward 8'})
    MERGE (c1)-[:LIVES_IN]->(b1)
    MERGE (i1:Issue {name: 'Road completion awareness low', urgency: 5})
    MERGE (c1)-[r:COMPLAINED_ABOUT]->(i1)
    
    MERGE (c2:Citizen {id: 'CIT-002', segment: 'Daily Wage', sentiment: 45})
    MERGE (b2:Booth {id: 'R1', name: 'Constituency A'})
    MERGE (c2)-[:LIVES_IN]->(b2)
    MERGE (i2:Issue {name: 'Water Supply Deterioration', urgency: 9})
    MERGE (c2)-[:COMPLAINED_ABOUT]->(i2)
    """
    async with graph_driver.session() as session:
        await session.run(query)
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
