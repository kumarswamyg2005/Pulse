import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate, useParams } from "react-router-dom"

import { Header } from "@/components/Header"
import { IncidentTable } from "@/components/IncidentTable"
import { StatusDot } from "@/components/StatusDot"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"
import { monitorIncidents } from "@/lib/incidents"
import { deleteMonitor, getMonitor, getResults, updateMonitor } from "@/lib/monitors"

export default function MonitorDetail() {
  const { id = "" } = useParams()
  const { me } = useAuth()
  const qc = useQueryClient()
  const nav = useNavigate()
  const canManage = me?.current_team?.role !== "member"

  const { data: m, isError } = useQuery({
    queryKey: ["monitor", id],
    queryFn: () => getMonitor(id),
    retry: false,
    refetchInterval: 15000,
  })
  const { data: results } = useQuery({
    queryKey: ["results", id],
    queryFn: () => getResults(id),
    enabled: !!m,
    refetchInterval: 15000,
  })
  const { data: incidents } = useQuery({
    queryKey: ["monitor-incidents", id],
    queryFn: () => monitorIncidents(id),
    enabled: !!m,
    refetchInterval: 15000,
  })

  const pauseMut = useMutation({
    mutationFn: () => updateMonitor(id, { paused: !m!.paused }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["monitor", id] }),
  })
  const publicMut = useMutation({
    mutationFn: () => updateMonitor(id, { public: !m!.public }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["monitor", id] }),
  })
  const deleteMut = useMutation({
    mutationFn: () => deleteMonitor(id),
    onSuccess: () => nav("/"),
  })

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="mx-auto max-w-3xl space-y-6 p-6">
        <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
          ← Monitors
        </Link>
        {isError || !m ? (
          <p className="text-muted-foreground">Monitor not found.</p>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold">{m.name}</h1>
                <StatusDot up={m.last_status} />
              </div>
              {canManage && (
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={() => publicMut.mutate()}>
                    {m.public ? "Make private" : "Make public"}
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => pauseMut.mutate()}>
                    {m.paused ? "Resume" : "Pause"}
                  </Button>
                  <Button variant="destructive" size="sm" onClick={() => deleteMut.mutate()}>
                    Delete
                  </Button>
                </div>
              )}
            </div>

            <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
              <Field label="Uptime 24h" value={m.uptime_24h !== null ? `${m.uptime_24h}%` : "—"} />
              <Field label="Type" value={m.type.toUpperCase()} />
              <Field label="Interval" value={`${m.interval_seconds}s`} />
              <Field label="State" value={m.paused ? "paused" : "active"} />
              <Field label="Target" value={m.url ?? `${m.host}:${m.port}`} />
              <Field
                label="Expected status"
                value={`${m.expected_status_min}–${m.expected_status_max}`}
              />
              <Field label="Keyword" value={m.keyword ?? "—"} />
              <Field label="Public" value={m.public ? "yes" : "no"} />
            </dl>

            <section>
              <h2 className="mb-2 font-semibold">Incidents</h2>
              <IncidentTable
                incidents={incidents ?? []}
                showMonitor={false}
                invalidateKey={["monitor-incidents", id]}
              />
            </section>

            <section>
              <h2 className="mb-2 font-semibold">Recent checks</h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="py-2">When</th>
                    <th className="py-2">Status</th>
                    <th className="py-2">Code</th>
                    <th className="py-2">Latency</th>
                    <th className="py-2">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {results?.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-3 text-muted-foreground">
                        No checks yet — the scheduler runs on the monitor's interval.
                      </td>
                    </tr>
                  )}
                  {results?.map((r, i) => (
                    <tr key={i} className="border-b">
                      <td className="py-2">{new Date(r.checked_at).toLocaleTimeString()}</td>
                      <td className="py-2">
                        <StatusDot up={r.up} />
                      </td>
                      <td className="py-2">{r.status_code ?? "—"}</td>
                      <td className="py-2">{r.latency_ms !== null ? `${r.latency_ms}ms` : "—"}</td>
                      <td className="py-2 text-muted-foreground">{r.error ?? ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </>
        )}
      </main>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  )
}
