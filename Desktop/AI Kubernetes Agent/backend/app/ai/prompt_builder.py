SYSTEM_PROMPT = """You are a Senior Kubernetes Site Reliability Engineer (SRE) with 10+ years of experience.

You are given evidence collected from a live Kubernetes cluster investigation.
Your job is to correlate the evidence, identify the root cause, and recommend precise, actionable fixes.

You MUST respond ONLY with a valid JSON object — no markdown, no extra text, nothing outside the JSON.

Required format:
{
  "root_cause": "One-sentence description of the root cause",
  "explanation": "Detailed explanation of why this failure is happening, referencing specific pod names, namespaces, and log lines",
  "fix": "Step-by-step fix in plain language that a junior engineer can follow",
  "kubectl_commands": ["kubectl command 1", "kubectl command 2"],
  "prevention": "Concrete recommendation to prevent this class of failure in the future",
  "confidence": 85
}

Rules:
- confidence is an integer 0-100. High (>80) when logs + events + pod state all agree. Low (<40) when evidence is sparse.
- kubectl_commands is a list of strings. Empty list [] if no commands are needed.
- Reference specific pod names, namespaces, and error messages from the evidence — never be generic.
- If the cluster appears healthy, set root_cause to "No issues detected" and confidence to 95.
- Do not invent problems that are not present in the evidence.
"""


def build_prompt(evidence: dict) -> str:
    """Convert a raw investigation payload into a structured prompt for the LLM."""
    pods = evidence.get("pods", {})
    logs = evidence.get("logs", {})
    events = evidence.get("events", {})
    deployments = evidence.get("deployments", {})
    network = evidence.get("network", {})

    lines: list[str] = ["## Kubernetes Cluster Investigation Evidence", ""]

    # --- Pods ---
    lines.append("### Pod Status")
    lines.append(f"- Total pods: {pods.get('total_pods', 'unknown')}")
    lines.append(f"- Cluster healthy: {pods.get('healthy', 'unknown')}")

    problematic = pods.get("problematic_pods", [])
    if problematic:
        lines.append(f"- Problematic pods ({len(problematic)}):")
        for pod in problematic:
            lines.append(f"  - {pod['namespace']}/{pod['name']}: {pod['status']}")
    else:
        lines.append("- No problematic pods detected")

    # --- Logs ---
    lines += ["", "### Container Logs (error-relevant lines from failed pods)"]
    collected = logs.get("collected", [])
    if collected:
        for entry in collected:
            lines.append(f"Pod: {entry['namespace']}/{entry['pod']}")
            relevant = entry.get("relevant_lines", [])
            if relevant:
                for line in relevant:
                    lines.append(f"  {line}")
            else:
                lines.append("  (no error-relevant log lines found)")
            if entry.get("fetch_error"):
                lines.append(f"  [fetch error: {entry['fetch_error']}]")
    else:
        lines.append(logs.get("message", "No logs collected"))

    # --- Events ---
    lines += ["", "### Kubernetes Warning Events"]
    warning_events = events.get("warning_events", [])
    if warning_events:
        # Cap at 20 to keep prompt size manageable
        for ev in warning_events[:20]:
            lines.append(
                f"  [{ev['reason']}] {ev['namespace']}/{ev['object_kind']}/{ev['object_name']}: "
                f"{ev['message']} (occurrences: {ev['count']})"
            )
    else:
        lines.append("  No warning events")

    # --- Deployments ---
    lines += ["", "### Deployment Health"]
    unhealthy = deployments.get("unhealthy_deployments", [])
    if unhealthy:
        for d in unhealthy:
            lines.append(
                f"  - {d['namespace']}/{d['name']}: "
                f"desired={d['desired_replicas']} ready={d['ready_replicas']} "
                f"unavailable={d['unavailable_replicas']}"
            )
            for cond in d.get("conditions", []):
                if cond.get("status") != "True" or cond.get("type") in ("Progressing", "Available"):
                    lines.append(
                        f"    Condition [{cond['type']}={cond['status']}]: "
                        f"{cond.get('reason', '')} — {cond.get('message', '')}"
                    )
    else:
        lines.append("  All deployments healthy")

    # --- Network ---
    lines += ["", "### Networking Issues"]
    net_issues = network.get("issues", [])
    if net_issues:
        for issue in net_issues:
            lines.append(f"  - {issue['namespace']}/{issue['service']}: {issue['issue']}")
    else:
        lines.append("  No networking issues detected")

    return "\n".join(lines)
