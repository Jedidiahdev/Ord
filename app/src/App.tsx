import { useMemo, useState } from 'react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts'
import { Activity, Briefcase, CircleDollarSign, GalleryHorizontal, Globe, Lock, MessagesSquare, Radar, RefreshCcw, ShieldCheck, Users, Video } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart'
import { useOrdLiveData } from '@/dashboard/useOrdLiveData'
import type { AgentSnapshot } from '@/dashboard/types'
import './App.css'

const chartConfig = {
  revenue: { label: 'Revenue', color: 'hsl(154 70% 45%)' },
  burn: { label: 'Burn', color: 'hsl(2 86% 63%)' },
  runway: { label: 'Runway', color: 'hsl(217 91% 60%)' },
  efficiency: { label: 'Efficiency', color: 'hsl(283 84% 67%)' },
}

function statusTone(status: AgentSnapshot['status']) {
  if (status === 'working') return 'bg-emerald-400/20 text-emerald-200 border-emerald-300/20'
  if (status === 'idle') return 'bg-sky-400/20 text-sky-200 border-sky-300/20'
  if (status === 'blocked') return 'bg-amber-400/20 text-amber-100 border-amber-200/20'
  return 'bg-zinc-400/20 text-zinc-200 border-zinc-200/20'
}

function AgentGrid({ title, agents }: { title: string; agents: AgentSnapshot[] }) {
  return (
    <Card className="glass-panel border-white/15">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>Live pulse of agent health, assignment, and execution speed.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2">
        {agents.map((agent) => (
          <div key={agent.id} className="rounded-xl border border-white/10 bg-white/5 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="font-semibold text-white">{agent.name}</p>
              <Badge className={statusTone(agent.status)}>{agent.status}</Badge>
            </div>
            <p className="mb-3 text-sm text-white/75">{agent.task}</p>
            <div className="space-y-2 text-xs text-white/70">
              <div className="flex items-center justify-between"><span>Utilization</span><span>{agent.utilization}%</span></div>
              <Progress value={agent.utilization} className="h-1.5 bg-white/10" />
              <div className="flex items-center justify-between"><span>Decision latency</span><span>{agent.latencyMs} ms</span></div>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

function App() {
  const [authed, setAuthed] = useState(false)
  const [username, setUsername] = useState('')
  const [secret, setSecret] = useState('')
  const [previewNonce, setPreviewNonce] = useState(0)
  const { snapshot, connected, boardRoomAgents, opsAgents } = useOrdLiveData()

  const totalMrr = useMemo(() => snapshot.products.reduce((acc, item) => acc + item.mrr, 0), [snapshot.products])

  if (!authed) {
    return (
      <main className="dark min-h-screen bg-slate-950 text-white">
        <div className="aurora-bg" />
        <section className="mx-auto flex min-h-screen max-w-md items-center px-6">
          <Card className="glass-panel w-full border-white/20">
            <CardHeader>
              <CardTitle className="text-2xl">Ord HQ Login</CardTitle>
              <CardDescription>Secure entry for executive and operations crew.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input placeholder="CEO handle" value={username} onChange={(e) => setUsername(e.target.value)} className="border-white/20 bg-white/10" />
              <Input placeholder="Access key" type="password" value={secret} onChange={(e) => setSecret(e.target.value)} className="border-white/20 bg-white/10" />
              <Button className="w-full" onClick={() => setAuthed(Boolean(username && secret))}>
                <Lock className="mr-2 h-4 w-4" /> Enter Ord HQ
              </Button>
            </CardContent>
          </Card>
        </section>
      </main>
    )
  }

  return (
    <main className="dark min-h-screen bg-slate-950 text-white">
      <div className="aurora-bg" />
      <div className="relative mx-auto max-w-7xl space-y-6 px-4 py-6 md:px-8">
        <header className="glass-panel sticky top-4 z-10 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-white/15 px-5 py-4">
          <div>
            <h1 className="text-2xl font-bold">Ord HQ Dashboard</h1>
            <p className="text-sm text-white/70">Living company control room with real-time multi-agent telemetry.</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={connected ? 'bg-emerald-500/20 text-emerald-200' : 'bg-rose-500/20 text-rose-200'}>{connected ? 'Live WebSocket' : 'Disconnected'}</Badge>
            <Badge className="bg-indigo-500/20 text-indigo-200">Updated {new Date(snapshot.updatedAt).toLocaleTimeString()}</Badge>
          </div>
        </header>

        <Tabs defaultValue="operations" className="space-y-4">
          <TabsList className="grid h-auto w-full grid-cols-2 md:grid-cols-4 lg:grid-cols-7 glass-panel">
            <TabsTrigger value="operations"><Users className="mr-1 h-4 w-4" />Ops</TabsTrigger>
            <TabsTrigger value="activity"><MessagesSquare className="mr-1 h-4 w-4" />Feed</TabsTrigger>
            <TabsTrigger value="financials"><CircleDollarSign className="mr-1 h-4 w-4" />DAA Finance</TabsTrigger>
            <TabsTrigger value="preview"><Globe className="mr-1 h-4 w-4" />Preview</TabsTrigger>
            <TabsTrigger value="products"><GalleryHorizontal className="mr-1 h-4 w-4" />Products</TabsTrigger>
            <TabsTrigger value="war-room"><Video className="mr-1 h-4 w-4" />War Room</TabsTrigger>
            <TabsTrigger value="security"><ShieldCheck className="mr-1 h-4 w-4" />Security</TabsTrigger>
          </TabsList>

          <TabsContent value="operations" className="grid gap-4 lg:grid-cols-2">
            <AgentGrid title="Board Room" agents={boardRoomAgents} />
            <AgentGrid title="Operations Floor" agents={opsAgents} />
          </TabsContent>

          <TabsContent value="activity">
            <Card className="glass-panel border-white/15">
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Activity className="h-4 w-4" /> Live Activity Feed</CardTitle>
                <CardDescription>Sweet banter + serious updates from every part of the company.</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[360px] rounded-xl border border-white/10 bg-black/20 p-4">
                  <div className="space-y-3">
                    {snapshot.activity.map((item) => (
                      <div key={item.id} className="rounded-lg border border-white/10 bg-white/5 p-3">
                        <div className="mb-1 flex items-center justify-between text-xs text-white/60">
                          <span>{item.speaker}</span>
                          <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <p className="text-sm text-white/90">{item.message}</p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="financials" className="grid gap-4 lg:grid-cols-2">
            <Card className="glass-panel border-white/15">
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Radar className="h-4 w-4" />Revenue vs Burn</CardTitle>
                <CardDescription>Combined reporting from CFA and COO controllers.</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer config={chartConfig} className="h-72 w-full">
                  <AreaChart data={snapshot.financials}>
                    <CartesianGrid vertical={false} strokeDasharray="4 4" />
                    <XAxis dataKey="period" tickLine={false} axisLine={false} />
                    <YAxis tickLine={false} axisLine={false} width={45} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Area dataKey="revenue" type="monotone" fill="var(--color-revenue)" fillOpacity={0.25} stroke="var(--color-revenue)" />
                    <Area dataKey="burn" type="monotone" fill="var(--color-burn)" fillOpacity={0.12} stroke="var(--color-burn)" />
                  </AreaChart>
                </ChartContainer>
              </CardContent>
            </Card>

            <Card className="glass-panel border-white/15">
              <CardHeader>
                <CardTitle>Runway & Efficiency</CardTitle>
                <CardDescription>DAA trend analysis for survivability and growth quality.</CardDescription>
              </CardHeader>
              <CardContent>
                <ChartContainer config={chartConfig} className="h-72 w-full">
                  <LineChart data={snapshot.financials}>
                    <CartesianGrid vertical={false} strokeDasharray="4 4" />
                    <XAxis dataKey="period" tickLine={false} axisLine={false} />
                    <YAxis yAxisId="left" tickLine={false} axisLine={false} width={40} />
                    <YAxis yAxisId="right" orientation="right" tickLine={false} axisLine={false} width={30} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Line yAxisId="left" dataKey="runway" stroke="var(--color-runway)" strokeWidth={2} dot={false} />
                    <Line yAxisId="right" dataKey="efficiency" stroke="var(--color-efficiency)" strokeWidth={2} dot={false} />
                  </LineChart>
                </ChartContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="preview">
            <Card className="glass-panel border-white/15">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Project Preview</CardTitle>
                  <CardDescription>Auto-refreshes when code pushes trigger new deploy previews.</CardDescription>
                </div>
                <Button size="sm" variant="outline" onClick={() => setPreviewNonce((value) => value + 1)}>
                  <RefreshCcw className="mr-2 h-4 w-4" /> Refresh
                </Button>
              </CardHeader>
              <CardContent>
                <iframe title="project-preview" src={`${snapshot.previewUrl}?v=${previewNonce}`} className="h-[460px] w-full rounded-xl border border-white/20 bg-white" />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="products">
            <Card className="glass-panel border-white/15">
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Briefcase className="h-4 w-4" /> Products Gallery</CardTitle>
                <CardDescription>Pipeline snapshot across ideation, beta, and live revenue lines.</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-3 md:grid-cols-3">
                {snapshot.products.map((product) => (
                  <div key={product.id} className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <p className="text-lg font-semibold">{product.name}</p>
                    <p className="text-xs text-white/70">Owner: {product.owner}</p>
                    <div className="mt-3 flex items-center justify-between">
                      <Badge className="bg-violet-500/20 text-violet-200">{product.stage}</Badge>
                      <p className="text-sm font-medium">${product.mrr.toLocaleString()} MRR</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="war-room" className="grid gap-4 lg:grid-cols-2">
            <Card className="glass-panel border-white/15">
              <CardHeader>
                <CardTitle>War Room Briefing</CardTitle>
                <CardDescription>Meeting focus and strategic asks from leadership.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="rounded-lg border border-white/10 bg-white/5 p-3 text-sm">{snapshot.warRoomTopic}</p>
                <p className="text-sm text-white/70">Suggested agenda: blockers, market pulse, fiscal risk, and launch decisions.</p>
              </CardContent>
            </Card>
            <Card className="glass-panel border-white/15">
              <CardHeader>
                <CardTitle>Execution Heatmap</CardTitle>
              </CardHeader>
              <CardContent>
                <ChartContainer config={chartConfig} className="h-56 w-full">
                  <BarChart data={snapshot.financials}>
                    <CartesianGrid vertical={false} strokeDasharray="4 4" />
                    <XAxis dataKey="period" tickLine={false} axisLine={false} />
                    <ChartTooltip content={<ChartTooltipContent />} />
                    <Bar dataKey="revenue" fill="var(--color-revenue)" radius={6} />
                  </BarChart>
                </ChartContainer>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card className="glass-panel border-white/15">
              <CardHeader>
                <CardTitle>Governance Snapshot</CardTitle>
                <CardDescription>Operational safeguards for the living company system.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-white/80">
                <p>• Signed WebSocket updates only; reject malformed events.</p>
                <p>• Executive login gate enabled for dashboard entry.</p>
                <p>• Message bus health mirrors agent responsiveness in real-time.</p>
                <p className="text-lg font-semibold text-white">Portfolio MRR: ${totalMrr.toLocaleString()}</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  )
}

export default App
