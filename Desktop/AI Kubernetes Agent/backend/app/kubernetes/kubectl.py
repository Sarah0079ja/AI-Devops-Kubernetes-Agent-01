import subprocess
from dataclasses import dataclass
from loguru import logger

from app.core.config import settings


@dataclass
class KubectlResult:
    command: str
    success: bool
    stdout: str
    stderr: str
    return_code: int


def run_kubectl(args: list[str], timeout: int = 30) -> KubectlResult:
    """Execute a kubectl command and return structured output."""
    cmd = _build_command(args)
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        success = result.returncode == 0
        if not success:
            logger.warning(f"kubectl exited {result.returncode}: {result.stderr.strip()}")

        return KubectlResult(
            command=" ".join(cmd),
            success=success,
            stdout=result.stdout,
            stderr=result.stderr,
            return_code=result.returncode,
        )

    except subprocess.TimeoutExpired:
        logger.error(f"kubectl timed out after {timeout}s: {' '.join(cmd)}")
        return KubectlResult(
            command=" ".join(cmd),
            success=False,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            return_code=-1,
        )
    except FileNotFoundError:
        logger.error("kubectl binary not found on PATH")
        return KubectlResult(
            command=" ".join(cmd),
            success=False,
            stdout="",
            stderr="kubectl not found — ensure it is installed and on PATH",
            return_code=-1,
        )
    except Exception as e:
        logger.error(f"Unexpected error running kubectl: {e}")
        return KubectlResult(
            command=" ".join(cmd),
            success=False,
            stdout="",
            stderr=str(e),
            return_code=-1,
        )


def _build_command(args: list[str]) -> list[str]:
    cmd = ["kubectl"]
    if settings.kubeconfig_path:
        cmd += ["--kubeconfig", settings.kubeconfig_path]
    cmd += args
    return cmd
