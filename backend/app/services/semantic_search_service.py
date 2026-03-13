"""
Semantic Search Service
Provides semantic search capabilities using pgvector
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from .embedding_service import embedding_service, EmbeddingService

logger = logging.getLogger(__name__)

# Check pgvector availability
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class SemanticSearchService:
    """
    Service for semantic search operations using pgvector.
    Supports similarity search on queries, content, and responses.
    """
    
    def __init__(self):
        self.embedding_service = embedding_service
    
    async def search_similar_queries(
        self,
        db: AsyncSession,
        query_text: str,
        project_id: str,
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find queries similar to the input text.
        
        Args:
            db: Database session
            query_text: Text to search for
            project_id: Project ID to scope search
            limit: Max results to return
            threshold: Minimum similarity (0-1)
            
        Returns:
            List of similar queries with similarity scores
        """
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_embedding(query_text)
        
        if not query_embedding:
            logger.warning("Failed to generate embedding for query")
            return []
        
        if PGVECTOR_AVAILABLE:
            return await self._pgvector_search_queries(
                db, query_embedding, project_id, limit, threshold
            )
        else:
            return await self._fallback_search_queries(
                db, query_embedding, project_id, limit, threshold
            )
    
    async def search_similar_content(
        self,
        db: AsyncSession,
        text: str,
        project_id: str,
        content_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find content similar to the input text.
        
        Args:
            db: Database session
            text: Text to search for
            project_id: Project ID to scope search
            content_type: Optional filter by type (article, faq, etc.)
            limit: Max results
            threshold: Minimum similarity
            
        Returns:
            List of similar content items
        """
        query_embedding = await self.embedding_service.generate_embedding(text)
        
        if not query_embedding:
            return []
        
        if PGVECTOR_AVAILABLE:
            return await self._pgvector_search_content(
                db, query_embedding, project_id, content_type, limit, threshold
            )
        else:
            return await self._fallback_search_content(
                db, query_embedding, project_id, content_type, limit, threshold
            )
    
    async def find_content_gaps(
        self,
        db: AsyncSession,
        project_id: str,
        brand_name: str,
        min_gap_score: float = 60
    ) -> List[Dict[str, Any]]:
        """
        Identify content gaps where competitors are mentioned but brand is not.
        
        Args:
            db: Database session
            project_id: Project ID
            brand_name: Brand to check for
            min_gap_score: Minimum importance score for gaps
            
        Returns:
            List of content gap opportunities
        """
        try:
            from ..db.vector_models import ResponseEmbedding, QueryEmbedding
            
            # Find responses where brand was NOT mentioned
            result = await db.execute(
                select(ResponseEmbedding)
                .where(
                    ResponseEmbedding.project_id == project_id,
                    ResponseEmbedding.brand_mentioned == "N"
                )
            )
            responses_without_brand = result.scalars().all()
            
            if not responses_without_brand:
                return []
            
            # Group by similar topics using semantic clustering
            gaps = []
            processed_queries = set()
            
            for response in responses_without_brand:
                if response.query_embedding_id in processed_queries:
                    continue
                
                processed_queries.add(response.query_embedding_id)
                
                # Get the original query
                query_result = await db.execute(
                    select(QueryEmbedding)
                    .where(QueryEmbedding.embedding_id == response.query_embedding_id)
                )
                query = query_result.scalar_one_or_none()
                
                if query:
                    # Calculate gap importance
                    importance = self._calculate_gap_importance(
                        query.query_type,
                        response.relevance_score or 0,
                        response.brand_role
                    )
                    
                    if importance >= min_gap_score:
                        gaps.append({
                            "query_text": query.query_text,
                            "query_type": query.query_type,
                            "importance_score": importance,
                            "competitor_mentioned": response.brand_role,
                            "ai_engine": response.ai_engine,
                            "suggested_action": self._suggest_gap_action(query.query_type)
                        })
            
            # Sort by importance
            gaps.sort(key=lambda x: x["importance_score"], reverse=True)
            
            return gaps[:20]  # Top 20 gaps
            
        except Exception as e:
            logger.error(f"Error finding content gaps: {e}")
            return []
    
    async def cluster_queries(
        self,
        db: AsyncSession,
        project_id: str,
        num_clusters: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Group similar queries into semantic clusters.
        Uses k-means style clustering on embeddings.
        
        Args:
            db: Database session
            project_id: Project ID
            num_clusters: Number of clusters to create
            
        Returns:
            List of clusters with queries
        """
        try:
            from ..db.vector_models import QueryEmbedding
            
            # Get all query embeddings for project
            result = await db.execute(
                select(QueryEmbedding)
                .where(QueryEmbedding.project_id == project_id)
            )
            queries = result.scalars().all()
            
            if len(queries) < num_clusters:
                # Not enough queries for clustering
                return [{
                    "cluster_id": 0,
                    "name": "Toutes les requêtes",
                    "queries": [
                        {"text": q.query_text, "type": q.query_type}
                        for q in queries
                    ]
                }]
            
            # Simple clustering by query type first
            clusters_by_type = {}
            for query in queries:
                qtype = query.query_type or "general"
                if qtype not in clusters_by_type:
                    clusters_by_type[qtype] = []
                clusters_by_type[qtype].append(query)
            
            clusters = []
            for i, (qtype, type_queries) in enumerate(clusters_by_type.items()):
                cluster = {
                    "cluster_id": i,
                    "name": self._query_type_to_name(qtype),
                    "query_type": qtype,
                    "query_count": len(type_queries),
                    "queries": [
                        {
                            "text": q.query_text,
                            "type": q.query_type,
                            "source": q.source
                        }
                        for q in type_queries[:10]  # Max 10 per cluster for display
                    ],
                    "keywords": self._extract_cluster_keywords(type_queries)
                }
                clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            logger.error(f"Error clustering queries: {e}")
            return []
    
    async def get_embedding_stats(
        self,
        db: AsyncSession,
        project_id: str
    ) -> Dict[str, Any]:
        """Get statistics about embeddings for a project"""
        try:
            from ..db.vector_models import QueryEmbedding, ContentEmbedding, ResponseEmbedding
            
            # Count embeddings by type
            query_count = await db.execute(
                select(func.count(QueryEmbedding.id))
                .where(QueryEmbedding.project_id == project_id)
            )
            
            content_count = await db.execute(
                select(func.count(ContentEmbedding.id))
                .where(ContentEmbedding.project_id == project_id)
            )
            
            response_count = await db.execute(
                select(func.count(ResponseEmbedding.id))
                .where(ResponseEmbedding.project_id == project_id)
            )
            
            return {
                "query_embeddings": query_count.scalar() or 0,
                "content_embeddings": content_count.scalar() or 0,
                "response_embeddings": response_count.scalar() or 0,
                "pgvector_available": PGVECTOR_AVAILABLE,
                "embedding_service_available": self.embedding_service.is_available()
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {
                "query_embeddings": 0,
                "content_embeddings": 0,
                "response_embeddings": 0,
                "pgvector_available": PGVECTOR_AVAILABLE,
                "embedding_service_available": self.embedding_service.is_available()
            }
    
    # ================== Private Methods ==================
    
    async def _pgvector_search_queries(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        project_id: str,
        limit: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Search using pgvector's native similarity search"""
        try:
            # Use pgvector's <=> operator for cosine distance
            # Convert to SQL with proper vector casting
            sql = text("""
                SELECT 
                    embedding_id,
                    query_text,
                    query_type,
                    source,
                    1 - (embedding <=> :query_vec::vector) as similarity
                FROM query_embeddings
                WHERE project_id = :project_id
                    AND embedding IS NOT NULL
                    AND 1 - (embedding <=> :query_vec::vector) >= :threshold
                ORDER BY embedding <=> :query_vec::vector
                LIMIT :limit
            """)
            
            result = await db.execute(
                sql,
                {
                    "query_vec": str(query_embedding),
                    "project_id": project_id,
                    "threshold": threshold,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            
            return [
                {
                    "embedding_id": row.embedding_id,
                    "query_text": row.query_text,
                    "query_type": row.query_type,
                    "source": row.source,
                    "similarity": round(row.similarity, 4)
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"pgvector search error: {e}")
            return await self._fallback_search_queries(
                db, query_embedding, project_id, limit, threshold
            )
    
    async def _fallback_search_queries(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        project_id: str,
        limit: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Fallback search using Python cosine similarity"""
        try:
            from ..db.vector_models import QueryEmbedding
            
            result = await db.execute(
                select(QueryEmbedding)
                .where(
                    QueryEmbedding.project_id == project_id,
                    QueryEmbedding.embedding.isnot(None)
                )
            )
            queries = result.scalars().all()
            
            # Build embedding tuples
            embeddings = []
            query_map = {}
            for q in queries:
                if q.embedding:
                    emb = q.embedding if isinstance(q.embedding, list) else list(q.embedding)
                    embeddings.append((q.embedding_id, emb))
                    query_map[q.embedding_id] = q
            
            # Find similar
            similar = EmbeddingService.find_similar(
                query_embedding, embeddings, limit, threshold
            )
            
            return [
                {
                    "embedding_id": s["id"],
                    "query_text": query_map[s["id"]].query_text,
                    "query_type": query_map[s["id"]].query_type,
                    "source": query_map[s["id"]].source,
                    "similarity": s["similarity"]
                }
                for s in similar
            ]
            
        except Exception as e:
            logger.error(f"Fallback search error: {e}")
            return []
    
    async def _pgvector_search_content(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        project_id: str,
        content_type: Optional[str],
        limit: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Search content using pgvector"""
        try:
            type_filter = "AND content_type = :content_type" if content_type else ""
            
            sql = text(f"""
                SELECT 
                    embedding_id,
                    title,
                    url,
                    content_type,
                    content_snippet,
                    1 - (embedding <=> :query_vec::vector) as similarity
                FROM content_embeddings
                WHERE project_id = :project_id
                    AND embedding IS NOT NULL
                    {type_filter}
                    AND 1 - (embedding <=> :query_vec::vector) >= :threshold
                ORDER BY embedding <=> :query_vec::vector
                LIMIT :limit
            """)
            
            params = {
                "query_vec": str(query_embedding),
                "project_id": project_id,
                "threshold": threshold,
                "limit": limit
            }
            if content_type:
                params["content_type"] = content_type
            
            result = await db.execute(sql, params)
            rows = result.fetchall()
            
            return [
                {
                    "embedding_id": row.embedding_id,
                    "title": row.title,
                    "url": row.url,
                    "content_type": row.content_type,
                    "snippet": row.content_snippet[:200] if row.content_snippet else None,
                    "similarity": round(row.similarity, 4)
                }
                for row in rows
            ]
            
        except Exception as e:
            logger.error(f"pgvector content search error: {e}")
            return await self._fallback_search_content(
                db, query_embedding, project_id, content_type, limit, threshold
            )
    
    async def _fallback_search_content(
        self,
        db: AsyncSession,
        query_embedding: List[float],
        project_id: str,
        content_type: Optional[str],
        limit: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """Fallback content search using Python"""
        try:
            from ..db.vector_models import ContentEmbedding
            
            query = select(ContentEmbedding).where(
                ContentEmbedding.project_id == project_id,
                ContentEmbedding.embedding.isnot(None)
            )
            if content_type:
                query = query.where(ContentEmbedding.content_type == content_type)
            
            result = await db.execute(query)
            contents = result.scalars().all()
            
            embeddings = []
            content_map = {}
            for c in contents:
                if c.embedding:
                    emb = c.embedding if isinstance(c.embedding, list) else list(c.embedding)
                    embeddings.append((c.embedding_id, emb))
                    content_map[c.embedding_id] = c
            
            similar = EmbeddingService.find_similar(
                query_embedding, embeddings, limit, threshold
            )
            
            return [
                {
                    "embedding_id": s["id"],
                    "title": content_map[s["id"]].title,
                    "url": content_map[s["id"]].url,
                    "content_type": content_map[s["id"]].content_type,
                    "snippet": content_map[s["id"]].content_snippet[:200] if content_map[s["id"]].content_snippet else None,
                    "similarity": s["similarity"]
                }
                for s in similar
            ]
            
        except Exception as e:
            logger.error(f"Fallback content search error: {e}")
            return []
    
    def _calculate_gap_importance(
        self, 
        query_type: str, 
        relevance: float,
        competitor_role: str
    ) -> float:
        """Calculate importance score for a content gap"""
        base_score = 50
        
        # Query type weights
        type_weights = {
            "transactional": 25,
            "comparative": 20,
            "informational": 15,
            "exploratory": 10,
            "local": 15
        }
        base_score += type_weights.get(query_type, 10)
        
        # Relevance bonus
        base_score += (relevance / 100) * 15
        
        # Competitor role bonus
        role_weights = {
            "leader": 15,
            "recommended": 12,
            "alternative": 8,
            "mentioned": 5
        }
        base_score += role_weights.get(competitor_role, 0)
        
        return min(100, base_score)
    
    def _suggest_gap_action(self, query_type: str) -> str:
        """Suggest action to address content gap"""
        suggestions = {
            "transactional": "Créer une page produit/service optimisée avec CTA clair",
            "comparative": "Créer un comparatif détaillé mettant en avant vos avantages",
            "informational": "Rédiger un article de blog ou guide complet sur le sujet",
            "exploratory": "Ajouter une section FAQ et des définitions claires",
            "local": "Optimiser votre fiche Google Business et pages locales"
        }
        return suggestions.get(query_type, "Analyser le besoin et créer du contenu pertinent")
    
    def _query_type_to_name(self, query_type: str) -> str:
        """Convert query type to French name"""
        names = {
            "transactional": "Intentions d'achat",
            "comparative": "Comparaisons",
            "informational": "Information",
            "exploratory": "Exploration",
            "local": "Recherche locale",
            "general": "Général"
        }
        return names.get(query_type, query_type.title())
    
    def _extract_cluster_keywords(self, queries) -> List[str]:
        """Extract common keywords from cluster queries"""
        import re
        from collections import Counter
        
        words = []
        for q in queries:
            # Extract words from query
            text_words = re.findall(r'\b\w{4,}\b', q.query_text.lower())
            words.extend(text_words)
        
        # Filter stopwords
        stopwords = {
            "pour", "dans", "avec", "comment", "quoi", "quel", "quelle",
            "quels", "quelles", "être", "avoir", "faire", "plus", "moins",
            "très", "bien", "donc", "mais", "aussi", "encore", "comme"
        }
        words = [w for w in words if w not in stopwords]
        
        # Get top keywords
        counter = Counter(words)
        return [w for w, _ in counter.most_common(5)]


# Singleton instance
semantic_search_service = SemanticSearchService()
