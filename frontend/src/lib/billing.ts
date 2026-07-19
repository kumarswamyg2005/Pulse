import { api } from "@/lib/api"

export interface PlanLimits {
  max_monitors: number
  min_interval: number
  max_seats: number
  webhooks: boolean
  retention_days: number
  max_status_pages: number
}

export interface Billing {
  tier: string
  status: string | null
  current_period_end: string | null
  limits: PlanLimits
}

export const getBilling = () => api<Billing>("/billing")
export const checkout = (tier: string) =>
  api<{ url: string }>("/billing/checkout", { method: "POST", body: JSON.stringify({ tier }) })
export const portal = () => api<{ url: string }>("/billing/portal", { method: "POST" })
