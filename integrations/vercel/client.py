import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class VercelConfig:
    token: str
    team_id: str = ""

    @classmethod
    def from_env(cls) -> "VercelConfig":
        return cls(token=os.getenv("VERCEL_TOKEN", ""), team_id=os.getenv("VERCEL_TEAM_ID", ""))


class VercelService:
    """Vercel deployment adapter with PM approval guard integration points."""

    API_BASE = "https://api.vercel.com"

    def __init__(self, config: Optional[VercelConfig] = None):
        self.config = config or VercelConfig.from_env()

    @property
    def enabled(self) -> bool:
        return bool(self.config.token)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.config.token}", "Content-Type": "application/json"}

    async def create_deployment(self, name: str, git_repo: str, branch: str, approved_by_pm: bool) -> Dict[str, Any]:
        if not approved_by_pm:
            return {"status": "blocked", "message": "PM approval required before Vercel deployment"}

        if not self.enabled:
            return {"status": "disabled", "message": "VERCEL_TOKEN not configured"}

        payload: Dict[str, Any] = {
            "name": name,
            "gitSource": {
                "type": "github",
                "repo": git_repo,
                "ref": branch,
            },
            "target": "production",
        }
        if self.config.team_id:
            payload["teamId"] = self.config.team_id

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{self.API_BASE}/v13/deployments", headers=self._headers(), json=payload)

        if response.status_code >= 400:
            return {"status": "error", "code": response.status_code, "message": response.text}

        data = response.json()
        return {
            "status": "queued",
            "deployment_id": data.get("id"),
            "url": data.get("url"),
            "inspector_url": data.get("inspectorUrl"),
        }
