"""
Structured Data Generator Router - Schema.org Markup Generation
Sprint D: GEO Action Engine

Generates JSON-LD structured data markup for:
- Organization
- Product
- FAQ
- Article
- HowTo
- LocalBusiness
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import logging

from ..routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["structured-data"])


# ================== MODELS ==================

class OrganizationSchemaRequest(BaseModel):
    name: str
    description: str
    url: str
    logo_url: Optional[str] = None
    social_profiles: Optional[List[str]] = []
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None


class ProductSchemaRequest(BaseModel):
    name: str
    description: str
    brand: str
    url: str
    image_url: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = "EUR"
    availability: Optional[str] = "InStock"
    rating: Optional[float] = None
    review_count: Optional[int] = None


class FAQSchemaRequest(BaseModel):
    questions: List[Dict[str, str]]  # [{"question": "...", "answer": "..."}]


class ArticleSchemaRequest(BaseModel):
    title: str
    description: str
    author_name: str
    date_published: str
    date_modified: Optional[str] = None
    image_url: Optional[str] = None
    publisher_name: str
    publisher_logo: Optional[str] = None


class HowToSchemaRequest(BaseModel):
    name: str
    description: str
    steps: List[Dict[str, str]]  # [{"name": "...", "text": "..."}]
    total_time: Optional[str] = None  # ISO 8601 duration
    image_url: Optional[str] = None


class LocalBusinessSchemaRequest(BaseModel):
    name: str
    description: str
    url: str
    address: Dict[str, str]  # streetAddress, addressLocality, postalCode, addressCountry
    phone: Optional[str] = None
    opening_hours: Optional[List[str]] = []  # ["Mo-Fr 09:00-18:00"]
    price_range: Optional[str] = None  # "$", "$$", "$$$"
    image_url: Optional[str] = None


# ================== GENERATORS ==================

def generate_organization_schema(data: OrganizationSchemaRequest) -> Dict[str, Any]:
    """Generate Schema.org Organization markup"""
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": data.name,
        "description": data.description,
        "url": data.url
    }
    
    if data.logo_url:
        schema["logo"] = data.logo_url
    
    if data.social_profiles:
        schema["sameAs"] = data.social_profiles
    
    if data.contact_email or data.contact_phone:
        schema["contactPoint"] = {
            "@type": "ContactPoint",
            "contactType": "customer service"
        }
        if data.contact_email:
            schema["contactPoint"]["email"] = data.contact_email
        if data.contact_phone:
            schema["contactPoint"]["telephone"] = data.contact_phone
    
    if data.address:
        schema["address"] = {
            "@type": "PostalAddress",
            **data.address
        }
    
    return schema


def generate_product_schema(data: ProductSchemaRequest) -> Dict[str, Any]:
    """Generate Schema.org Product markup"""
    schema = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": data.name,
        "description": data.description,
        "brand": {
            "@type": "Brand",
            "name": data.brand
        },
        "url": data.url
    }
    
    if data.image_url:
        schema["image"] = data.image_url
    
    if data.price is not None:
        schema["offers"] = {
            "@type": "Offer",
            "price": data.price,
            "priceCurrency": data.currency,
            "availability": f"https://schema.org/{data.availability}"
        }
    
    if data.rating is not None:
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": data.rating,
            "bestRating": 5,
            "worstRating": 1,
            "reviewCount": data.review_count or 1
        }
    
    return schema


def generate_faq_schema(data: FAQSchemaRequest) -> Dict[str, Any]:
    """Generate Schema.org FAQPage markup"""
    main_entity = []
    
    for item in data.questions:
        main_entity.append({
            "@type": "Question",
            "name": item.get("question", ""),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": item.get("answer", "")
            }
        })
    
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity
    }


def generate_article_schema(data: ArticleSchemaRequest) -> Dict[str, Any]:
    """Generate Schema.org Article markup"""
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": data.title,
        "description": data.description,
        "author": {
            "@type": "Person",
            "name": data.author_name
        },
        "datePublished": data.date_published,
        "publisher": {
            "@type": "Organization",
            "name": data.publisher_name
        }
    }
    
    if data.date_modified:
        schema["dateModified"] = data.date_modified
    
    if data.image_url:
        schema["image"] = data.image_url
    
    if data.publisher_logo:
        schema["publisher"]["logo"] = {
            "@type": "ImageObject",
            "url": data.publisher_logo
        }
    
    return schema


def generate_howto_schema(data: HowToSchemaRequest) -> Dict[str, Any]:
    """Generate Schema.org HowTo markup"""
    steps = []
    
    for i, step in enumerate(data.steps, 1):
        steps.append({
            "@type": "HowToStep",
            "position": i,
            "name": step.get("name", f"Étape {i}"),
            "text": step.get("text", "")
        })
    
    schema = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": data.name,
        "description": data.description,
        "step": steps
    }
    
    if data.total_time:
        schema["totalTime"] = data.total_time
    
    if data.image_url:
        schema["image"] = data.image_url
    
    return schema


def generate_local_business_schema(data: LocalBusinessSchemaRequest) -> Dict[str, Any]:
    """Generate Schema.org LocalBusiness markup"""
    schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": data.name,
        "description": data.description,
        "url": data.url,
        "address": {
            "@type": "PostalAddress",
            **data.address
        }
    }
    
    if data.phone:
        schema["telephone"] = data.phone
    
    if data.opening_hours:
        schema["openingHours"] = data.opening_hours
    
    if data.price_range:
        schema["priceRange"] = data.price_range
    
    if data.image_url:
        schema["image"] = data.image_url
    
    return schema


def format_json_ld(schema: Dict[str, Any]) -> str:
    """Format schema as JSON-LD script tag"""
    json_str = json.dumps(schema, indent=2, ensure_ascii=False)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'


# ================== ENDPOINTS ==================

@router.post("/structured-data/organization")
async def create_organization_schema(
    request: OrganizationSchemaRequest,
    user: dict = Depends(get_current_user)
):
    """Generate Schema.org Organization markup"""
    schema = generate_organization_schema(request)
    return {
        "schema": schema,
        "json_ld": format_json_ld(schema),
        "type": "Organization",
        "validation_url": "https://validator.schema.org/"
    }


@router.post("/structured-data/product")
async def create_product_schema(
    request: ProductSchemaRequest,
    user: dict = Depends(get_current_user)
):
    """Generate Schema.org Product markup"""
    schema = generate_product_schema(request)
    return {
        "schema": schema,
        "json_ld": format_json_ld(schema),
        "type": "Product",
        "validation_url": "https://validator.schema.org/"
    }


@router.post("/structured-data/faq")
async def create_faq_schema(
    request: FAQSchemaRequest,
    user: dict = Depends(get_current_user)
):
    """Generate Schema.org FAQPage markup"""
    schema = generate_faq_schema(request)
    return {
        "schema": schema,
        "json_ld": format_json_ld(schema),
        "type": "FAQPage",
        "validation_url": "https://validator.schema.org/"
    }


@router.post("/structured-data/article")
async def create_article_schema(
    request: ArticleSchemaRequest,
    user: dict = Depends(get_current_user)
):
    """Generate Schema.org Article markup"""
    schema = generate_article_schema(request)
    return {
        "schema": schema,
        "json_ld": format_json_ld(schema),
        "type": "Article",
        "validation_url": "https://validator.schema.org/"
    }


@router.post("/structured-data/howto")
async def create_howto_schema(
    request: HowToSchemaRequest,
    user: dict = Depends(get_current_user)
):
    """Generate Schema.org HowTo markup"""
    schema = generate_howto_schema(request)
    return {
        "schema": schema,
        "json_ld": format_json_ld(schema),
        "type": "HowTo",
        "validation_url": "https://validator.schema.org/"
    }


@router.post("/structured-data/local-business")
async def create_local_business_schema(
    request: LocalBusinessSchemaRequest,
    user: dict = Depends(get_current_user)
):
    """Generate Schema.org LocalBusiness markup"""
    schema = generate_local_business_schema(request)
    return {
        "schema": schema,
        "json_ld": format_json_ld(schema),
        "type": "LocalBusiness",
        "validation_url": "https://validator.schema.org/"
    }


@router.get("/structured-data/templates")
async def get_schema_templates(user: dict = Depends(get_current_user)):
    """Get available schema templates and their required fields"""
    return {
        "templates": [
            {
                "type": "Organization",
                "endpoint": "/api/structured-data/organization",
                "required_fields": ["name", "description", "url"],
                "optional_fields": ["logo_url", "social_profiles", "contact_email", "contact_phone", "address"],
                "description": "Pour les pages À propos et Contact"
            },
            {
                "type": "Product",
                "endpoint": "/api/structured-data/product",
                "required_fields": ["name", "description", "brand", "url"],
                "optional_fields": ["image_url", "price", "currency", "availability", "rating", "review_count"],
                "description": "Pour les fiches produit"
            },
            {
                "type": "FAQPage",
                "endpoint": "/api/structured-data/faq",
                "required_fields": ["questions"],
                "optional_fields": [],
                "description": "Pour les sections FAQ"
            },
            {
                "type": "Article",
                "endpoint": "/api/structured-data/article",
                "required_fields": ["title", "description", "author_name", "date_published", "publisher_name"],
                "optional_fields": ["date_modified", "image_url", "publisher_logo"],
                "description": "Pour les articles de blog"
            },
            {
                "type": "HowTo",
                "endpoint": "/api/structured-data/howto",
                "required_fields": ["name", "description", "steps"],
                "optional_fields": ["total_time", "image_url"],
                "description": "Pour les tutoriels et guides"
            },
            {
                "type": "LocalBusiness",
                "endpoint": "/api/structured-data/local-business",
                "required_fields": ["name", "description", "url", "address"],
                "optional_fields": ["phone", "opening_hours", "price_range", "image_url"],
                "description": "Pour les entreprises locales"
            }
        ]
    }
