from neo4j import AsyncGraphDatabase
import logging
from app.core.config import settings

logger = logging.getLogger("neo4j")

_driver_cache = {}
_active_driver_uri = None


def _is_secure_uri(uri: str) -> bool:
    return uri.startswith("neo4j+s://") or uri.startswith("bolt+s://")


def _build_driver(uri: str):
    """Build a driver for one Neo4j endpoint."""
    is_secure = _is_secure_uri(uri)
    driver_kwargs = {
        "auth": settings.neo4j_auth_token,
        "max_connection_lifetime": 200,
        "max_connection_pool_size": 50,
        "connection_acquisition_timeout": 5.0,
        "keep_alive": True,
    }
    if not is_secure:
        driver_kwargs["encrypted"] = False
    return AsyncGraphDatabase.driver(uri, **driver_kwargs)


def _get_driver(uri: str):
    """Return a cached driver for a specific URI."""
    if uri not in _driver_cache:
        _driver_cache[uri] = _build_driver(uri)
    return _driver_cache[uri]


driver = None
for candidate_uri in settings.neo4j_connection_uris:
    try:
        driver = _get_driver(candidate_uri)
        logger.info(f"Neo4j Driver initialized: {candidate_uri} (Secure TLS: {_is_secure_uri(candidate_uri)})")
        break
    except Exception as e:
        logger.warning(f"Failed to initialize Neo4j Driver for {candidate_uri}: {e}")

if driver is None:
    logger.error("Failed to initialize Neo4j Driver for all configured URIs")

async def get_graph_driver():
    """Return the first Neo4j driver that can actually verify connectivity."""
    global _active_driver_uri

    candidate_uris = settings.neo4j_connection_uris
    if _active_driver_uri and _active_driver_uri in _driver_cache:
        cached_driver = _driver_cache[_active_driver_uri]
        try:
            await cached_driver.verify_connectivity()
            return cached_driver
        except Exception:
            logger.warning(f"Cached Neo4j driver no longer reachable: {_active_driver_uri}")

    last_error = None
    for candidate_uri in candidate_uris:
        try:
            candidate_driver = _get_driver(candidate_uri)
            await candidate_driver.verify_connectivity()
            _active_driver_uri = candidate_uri
            logger.info(f"Neo4j connectivity verified for {candidate_uri}")
            return candidate_driver
        except Exception as e:
            last_error = e
            logger.warning(f"Neo4j connectivity check failed for {candidate_uri}: {e}")

    raise RuntimeError(f"Neo4j driver not initialized: {last_error}")


async def verify_graph_connectivity() -> None:
    """Verify that at least one configured Neo4j endpoint is reachable."""
    active_driver = await get_graph_driver()
    await active_driver.verify_connectivity()


async def run_neo4j_query(query: str, **parameters):
    """Execute a parameterized query with database selection in one place."""
    active_driver = await get_graph_driver()
    return await active_driver.execute_query(
        query,
        database_=settings.NEO4J_DATABASE,
        **parameters,
    )

async def get_graph_session():
    """ Dependency for Neo4j Session handling """
    if not settings.neo4j_connection_uris:
        raise RuntimeError("No Neo4j URIs configured")

    active_driver = await get_graph_driver()
    async with active_driver.session(database=settings.NEO4J_DATABASE) as session:
        yield session

async def close_graph_driver():
    closed = set()
    for uri, cached_driver in list(_driver_cache.items()):
        if cached_driver in closed:
            continue
        await cached_driver.close()
        closed.add(cached_driver)
        logger.info(f"Neo4j Driver Closed for {uri}")
