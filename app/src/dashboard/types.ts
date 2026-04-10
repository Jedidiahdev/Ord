export type AgentZone = 'board_room' | 'operations_floor'

export type AgentStatus = 'idle' | 'working' | 'blocked' | 'offline'

export interface AgentSnapshot {
  id: string
  name: string
  zone: AgentZone
  status: AgentStatus
  task: string
  utilization: number
  latencyMs: number
}

export interface ActivityItem {
  id: string
  timestamp: string
  speaker: string
  message: string
  tone: 'banter' | 'ops' | 'finance'
}

export interface FinancialPoint {
  period: string
  revenue: number
  burn: number
  runway: number
  efficiency: number
}

export interface ProductCard {
  id: string
  name: string
  stage: 'Ideation' | 'Beta' | 'Live'
  owner: string
  mrr: number
}

export interface DashboardSnapshot {
  agents: AgentSnapshot[]
  activity: ActivityItem[]
  financials: FinancialPoint[]
  products: ProductCard[]
  previewUrl: string
  warRoomTopic: string
  updatedAt: string
}

export interface DashboardEvent {
  type: 'snapshot' | 'activity' | 'agent' | 'financial' | 'product' | 'preview' | 'war_room'
  payload: Partial<DashboardSnapshot>
}
