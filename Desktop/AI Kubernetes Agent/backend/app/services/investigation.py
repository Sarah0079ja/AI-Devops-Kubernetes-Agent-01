from loguru import logger

from app.kubernetes.pod_inspector import inspect_pods
from app.kubernetes.logs_collector import collect_logs
from app.kubernetes.events_analyzer import analyze_events
from app.kubernetes.deployment_inspector import inspect_deployments
from app.kubernetes.network_inspector import inspect_network


def run_investigation() -> dict:
    """
    Orchestrate the full Kubernetes investigation pipeline.

    Runs each inspector in sequence and returns a single evidence payload
    ready for AI reasoning in a later stage.
    """
    logger.info("Starting Kubernetes cluster investigation")

    pods = inspect_pods()
    logger.info("Pod inspection complete")

    logs = collect_logs(pods.get("problematic_pods", []))
    logger.info("Log collection complete")

    events = analyze_events()
    logger.info("Events analysis complete")

    deployments = inspect_deployments()
    logger.info("Deployment inspection complete")

    network = inspect_network()
    logger.info("Network inspection complete")

    logger.info("Investigation complete")

    return {
        "pods": pods,
        "logs": logs,
        "events": events,
        "deployments": deployments,
        "network": network,
    }
