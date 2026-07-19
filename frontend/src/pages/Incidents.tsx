import { useQuery } from "@tanstack/react-query"

import { Header } from "@/components/Header"
import { IncidentTable } from "@/components/IncidentTable"
import { useAuth } from "@/lib/auth"
import { listIncidents } from "@/lib/incidents"

export default function Incidents() {
  const { me } = useAuth()
  const { data: incidents } = useQuery({
    queryKey: ["incidents", me?.current_team?.id],
    queryFn: listIncidents,
    enabled: !!me,
    refetchInterval: 15000,
  })

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="mx-auto max-w-5xl space-y-4 p-6">
        <h1 className="text-2xl font-bold">Incidents</h1>
        <IncidentTable
          incidents={incidents ?? []}
          invalidateKey={["incidents", me?.current_team?.id]}
        />
      </main>
    </div>
  )
}
