import { useEffect, useMemo, useState } from 'react'
import { initialSnapshot } from './mockData'
import type { DashboardEvent, DashboardSnapshot } from './types'

const wsUrl = import.meta.env.VITE_ORD_WS_URL ?? 'ws://localhost:8000/ws/dashboard'

function mergeSnapshot(current: DashboardSnapshot, patch: Partial<DashboardSnapshot>): DashboardSnapshot {
  return {
    ...current,
    ...patch,
    agents: patch.agents ?? current.agents,
    activity: patch.activity ?? current.activity,
    financials: patch.financials ?? current.financials,
    products: patch.products ?? current.products,
    updatedAt: patch.updatedAt ?? new Date().toISOString(),
  }
}

export function useOrdLiveData() {
  const [snapshot, setSnapshot] = useState<DashboardSnapshot>(initialSnapshot)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const socket = new WebSocket(wsUrl)

    socket.onopen = () => setConnected(true)
    socket.onclose = () => setConnected(false)
    socket.onerror = () => setConnected(false)

    socket.onmessage = (message) => {
      try {
        const event = JSON.parse(message.data) as DashboardEvent
        setSnapshot((current) => mergeSnapshot(current, event.payload))
      } catch {
        // ignore malformed payloads
      }
    }

    return () => {
      socket.close()
    }
  }, [])

  const boardRoomAgents = useMemo(() => snapshot.agents.filter((agent) => agent.zone === 'board_room'), [snapshot.agents])
  const opsAgents = useMemo(() => snapshot.agents.filter((agent) => agent.zone === 'operations_floor'), [snapshot.agents])

  return {
    snapshot,
    connected,
    boardRoomAgents,
    opsAgents,
  }
}
