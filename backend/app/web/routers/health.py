"""Health metrics API endpoints for MISIX backend."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.shared.supabase import get_supabase_client
from app.web.auth import get_current_user_id

router = APIRouter()


class HealthMetricBase(BaseModel):
    metric_type: str = Field(..., description="Тип показателя, например weight, pulse, sleep")
    metric_value: float = Field(..., description="Значение показателя")
    unit: Optional[str] = Field(None, description="Единица измерения, например kg, bpm, hours")
    recorded_at: Optional[datetime] = Field(None, description="Дата и время измерения")
    note: Optional[str] = Field(None, description="Дополнительная заметка")


class HealthMetric(HealthMetricBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


@router.get("/health/metrics", response_model=List[HealthMetric])
async def get_health_metrics(
    metric_type: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user_id),
) -> List[HealthMetric]:
    """Get health metrics for a user with optional filtering."""
    supabase = get_supabase_client()

    query = (
        supabase
        .table("health_metrics")
        .select("*")
        .eq("user_id", user_id)
        .order("recorded_at", desc=True)
        .limit(max(1, min(limit, 200)))
    )

    if metric_type:
        query = query.eq("metric_type", metric_type)

    response = query.execute()
    return response.data or []


@router.post("/health/metrics", response_model=HealthMetric)
async def create_health_metric(
    metric: HealthMetricBase,
    user_id: str = Depends(get_current_user_id),
) -> HealthMetric:
    """Store a new health metric entry."""
    supabase = get_supabase_client()

    payload = {
        "user_id": user_id,
        "metric_type": metric.metric_type.lower(),
        "metric_value": metric.metric_value,
        "unit": metric.unit,
        "recorded_at": metric.recorded_at.isoformat() if metric.recorded_at else datetime.utcnow().isoformat(),
        "note": metric.note,
    }

    response = supabase.table("health_metrics").insert(payload).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create health metric")

    return response.data[0]


@router.delete("/health/metrics/{metric_id}")
async def delete_health_metric(metric_id: str, user_id: str = Depends(get_current_user_id)) -> dict[str, str]:
    """Delete a health metric by ID."""
    supabase = get_supabase_client()

    response = (
        supabase
        .table("health_metrics")
        .delete()
        .eq("user_id", user_id)
        .eq("id", metric_id)
        .execute()
    )

    if response.data is None:
        raise HTTPException(status_code=404, detail="Health metric not found")

    return {"status": "deleted"}
