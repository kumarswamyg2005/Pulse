import { api } from "@/lib/api"

export type MonitorType = "http" | "tcp" | "ping"

export interface Monitor {
  id: string
  team_id: string
  name: string
  type: MonitorType
  url: string | null
  host: string | null
  port: number | null
  expected_status_min: number
  expected_status_max: number
  keyword: string | null
  timeout_seconds: number
  interval_seconds: number
  public: boolean
  paused: boolean
  next_check_at: string | null
  cert_expires_at: string | null
  last_status: boolean | null
  last_checked_at: string | null
  uptime_24h: number | null
}

export interface CheckResult {
  checked_at: string
  up: boolean
  status_code: number | null
  latency_ms: number | null
  error: string | null
}

export interface MonitorInput {
  name: string
  type?: MonitorType
  url?: string
  host?: string
  port?: number
  keyword?: string
  interval_seconds?: number
  timeout_seconds?: number
  public?: boolean
}

export const listMonitors = () => api<Monitor[]>("/monitors")
export const getMonitor = (id: string) => api<Monitor>(`/monitors/${id}`)
export const getResults = (id: string) => api<CheckResult[]>(`/monitors/${id}/results`)
export const createMonitor = (body: MonitorInput) =>
  api<Monitor>("/monitors", { method: "POST", body: JSON.stringify(body) })
export const updateMonitor = (id: string, body: Partial<Monitor>) =>
  api<Monitor>(`/monitors/${id}`, { method: "PATCH", body: JSON.stringify(body) })
export const deleteMonitor = (id: string) => api(`/monitors/${id}`, { method: "DELETE" })
