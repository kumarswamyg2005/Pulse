import { useQuery } from "@tanstack/react-query"
import { useParams } from "react-router-dom"

import { StatusDot } from "@/components/StatusDot"
import { getStatus } from "@/lib/status"

export default function StatusPage() {
  const { slug = "" } = useParams()
  const { data, isError } = useQuery({
    queryKey: ["status", slug],
    queryFn: () => getStatus(slug),
    retry: false,
    refetchInterval: 30000,
  })

  if (isError) {
    return (
      <div className="grid min-h-screen place-items-center text-muted-foreground">
        Status page not found.
      </div>
    )
  }
  if (!data) {
    return <div className="grid min-h-screen place-items-center text-muted-foreground">Loading…</div>
  }

  const allUp = data.monitors.every((m) => m.status !== false)

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto max-w-3xl space-y-8 p-8">
        <header className="space-y-1">
          <h1 className="text-3xl font-bold">{data.team}</h1>
          <p className={allUp ? "text-green-600" : "text-destructive"}>
            {allUp ? "All systems operational" : "Some systems are experiencing issues"}
          </p>
        </header>

        <section className="divide-y rounded-md border">
          {data.monitors.length === 0 && (
            <p className="p-4 text-muted-foreground">No public monitors.</p>
          )}
          {data.monitors.map((m, i) => (
            <div key={i} className="flex items-center justify-between p-4">
              <span className="font-medium">{m.name}</span>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                {m.uptime_24h !== null && <span>{m.uptime_24h}% 24h</span>}
                <StatusDot up={m.status} />
              </div>
            </div>
          ))}
        </section>

        {data.incidents.length > 0 && (
          <section className="space-y-2">
            <h2 className="font-semibold">Recent incidents</h2>
            {data.incidents.map((inc, i) => (
              <div key={i} className="rounded-md border p-3 text-sm">
                <span className="font-medium">{inc.monitor_name}</span>
                <span
                  className={
                    inc.status === "open" ? "text-destructive" : "text-muted-foreground"
                  }
                >
                  {" "}
                  — {inc.status}
                </span>
                <span className="text-muted-foreground">
                  {" · "}
                  {new Date(inc.started_at).toLocaleString()}
                </span>
              </div>
            ))}
          </section>
        )}

        <footer className="text-center text-xs text-muted-foreground">Powered by Pulse</footer>
      </div>
    </div>
  )
}
