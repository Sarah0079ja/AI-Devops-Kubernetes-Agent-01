import json
import re
from loguru import logger


def parse_diagnosis(llm_response: str) -> dict:
    """
    Extract the JSON diagnosis object from the LLM response.

    Handles responses that are clean JSON, JSON wrapped in markdown fences,
    or JSON embedded inside surrounding prose.
    """
    text = llm_response.strip()

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)

    data = _try_parse_json(text)

    if data is None:
        # Last resort: find the first {...} block in the response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = _try_parse_json(match.group())

    if data is None:
        logger.error("Could not parse LLM response as JSON — using fallback")
        return _fallback(llm_response)

    return _normalize(data)


def _try_parse_json(text: str) -> dict | None:
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    return None


def _normalize(data: dict) -> dict:
    """Coerce fields to the expected types and clamp confidence to 0-100."""
    confidence = data.get("confidence", 50)
    if isinstance(confidence, str):
        digits = re.sub(r"[^0-9]", "", confidence)
        confidence = int(digits) if digits else 50
    confidence = max(0, min(100, int(confidence)))

    kubectl_commands = data.get("kubectl_commands", [])
    if isinstance(kubectl_commands, str):
        kubectl_commands = [kubectl_commands] if kubectl_commands.strip() else []

    return {
        "root_cause": str(data.get("root_cause", "Unknown")),
        "explanation": str(data.get("explanation", "")),
        "fix": str(data.get("fix", "")),
        "kubectl_commands": [str(c) for c in kubectl_commands],
        "prevention": str(data.get("prevention", "")),
        "confidence": confidence,
    }


def _fallback(raw: str) -> dict:
    return {
        "root_cause": "AI response could not be parsed",
        "explanation": raw[:500],
        "fix": "Retry the investigation or check the LLM response format",
        "kubectl_commands": [],
        "prevention": "",
        "confidence": 0,
    }
