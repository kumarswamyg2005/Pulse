import { createContext, useContext, type ReactNode } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { api, ApiError } from "@/lib/api"

export type Role = "owner" | "admin" | "member"

export interface Team {
  id: string
  name: string
  slug: string
  role: Role
}

export interface Me {
  user: { id: string; email: string }
  current_team: Team | null
  teams: Team[]
}

interface AuthContextValue {
  me: Me | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

async function fetchMe(): Promise<Me | null> {
  try {
    return await api<Me>("/auth/me")
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) return null
    throw e
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ["me"], queryFn: fetchMe })
  const refresh = () => qc.invalidateQueries({ queryKey: ["me"] })

  const loginMut = useMutation({
    mutationFn: (v: { email: string; password: string }) =>
      api("/auth/login", { method: "POST", body: JSON.stringify(v) }),
    onSuccess: refresh,
  })
  const signupMut = useMutation({
    mutationFn: (v: { email: string; password: string }) =>
      api("/auth/signup", { method: "POST", body: JSON.stringify(v) }),
    onSuccess: refresh,
  })
  const logoutMut = useMutation({
    mutationFn: () => api("/auth/logout", { method: "POST" }),
    onSuccess: refresh,
  })

  const value: AuthContextValue = {
    me: data ?? null,
    loading: isLoading,
    login: async (email, password) => {
      await loginMut.mutateAsync({ email, password })
    },
    signup: async (email, password) => {
      await signupMut.mutateAsync({ email, password })
    },
    logout: async () => {
      await logoutMut.mutateAsync()
    },
  }
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
