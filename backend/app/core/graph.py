from neo4j import AsyncGraphDatabase
import logging
from app.core.config import settings

logger = logging.getLogger("neo4j")

# Neo4j Driver Connection Pooling Strategy
# This driver instance will handle multiple graph queries concurrently from API endpoints.
# Supports both local Neo4j (bolt://) and Neo4j Aura (neo4j+s://)
try:
    driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        max_connection_lifetime=3600,
        max_connection_pool_size=50,  # Handles sudden influx of dashboard queries
        connection_acquisition_timeout=2.0,
        encrypted=settings.NEO4J_URI.startswith("neo4j+s"),  # Auto-enable encryption for Aura
    )
    logger.info(f"Neo4j Driver initialized: {settings.NEO4J_URI}")
except Exception as e:
    logger.error(f"Failed to initialize Neo4j Driver: {e}")
    driver = None

async def get_graph_session():
    """ Dependency for Neo4j Session handling """
    if not driver:
        raise RuntimeError("Neo4j driver not initialized")
    async with driver.session(database=settings.NEO4J_DATABASE) as session:
        yield session

async def close_graph_driver():
    if driver:
        await driver.close()
        logger.info("Neo4j Driver Closed")
