import json
from loguru import logger

from app.kubernetes.kubectl import run_kubectl

WARNING_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
    "OOMKilling",
    "FailedCreate",
    "FailedAttachVolume",
    "NodeNotReady",
    "Evicted",
    "FailedPostStartHook",
    "NetworkNotReady",
}


def analyze_events() -> dict:
    """Read cluster events and surface warning-level findings."""
    result = run_kubectl(["get", "events", "-A", "-o", "json"])

    if not result.success:
        logger.warning("Events analysis failed")
        return {"error": result.stderr, "warning_events": [], "total_events": 0}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Could not parse kubectl output", "warning_events": [], "total_events": 0}

    items = data.get("items", [])
    warning_events: list[dict] = []

    for event in items:
        event_type = event.get("type", "")
        reason = event.get("reason", "")
        message = event.get("message", "")
        namespace = event.get("metadata", {}).get("namespace", "unknown")
        involved = event.get("involvedObject", {})
        count = event.get("count", 1)

        if event_type == "Warning" or reason in WARNING_REASONS:
            warning_events.append({
                "reason": reason,
                "message": message,
                "namespace": namespace,
                "object_kind": involved.get("kind", ""),
                "object_name": involved.get("name", ""),
                "count": count,
            })

    # Sort by count descending so the most repeated issues appear first
    warning_events.sort(key=lambda e: e["count"], reverse=True)

    logger.info(f"Events: {len(items)} total, {len(warning_events)} warnings")
    return {
        "total_events": len(items),
        "warning_count": len(warning_events),
        "warning_events": warning_events,
    }
