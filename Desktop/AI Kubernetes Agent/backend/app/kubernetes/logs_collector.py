from loguru import logger

from app.kubernetes.kubectl import run_kubectl

MAX_LOG_LINES = 50

ERROR_KEYWORDS = [
    "exception",
    "error",
    "fatal",
    "panic",
    "traceback",
    "connection refused",
    "connection timeout",
    "no such file",
    "permission denied",
    "env",
    "undefined",
    "cannot connect",
    "failed to",
    "crash",
    "oom",
    "killed",
]


def collect_logs(problematic_pods: list[dict]) -> dict:
    """Fetch and filter logs for every problematic pod."""
    if not problematic_pods:
        return {"collected": [], "message": "No problematic pods — skipping log collection"}

    collected: list[dict] = []

    for pod in problematic_pods:
        name = pod["name"]
        namespace = pod["namespace"]

        entry = _fetch_pod_logs(name, namespace)
        collected.append(entry)

    logger.info(f"Collected logs for {len(collected)} pod(s)")
    return {"collected": collected}


def _fetch_pod_logs(name: str, namespace: str) -> dict:
    result = run_kubectl([
        "logs", name,
        "-n", namespace,
        "--tail", str(MAX_LOG_LINES),
        "--previous",          # fetch logs from the previous (crashed) container
    ])

    # Fall back to current container logs if --previous has nothing
    if not result.success or not result.stdout.strip():
        result = run_kubectl([
            "logs", name,
            "-n", namespace,
            "--tail", str(MAX_LOG_LINES),
        ])

    raw_lines = result.stdout.splitlines() if result.success else []
    relevant_lines = _filter_relevant(raw_lines)

    return {
        "pod": name,
        "namespace": namespace,
        "relevant_lines": relevant_lines,
        "fetch_error": result.stderr if not result.success else None,
    }


def _filter_relevant(lines: list[str]) -> list[str]:
    """Return only lines that contain error-related keywords (case-insensitive)."""
    out: list[str] = []
    for line in lines:
        lower = line.lower()
        if any(kw in lower for kw in ERROR_KEYWORDS):
            out.append(line.strip())
    # Always return at least the last 10 lines if nothing matched
    if not out and lines:
        out = [l.strip() for l in lines[-10:]]
    return out
