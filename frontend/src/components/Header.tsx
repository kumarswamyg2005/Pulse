import { type ChangeEvent } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"
import { switchTeam } from "@/lib/teams"

export function Header() {
  const { me, logout } = useAuth()
  const qc = useQueryClient()
  const nav = useNavigate()
  if (!me) return null

  const onSwitch = async (e: ChangeEvent<HTMLSelectElement>) => {
    await switchTeam(e.target.value)
    await qc.invalidateQueries()
    nav("/")
  }

  return (
    <header className="border-b">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 p-4">
        <div className="flex items-center gap-4">
          <Link to="/" className="font-semibold">
            Pulse
          </Link>
          <select
            className="rounded-md border border-input bg-background px-2 py-1 text-sm"
            value={me.current_team?.id ?? ""}
            onChange={onSwitch}
          >
            {me.teams.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
          <nav className="flex gap-3 text-sm text-muted-foreground">
            <Link to="/" className="hover:text-foreground">
              Monitors
            </Link>
            <Link to="/incidents" className="hover:text-foreground">
              Incidents
            </Link>
            <Link to="/team" className="hover:text-foreground">
              Team
            </Link>
            <Link to="/billing" className="hover:text-foreground">
              Billing
            </Link>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">{me.user.email}</span>
          <Button variant="outline" size="sm" onClick={() => logout()}>
            Sign out
          </Button>
        </div>
      </div>
    </header>
  )
}
