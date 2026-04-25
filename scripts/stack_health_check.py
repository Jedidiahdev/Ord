#!/usr/bin/env python3
"""Preflight + runtime health checks for the Ord application stack."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ServiceHealth:
    service: str
    mode: str
    status: str
    details: str


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)


def check_stack_health() -> Dict[str, object]:
    services: List[ServiceHealth] = []

    docker_path = shutil.which("docker")
    docker_ready = False
    docker_reason = "docker binary not installed"

    if docker_path:
        compose_probe = _run(["docker", "compose", "version"])
        docker_ready = compose_probe.returncode == 0
        docker_reason = "docker compose available" if docker_ready else compose_probe.stderr.strip() or "docker compose unavailable"

    if docker_ready:
        up = _run(["docker", "compose", "up", "-d"])
        if up.returncode != 0:
            services.append(ServiceHealth("docker-compose", "container", "unhealthy", up.stderr.strip() or up.stdout.strip()))
        ps = _run(["docker", "compose", "ps", "--format", "json"])
        if ps.returncode == 0 and ps.stdout.strip():
            for line in ps.stdout.splitlines():
                row = json.loads(line)
                services.append(
                    ServiceHealth(
                        service=row.get("Service", "unknown"),
                        mode="container",
                        status="healthy" if row.get("State") == "running" else "unhealthy",
                        details=f"state={row.get('State')} health={row.get('Health', 'n/a')}",
                    )
                )
    else:
        for name in ["ord", "redis", "postgres", "chroma", "dashboard", "nginx"]:
            services.append(ServiceHealth(name, "container", "skipped", docker_reason))

    python_ok = shutil.which("python") is not None
    core_requirements = ["chromadb", "sqlalchemy", "redis", "fastapi"]
    missing_core = [name for name in core_requirements if not _has_module(name)]
    services.append(
        ServiceHealth(
            service="ord-core-local",
            mode="local",
            status="healthy" if python_ok and not missing_core else "unhealthy",
            details="all runtime dependencies available" if python_ok and not missing_core else f"missing modules: {', '.join(missing_core)}",
        )
    )

    dashboard_requirements = ["fastapi", "uvicorn"]
    missing_dashboard = [name for name in dashboard_requirements if not _has_module(name)]
    services.append(
        ServiceHealth(
            service="dashboard-realtime-api-local",
            mode="local",
            status="healthy" if python_ok and not missing_dashboard else "unhealthy",
            details="ready to run uvicorn dashboard.realtime_api:app" if python_ok and not missing_dashboard else f"missing modules: {', '.join(missing_dashboard)}",
        )
    )

    node_ok = shutil.which("node") is not None
    npm_ok = shutil.which("npm") is not None
    services.append(
        ServiceHealth(
            service="dashboard-nextjs-local",
            mode="local",
            status="healthy" if node_ok and npm_ok else "unhealthy",
            details="node/npm available" if node_ok and npm_ok else "node and/or npm not installed",
        )
    )

    return {
        "services": [asdict(svc) for svc in services],
    }


if __name__ == "__main__":
    print(json.dumps(check_stack_health(), indent=2))
