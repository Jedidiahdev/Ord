import type { DashboardSnapshot } from './types'

export const initialSnapshot: DashboardSnapshot = {
  agents: [
    { id: 'ord-pm', name: 'Ord-PM', zone: 'board_room', status: 'working', task: 'Quarterly alignment sprint', utilization: 82, latencyMs: 161 },
    { id: 'ord-coo', name: 'Ord-COO', zone: 'board_room', status: 'working', task: 'Cross-team standup orchestration', utilization: 74, latencyMs: 139 },
    { id: 'ord-cfa', name: 'Ord-CFA', zone: 'board_room', status: 'idle', task: 'Monitoring treasury variance', utilization: 58, latencyMs: 129 },
    { id: 'ord-daa', name: 'Ord-DAA', zone: 'operations_floor', status: 'working', task: 'Forecast model refresh', utilization: 79, latencyMs: 145 },
    { id: 'ord-design', name: 'Ord-Design', zone: 'operations_floor', status: 'working', task: 'Polishing launch visuals', utilization: 91, latencyMs: 178 },
    { id: 'ord-backend', name: 'Ord-Backend', zone: 'operations_floor', status: 'blocked', task: 'Waiting on deploy window', utilization: 44, latencyMs: 211 },
  ],
  activity: [
    { id: 'a1', timestamp: new Date().toISOString(), speaker: 'Ord-COO', message: 'Team, hydrate and ship. Velocity is beautiful today.', tone: 'banter' },
    { id: 'a2', timestamp: new Date().toISOString(), speaker: 'Ord-CFA', message: 'Revenue trendline is up 14%. Coffee budget also up 14%. Correlation noted.', tone: 'finance' },
    { id: 'a3', timestamp: new Date().toISOString(), speaker: 'Ord-PM', message: 'War Room starts in 10. Bring risks, receipts, and vibes.', tone: 'ops' },
  ],
  financials: [
    { period: 'Jan', revenue: 220000, burn: 128000, runway: 17.8, efficiency: 1.72 },
    { period: 'Feb', revenue: 236000, burn: 132000, runway: 18.1, efficiency: 1.79 },
    { period: 'Mar', revenue: 251000, burn: 138000, runway: 18.7, efficiency: 1.82 },
    { period: 'Apr', revenue: 266000, burn: 141000, runway: 19.2, efficiency: 1.89 },
    { period: 'May', revenue: 281000, burn: 145000, runway: 19.8, efficiency: 1.93 },
    { period: 'Jun', revenue: 298000, burn: 149000, runway: 20.2, efficiency: 2.0 },
  ],
  products: [
    { id: 'p1', name: 'Ord HQ', stage: 'Live', owner: 'Ord-PM', mrr: 88000 },
    { id: 'p2', name: 'Variation Forge', stage: 'Beta', owner: 'Ord-Design', mrr: 43000 },
    { id: 'p3', name: 'Treasury Lens', stage: 'Ideation', owner: 'Ord-CFA', mrr: 17000 },
  ],
  previewUrl: 'https://example.com',
  warRoomTopic: 'Launch readiness for the next product sprint',
  updatedAt: new Date().toISOString(),
}
