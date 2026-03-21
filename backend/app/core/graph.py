from neo4j import AsyncGraphDatabase
import logging
from app.core.config import settings

logger = logging.getLogger("neo4j")

# Neo4j Driver Connection Pooling Strategy
# This driver instance will handle multiple graph queries concurrently from API endpoints.
driver = AsyncGraphDatabase.driver(
    settings.NEO4J_URI,
    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
    max_connection_lifetime=3600,
    max_connection_pool_size=50, # Handles sudden influx of dashboard queries
    connection_acquisition_timeout=2.0
)

async def get_graph_session():
    """ Dependency for Neo4j Session handling """
    async with driver.session() as session:
        yield session

async def close_graph_driver():
    await driver.close()
    logger.info("Neo4j Driver Closed")
