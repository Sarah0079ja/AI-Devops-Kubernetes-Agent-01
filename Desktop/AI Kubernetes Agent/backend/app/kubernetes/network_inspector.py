import json
from loguru import logger

from app.kubernetes.kubectl import run_kubectl


def inspect_network() -> dict:
    """Inspect services and endpoints to surface networking issues."""
    services = _get_services()
    endpoints = _get_endpoints()

    issues: list[dict] = []

    for svc in services:
        name = svc["name"]
        namespace = svc["namespace"]
        svc_type = svc["type"]

        # Skip headless and ExternalName services
        if svc_type in ("ExternalName",):
            continue

        matching_ep = _find_endpoint(endpoints, name, namespace)

        if matching_ep is None:
            issues.append({
                "service": name,
                "namespace": namespace,
                "issue": "No Endpoints object found",
            })
        elif not matching_ep["has_ready_addresses"]:
            issues.append({
                "service": name,
                "namespace": namespace,
                "issue": "Endpoints exist but no ready addresses — possible selector mismatch or no healthy pods",
            })

    logger.info(f"Network: {len(services)} services, {len(issues)} issue(s)")
    return {
        "total_services": len(services),
        "services": services,
        "issues": issues,
    }


def _get_services() -> list[dict]:
    result = run_kubectl(["get", "svc", "-A", "-o", "json"])
    if not result.success:
        logger.warning("Failed to list services")
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    services: list[dict] = []
    for item in data.get("items", []):
        meta = item.get("metadata", {})
        spec = item.get("spec", {})
        services.append({
            "name": meta.get("name", "unknown"),
            "namespace": meta.get("namespace", "unknown"),
            "type": spec.get("type", "ClusterIP"),
            "cluster_ip": spec.get("clusterIP", ""),
            "selector": spec.get("selector", {}),
            "ports": [
                {"port": p.get("port"), "protocol": p.get("protocol"), "target_port": p.get("targetPort")}
                for p in spec.get("ports", [])
            ],
        })
    return services


def _get_endpoints() -> list[dict]:
    result = run_kubectl(["get", "endpoints", "-A", "-o", "json"])
    if not result.success:
        logger.warning("Failed to list endpoints")
        return []

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []

    endpoints: list[dict] = []
    for item in data.get("items", []):
        meta = item.get("metadata", {})
        subsets = item.get("subsets", [])
        has_ready = any(s.get("addresses") for s in subsets)
        endpoints.append({
            "name": meta.get("name", "unknown"),
            "namespace": meta.get("namespace", "unknown"),
            "has_ready_addresses": has_ready,
        })
    return endpoints


def _find_endpoint(endpoints: list[dict], name: str, namespace: str) -> dict | None:
    for ep in endpoints:
        if ep["name"] == name and ep["namespace"] == namespace:
            return ep
    return None
