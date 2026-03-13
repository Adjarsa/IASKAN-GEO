"""
Semantic Search Router
API endpoints for semantic search using pgvector
"""
from fastapi import APIRouter, HTTPException, Request, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import logging

from ..db.database import async_session_maker
from ..db.services import UserService, SessionService, ProjectService
from ..services.semantic_search_service import semantic_search_service
from ..services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/semantic", tags=["Semantic Search"])


# ================== HELPER FUNCTIONS ==================

async def get_current_user(request: Request) -> dict:
    """Get current authenticated user"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    async with async_session_maker() as db:
        session = await SessionService.get_by_token(db, token)
        if not session:
            raise HTTPException(status_code=401, detail="Session expirée")
        
        user = await UserService.get_by_user_id(db, session.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        return UserService.to_dict(user)


async def verify_project_access(project_id: str, user_id: str) -> bool:
    """Verify user has access to project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        return True


# ================== REQUEST MODELS ==================

class SemanticSearchRequest(BaseModel):
    query: str
    project_id: str
    limit: int = 10
    threshold: float = 0.5


class ContentSearchRequest(BaseModel):
    text: str
    project_id: str
    content_type: Optional[str] = None
    limit: int = 10
    threshold: float = 0.5


class IndexContentRequest(BaseModel):
    project_id: str
    content_type: str  # article, faq, page, product
    title: str
    url: Optional[str] = None
    content: str


class IndexQueryRequest(BaseModel):
    project_id: str
    query_text: str
    query_type: Optional[str] = None  # transactional, comparative, etc.
    source: Optional[str] = "user_input"


class BulkIndexRequest(BaseModel):
    project_id: str
    items: List[Dict[str, Any]]  # List of {text, type, source}


# ================== ENDPOINTS ==================

@router.get("/status")
async def get_semantic_status(
    user: dict = Depends(get_current_user)
):
    """
    Get semantic search service status.
    Returns availability of pgvector and embedding service.
    """
    return {
        "embedding_service_available": embedding_service.is_available(),
        "embedding_model": "text-embedding-3-small",
        "embedding_dimensions": 1536,
        "status": "operational" if embedding_service.is_available() else "limited"
    }


@router.get("/stats/{project_id}")
async def get_project_embedding_stats(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get embedding statistics for a project.
    """
    await verify_project_access(project_id, user["user_id"])
    
    async with async_session_maker() as db:
        stats = await semantic_search_service.get_embedding_stats(db, project_id)
        return stats


@router.post("/search/queries")
async def search_similar_queries(
    request_data: SemanticSearchRequest,
    user: dict = Depends(get_current_user)
):
    """
    Find queries similar to the input text.
    Uses semantic similarity to find related questions.
    """
    await verify_project_access(request_data.project_id, user["user_id"])
    
    async with async_session_maker() as db:
        results = await semantic_search_service.search_similar_queries(
            db,
            request_data.query,
            request_data.project_id,
            request_data.limit,
            request_data.threshold
        )
        
        return {
            "query": request_data.query,
            "results": results,
            "count": len(results)
        }


@router.post("/search/content")
async def search_similar_content(
    request_data: ContentSearchRequest,
    user: dict = Depends(get_current_user)
):
    """
    Find content similar to the input text.
    Useful for finding related articles, pages, or FAQs.
    """
    await verify_project_access(request_data.project_id, user["user_id"])
    
    async with async_session_maker() as db:
        results = await semantic_search_service.search_similar_content(
            db,
            request_data.text,
            request_data.project_id,
            request_data.content_type,
            request_data.limit,
            request_data.threshold
        )
        
        return {
            "query": request_data.text[:100] + "..." if len(request_data.text) > 100 else request_data.text,
            "content_type_filter": request_data.content_type,
            "results": results,
            "count": len(results)
        }


@router.get("/gaps/{project_id}")
async def find_content_gaps(
    project_id: str,
    brand_name: Optional[str] = None,
    min_score: float = Query(default=60, ge=0, le=100),
    user: dict = Depends(get_current_user)
):
    """
    Identify content gaps where competitors are mentioned but brand is not.
    Returns opportunities for content creation.
    """
    await verify_project_access(project_id, user["user_id"])
    
    # Get brand name from project if not provided
    if not brand_name:
        async with async_session_maker() as db:
            project = await ProjectService.get_by_id(db, project_id)
            brand_name = project.brand_name if project else "unknown"
    
    async with async_session_maker() as db:
        gaps = await semantic_search_service.find_content_gaps(
            db,
            project_id,
            brand_name,
            min_score
        )
        
        return {
            "project_id": project_id,
            "brand_name": brand_name,
            "gaps": gaps,
            "count": len(gaps),
            "min_score_filter": min_score
        }


@router.get("/clusters/{project_id}")
async def get_query_clusters(
    project_id: str,
    num_clusters: int = Query(default=5, ge=2, le=10),
    user: dict = Depends(get_current_user)
):
    """
    Get semantic clusters of queries for the project.
    Groups similar queries together for analysis.
    """
    await verify_project_access(project_id, user["user_id"])
    
    async with async_session_maker() as db:
        clusters = await semantic_search_service.cluster_queries(
            db,
            project_id,
            num_clusters
        )
        
        return {
            "project_id": project_id,
            "clusters": clusters,
            "count": len(clusters)
        }


@router.post("/index/query")
async def index_query(
    request_data: IndexQueryRequest,
    user: dict = Depends(get_current_user)
):
    """
    Index a query for semantic search.
    Generates embedding and stores it for similarity search.
    """
    await verify_project_access(request_data.project_id, user["user_id"])
    
    # Generate embedding
    embedding = await embedding_service.generate_embedding(request_data.query_text)
    
    if not embedding:
        raise HTTPException(
            status_code=503, 
            detail="Service d'embedding non disponible"
        )
    
    try:
        from ..db.vector_models import QueryEmbedding
        
        async with async_session_maker() as db:
            # Create query embedding record
            query_emb = QueryEmbedding(
                project_id=request_data.project_id,
                user_id=user["user_id"],
                query_text=request_data.query_text,
                query_type=request_data.query_type,
                source=request_data.source,
                embedding=embedding
            )
            db.add(query_emb)
            await db.commit()
            await db.refresh(query_emb)
            
            return {
                "success": True,
                "embedding_id": query_emb.embedding_id,
                "query_text": request_data.query_text,
                "message": "Query indexed successfully"
            }
            
    except Exception as e:
        logger.error(f"Error indexing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/content")
async def index_content(
    request_data: IndexContentRequest,
    user: dict = Depends(get_current_user)
):
    """
    Index content for semantic search.
    Stores article/page/FAQ with embedding for similarity search.
    """
    await verify_project_access(request_data.project_id, user["user_id"])
    
    # Generate embedding
    embedding = await embedding_service.generate_embedding(
        f"{request_data.title} {request_data.content}"
    )
    
    if not embedding:
        raise HTTPException(
            status_code=503, 
            detail="Service d'embedding non disponible"
        )
    
    try:
        from ..db.vector_models import ContentEmbedding
        
        async with async_session_maker() as db:
            content_emb = ContentEmbedding(
                project_id=request_data.project_id,
                user_id=user["user_id"],
                content_type=request_data.content_type,
                title=request_data.title,
                url=request_data.url,
                content_snippet=request_data.content[:500],
                full_content_hash=embedding_service.content_hash(request_data.content),
                embedding=embedding,
                word_count=len(request_data.content.split())
            )
            db.add(content_emb)
            await db.commit()
            await db.refresh(content_emb)
            
            return {
                "success": True,
                "embedding_id": content_emb.embedding_id,
                "title": request_data.title,
                "content_type": request_data.content_type,
                "message": "Content indexed successfully"
            }
            
    except Exception as e:
        logger.error(f"Error indexing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/bulk")
async def bulk_index_queries(
    request_data: BulkIndexRequest,
    user: dict = Depends(get_current_user)
):
    """
    Bulk index multiple queries at once.
    More efficient than indexing one by one.
    """
    await verify_project_access(request_data.project_id, user["user_id"])
    
    if len(request_data.items) > 100:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 100 items per bulk request"
        )
    
    # Extract texts for batch embedding
    texts = [item.get("text", "") for item in request_data.items]
    
    # Generate embeddings in batch
    embeddings = await embedding_service.generate_embeddings_batch(texts)
    
    try:
        from ..db.vector_models import QueryEmbedding
        
        indexed = 0
        failed = 0
        
        async with async_session_maker() as db:
            for i, item in enumerate(request_data.items):
                if embeddings[i] is None:
                    failed += 1
                    continue
                
                query_emb = QueryEmbedding(
                    project_id=request_data.project_id,
                    user_id=user["user_id"],
                    query_text=item.get("text", ""),
                    query_type=item.get("type"),
                    source=item.get("source", "bulk_import"),
                    embedding=embeddings[i]
                )
                db.add(query_emb)
                indexed += 1
            
            await db.commit()
            
            return {
                "success": True,
                "indexed": indexed,
                "failed": failed,
                "total": len(request_data.items),
                "message": f"{indexed} queries indexed successfully"
            }
            
    except Exception as e:
        logger.error(f"Error bulk indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/index/{embedding_id}")
async def delete_embedding(
    embedding_id: str,
    embedding_type: str = Query(default="query", enum=["query", "content", "response"]),
    user: dict = Depends(get_current_user)
):
    """
    Delete an indexed embedding.
    """
    try:
        from ..db.vector_models import QueryEmbedding, ContentEmbedding, ResponseEmbedding
        
        model_map = {
            "query": QueryEmbedding,
            "content": ContentEmbedding,
            "response": ResponseEmbedding
        }
        
        Model = model_map.get(embedding_type)
        if not Model:
            raise HTTPException(status_code=400, detail="Invalid embedding type")
        
        async with async_session_maker() as db:
            from sqlalchemy import select, delete
            
            # Verify ownership
            result = await db.execute(
                select(Model).where(Model.embedding_id == embedding_id)
            )
            embedding = result.scalar_one_or_none()
            
            if not embedding:
                raise HTTPException(status_code=404, detail="Embedding non trouvé")
            
            if embedding.user_id != user["user_id"]:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            
            await db.execute(
                delete(Model).where(Model.embedding_id == embedding_id)
            )
            await db.commit()
            
            return {
                "success": True,
                "message": "Embedding deleted successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-embedding")
async def generate_embedding_for_text(
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Generate embedding for text without storing it.
    Useful for testing or one-time similarity checks.
    """
    body = await request.json()
    text = body.get("text", "")
    
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    if len(text) > 30000:
        raise HTTPException(status_code=400, detail="Text too long (max 30000 chars)")
    
    embedding = await embedding_service.generate_embedding(text)
    
    if not embedding:
        raise HTTPException(
            status_code=503, 
            detail="Embedding service not available"
        )
    
    return {
        "text_length": len(text),
        "embedding_dimensions": len(embedding),
        "embedding_preview": embedding[:10],  # First 10 values
        "message": "Embedding generated successfully"
    }
