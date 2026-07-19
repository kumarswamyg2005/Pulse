import { api } from "@/lib/api"
import type { Role } from "@/lib/auth"

export interface Member {
  user_id: string
  email: string
  role: Role
}

export interface InviteInfo {
  team_name: string
  email: string
  role: Role
}

export const listMembers = (teamId: string) => api<Member[]>(`/teams/${teamId}/members`)

export const invite = (teamId: string, email: string, role: Role) =>
  api(`/teams/${teamId}/invites`, { method: "POST", body: JSON.stringify({ email, role }) })

export const changeRole = (teamId: string, userId: string, role: Role) =>
  api(`/teams/${teamId}/members/${userId}`, { method: "PATCH", body: JSON.stringify({ role }) })

export const removeMember = (teamId: string, userId: string) =>
  api(`/teams/${teamId}/members/${userId}`, { method: "DELETE" })

export const switchTeam = (teamId: string) => api(`/teams/${teamId}/switch`, { method: "POST" })

export const getInvite = (token: string) => api<InviteInfo>(`/invites/${token}`)

export const acceptInvite = (token: string) => api(`/invites/${token}/accept`, { method: "POST" })

export const createTeam = (name: string) =>
  api<{ id: string }>("/teams", { method: "POST", body: JSON.stringify({ name }) })
