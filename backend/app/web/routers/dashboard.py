"""Dashboard summary endpoints for MISIX frontend."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
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

    def _fetch_limited(table: str, *, select: str = "*", limit: int = 5, order: str | None = None, desc: bool = True):
        query = supabase.table(table).select(select, count="exact").eq("user_id", user_id)
        if order:
            query = query.order(order, desc=desc)
        if limit:
            query = query.limit(limit)
        result = query.execute()
        items = result.data or []
        total = getattr(result, "count", None)
        if total is None:
            total = len(items)
        return items, total

    try:
        tasks, tasks_total = _fetch_limited("tasks", order="created_at", limit=5)
        notes, notes_total = _fetch_limited("notes", order="created_at", limit=5)
        finances, finances_total = _fetch_limited("finance_transactions", order="transaction_date", desc=True, limit=5)
        debts, debts_total = _fetch_limited("finance_debts", order="due_date", desc=False, limit=5)
        reminders, reminders_total = _fetch_limited("reminders", order="reminder_time", desc=False, limit=5)

        sleep_sessions, _ = _fetch_limited("sleep_sessions", order="created_at", desc=True, limit=5)
        health_metrics, _ = _fetch_limited("health_metrics", order="recorded_at", desc=True, limit=50)
        personal_entries, personal_total = _fetch_limited("personal_data_entries", order="created_at", desc=True, limit=5)
        messages, _ = _fetch_limited("assistant_messages", order="created_at", desc=True, limit=20)

        # Task stats
        task_status_resp = supabase.table("tasks").select("status").eq("user_id", user_id).execute()
        task_statuses = Counter(item.get("status", "new") for item in (task_status_resp.data or []))
        task_open = task_statuses.get("new", 0) + task_statuses.get("in_progress", 0) + task_statuses.get("waiting", 0)
        task_completed = task_statuses.get("completed", 0)

        # Finance summaries
        finance_all = supabase.table("finance_transactions").select("amount,type").eq("user_id", user_id).execute()
        total_income = 0.0
        total_expense = 0.0
        for item in finance_all.data or []:
            amount = float(item.get("amount") or 0)
            if item.get("type") == "income":
                total_income += amount
            else:
                total_expense += amount
        finance_balance = total_income - total_expense

        # Debt summaries
        debt_all = supabase.table("finance_debts").select("amount,status").eq("user_id", user_id).execute()
        open_debt_amount = 0.0
        open_debt_count = 0
        for item in debt_all.data or []:
            if item.get("status") in {"pending", "overdue"}:
                open_debt_count += 1
                open_debt_amount += float(item.get("amount") or 0)

        # Reminder summaries
        reminder_all = supabase.table("reminders").select("status,reminder_time").eq("user_id", user_id).execute()
        scheduled_count = 0
        next_reminder_time: datetime | None = None
        for item in reminder_all.data or []:
            if item.get("status") == "scheduled":
                scheduled_count += 1
                raw_time = item.get("reminder_time")
                if raw_time:
                    try:
                        parsed = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
                        if not next_reminder_time or parsed < next_reminder_time:
                            next_reminder_time = parsed
                    except ValueError:
                        continue

        overview = {
            "tasks": {
                "total": tasks_total,
                "open": task_open,
                "completed": task_completed,
            },
            "notes": {
                "total": notes_total,
            },
            "finances": {
                "total": finances_total,
                "income": total_income,
                "expense": total_expense,
                "balance": finance_balance,
            },
            "debts": {
                "total": debts_total,
                "openCount": open_debt_count,
                "openAmount": open_debt_amount,
            },
            "reminders": {
                "total": reminders_total,
                "scheduled": scheduled_count,
                "next": next_reminder_time.isoformat() if next_reminder_time else None,
            },
            "personal": {
                "total": personal_total,
            },
        }

        return {
            "tasks": tasks,
            "notes": notes,
            "finances": finances,
            "debts": debts,
            "reminders": reminders,
            "sleepSessions": sleep_sessions,
            "healthMetrics": health_metrics,
            "personalEntries": personal_entries,
            "messages": messages,
            "overview": overview,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {exc}") from exc
