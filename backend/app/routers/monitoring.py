"""
GEO Monitoring & Alerts Router - Sprint D
Automated monitoring with smart alerts for GEO visibility changes

Alert Types:
- score_change: Score GEO change > 10 points
- competitor_overtake: Competitor surpasses brand in rankings
- new_mention: Brand mentioned by new AI engine
- visibility_drop: Visibility drops below threshold
- weekly_summary: Weekly digest of all changes
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
import uuid

from ..db.database import async_session_maker
from ..db.services import ProjectService
from ..routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


# ================== ENUMS & MODELS ==================

class AlertType(str, Enum):
    SCORE_CHANGE = "score_change"
    COMPETITOR_OVERTAKE = "competitor_overtake"
    NEW_MENTION = "new_mention"
    VISIBILITY_DROP = "visibility_drop"
    WEEKLY_SUMMARY = "weekly_summary"
    ANALYSIS_COMPLETE = "analysis_complete"


class AlertSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"


class AlertChannel(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SLACK = "slack"
    WEBHOOK = "webhook"


class AlertConfigCreate(BaseModel):
    project_id: str
    alert_type: AlertType
    enabled: bool = True
    threshold: Optional[int] = None  # For score_change: minimum point change
    channels: List[AlertChannel] = [AlertChannel.IN_APP, AlertChannel.EMAIL]
    email_recipients: Optional[List[EmailStr]] = []
    slack_webhook: Optional[str] = None
    custom_webhook: Optional[str] = None


class AlertConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    threshold: Optional[int] = None
    channels: Optional[List[AlertChannel]] = None
    email_recipients: Optional[List[EmailStr]] = None
    slack_webhook: Optional[str] = None
    custom_webhook: Optional[str] = None


class Alert(BaseModel):
    alert_id: str
    project_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    data: Dict[str, Any] = {}
    read: bool = False
    created_at: datetime


# ================== IN-MEMORY STORAGE (for demo - would be DB in production) ==================

# Alert configurations per project
alert_configs: Dict[str, Dict[str, Any]] = {}

# Alert history
alert_history: Dict[str, List[Dict[str, Any]]] = {}


# ================== HELPER FUNCTIONS ==================

def generate_alert_id() -> str:
    return f"alert_{uuid.uuid4().hex[:12]}"


def create_alert(
    project_id: str,
    alert_type: AlertType,
    severity: AlertSeverity,
    title: str,
    message: str,
    data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a new alert"""
    alert = {
        "alert_id": generate_alert_id(),
        "project_id": project_id,
        "alert_type": alert_type.value,
        "severity": severity.value,
        "title": title,
        "message": message,
        "data": data or {},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Store in history
    if project_id not in alert_history:
        alert_history[project_id] = []
    alert_history[project_id].insert(0, alert)
    
    # Keep only last 100 alerts per project
    alert_history[project_id] = alert_history[project_id][:100]
    
    return alert


async def check_score_change_alert(
    project_id: str,
    old_score: float,
    new_score: float,
    threshold: int = 10
) -> Optional[Dict[str, Any]]:
    """Check if score change triggers an alert"""
    change = new_score - old_score
    
    if abs(change) >= threshold:
        if change > 0:
            return create_alert(
                project_id=project_id,
                alert_type=AlertType.SCORE_CHANGE,
                severity=AlertSeverity.SUCCESS,
                title=f"Score GEO en hausse de {change:+.0f} points",
                message=f"Votre score GEO est passé de {old_score:.0f} à {new_score:.0f}. Excellent travail !",
                data={"old_score": old_score, "new_score": new_score, "change": change}
            )
        else:
            severity = AlertSeverity.CRITICAL if change < -20 else AlertSeverity.WARNING
            return create_alert(
                project_id=project_id,
                alert_type=AlertType.SCORE_CHANGE,
                severity=severity,
                title=f"Score GEO en baisse de {abs(change):.0f} points",
                message=f"Votre score GEO est passé de {old_score:.0f} à {new_score:.0f}. Action recommandée.",
                data={"old_score": old_score, "new_score": new_score, "change": change}
            )
    return None


async def check_competitor_overtake_alert(
    project_id: str,
    brand_name: str,
    competitor_name: str,
    brand_score: float,
    competitor_score: float
) -> Optional[Dict[str, Any]]:
    """Check if a competitor has overtaken the brand"""
    if competitor_score > brand_score:
        return create_alert(
            project_id=project_id,
            alert_type=AlertType.COMPETITOR_OVERTAKE,
            severity=AlertSeverity.WARNING,
            title=f"{competitor_name} vous dépasse",
            message=f"{competitor_name} ({competitor_score:.0f}) a dépassé {brand_name} ({brand_score:.0f}) en visibilité GEO.",
            data={
                "brand_name": brand_name,
                "brand_score": brand_score,
                "competitor_name": competitor_name,
                "competitor_score": competitor_score,
                "gap": competitor_score - brand_score
            }
        )
    return None


async def check_visibility_drop_alert(
    project_id: str,
    current_score: float,
    threshold: int = 30
) -> Optional[Dict[str, Any]]:
    """Check if visibility has dropped below threshold"""
    if current_score < threshold:
        return create_alert(
            project_id=project_id,
            alert_type=AlertType.VISIBILITY_DROP,
            severity=AlertSeverity.CRITICAL,
            title="Visibilité GEO critique",
            message=f"Votre score GEO ({current_score:.0f}) est en dessous du seuil critique ({threshold}). Actions urgentes requises.",
            data={"current_score": current_score, "threshold": threshold}
        )
    return None


def generate_weekly_summary(
    project_id: str,
    brand_name: str,
    current_score: float,
    score_change: float,
    analyses_count: int,
    top_queries: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Generate a weekly summary alert"""
    trend = "hausse" if score_change > 0 else "baisse" if score_change < 0 else "stable"
    
    return create_alert(
        project_id=project_id,
        alert_type=AlertType.WEEKLY_SUMMARY,
        severity=AlertSeverity.INFO,
        title=f"Résumé hebdomadaire - {brand_name}",
        message=f"Score GEO: {current_score:.0f}/100 ({score_change:+.0f} pts). {analyses_count} analyses effectuées cette semaine.",
        data={
            "current_score": current_score,
            "score_change": score_change,
            "trend": trend,
            "analyses_count": analyses_count,
            "top_queries": top_queries[:5]
        }
    )


# ================== ENDPOINTS ==================

@router.get("/alerts/{project_id}")
async def get_project_alerts(
    project_id: str,
    limit: int = 50,
    unread_only: bool = False,
    user: dict = Depends(get_current_user)
):
    """Get alerts for a project"""
    async with async_session_maker() as db:
        # Verify project belongs to user
        project = await ProjectService.get_by_id(db, project_id)
        if not project or project.user_id != user["user_id"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    alerts = alert_history.get(project_id, [])
    
    if unread_only:
        alerts = [a for a in alerts if not a.get("read", False)]
    
    return {
        "alerts": alerts[:limit],
        "total": len(alerts),
        "unread_count": len([a for a in alerts if not a.get("read", False)])
    }


@router.post("/alerts/{project_id}/mark-read")
async def mark_alerts_read(
    project_id: str,
    alert_ids: List[str] = None,
    user: dict = Depends(get_current_user)
):
    """Mark alerts as read"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        if not project or project.user_id != user["user_id"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    alerts = alert_history.get(project_id, [])
    marked_count = 0
    
    for alert in alerts:
        if alert_ids is None or alert["alert_id"] in alert_ids:
            if not alert.get("read", False):
                alert["read"] = True
                marked_count += 1
    
    return {"marked_count": marked_count}


@router.get("/config/{project_id}")
async def get_alert_config(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    """Get alert configuration for a project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        if not project or project.user_id != user["user_id"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    config = alert_configs.get(project_id, get_default_alert_config(project_id))
    return config


@router.put("/config/{project_id}")
async def update_alert_config(
    project_id: str,
    config: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """Update alert configuration for a project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        if not project or project.user_id != user["user_id"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Merge with existing config
    existing = alert_configs.get(project_id, get_default_alert_config(project_id))
    existing.update(config)
    alert_configs[project_id] = existing
    
    return existing


@router.post("/test-alert/{project_id}")
async def send_test_alert(
    project_id: str,
    alert_type: AlertType = AlertType.SCORE_CHANGE,
    user: dict = Depends(get_current_user)
):
    """Send a test alert for a project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        if not project or project.user_id != user["user_id"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Create test alert based on type
    if alert_type == AlertType.SCORE_CHANGE:
        alert = create_alert(
            project_id=project_id,
            alert_type=AlertType.SCORE_CHANGE,
            severity=AlertSeverity.SUCCESS,
            title="[TEST] Score GEO en hausse de +15 points",
            message="Ceci est un test d'alerte. Votre score GEO serait passé de 45 à 60.",
            data={"old_score": 45, "new_score": 60, "change": 15, "is_test": True}
        )
    elif alert_type == AlertType.COMPETITOR_OVERTAKE:
        alert = create_alert(
            project_id=project_id,
            alert_type=AlertType.COMPETITOR_OVERTAKE,
            severity=AlertSeverity.WARNING,
            title="[TEST] Un concurrent vous dépasse",
            message="Ceci est un test d'alerte. Un concurrent aurait dépassé votre marque.",
            data={"is_test": True}
        )
    elif alert_type == AlertType.VISIBILITY_DROP:
        alert = create_alert(
            project_id=project_id,
            alert_type=AlertType.VISIBILITY_DROP,
            severity=AlertSeverity.CRITICAL,
            title="[TEST] Visibilité GEO critique",
            message="Ceci est un test d'alerte. Votre visibilité serait en dessous du seuil critique.",
            data={"is_test": True}
        )
    else:
        alert = create_alert(
            project_id=project_id,
            alert_type=alert_type,
            severity=AlertSeverity.INFO,
            title=f"[TEST] Alerte {alert_type.value}",
            message="Ceci est un test d'alerte.",
            data={"is_test": True}
        )
    
    return {"alert": alert, "message": "Alerte de test envoyée"}


@router.get("/summary/{project_id}")
async def get_monitoring_summary(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    """Get monitoring summary for a project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        if not project or project.user_id != user["user_id"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    alerts = alert_history.get(project_id, [])
    config = alert_configs.get(project_id, get_default_alert_config(project_id))
    
    # Count alerts by type and severity
    alerts_by_type = {}
    alerts_by_severity = {}
    
    for alert in alerts:
        atype = alert.get("alert_type", "unknown")
        severity = alert.get("severity", "info")
        
        alerts_by_type[atype] = alerts_by_type.get(atype, 0) + 1
        alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1
    
    return {
        "project_id": project_id,
        "total_alerts": len(alerts),
        "unread_alerts": len([a for a in alerts if not a.get("read", False)]),
        "alerts_by_type": alerts_by_type,
        "alerts_by_severity": alerts_by_severity,
        "config": config,
        "last_alert": alerts[0] if alerts else None
    }


def get_default_alert_config(project_id: str) -> Dict[str, Any]:
    """Get default alert configuration"""
    return {
        "project_id": project_id,
        "alerts": {
            AlertType.SCORE_CHANGE.value: {
                "enabled": True,
                "threshold": 10,
                "channels": [AlertChannel.IN_APP.value, AlertChannel.EMAIL.value]
            },
            AlertType.COMPETITOR_OVERTAKE.value: {
                "enabled": True,
                "channels": [AlertChannel.IN_APP.value, AlertChannel.EMAIL.value]
            },
            AlertType.VISIBILITY_DROP.value: {
                "enabled": True,
                "threshold": 30,
                "channels": [AlertChannel.IN_APP.value, AlertChannel.EMAIL.value]
            },
            AlertType.WEEKLY_SUMMARY.value: {
                "enabled": True,
                "channels": [AlertChannel.EMAIL.value]
            },
            AlertType.ANALYSIS_COMPLETE.value: {
                "enabled": True,
                "channels": [AlertChannel.IN_APP.value]
            }
        },
        "email_recipients": [],
        "slack_webhook": None,
        "custom_webhook": None
    }


# ================== TRIGGER FUNCTIONS (called by analysis runner) ==================

async def trigger_analysis_complete_alert(
    project_id: str,
    analysis_id: str,
    score: float,
    brand_name: str
):
    """Trigger alert when analysis completes"""
    return create_alert(
        project_id=project_id,
        alert_type=AlertType.ANALYSIS_COMPLETE,
        severity=AlertSeverity.INFO,
        title=f"Analyse terminée - Score {score:.0f}/100",
        message=f"L'analyse GEO de {brand_name} est terminée. Consultez les résultats.",
        data={"analysis_id": analysis_id, "score": score, "brand_name": brand_name}
    )
