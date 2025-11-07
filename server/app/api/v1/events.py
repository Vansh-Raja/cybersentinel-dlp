"""
DLP Events API Endpoints
Query, filter, and manage DLP events
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
import structlog

from app.core.security import get_current_user
from app.core.database import get_mongodb

logger = structlog.get_logger()
router = APIRouter()


class DLPEvent(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    source: str
    user_email: str
    classification_score: float
    classification_labels: List[str]
    policy_id: Optional[str]
    action_taken: str
    severity: str
    file_path: Optional[str]
    destination: Optional[str]
    blocked: bool


class EventQueryParams(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[List[str]] = None
    source: Optional[List[str]] = None
    user_email: Optional[str] = None
    blocked_only: bool = False


@router.post("", status_code=status.HTTP_201_CREATED)
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a new DLP event (public endpoint for agents to submit events)
    Supports both /events and /events/ URLs
    """
    db = get_mongodb()
    
    # Prepare event document
    event_doc = {
        **event_data,
        "timestamp": datetime.utcnow(),
        "id": event_data.get("event_id") or event_data.get("id"),
    }
    
    # Insert into MongoDB
    await db.dlp_events.insert_one(event_doc)
    
    logger.info("Event created", event_id=event_doc.get("id"), agent_id=event_data.get("agent_id"))
    
    return {"status": "success", "event_id": event_doc.get("id")}


@router.get("", response_model=List[DLPEvent])
@router.get("/", response_model=List[DLPEvent])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    severity: Optional[str] = None,
    source: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    """
    Get DLP events with pagination and filtering
    """
    db = get_mongodb()

    # Build query filter
    query_filter = {}
    if severity:
        query_filter["severity"] = severity
    if source:
        query_filter["source"] = source

    # Query MongoDB
    cursor = db.dlp_events.find(query_filter).sort("timestamp", -1).skip(skip).limit(limit)
    raw_events = await cursor.to_list(length=limit)

    # Transform MongoDB documents to match DLPEvent model
    events = []
    for event_doc in raw_events:
        # Convert agent event format to DLPEvent format
        transformed_event = {
            "id": event_doc.get("id") or event_doc.get("event_id", ""),
            "timestamp": event_doc.get("timestamp", datetime.utcnow()),
            "event_type": event_doc.get("event_type", "unknown"),
            "source": event_doc.get("source") or event_doc.get("source_type", "unknown"),
            "user_email": event_doc.get("user_email", ""),
            "classification_score": event_doc.get("classification", {}).get("score", 0.0) if isinstance(event_doc.get("classification"), dict) else event_doc.get("classification_score", 0.0),
            "classification_labels": event_doc.get("classification", {}).get("labels", []) if isinstance(event_doc.get("classification"), dict) else event_doc.get("classification_labels", []),
            "policy_id": event_doc.get("policy_id"),
            "action_taken": event_doc.get("action_taken") or event_doc.get("action", "logged"),
            "severity": event_doc.get("severity", "low"),
            "file_path": event_doc.get("file_path"),
            "destination": event_doc.get("destination"),
            "blocked": event_doc.get("blocked", False) or (event_doc.get("action") == "blocked"),
        }
        events.append(transformed_event)

    logger.info(
        "Events queried",
        user=current_user["email"],
        count=len(events),
        filters=query_filter,
    )

    return events


@router.get("/{event_id}", response_model=DLPEvent)
async def get_event(
    event_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get specific DLP event by ID
    """
    db = get_mongodb()
    event = await db.dlp_events.find_one({"id": event_id})

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


@router.get("/stats/summary")
async def get_event_stats(
    current_user: dict = Depends(get_current_user),
):
    """
    Get event statistics summary
    """
    db = get_mongodb()

    # Aggregate statistics
    total_events = await db.dlp_events.count_documents({})
    blocked_events = await db.dlp_events.count_documents({"blocked": True})

    # Events by severity
    severity_pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    severity_stats = await db.dlp_events.aggregate(severity_pipeline).to_list(None)

    # Events by source
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    source_stats = await db.dlp_events.aggregate(source_pipeline).to_list(None)

    return {
        "total_events": total_events,
        "blocked_events": blocked_events,
        "by_severity": {item["_id"]: item["count"] for item in severity_stats},
        "by_source": {item["_id"]: item["count"] for item in source_stats},
    }
