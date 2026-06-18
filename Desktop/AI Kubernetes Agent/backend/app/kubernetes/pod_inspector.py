import json
from loguru import logger

from app.kubernetes.kubectl import run_kubectl

UNHEALTHY_STATUSES = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "Pending",
    "Error",
    "OOMKilled",
    "ContainerCreating",
    "Terminating",
    "Unknown",
}


def inspect_pods() -> dict:
    """Get all pods and flag any that are unhealthy."""
    result = run_kubectl(["get", "pods", "-A", "-o", "json"])

    if not result.success:
        logger.warning("Pod inspection failed")
        return {"healthy": False, "error": result.stderr, "problematic_pods": [], "all_pods": []}

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"healthy": False, "error": "Could not parse kubectl output", "problematic_pods": [], "all_pods": []}

    all_pods: list[dict] = []
    problematic_pods: list[dict] = []

    for item in data.get("items", []):
        meta = item.get("metadata", {})
        status = item.get("status", {})

        pod_name = meta.get("name", "unknown")
        namespace = meta.get("namespace", "unknown")
        phase = status.get("phase", "Unknown")

        container_statuses = status.get("containerStatuses", []) + status.get("initContainerStatuses", [])
        detected_status = _detect_container_status(container_statuses) or phase

        pod_info = {
            "name": pod_name,
            "namespace": namespace,
            "phase": phase,
            "status": detected_status,
        }
        all_pods.append(pod_info)

        if detected_status in UNHEALTHY_STATUSES or phase in {"Failed", "Unknown", "Pending"}:
            problematic_pods.append(pod_info)

    is_healthy = len(problematic_pods) == 0

    logger.info(f"Pods: {len(all_pods)} total, {len(problematic_pods)} problematic")
    return {
        "healthy": is_healthy,
        "total_pods": len(all_pods),
        "problematic_pods": problematic_pods,
        "all_pods": all_pods,
    }


def _detect_container_status(container_statuses: list[dict]) -> str | None:
    """Extract the first notable waiting reason from container statuses."""
    for cs in container_statuses:
        state = cs.get("state", {})
        waiting = state.get("waiting", {})
        reason = waiting.get("reason")
        if reason:
            return reason

        terminated = state.get("terminated", {})
        reason = terminated.get("reason")
        if reason and reason != "Completed":
            return reason

    return None
