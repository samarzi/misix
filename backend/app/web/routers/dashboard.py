"""Dashboard summary endpoints for MISIX frontend."""

from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException

from app.shared.supabase import get_supabase_client

router = APIRouter()
logger = logging.getLogger(__name__)


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
        try:
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
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch %s for dashboard: %s", table, exc)
            return [], 0

    def _safe_select_all(table: str, columns: str = "*") -> list[dict]:
        try:
            response = (
                supabase
                .table(table)
                .select(columns)
                .eq("user_id", user_id)
                .execute()
            )
            return response.data or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to select from %s for dashboard: %s", table, exc)
            return []

    def _select_since(
        table: str,
        timestamp_column: str,
        since_iso: str,
        *,
        columns: str = "*",
    ) -> list[dict]:
        try:
            response = (
                supabase
                .table(table)
                .select(columns)
                .eq("user_id", user_id)
                .gte(timestamp_column, since_iso)
                .execute()
            )
            return response.data or []
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to select recent rows from %s: %s", table, exc)
            return []

    try:
        tasks, tasks_total = _fetch_limited("tasks", order="created_at", limit=5)
        notes, notes_total = _fetch_limited("notes", order="created_at", limit=5)
        finances, finances_total = _fetch_limited("finance_transactions", order="transaction_date", desc=True, limit=5)
        debts, debts_total = _fetch_limited("finance_debts", order="due_date", desc=False, limit=5)
        reminders, reminders_total = _fetch_limited("reminders", order="reminder_time", desc=False, limit=5)

        sleep_sessions, _ = _fetch_limited("sleep_sessions", order="created_at", desc=True, limit=5)
        health_metrics, _ = _fetch_limited("health_metrics", order="recorded_at", desc=True, limit=50)
        personal_entries, personal_total = _fetch_limited("personal_data_entries", order="created_at", desc=True, limit=5)
        personal_categories_raw = _safe_select_all(
            "personal_data_categories",
            "id,name,description,color,icon,is_confidential,sort_order"
        )
        personal_categories = sorted(
            personal_categories_raw,
            key=lambda row: ((row.get("sort_order") or 0), (row.get("name") or ""))
        )
        messages, _ = _fetch_limited("assistant_messages", order="created_at", desc=True, limit=20)

        finance_categories_raw = _safe_select_all(
            "finance_categories",
            "id,name,type,color,icon,parent_id,is_default,sort_order"
        )
        finance_accounts = _safe_select_all(
            "finance_accounts",
            "id,name,account_type,currency,balance,color,icon,is_archived,sort_order"
        )
        finance_category_rules = _safe_select_all(
            "finance_category_rules",
            "id,match_type,match_pattern,category_id,confidence,is_active"
        )

        # Task stats
        task_status_rows = _safe_select_all("tasks", "status")
        task_statuses = Counter(item.get("status", "new") for item in task_status_rows)
        task_open = task_statuses.get("new", 0) + task_statuses.get("in_progress", 0) + task_statuses.get("waiting", 0)
        task_completed = task_statuses.get("completed", 0)

        # Finance summaries
        finance_all = _safe_select_all("finance_transactions", "amount,type,category_id")
        total_income = 0.0
        total_expense = 0.0
        category_totals: dict[str, dict[str, float]] = {}
        for item in finance_all:
            amount = float(item.get("amount") or 0)
            if item.get("type") == "income":
                total_income += amount
                category_id = item.get("category_id")
                if category_id:
                    bucket = category_totals.setdefault(category_id, {"income": 0.0, "expense": 0.0})
                    bucket["income"] += amount
            else:
                total_expense += amount
                category_id = item.get("category_id")
                if category_id:
                    bucket = category_totals.setdefault(category_id, {"income": 0.0, "expense": 0.0})
                    bucket["expense"] += amount
        finance_balance = total_income - total_expense

        finance_categories = []
        for category in sorted(finance_categories_raw, key=lambda row: (row.get("sort_order") or 0, row.get("name") or "")):
            totals = category_totals.get(category.get("id"), {"income": 0.0, "expense": 0.0})
            finance_categories.append(
                {
                    "id": category.get("id"),
                    "name": category.get("name"),
                    "type": category.get("type"),
                    "color": category.get("color"),
                    "icon": category.get("icon"),
                    "parent_id": category.get("parent_id"),
                    "is_default": category.get("is_default", False),
                    "sort_order": category.get("sort_order", 0),
                    "total_income": round(totals.get("income", 0.0), 2),
                    "total_expense": round(totals.get("expense", 0.0), 2),
                }
            )

        # Debt summaries
        debt_all = _safe_select_all("finance_debts", "amount,status")
        open_debt_amount = 0.0
        open_debt_count = 0
        for item in debt_all:
            if item.get("status") in {"pending", "overdue"}:
                open_debt_count += 1
                open_debt_amount += float(item.get("amount") or 0)

        # Reminder summaries
        reminder_all = _safe_select_all("reminders", "status,reminder_time")
        scheduled_count = 0
        next_reminder_time: datetime | None = None
        for item in reminder_all:
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

        now_utc = datetime.now(timezone.utc)
        seven_days_ago = now_utc - timedelta(days=7)
        since_iso = seven_days_ago.isoformat()

        recent_tasks = _select_since(
            "tasks",
            "created_at",
            since_iso,
            columns="status,created_at",
        )
        tasks_created_last7 = len(recent_tasks)
        tasks_completed_last7 = sum(1 for item in recent_tasks if item.get("status") == "completed")

        recent_transactions = _select_since(
            "finance_transactions",
            "transaction_date",
            since_iso,
            columns="amount,type,category_id,transaction_date",
        )
        income_last7 = 0.0
        expense_last7 = 0.0
        category_totals_last7: dict[str | None, float] = {}
        for item in recent_transactions:
            amount = float(item.get("amount") or 0)
            if item.get("type") == "income":
                income_last7 += amount
            else:
                expense_last7 += amount
            key = item.get("category_id")
            category_totals_last7[key] = category_totals_last7.get(key, 0.0) + amount

        recent_personal_entries = _select_since(
            "personal_data_entries",
            "created_at",
            since_iso,
            columns="is_favorite,is_confidential,created_at",
        )
        personal_created_last7 = len(recent_personal_entries)
        personal_favorites = sum(1 for item in recent_personal_entries if item.get("is_favorite"))

        reminder_upcoming_count = 0
        reminder_horizon = now_utc + timedelta(days=7)
        for item in reminder_all:
            if item.get("status") != "scheduled":
                continue
            raw_time = item.get("reminder_time")
            if not raw_time:
                continue
            try:
                parsed = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
            except ValueError:
                continue
            if now_utc <= parsed <= reminder_horizon:
                reminder_upcoming_count += 1

        top_category_entries = []
        for category in finance_categories:
            total = category_totals_last7.get(category.get("id"), 0.0)
            if total:
                top_category_entries.append(
                    {
                        "category_id": category.get("id"),
                        "category_name": category.get("name"),
                        "total": round(total, 2),
                    }
                )
        uncategorized_total = category_totals_last7.get(None, 0.0)
        if uncategorized_total:
            top_category_entries.append(
                {
                    "category_id": None,
                    "category_name": "Без категории",
                    "total": round(uncategorized_total, 2),
                }
            )
        top_category_entries.sort(key=lambda item: item["total"], reverse=True)
        top_categories_last7 = top_category_entries[:5]

        statistics = {
            "tasks": {
                "createdLast7": tasks_created_last7,
                "completedLast7": tasks_completed_last7,
            },
            "finances": {
                "incomeLast7": round(income_last7, 2),
                "expenseLast7": round(expense_last7, 2),
                "topCategoriesLast7": top_categories_last7,
            },
            "personal": {
                "createdLast7": personal_created_last7,
                "favorites": personal_favorites,
            },
            "reminders": {
                "upcoming7Days": reminder_upcoming_count,
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
            "personalCategories": personal_categories,
            "messages": messages,
            "financeCategories": finance_categories,
            "financeAccounts": finance_accounts,
            "financeCategoryRules": finance_category_rules,
            "overview": overview,
            "statistics": statistics,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard data: {exc}") from exc
