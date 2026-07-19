import { api } from "@/lib/api"

export interface Incident {
  id: string
  monitor_id: string
  monitor_name: string | null
  status: "open" | "resolved"
  started_at: string
  resolved_at: string | null
  acknowledged_at: string | null
  acknowledged_by: string | null
}

export const listIncidents = () => api<Incident[]>("/incidents")
export const monitorIncidents = (id: string) => api<Incident[]>(`/monitors/${id}/incidents`)
export const acknowledgeIncident = (id: string) =>
  api<Incident>(`/incidents/${id}/acknowledge`, { method: "POST" })
