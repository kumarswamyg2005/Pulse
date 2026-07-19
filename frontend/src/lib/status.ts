import { api } from "@/lib/api"

export interface StatusMonitor {
  name: string
  type: string
  status: boolean | null
  uptime_24h: number | null
}

export interface StatusIncident {
  monitor_name: string
  status: string
  started_at: string
  resolved_at: string | null
}

export interface StatusPageData {
  team: string
  monitors: StatusMonitor[]
  incidents: StatusIncident[]
}

export const getStatus = (slug: string) => api<StatusPageData>(`/status/${slug}`)
