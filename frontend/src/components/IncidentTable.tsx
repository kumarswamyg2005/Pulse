import { useMutation, useQueryClient } from "@tanstack/react-query"

import { Button } from "@/components/ui/button"
import { acknowledgeIncident, type Incident } from "@/lib/incidents"

export function IncidentTable({
  incidents,
  showMonitor = true,
  invalidateKey,
}: {
  incidents: Incident[]
  showMonitor?: boolean
  invalidateKey: unknown[]
}) {
  const qc = useQueryClient()
  const ackMut = useMutation({
    mutationFn: (id: string) => acknowledgeIncident(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: invalidateKey }),
  })

  if (incidents.length === 0) {
    return <p className="text-sm text-muted-foreground">No incidents.</p>
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-left text-muted-foreground">
          {showMonitor && <th className="py-2">Monitor</th>}
          <th className="py-2">Status</th>
          <th className="py-2">Started</th>
          <th className="py-2">Resolved</th>
          <th className="py-2"></th>
        </tr>
      </thead>
      <tbody>
        {incidents.map((inc) => (
          <tr key={inc.id} className="border-b">
            {showMonitor && <td className="py-2">{inc.monitor_name}</td>}
            <td className="py-2">
              <span
                className={
                  inc.status === "open"
                    ? "rounded bg-destructive/10 px-2 py-0.5 text-destructive"
                    : "rounded bg-muted px-2 py-0.5"
                }
              >
                {inc.status}
              </span>
            </td>
            <td className="py-2">{new Date(inc.started_at).toLocaleString()}</td>
            <td className="py-2">
              {inc.resolved_at ? new Date(inc.resolved_at).toLocaleString() : "—"}
            </td>
            <td className="py-2 text-right">
              {inc.status === "open" &&
                (inc.acknowledged_at ? (
                  <span className="text-muted-foreground">acknowledged</span>
                ) : (
                  <Button size="sm" variant="outline" onClick={() => ackMut.mutate(inc.id)}>
                    Acknowledge
                  </Button>
                ))}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
