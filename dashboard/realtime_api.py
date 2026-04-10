"""Ord HQ real-time API for dashboard streaming."""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Ord HQ Realtime API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DashboardStream:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._snapshot = self._make_snapshot()

    def _make_snapshot(self) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "agents": [
                {
                    "id": "ord-pm",
                    "name": "Ord-PM",
                    "zone": "board_room",
                    "status": "working",
                    "task": "Orchestrating next mission",
                    "utilization": 81,
                    "latencyMs": 142,
                },
                {
                    "id": "ord-coo",
                    "name": "Ord-COO",
                    "zone": "board_room",
                    "status": "working",
                    "task": "Scheduling War Room",
                    "utilization": 76,
                    "latencyMs": 128,
                },
                {
                    "id": "ord-daa",
                    "name": "Ord-DAA",
                    "zone": "operations_floor",
                    "status": "working",
                    "task": "Refreshing CFO-ready forecast",
                    "utilization": 84,
                    "latencyMs": 138,
                },
            ],
            "activity": [
                {
                    "id": "boot",
                    "timestamp": now,
                    "speaker": "Ord-Orchestrator",
                    "message": "Ord HQ stream online. All rooms synced.",
                    "tone": "ops",
                }
            ],
            "financials": [
                {"period": "Jan", "revenue": 220000, "burn": 128000, "runway": 17.8, "efficiency": 1.72},
                {"period": "Feb", "revenue": 236000, "burn": 132000, "runway": 18.1, "efficiency": 1.79},
                {"period": "Mar", "revenue": 251000, "burn": 138000, "runway": 18.7, "efficiency": 1.82},
                {"period": "Apr", "revenue": 266000, "burn": 141000, "runway": 19.2, "efficiency": 1.89},
            ],
            "products": [
                {"id": "ord-hq", "name": "Ord HQ", "stage": "Live", "owner": "Ord-PM", "mrr": 88000}
            ],
            "previewUrl": "https://example.com",
            "warRoomTopic": "Cut launch risk while preserving momentum",
            "updatedAt": now,
        }

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)
        await websocket.send_json({"type": "snapshot", "payload": self._snapshot})

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        for client in list(self._clients):
            try:
                await client.send_json(event)
            except RuntimeError:
                self.disconnect(client)

    async def tick(self) -> None:
        banter = [
            "CFA says margins look clean. COO says ship cleaner.",
            "Board Room approves faster experiments.",
            "Operations Floor reports blockers evaporating.",
        ]
        while True:
            await asyncio.sleep(5)
            now = datetime.now(timezone.utc).isoformat()
            revenue_delta = random.randint(1000, 4000)
            burn_delta = random.randint(500, 1800)
            self._snapshot["financials"][-1]["revenue"] += revenue_delta
            self._snapshot["financials"][-1]["burn"] += burn_delta
            self._snapshot["updatedAt"] = now
            self._snapshot["activity"] = [
                {
                    "id": f"evt-{int(datetime.now(timezone.utc).timestamp())}",
                    "timestamp": now,
                    "speaker": "Ord-COO",
                    "message": random.choice(banter),
                    "tone": "banter",
                },
                *self._snapshot["activity"][:39],
            ]
            await self.broadcast({"type": "snapshot", "payload": self._snapshot})


stream = DashboardStream()


@app.on_event("startup")
async def on_startup() -> None:
    asyncio.create_task(stream.tick())


@app.get("/api/dashboard/snapshot")
async def get_snapshot() -> dict[str, Any]:
    return stream._snapshot


@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket) -> None:
    await stream.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        stream.disconnect(websocket)
