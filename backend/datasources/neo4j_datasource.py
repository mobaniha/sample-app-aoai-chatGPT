from typing import List, Dict, Any
import logging
from neo4j import GraphDatabase


# Implement as standalone class instead of inheriting from BaseDatasource
class Neo4jDatasource:
    """Neo4j implementation for RAG retrieval."""
    
    def __init__(self, settings):
        """Initialize with application settings."""
        # No inheritance, no super() call
        self.settings = settings.neo4j
        self.driver = GraphDatabase.driver(
            self.settings.uri, 
            auth=(self.settings.username, self.settings.password),
            database=self.settings.database
        )
        logging.info(f"Neo4j datasource initialized with URI: {self.settings.uri}, database: {self.settings.database}")
        
    def close(self):
        """Close the Neo4j driver connection."""
        if hasattr(self, 'driver') and self.driver:
            self.driver.close()
            
    def __del__(self):
        """Ensure driver is closed when object is deleted."""
        self.close()

    
    def semantic_search(self, query_vector: List[float], top_k: int, kind: str) -> List[Dict[str, Any]]:
        """Semantic search using Neo4j vector search."""
        try:
            with self.driver.session(database=self.settings.database) as session:
                # Execute semantic search query
                vector_field = "embedding"#self.settings.vector_column
                content_field = "content" #self.settings.content_column
                title_field = "title" #self.settings.title_column
                id_field = "chunk_id" #self.settings.id_column
                
                if kind is not None:
                    kind_query = f"AND c.kind = '{kind}'"
                else :
                    kind_query = ""

                result = session.run(f"""
                    MATCH (c)
                    WHERE c.{vector_field} IS NOT NULL
                    {kind_query}
                    WITH c, vector.similarity.cosine(c.{vector_field}, $query_vector) AS score
                    ORDER BY score DESC
                    LIMIT $top_k
                    RETURN 
                        c.{id_field} AS id, 
                        c.{title_field} AS title, 
                        c.{content_field} AS content, 
                        c.webUrl AS webUrl,
                        c.kind as kind,
                        score
                """, query_vector=query_vector, top_k=top_k)


                # Format results to match expected output format
                results = []
                for record in result:
                    results.append({
                        "id": str(record["id"]),
                        "title": record["title"] or "",
                        "webUrl": record["webUrl"] or "",
                        "kind": record["kind"] or "",
                        "content": record["content"],
                        #"path": record["path"] or "",
                        "@search.score": float(record["score"]),
                        "source": "neo4j"
                    })
                
                return results
                
        except Exception as e:
            logging.exception(f"Error during Neo4j semantic search: {str(e)}")
            return []
        
    def keyword_search(self, keywords: List[str], top_k: int) -> List[Dict[str, Any]]:
        """Keyword search using Neo4j vector search."""
        try:
            with self.driver.session(database=self.settings.database) as session:
                
                content_field = "content" #self.settings.content_column
                title_field = "title" #self.settings.title_column
                id_field = "chunk_id" #self.settings.id_column
            
                result = session.run(f"""
                    MATCH (c)-[:HAS_KEYWORD]->(k:Keyword)
                    WHERE k.name IN $keywords
                    WITH c, collect(k.name) AS matched_keywords, count(k) AS keyword_count
                    RETURN c,
                        c.{id_field} AS id, 
                        c.{title_field} AS title, 
                        c.{content_field} AS content, 
                        c.webUrl AS webUrl,
                        c.kind as kind,
                        matched_keywords, keyword_count
                    ORDER BY keyword_count DESC
                    LIMIT $top_k
                """, keywords=keywords, top_k=top_k)
                
                # result = session.run(f"""
                #     MATCH (c:Chunk)-[:HAS_KEYWORD]->(k:Keyword)
                #     WHERE k.value IN $keywords
                #     WITH c, collect(k.value) AS matched_keywords, count(k) AS keyword_count
                #     RETURN c, matched_keywords, keyword_count
                #     ORDER BY keyword_count DESC
                #     LIMIT $top_k
                # """, keywords=keywords, top_k=top_k)
                
                # return [{
                #         "document": dict(record["c"]),
                #         "matched_keywords": record["matched_keywords"],
                #         "keyword_count": record["keyword_count"],
                #         "source": "neo4j"}
                #         for record in result]

                # Format results to match expected output format
                results = []
                for record in result:
                    results.append({
                        "id": str(record["id"]),
                        "title": record["title"] or "",
                        "webUrl": record["webUrl"] or "",
                        "kind": record["kind"] or "",
                        "content": record["content"],
                        "matched_keywords": record["matched_keywords"],
                        "@search.score": float(record["keyword_count"]),
                        "source": "neo4j"
                    })
                
                return results
                
        except Exception as e:
            logging.exception(f"Error during Neo4j keyword search: {str(e)}")
            return []