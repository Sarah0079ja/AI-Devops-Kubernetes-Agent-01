from loguru import logger

from app.ai.prompt_builder import SYSTEM_PROMPT, build_prompt
from app.ai.llm_client import call_llm
from app.ai.parser import parse_diagnosis


def analyze_cluster(evidence: dict) -> dict:
    """
    Entry point for AI reasoning.

    Takes the raw investigation payload from the Kubernetes layer,
    sends it to the LLM, and returns a structured diagnosis.
    """
    logger.info("Building prompt from investigation evidence")
    user_prompt = build_prompt(evidence)

    logger.info("Sending evidence to LLM for root cause analysis")
    raw_response = call_llm(SYSTEM_PROMPT, user_prompt)

    logger.info("Parsing LLM diagnosis")
    diagnosis = parse_diagnosis(raw_response)

    logger.info(f"AI diagnosis complete — confidence: {diagnosis['confidence']}%")
    return diagnosis
