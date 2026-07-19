import { useState, type FormEvent } from "react"

import { Link } from "react-router-dom"

import { AuthShell } from "@/components/AuthShell"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"

export default function ForgotPassword() {
  const [email, setEmail] = useState("")
  const [sent, setSent] = useState(false)
  const [busy, setBusy] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    try {
      await api("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }) })
      setSent(true)
    } finally {
      setBusy(false)
    }
  }

  if (sent) {
    return (
      <AuthShell title="Check your email">
        <p className="text-center text-sm text-muted-foreground">
          If an account exists for {email}, a reset link is on its way.
        </p>
        <p className="text-center text-sm">
          <Link className="underline" to="/login">
            Back to sign in
          </Link>
        </p>
      </AuthShell>
    )
  }

  return (
    <AuthShell title="Reset your password">
      <form onSubmit={submit} className="space-y-3">
        <Input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Button type="submit" className="w-full" disabled={busy}>
          {busy ? "Sending…" : "Send reset link"}
        </Button>
      </form>
      <p className="text-center text-sm text-muted-foreground">
        <Link className="underline" to="/login">
          Back to sign in
        </Link>
      </p>
    </AuthShell>
  )
}
