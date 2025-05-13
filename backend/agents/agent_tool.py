# Extended implementation with custom workflows and tools

from typing import Dict, List, Any, Optional, Tuple
from backend.datasources.neo4j_datasource import Neo4jDatasource
import os 

# Create a custom tool registry for our agents
class AgentTools:
    def __init__(self):
        
        neo4j_uri = os.environ.get("NEO4J_URI")
        neo4j_user=os.environ.get("NEO4J_USERNAME")
        neo4j_password=os.environ.get("NEO4J_PASSWORD")
        neo4j_database=os.environ.get("NEO4J_DATABASE")

        from backend.utils import NestedAppSettings
        nested_config = {
            "neo4j":{
                "uri": neo4j_uri,
                "username": neo4j_user,
                "password": neo4j_password,
                "database": neo4j_database
            }
        }
        app_settings = NestedAppSettings(**nested_config)
        self.neo4j_datasource = Neo4jDatasource(app_settings)
        print("Tools instance initiated!")

    
    def get_embedding(self, text: str) -> List[float]:
        from backend.utils import get_ada_large_embeddings
        return get_ada_large_embeddings(text)
    
    def semantic_search(self, query: str, top_k: int = 5, kind: str = None) -> List[Dict]:
        print("started semantic search")
        embedding = self.get_embedding(query)
        result = self.neo4j_datasource.semantic_search(embedding, top_k=top_k, kind=kind)
        formatted_result = self.format_documents(result)
        return formatted_result
    
    def keyword_search(self, keywords: List[str], top_k: int = 5) -> List[Dict]:
        result = self.neo4j_datasource.keyword_search(keywords, top_k=top_k)
        return result

    def format_documents(self, documents: List[Dict]) -> str:
        """Format documents for agent consumption while preserving references"""
        formatted = []
        references = []
        
        for i, doc in enumerate(documents):
            # Format based on document kind
            kind = doc.get("kind", "unknown")
            ref_id = f"REF-{i+1}"
            
            # Create reference entry
            reference = {
                "ref_id": ref_id,
                "kind": kind
            }
            
            # Add URLs or paths based on document kind
            if kind == "teams_thread" and "webUrl" in doc:
                reference["url"] = doc["webUrl"]
            elif kind == "tsg" and "path" in doc:
                reference["path"] = "https://dev.supportability.microsoft.com" + doc["path"]
            
            # Add reference to the list
            references.append(reference)
            
            # Format document with reference ID
            formatted_doc = f"DOCUMENT {ref_id}:\n"
            formatted_doc += f"Type: {kind}\n"
            
            if "content" in doc:
                formatted_doc += f"Content: {doc['content']}\n"
            
            # Add reference links
            if kind == "teams_thread" and "webUrl" in doc:
                formatted_doc += f"Teams URL: {doc['webUrl']} (Reference: {ref_id})\n"
            elif kind == "tsg" and "path" in doc:
                formatted_doc += f"TSG Path: {doc['path']} (Reference: {ref_id})\n"
            formatted_doc += "---------\n"
            formatted.append(formatted_doc)
        
        # Add formatted documents
        formatted_doc = "\n\n".join(formatted)
        
        # Add references section
        references_section = "\n\n=== DOCUMENT REFERENCES ===\n"
        for ref in references:
            ref_line = f"{ref['ref_id']}: {ref['kind']} - {ref['title']}"
            if "url" in ref:
                ref_line += f" - {ref['url']}"
            if "path" in ref:
                ref_line += f" - {ref['path']}"
            references_section += ref_line + "\n"
        
        formatted_doc += references_section
        
        # Store references in a property for later retrieval
        self._last_document_references = references
        
        return formatted_doc

    def execute_kusto_query(self, query: str) -> Dict:
        """Mock function to execute Kusto queries - replace with actual implementation"""
        # This is a placeholder - implement actual Kusto client
        return {
            "status": "success",
            "message": "This is a mock Kusto result. Replace with actual Kusto client implementation.",
            "data": []
        }