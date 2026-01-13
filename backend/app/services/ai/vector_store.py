"""
Vector store service for interacting with Qdrant.
"""

from typing import Any, List
from uuid import UUID

import structlog
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models

from app.config import settings

logger = structlog.get_logger()


class VectorStoreService:
    """Service for managing vector embeddings and Qdrant interactions."""

    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            # api_key=settings.qdrant_api_key, # Uncomment if using Cloud
        )
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model="text-embedding-3-small"
        )
        self.collection_name = "em_system_documents"
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the Qdrant collection exists."""
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI text-embedding-3-small dimension
                    distance=models.Distance.COSINE
                )
            )
            logger.info("created_qdrant_collection", name=self.collection_name)

    async def add_texts(self, texts: List[str], metadatas: List[dict]) -> None:
        """Add texts and metadata to the vector store."""
        
        # Initialize LangChain Qdrant wrapper
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        
        await vector_store.aadd_texts(texts=texts, metadatas=metadatas)
        logger.info("added_vectors", count=len(texts))

    async def search(self, query: str, organization_id: UUID, limit: int = 5) -> List[Document]:
        """
        Search for relevant documents, filtered by organization.
        
        Args:
            query: The search query string
            organization_id: Organization ID to filter by (Multi-tenancy isolation)
            limit: Number of results
            
        Returns:
            List of LangChain Documents
        """
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.collection_name,
            embedding=self.embeddings,
        )
        
        # Filter by organization_id in metadata
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="organization_id",
                    match=models.MatchValue(value=str(organization_id))
                )
            ]
        )
        
        results = await vector_store.asimilarity_search(
            query=query,
            k=limit,
            filter=filter_condition 
        )
        
        return results

    async def index_entity(self, entity_type: str, entity_id: UUID, content: str, organization_id: UUID, extra_meta: dict = None):
        """
        Helper to index a generic entity.
        
        Args:
            entity_type: e.g., "task", "meeting", "transaction"
            entity_id: The UUID of the entity
            content: Text representation of the entity to embed
            organization_id: Owner org
            extra_meta: Additional filtering metadata
        """
        meta = {
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "organization_id": str(organization_id)
        }
        if extra_meta:
            meta.update(extra_meta)
            
        await self.add_texts(texts=[content], metadatas=[meta])
