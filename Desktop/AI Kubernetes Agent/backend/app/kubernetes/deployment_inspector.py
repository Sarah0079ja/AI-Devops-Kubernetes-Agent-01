import json
from loguru import logger

from app.kubernetes.kubectl import run_kubectl


def inspect_deployments() -> dict:
    """Inspect all deployments and flag any that are unhealthy."""
    result = run_kubectl(["get", "deployments", "-A", "-o", "json"])

    if not result.success:
        logger.warning("Deployment inspection failed")
        return {"error": result.stderr, "unhealthy_deployments": [], "all_deployments": []}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Could not parse kubectl output", "unhealthy_deployments": [], "all_deployments": []}

    all_deployments: list[dict] = []
    unhealthy_deployments: list[dict] = []

    for item in data.get("items", []):
        meta = item.get("metadata", {})
        spec = item.get("spec", {})
        status = item.get("status", {})

        name = meta.get("name", "unknown")
        namespace = meta.get("namespace", "unknown")

        desired = spec.get("replicas", 0)
        ready = status.get("readyReplicas", 0)
        available = status.get("availableReplicas", 0)
        unavailable = status.get("unavailableReplicas", 0)
        updated = status.get("updatedReplicas", 0)

        conditions = _parse_conditions(status.get("conditions", []))
        is_healthy = unavailable == 0 and ready == desired and desired > 0

        deployment_info = {
            "name": name,
            "namespace": namespace,
            "desired_replicas": desired,
            "ready_replicas": ready,
            "available_replicas": available,
            "unavailable_replicas": unavailable,
            "updated_replicas": updated,
            "conditions": conditions,
            "healthy": is_healthy,
        }

        all_deployments.append(deployment_info)
        if not is_healthy:
            unhealthy_deployments.append(deployment_info)

    logger.info(f"Deployments: {len(all_deployments)} total, {len(unhealthy_deployments)} unhealthy")
    return {
        "total_deployments": len(all_deployments),
        "unhealthy_deployments": unhealthy_deployments,
        "all_deployments": all_deployments,
    }


def _parse_conditions(conditions: list[dict]) -> list[dict]:
    return [
        {
            "type": c.get("type"),
            "status": c.get("status"),
            "reason": c.get("reason"),
            "message": c.get("message"),
        }
        for c in conditions
    ]
