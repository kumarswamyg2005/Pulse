import { useState, type FormEvent } from "react"

import { Link, useNavigate, useSearchParams } from "react-router-dom"

import { AuthShell } from "@/components/AuthShell"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

export default function ResetPassword() {
  const [params] = useSearchParams()
  const token = params.get("token") ?? ""
  const nav = useNavigate()
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await api("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      })
      nav("/login")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset failed")
    } finally {
      setBusy(false)
    }
  }

  if (!token) {
    return (
      <AuthShell title="Invalid reset link">
        <p className="text-center text-sm text-muted-foreground">
          This link is missing its token.{" "}
          <Link className="underline" to="/forgot-password">
            Request a new one
          </Link>
          .
        </p>
      </AuthShell>
    )
  }

  return (
    <AuthShell title="Choose a new password">
      <form onSubmit={submit} className="space-y-3">
        <Input
          type="password"
          placeholder="New password (min 8 chars)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? "Saving…" : "Set new password"}
        </Button>
      </form>
    </AuthShell>
  )
}
