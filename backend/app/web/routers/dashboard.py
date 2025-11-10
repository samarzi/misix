"""Dashboard summary endpoints for MISIX frontend."""

from __future__ import annotations

import re
from fastapi import APIRouter, HTTPException

from app.shared.supabase import get_supabase_client

router = APIRouter()


@router.get("/dashboard/summary")
async def get_dashboard_summary(user_id: str):
    """Return aggregated dashboard data for the given user."""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # Validate user_id is a valid UUID
    uuid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    if not re.match(uuid_pattern, user_id):
        raise HTTPException(status_code=400, detail="user_id must be a valid UUID")

    supabase = get_supabase_client()

    def _table(table: str, *, select: str = "*", limit: int = 10, order: str | None = None, desc: bool = True):
        query = supabase.table(table).select(select).eq("user_id", user_id)
        if order:
            query = query.order(order, desc=desc)
        if limit:
            query = query.limit(limit)
        result = query.execute()
        return result.data or []

    try:
        tasks = _table("tasks", order="created_at", limit=10)
        notes = _table("notes", order="created_at", limit=10)
        finances = _table("finance_transactions", order="transaction_date", limit=10)
        sleep_sessions = _table("sleep_sessions", order="created_at", limit=10)
        health_metrics = _table("health_metrics", order="recorded_at", limit=50)
        personal_entries = _table("personal_data_entries", order="created_at", limit=10)
        messages = _table("assistant_messages", order="created_at", limit=50)

        return {
            "tasks": tasks,
            "notes": notes,
            "finances": finances,
            "sleepSessions": sleep_sessions,
            "healthMetrics": health_metrics,
            "personalEntries": personal_entries,
            "messages": messages,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {exc}") from exc
