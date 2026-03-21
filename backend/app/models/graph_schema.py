from app.core.graph import get_graph_session
import logging

logger = logging.getLogger("neo4j_schema")

# Graph Schema Design Documented in Code:
# (Citizen:Person) -[:LIVES_IN]-> (Booth:Region)
# (Citizen:Person) -[:QUALIFIES_FOR]-> (Scheme)
# (Citizen) -[:COMPLAINED_ABOUT]-> (Issue)
# (Issue) -[:AFFECTS_REGION]-> (Booth)
# (Worker) -[:ASSIGNED_TO]-> (Booth)
# (Booth) -[:PART_OF]-> (Ward) -> (Constituency)

async def initialize_neo4j_constraints(driver):
    """
    Enforces uniqueness and creates indexes for Neo4j.
    This replaces traditional tabular migrations with graph structure mapping.
    """
    queries = [
        # Uniqueness
        "CREATE CONSTRAINT citizen_id IF NOT EXISTS FOR (c:Citizen) REQUIRE c.id IS UNIQUE",
        "CREATE CONSTRAINT booth_id IF NOT EXISTS FOR (b:Booth) REQUIRE b.id IS UNIQUE",
        "CREATE CONSTRAINT scheme_id IF NOT EXISTS FOR (s:Scheme) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT issue_name IF NOT EXISTS FOR (i:Issue) REQUIRE i.name IS UNIQUE",
        
        # Performance Indexes
        "CREATE INDEX citizen_segment IF NOT EXISTS FOR (c:Citizen) ON (c.segment)",
        "CREATE INDEX citizen_sentiment IF NOT EXISTS FOR (c:Citizen) ON (c.sentiment)",
        "CREATE INDEX issue_urgency IF NOT EXISTS FOR (i:Issue) ON (i.urgency)",
    ]
    
    async with driver.session() as session:
        for query in queries:
            try:
                await session.run(query)
            except Exception as e:
                logger.error(f"Error enforcing constraint: {e}")
                
    logger.info("Neo4j Graph Schema Initialized.")

class GraphQueries:
    """ Singleton containing enterprise-critical pre-validated cypher queries """

    @staticmethod
    async def get_booth_intelligence(session, booth_id: str):
        query = """
        MATCH (b:Booth {id: $booth_id})<-[:LIVES_IN]-(c:Citizen)
        OPTIONAL MATCH (c)-[:COMPLAINED_ABOUT]->(i:Issue)
        OPTIONAL MATCH (w:Worker)-[:ASSIGNED_TO]->(b)
        RETURN 
            b.name AS name,
            count(c) AS population,
            avg(c.sentiment) AS average_sentiment,
            collect(DISTINCT i.name) AS top_issues,
            count(DISTINCT w) AS active_workers
        """
        result = await session.run(query, booth_id=booth_id)
        return await result.single()

    @staticmethod
    async def register_citizen_complaint(session, citizen_id: str, issue_name: str, urgency: int):
        # Merge pattern prevents creating duplicate nodes
        query = """
        MATCH (c:Citizen {id: $citizen_id})
        MERGE (i:Issue {name: $issue_name})
        SET i.urgency = CASE WHEN i.urgency < $urgency THEN $urgency ELSE i.urgency END
        MERGE (c)-[r:COMPLAINED_ABOUT]->(i)
        SET r.timestamp = datetime()
        RETURN c, i
        """
        await session.run(query, citizen_id=citizen_id, issue_name=issue_name, urgency=urgency)
