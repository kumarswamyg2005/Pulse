import { api } from "@/lib/api"

export interface Webhook {
  id: string
  url: string
  active: boolean
}

export const listWebhooks = () => api<Webhook[]>("/webhooks")
export const createWebhook = (url: string) =>
  api<Webhook>("/webhooks", { method: "POST", body: JSON.stringify({ url }) })
export const deleteWebhook = (id: string) => api(`/webhooks/${id}`, { method: "DELETE" })
