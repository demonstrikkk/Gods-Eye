import logging
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
try:
    from langchain_neo4j import Neo4jGraph
except Exception:
    from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import PromptTemplate
from app.services.llm_provider import get_enterprise_llm
from app.core.config import settings

logger = logging.getLogger("nlp_query_engine")

class CivicIntelligenceQA:
    """
    Implements the Natural Language to Graph Query capability.
    "Show booths in this constituency where youth population is high, 
    sentiment is negative, and PM Kisan coverage is low."
    """
    def __init__(self):
        # Establish Langchain Neo4j Integration
        # Caution: This requires the db to be reachable. Handled gracefully.
        self.graph = None
        last_error = None
        for uri in settings.neo4j_connection_uris:
            try:
                self.graph = Neo4jGraph(
                    url=uri,
                    username=settings.NEO4J_USER,
                    password=settings.NEO4J_PASSWORD,
                    database=settings.NEO4J_DATABASE,
                )
                # Pull down the schema definitions automatically for LLM context
                self.graph.refresh_schema()
                logger.info(f"Neo4j graph connected for NL query engine via {uri}")
                break
            except Exception as e:
                last_error = e
                logger.warning(f"Neo4j Integration unavailable at {uri}, NL Query disabled: {e}")
                self.graph = None

        if self.graph is None:
            logger.warning(f"Neo4j Integration unavailable at bootstrap across all URIs: {last_error}")

    def execute_query(self, user_question: str) -> str:
        if not self.graph:
            return "Air-gap security mode: Graph DB unreachable. Ensure containers are running."
            
        llm = get_enterprise_llm(temperature=0) # Zero variance for SQL/Cypher writing
        
        CYPHER_GENERATION_TEMPLATE = """
        You are a principal intelligence analyst querying a Civic Knowledge Graph.
        Translate the user's natural language question into a strictly valid Cypher query for Neo4j.
        Schema:
        {schema}
        
        Rules:
        - Only use the node types and properties provided in the schema.
        - Do not map PM Kisan to random properties unless it exists as a Scheme node.
        - Ensure relationships like (Citizen)-[:LIVES_IN]->(Booth) are respected.
        
        Question: {question}
        Cypher Query:"""

        cypher_prompt = PromptTemplate(
            template=CYPHER_GENERATION_TEMPLATE,
            input_variables=["schema", "question"],
        )
        
        chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=self.graph,
            cypher_prompt=cypher_prompt,
            verbose=True,
            return_direct=False # False allows LLM to parse the data into a natural language insight
        )
        
        try:
            # Executes the generated cypher query against the DB, then answers the question using the returned context
            response = chain.invoke({"query": user_question})
            return response.get('result', "No actionable intelligence found for this query.")
        except Exception as e:
            logger.error(f"NL to Graph Failure: {e}")
            return "Unable to parse intelligence pattern. Please rephrase your query string."

# Singleton
qa_engine = CivicIntelligenceQA()
