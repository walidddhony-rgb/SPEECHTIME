"""Collect reproducibility metadata for SpeechScribe benchmark runs."""
from __future__ import annotations

import platform
import sys
from importlib import metadata


def _package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def collect_system_info() -> dict:
    """Return JSON-serializable OS, Python, hardware, and package metadata."""
    info = {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": sys.version.split()[0],
        "python_implementation": platform.python_implementation(),
        "cpu_logical_cores": None,
        "cpu_physical_cores": None,
        "memory_total_mb": None,
        "packages": {
            name: _package_version(name)
            for name in ("numpy", "scipy", "jiwer", "psutil", "speechscribe")
        },
    }
    try:
        import psutil

        info.update(
            {
                "cpu_logical_cores": psutil.cpu_count(logical=True),
                "cpu_physical_cores": psutil.cpu_count(logical=False),
                "memory_total_mb": round(psutil.virtual_memory().total / (1024 * 1024), 2),
            }
        )
    except Exception:
        pass
    return info
