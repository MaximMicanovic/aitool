"""Startup sequence for backend/provider selection."""

import os
from dataclasses import dataclass

OLLAMA_DEFAULT_HOST = "http://localhost:11434"
LM_STUDIO_DEFAULT_HOST = "http://192.168.1.56:1234"


@dataclass(frozen=True)
class StartupConfig:
    provider: str
    host: str
    is_wsl: bool


def is_wsl():
    """Return True when running inside Windows Subsystem for Linux."""
    if os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP"):
        return True

    try:
        with open("/proc/sys/kernel/osrelease") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


def detect_provider():
    """
    Pick backend provider.
    - AI_PROVIDER=ollama|lmstudio overrides auto-detection.
    - WSL defaults to LM Studio.
    - Non-WSL Linux defaults to Ollama.
    """
    provider = os.environ.get("AI_PROVIDER", "").strip().lower()
    if provider in ("ollama", "lmstudio"):
        return provider
    return "lmstudio" if is_wsl() else "ollama"


def default_host(provider):
    """Return provider default host with env overrides."""
    if provider == "lmstudio":
        return os.environ.get("LM_STUDIO_HOST", LM_STUDIO_DEFAULT_HOST)
    return os.environ.get("OLLAMA_HOST", OLLAMA_DEFAULT_HOST)


def startup_sequence(cli_host=None):
    """Resolve provider + host for this run."""
    provider = detect_provider()
    host = cli_host or default_host(provider)
    return StartupConfig(provider=provider, host=host, is_wsl=is_wsl())
