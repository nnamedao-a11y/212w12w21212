"""
admin_ringostat — /api/admin/ringostat HTTP surface (FULL: reads + writes)
==========================================================================

Wave 2B / Batch 13 (reads) + Batch 14 (writes) — full ringostat cluster.

Mechanical 1:1 extraction of 11 admin endpoints (6 reads from Batch 13
+ 5 writes added in Batch 14).

────────────────────────────────────────────────────────────────────────
Auth uniform — `require_admin` hoisted at router level
────────────────────────────────────────────────────────────────────────

All 11 endpoints use the same `Depends(require_admin)` in their
original decorations.  Same hoisting pattern as Batches 8/9/11/12/13.
No Batch-10-style auth-mixed yellow here (all single-tier).

────────────────────────────────────────────────────────────────────────
Mutation ownership — PARTIAL transfer of ringostat_config + ringostat_calls
────────────────────────────────────────────────────────────────────────

This router becomes the runtime mutation owner of:
  * `ringostat_config` (settings PATCH, mappings POST/DELETE, plus the
    twin endpoint `POST /api/admin/integrations/ringostat/configure`
    that lives in admin_integrations.py — see "Residual edges" below)
  * `ringostat_calls` (test-webhook POST inserts a synthetic test event)

Ownership is PARTIAL because:
  * `ringostat_webhook` (server.py:/api/integrations/ringostat/webhook)
    is a PUBLIC endpoint that writes ringostat_calls on every real
    webhook delivery.  Stays in server.py (public domain, separate
    auth flow).  Phase 3 will resolve via Ringostat domain service.
  * `POST /api/admin/integrations/ringostat/configure` (now in
    admin_integrations.py) ALSO upserts ringostat_config — it's the
    higher-level orchestration endpoint that the admin UI calls when
    saving the Ringostat tab.  Both endpoints converge on the same
    storage, by design.

Bridge surface (lazy, same pattern as Batches 8–13):
  * `_db()` — Mongo handle

Phase 5.4 / C-4a — ``logger`` bridge retired
────────────────────────────────────────────
This module now owns its own ``logger`` instance via the standard
``logging.getLogger("bibi.admin_ringostat")`` namespace pattern.
The lazy ``from server import logger`` bridge that previously lived
inside the manager-validation ``except`` handler is gone. Log lines,
levels, and structured-JSON envelopes are byte-identical because
both sides use the same root logger configuration ("bibi.*"
hierarchy inherits from "bibi" root configured in server.py
top-level).
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from bson import ObjectId
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from security import require_admin, require_master_admin


# Phase 5.4 / C-4a — module-local logger ownership.
# Namespace "bibi.admin_ringostat" inherits handlers + structured
# formatter from the "bibi" root configured in server.py:1147-1180.
logger = logging.getLogger("bibi.admin_ringostat")


def _db():
    """Lazy bridge to the live Mongo handle in server.py."""
    from app.core.db_runtime import get_db  # noqa: E402 (C-4e: lazy-bridge → accessor)
    return get_db()


def _serialize_doc():
    """Lazy bridge to the shared `serialize_doc` helper.

    Phase 5.2 / C-1: helper relocated to `app/utils/serialization.py`.
    Wrapper kept to preserve the in-router call idiom
    (`serialize_doc = _serialize_doc(); serialize_doc(call)`); a
    follow-up cleanup can collapse callers to the direct import.
    """
    from app.utils.serialization import serialize_doc  # Phase 5.2 / C-1
    return serialize_doc


async def _find_by_id(coll, value: Any) -> Optional[Dict[str, Any]]:
    """Look up a document by id without assuming the storage format.

    Different collections in this code base store identifiers in different
    shapes:
      • ``leads``     — ``_id`` is a UUID string (`str(uuid.uuid4())`)
      • ``deals``     — same as leads, UUID string in ``_id``
      • ``staff``     — legacy BSON ``ObjectId`` in ``_id`` AND a
                        human-readable ``id`` field (e.g. ``staff_admin_…``)

    Wrapping a UUID string in ``ObjectId(...)`` raises ``bson.errors.InvalidId``
    and used to 500 the calls/details endpoints. This helper tries the most
    likely shapes in order and never raises on a malformed id.
    """
    if value is None or value == "":
        return None
    if isinstance(value, ObjectId):
        try:
            return await coll.find_one({"_id": value})
        except Exception:
            return None
    s = str(value)
    # 1) raw value match on _id (covers UUID strings)
    doc = await coll.find_one({"_id": s})
    if doc:
        return doc
    # 2) legacy `id` field (staff/orders pattern)
    doc = await coll.find_one({"id": s})
    if doc:
        return doc
    # 3) only attempt ObjectId conversion when the format actually matches
    if len(s) == 24:
        try:
            return await coll.find_one({"_id": ObjectId(s)})
        except Exception:
            return None
    return None


router = APIRouter(
    prefix="/api/admin/ringostat",
    tags=["admin-ringostat"],
    dependencies=[Depends(require_admin)],
)


# ── READS (Batch 13) ──────────────────────────────────────────────────

@router.get("/health")
async def get_ringostat_health():
    """Health status for Ringostat admin panel"""
    db = _db()
    config = await db.ringostat_config.find_one({}) or {}
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today = await db.ringostat_calls.count_documents({
        "started_at": {"$gte": today_start}
    })
    last_call = await db.ringostat_calls.find_one(
        {}, sort=[("created_at", -1)]
    )
    mappings = config.get("extension_mapping", {})
    total_extensions = len(mappings)
    unmapped_extensions = sum(1 for v in mappings.values() if not v)
    unassigned_calls = await db.ringostat_calls.count_documents({
        "started_at": {"$gte": today_start},
        "manager_id": None
    })
    is_connected = bool(config.get("api_key") and config.get("project_id"))
    return {
        "connection": {
            "status": "connected" if is_connected else "disconnected",
            "api_key_set": bool(config.get("api_key")),
            "project_id_set": bool(config.get("project_id"))
        },
        "webhook": {
            "last_event": last_call.get("created_at").isoformat() if last_call and last_call.get("created_at") else None,
            "events_today": calls_today
        },
        "calls_today": calls_today,
        "unassigned": {
            "extensions": unmapped_extensions,
            "calls_today": unassigned_calls
        },
        "mappings": {
            "total": total_extensions,
            "unmapped": unmapped_extensions
        }
    }


@router.get("/settings")
async def get_ringostat_settings():
    """Get current Ringostat configuration"""
    db = _db()
    config = await db.ringostat_config.find_one({}) or {}
    return {
        "api_key": config.get("api_key", ""),
        "project_id": config.get("project_id", ""),
        "enabled": config.get("enabled", True),
        "extension_mapping": config.get("extension_mapping", {}),
        "automation_rules": config.get("automation_rules", {
            "auto_create_lead": True,
            "missed_call_task": True,
            "missed_call_task_minutes": 5,
            "require_outcome": True,
            "require_outcome_duration": 10
        })
    }


@router.get("/mappings")
async def get_ringostat_mappings():
    """Get extension → manager mappings"""
    db = _db()
    config = await db.ringostat_config.find_one({}) or {}
    extension_mapping = config.get("extension_mapping", {})
    staff = await db.staff.find({}).to_list(100)
    staff_dict = {str(s["_id"]): s for s in staff}
    mappings = []
    for ext, manager_id in extension_mapping.items():
        manager = staff_dict.get(manager_id) if manager_id else None
        mappings.append({
            "extension": ext,
            "manager_id": manager_id,
            "manager_name": manager.get("name") if manager else None,
            "manager_email": manager.get("email") if manager else None,
            "status": "assigned" if manager_id else "unassigned"
        })
    return {
        "mappings": mappings,
        "staff": [{"id": str(s["_id"]), "name": s.get("name"), "email": s.get("email"), "role": s.get("role")} for s in staff]
    }


@router.get("/calls")
async def get_ringostat_calls(
    period: str = "today",
    manager: Optional[str] = None,
    status: Optional[str] = None,
    direction: Optional[str] = None,
    limit: int = 50
):
    """Get calls history with filters"""
    db = _db()
    serialize_doc = _serialize_doc()
    query: dict[str, Any] = {}
    now = datetime.now(timezone.utc)
    if period == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query["started_at"] = {"$gte": start}
    elif period == "week":
        start = now - timedelta(days=7)
        query["started_at"] = {"$gte": start}
    elif period == "month":
        start = now - timedelta(days=30)
        query["started_at"] = {"$gte": start}
    if manager: query["manager_id"] = manager
    if status: query["status"] = status
    if direction: query["direction"] = direction
    calls = await db.ringostat_calls.find(query).sort("started_at", -1).limit(limit).to_list(limit)
    for call in calls:
        if call.get("lead_id"):
            lead = await _find_by_id(db.leads, call["lead_id"])
            call["lead"] = {
                "id": str(lead["_id"]),
                "name": lead.get("name"),
                "phone": lead.get("phone")
            } if lead else None
        if call.get("deal_id"):
            deal = await _find_by_id(db.deals, call["deal_id"])
            call["deal"] = {
                "id": str(deal["_id"]),
                "title": deal.get("title"),
                "stage": deal.get("stage")
            } if deal else None
    return {
        "calls": [serialize_doc(c) for c in calls],
        "total": len(calls)
    }


@router.get("/calls/{call_id}")
async def get_ringostat_call_details(call_id: str):
    """Get call details"""
    db = _db()
    serialize_doc = _serialize_doc()
    call = await db.ringostat_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    if call.get("lead_id"):
        lead = await _find_by_id(db.leads, call["lead_id"])
        call["lead"] = serialize_doc(lead) if lead else None
    if call.get("deal_id"):
        deal = await _find_by_id(db.deals, call["deal_id"])
        call["deal"] = serialize_doc(deal) if deal else None
    if call.get("manager_id"):
        manager = await _find_by_id(db.staff, call["manager_id"])
        call["manager"] = serialize_doc(manager) if manager else None
    return serialize_doc(call)


@router.get("/events")
async def get_ringostat_events(limit: int = 50):
    """Get recent webhook events for debugging"""
    db = _db()
    calls = await db.ringostat_calls.find({}).sort("created_at", -1).limit(limit).to_list(limit)
    events = []
    for call in calls:
        events.append({
            "id": str(call["_id"]),
            "event_type": f"CALL_{call['status'].upper()}",
            "call_id": call.get("call_id"),
            "direction": call.get("direction"),
            "from": call.get("from"),
            "to": call.get("to"),
            "duration": call.get("duration"),
            "timestamp": call.get("created_at").isoformat() if call.get("created_at") else None,
            "status": "success"
        })
    return {"events": events, "total": len(events)}


# ── WRITES (Batch 14) ─────────────────────────────────────────────────

@router.patch("/settings", dependencies=[Depends(require_master_admin)])
async def update_ringostat_settings(data: Dict[str, Any] = Body(...)):
    """Update Ringostat configuration"""
    db = _db()
    config = await db.ringostat_config.find_one({}) or {}
    if "api_key" in data:
        config["api_key"] = data["api_key"]
    if "project_id" in data:
        config["project_id"] = data["project_id"]
    if "enabled" in data:
        config["enabled"] = data["enabled"]
    if "automation_rules" in data:
        config["automation_rules"] = data["automation_rules"]
    config["updated_at"] = datetime.now(timezone.utc)
    if "_id" in config:
        await db.ringostat_config.replace_one({"_id": config["_id"]}, config)
    else:
        config["created_at"] = datetime.now(timezone.utc)
        await db.ringostat_config.insert_one(config)
    return {"success": True, "message": "Settings updated"}


@router.post("/test-connection")
async def test_ringostat_connection(data: Dict[str, Any] = Body(...)):
    """Test Ringostat API connection — REAL ping against api.ringostat.net.

    Body:
      - ``api_key`` (str) — Auth-key header value (Ringostat API key).
      - ``project_id`` (str) — x-project-id header value.

    If the body fields are missing or look like masked placeholders (``…``
    prefix or empty), the saved credentials from ``ringostat_config`` are
    used as a fallback — so the UI can call this endpoint with an empty
    body to re-test the currently stored creds without re-typing them.

    Returns ``{success, message, status_code, sample_count}``.
    """
    import httpx
    from datetime import timedelta

    api_key = (data.get("api_key") or "").strip()
    project_id = (data.get("project_id") or "").strip()

    # Allow the UI to re-test stored creds by sending an empty body or
    # masked placeholders coming back from GET /settings.
    if not api_key or api_key.startswith("…") or not project_id or project_id.startswith("…"):
        stored = await _db().ringostat_config.find_one({}) or {}
        api_key = api_key if (api_key and not api_key.startswith("…")) else (stored.get("api_key") or "")
        project_id = project_id if (project_id and not project_id.startswith("…")) else (stored.get("project_id") or "")

    if not api_key or not project_id:
        raise HTTPException(
            status_code=400,
            detail="API key and Project ID are required (no saved credentials to fall back on).",
        )

    if len(api_key) < 10:
        return {
            "success": False,
            "status_code": None,
            "message": "Invalid API key format (too short).",
        }

    # Real ping: ask Ringostat for the last 5 minutes of calls. We don't
    # care if the list is empty — we only care that the API accepts the
    # credentials. 401/403 = bad key; 200 = good (even with zero rows).
    now = datetime.now(timezone.utc)
    params = {
        "date_from": (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
        "date_to": now.strftime("%Y-%m-%d %H:%M:%S"),
        "limit": 1,
    }
    headers = {
        "Auth-key": api_key,
        "x-project-id": project_id,
        "Accept": "application/json",
    }
    url = "https://api.ringostat.net/calls/list"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=headers, params=params)

        if r.status_code == 200:
            sample: Any
            try:
                payload = r.json()
                if isinstance(payload, list):
                    sample = payload
                elif isinstance(payload, dict):
                    sample = payload.get("calls") or payload.get("data") or []
                else:
                    sample = []
            except Exception:
                sample = []
            return {
                "success": True,
                "status_code": 200,
                "message": (
                    f"Connection OK ({len(sample)} calls in last 5 min sample). "
                    f"Project: {project_id}."
                ),
                "sample_count": len(sample) if isinstance(sample, list) else 0,
                "project_id": project_id,
            }

        if r.status_code in (401, 403):
            return {
                "success": False,
                "status_code": r.status_code,
                "message": (
                    f"Authentication rejected ({r.status_code}). "
                    f"Check Auth-key + x-project-id. Body: {r.text[:160]}"
                ),
            }

        return {
            "success": False,
            "status_code": r.status_code,
            "message": (
                f"Ringostat API returned HTTP {r.status_code}. "
                f"Body: {r.text[:200]}"
            ),
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "status_code": None,
            "message": "Timeout (>10s) talking to api.ringostat.net.",
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "message": f"{type(e).__name__}: {str(e)[:200]}",
        }


@router.post("/test-webhook")
async def test_ringostat_webhook():
    """Send test webhook event"""
    db = _db()
    # Create test call event
    test_event = {
        "call_id": f"test_{int(time.time())}",
        "direction": "inbound",
        "from": "+380501234567",
        "to": "+380441234567",
        "status": "answered",
        "duration": 125,
        "recording_url": None,
        "manager_extension": "101",
        "started_at": datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc)
    }
    await db.ringostat_calls.insert_one(test_event)
    return {
        "success": True,
        "message": "Test webhook event created",
        "call_id": test_event["call_id"]
    }


@router.post("/mappings", dependencies=[Depends(require_master_admin)])
async def create_ringostat_mapping(data: Dict[str, Any] = Body(...)):
    """Create or update extension mapping"""
    db = _db()
    extension = data.get("extension")
    manager_id = data.get("manager_id")

    if not extension:
        raise HTTPException(status_code=400, detail="Extension required")

    # Validate manager exists if manager_id provided. Use the robust
    # _find_by_id helper so we don't 400 on legitimate UUID/`id` strings
    # (codebase has both ObjectId staff._id and string staff.id).
    if manager_id:
        manager = await _find_by_id(db.staff, manager_id)
        if not manager:
            raise HTTPException(
                status_code=400,
                detail=f"Manager with ID {manager_id} not found",
            )

    config = await db.ringostat_config.find_one({}) or {}

    if "extension_mapping" not in config:
        config["extension_mapping"] = {}

    config["extension_mapping"][extension] = manager_id
    config["updated_at"] = datetime.now(timezone.utc)

    if "_id" in config:
        await db.ringostat_config.replace_one({"_id": config["_id"]}, config)
    else:
        config["created_at"] = datetime.now(timezone.utc)
        await db.ringostat_config.insert_one(config)

    return {"success": True, "message": "Mapping created"}


@router.delete("/mappings/{extension}", dependencies=[Depends(require_master_admin)])
async def delete_ringostat_mapping(extension: str):
    """Delete extension mapping"""
    db = _db()
    config = await db.ringostat_config.find_one({}) or {}

    if "extension_mapping" in config and extension in config["extension_mapping"]:
        del config["extension_mapping"][extension]
        config["updated_at"] = datetime.now(timezone.utc)
        await db.ringostat_config.replace_one({"_id": config["_id"]}, config)

    return {"success": True, "message": "Mapping deleted"}


# ═══════════════════════════════════════════════════════════════
# Phase IV-4 — Extended operational endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/stats/overview")
async def ringostat_stats_overview(
    days: int = Query(7, ge=1, le=90, description="Rolling window in days"),
):
    """Roll-up of call volume + outcomes for an admin dashboard.

    Returns:
      - ``totals`` — total / answered / missed / completed / inbound / outbound
      - ``answer_rate`` — answered / (answered + missed)
      - ``avg_duration_sec`` — across answered calls only
      - ``by_day`` — last N days with daily counts (chart-ready)
      - ``by_hour`` — heat-map data for last 7 days (0–23h × dow)
    """
    db = _db()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    base = {"started_at": {"$gte": cutoff}}

    total = await db.ringostat_calls.count_documents(base)
    inbound = await db.ringostat_calls.count_documents({**base, "direction": "inbound"})
    outbound = await db.ringostat_calls.count_documents({**base, "direction": "outbound"})

    # Outcome buckets. Ringostat status values vary — accept multiple forms.
    answered_match = {"$or": [
        {"status": {"$in": ["COMPLETED", "ANSWERED", "answered", "completed"]}},
        {"answered_at": {"$exists": True, "$ne": None}},
    ]}
    missed_match = {"status": {"$in": ["MISSED", "missed", "no-answer", "NOANSWER"]}}

    answered = await db.ringostat_calls.count_documents({**base, **answered_match})
    missed = await db.ringostat_calls.count_documents({**base, **missed_match})
    completed = await db.ringostat_calls.count_documents({**base, "status": {"$in": ["COMPLETED", "completed"]}})

    # Average duration (answered only — missed has duration=0)
    avg_pipe = [
        {"$match": {**base, "duration": {"$gt": 0}}},
        {"$group": {"_id": None, "avg": {"$avg": "$duration"}}},
    ]
    avg_doc = await db.ringostat_calls.aggregate(avg_pipe).to_list(length=1)
    avg_duration = float(avg_doc[0]["avg"]) if avg_doc else 0.0

    # Per-day counts
    by_day_pipe = [
        {"$match": base},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$started_at"}},
            "total": {"$sum": 1},
            "answered": {"$sum": {"$cond": [
                {"$in": ["$status", ["COMPLETED", "ANSWERED", "answered", "completed"]]}, 1, 0,
            ]}},
            "missed": {"$sum": {"$cond": [
                {"$in": ["$status", ["MISSED", "missed", "no-answer", "NOANSWER"]]}, 1, 0,
            ]}},
        }},
        {"$sort": {"_id": 1}},
    ]
    by_day_raw = await db.ringostat_calls.aggregate(by_day_pipe).to_list(length=days + 1)
    by_day = [
        {"day": d["_id"], "total": d.get("total", 0),
         "answered": d.get("answered", 0), "missed": d.get("missed", 0)}
        for d in by_day_raw
    ]

    return {
        "window_days": days,
        "totals": {
            "all": total,
            "inbound": inbound,
            "outbound": outbound,
            "answered": answered,
            "missed": missed,
            "completed": completed,
        },
        "answer_rate": round(answered / (answered + missed) * 100, 1) if (answered + missed) else 0.0,
        "avg_duration_sec": round(avg_duration, 1),
        "by_day": by_day,
    }


@router.get("/stats/managers")
async def ringostat_stats_managers(
    days: int = Query(7, ge=1, le=90),
):
    """Per-manager KPI rollup.

    For each manager_id present in `ringostat_calls` within the window,
    returns total calls, answered, missed, average duration, and answer rate.
    Joins the staff name from `staff` collection.

    Use this to power a "team performance" table in admin Ringostat tab.
    """
    db = _db()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    pipe = [
        {"$match": {"started_at": {"$gte": cutoff}, "manager_id": {"$ne": None}}},
        {"$group": {
            "_id": "$manager_id",
            "total": {"$sum": 1},
            "answered": {"$sum": {"$cond": [
                {"$in": ["$status", ["COMPLETED", "ANSWERED", "answered", "completed"]]}, 1, 0,
            ]}},
            "missed": {"$sum": {"$cond": [
                {"$in": ["$status", ["MISSED", "missed", "no-answer", "NOANSWER"]]}, 1, 0,
            ]}},
            "inbound": {"$sum": {"$cond": [{"$eq": ["$direction", "inbound"]}, 1, 0]}},
            "outbound": {"$sum": {"$cond": [{"$eq": ["$direction", "outbound"]}, 1, 0]}},
            "duration_sum": {"$sum": {"$cond": [{"$gt": ["$duration", 0]}, "$duration", 0]}},
            "duration_count": {"$sum": {"$cond": [{"$gt": ["$duration", 0]}, 1, 0]}},
            "last_call_at": {"$max": "$started_at"},
        }},
        {"$sort": {"total": -1}},
    ]
    rows = await db.ringostat_calls.aggregate(pipe).to_list(length=500)

    # Enrich with manager name
    out = []
    for r in rows:
        manager_id = r["_id"]
        manager = await _find_by_id(db.staff, manager_id) if manager_id else None
        answered = int(r.get("answered", 0))
        missed = int(r.get("missed", 0))
        dur_count = int(r.get("duration_count", 0))
        avg_dur = (r.get("duration_sum", 0) / dur_count) if dur_count else 0.0
        out.append({
            "manager_id": manager_id,
            "manager_name": (manager or {}).get("name") or (manager or {}).get("email") or "unknown",
            "extension": (manager or {}).get("extension"),
            "total": int(r.get("total", 0)),
            "answered": answered,
            "missed": missed,
            "inbound": int(r.get("inbound", 0)),
            "outbound": int(r.get("outbound", 0)),
            "answer_rate": round(answered / (answered + missed) * 100, 1) if (answered + missed) else 0.0,
            "avg_duration_sec": round(avg_dur, 1),
            "last_call_at": r.get("last_call_at").isoformat() if r.get("last_call_at") else None,
        })

    # Also surface unassigned calls (manager_id missing) as a synthetic row
    unassigned_total = await db.ringostat_calls.count_documents(
        {"started_at": {"$gte": cutoff}, "$or": [{"manager_id": None}, {"manager_id": ""}, {"manager_id": {"$exists": False}}]}
    )
    if unassigned_total > 0:
        out.append({
            "manager_id": None,
            "manager_name": "(unassigned)",
            "extension": None,
            "total": unassigned_total,
            "answered": 0, "missed": 0, "inbound": 0, "outbound": 0,
            "answer_rate": 0.0, "avg_duration_sec": 0.0, "last_call_at": None,
        })

    return {"window_days": days, "managers": out}


@router.get("/calls/{call_id}/recording")
async def ringostat_call_recording_proxy(call_id: str):
    """Stream a call recording through our backend.

    Why a proxy: Ringostat increasingly returns *signed* recording URLs that
    expire within minutes. The browser tries to play a stale URL and gets
    403/404. This endpoint:

      1. Looks up the call in ``ringostat_calls``.
      2. Returns 404 if there's no call or no recording_url yet.
      3. If the URL is still fresh (basic HEAD check), redirects the browser
         straight to it (browser does the actual streaming — efficient).
      4. If the URL is dead, attempts to re-fetch a fresh one through the
         Ringostat list API using the saved ``project_id``/``api_key`` and
         updates the call in place, then redirects.

    The frontend can simply set ``<audio src="/api/admin/ringostat/calls/<id>/recording" />``
    and the browser handles the rest. Behind ``require_admin`` so only logged-in
    staff can listen to recordings.
    """
    import httpx
    from fastapi.responses import RedirectResponse

    db = _db()
    call = await db.ringostat_calls.find_one({"call_id": call_id})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    recording_url = call.get("recording_url")

    async def _try_refetch() -> Optional[str]:
        cfg = await db.ringostat_config.find_one({})
        if not cfg or not cfg.get("api_key") or not cfg.get("project_id"):
            return None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://api.ringostat.net/calls/list",
                    headers={"Auth-key": cfg["api_key"], "x-project-id": cfg["project_id"]},
                    params={"call_id": call_id},
                )
                if r.status_code != 200:
                    return None
                data = r.json()
                calls_api = data if isinstance(data, list) else data.get("calls", [])
                if not calls_api:
                    return None
                fresh = calls_api[0].get("recording") or calls_api[0].get("record_url")
                if fresh:
                    await db.ringostat_calls.update_one(
                        {"call_id": call_id},
                        {"$set": {
                            "recording_url": fresh,
                            "recording_fetched_at": datetime.now(timezone.utc),
                        }},
                    )
                    return fresh
        except Exception as e:
            logger.warning(f"[recording-proxy] refetch err for {call_id}: {e}")
        return None

    # If no URL stored, try to fetch fresh
    if not recording_url:
        recording_url = await _try_refetch()
        if not recording_url:
            raise HTTPException(
                status_code=404,
                detail="No recording available for this call yet (Ringostat usually takes 15s–2min after CALL_END).",
            )

    # Quick HEAD check — if dead/expired, refetch once
    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            head = await client.head(recording_url)
            if head.status_code >= 400:
                refreshed = await _try_refetch()
                if refreshed:
                    recording_url = refreshed
    except Exception:
        # Network/HEAD failure — still try the URL, browser may succeed
        pass

    return RedirectResponse(url=recording_url, status_code=302)


@router.get("/callbacks")
async def ringostat_callbacks_log(limit: int = Query(50, ge=1, le=500)):
    """Audit log of outbound click-to-call attempts (who dialled what when)."""
    db = _db()
    serialize_doc = _serialize_doc()
    rows = await db.ringostat_callbacks.find({}).sort("initiated_at", -1).limit(limit).to_list(length=limit)
    return {"callbacks": [serialize_doc(r) for r in rows], "total": len(rows)}

