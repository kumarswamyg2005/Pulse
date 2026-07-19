import { useState, type FormEvent } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"

import { Header } from "@/components/Header"
import { StatusDot } from "@/components/StatusDot"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useAuth } from "@/lib/auth"
import { createMonitor, listMonitors, type MonitorType } from "@/lib/monitors"

export default function Dashboard() {
  const { me } = useAuth()
  const qc = useQueryClient()
  const canManage = me?.current_team?.role !== "member"

  const { data: monitors } = useQuery({
    queryKey: ["monitors", me?.current_team?.id],
    queryFn: listMonitors,
    enabled: !!me,
    refetchInterval: 15000,
  })

  const [name, setName] = useState("")
  const [type, setType] = useState<MonitorType>("http")
  const [target, setTarget] = useState("")
  const [port, setPort] = useState("")
  const [err, setErr] = useState<string | null>(null)

  const createMut = useMutation({
    mutationFn: () =>
      createMonitor(
        type === "http"
          ? { name, type, url: target }
          : type === "tcp"
            ? { name, type, host: target, port: Number(port) }
            : { name, type, host: target }
      ),
    onSuccess: () => {
      setName("")
      setTarget("")
      setPort("")
      setErr(null)
      qc.invalidateQueries({ queryKey: ["monitors"] })
    },
    onError: (e) => setErr(e instanceof Error ? e.message : "Failed to create monitor"),
  })

  const onCreate = (e: FormEvent) => {
    e.preventDefault()
    createMut.mutate()
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="mx-auto max-w-5xl space-y-6 p-6">
        <h1 className="text-2xl font-bold">Monitors</h1>

        {canManage && (
          <form onSubmit={onCreate} className="flex flex-wrap items-center gap-2">
            <Input
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="max-w-[10rem]"
              required
            />
            <select
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              value={type}
              onChange={(e) => setType(e.target.value as MonitorType)}
            >
              <option value="http">HTTP</option>
              <option value="tcp">TCP</option>
              <option value="ping">Ping</option>
            </select>
            <Input
              placeholder={type === "http" ? "https://example.com" : "host.example.com"}
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="max-w-xs"
              required
            />
            {type === "tcp" && (
              <Input
                type="number"
                placeholder="port"
                value={port}
                onChange={(e) => setPort(e.target.value)}
                className="max-w-[6rem]"
                required
              />
            )}
            <Button type="submit" disabled={createMut.isPending}>
              Add monitor
            </Button>
            {err && <span className="text-sm text-destructive">{err}</span>}
          </form>
        )}

        <div className="divide-y rounded-md border">
          {monitors?.length === 0 && (
            <p className="p-4 text-sm text-muted-foreground">No monitors yet.</p>
          )}
          {monitors?.map((m) => (
            <Link
              key={m.id}
              to={`/monitors/${m.id}`}
              className="flex items-center justify-between p-4 hover:bg-accent"
            >
              <div>
                <div className="font-medium">{m.name}</div>
                <div className="text-sm text-muted-foreground">{m.url ?? `${m.host}:${m.port}`}</div>
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                {m.uptime_24h !== null && <span>{m.uptime_24h}% 24h</span>}
                <StatusDot up={m.last_status} />
                {m.paused && (
                  <span className="rounded bg-muted px-2 py-0.5 text-xs">paused</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  )
}
