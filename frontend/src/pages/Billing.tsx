import { useMutation, useQuery } from "@tanstack/react-query"

import { Header } from "@/components/Header"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"
import { checkout, getBilling, portal } from "@/lib/billing"

export default function Billing() {
  const { me } = useAuth()
  const isOwner = me?.current_team?.role === "owner"
  const { data: billing } = useQuery({
    queryKey: ["billing", me?.current_team?.id],
    queryFn: getBilling,
    enabled: !!me,
  })

  const checkoutMut = useMutation({
    mutationFn: (tier: string) => checkout(tier),
    onSuccess: ({ url }) => {
      window.location.href = url
    },
  })
  const portalMut = useMutation({
    mutationFn: portal,
    onSuccess: ({ url }) => {
      window.location.href = url
    },
  })

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="mx-auto max-w-3xl space-y-6 p-6">
        <h1 className="text-2xl font-bold">Billing</h1>

        {billing && (
          <div className="space-y-4">
            <div className="rounded-md border p-4">
              <div className="flex items-baseline justify-between">
                <div>
                  <div className="text-sm text-muted-foreground">Current plan</div>
                  <div className="text-xl font-semibold capitalize">{billing.tier}</div>
                </div>
                {billing.status && (
                  <span className="rounded bg-muted px-2 py-0.5 text-sm">{billing.status}</span>
                )}
              </div>
              {billing.current_period_end && (
                <p className="mt-2 text-sm text-muted-foreground">
                  Renews {new Date(billing.current_period_end).toLocaleDateString()}
                </p>
              )}
              <dl className="mt-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Monitors</dt>
                  <dd>{billing.limits.max_monitors}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Min interval</dt>
                  <dd>{billing.limits.min_interval}s</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Seats</dt>
                  <dd>{billing.limits.max_seats}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Webhooks</dt>
                  <dd>{billing.limits.webhooks ? "yes" : "no"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Retention</dt>
                  <dd>{billing.limits.retention_days}d</dd>
                </div>
              </dl>
            </div>

            {isOwner && billing.tier !== "team" && (
              <div className="flex gap-3">
                {billing.tier === "free" && (
                  <Button
                    onClick={() => checkoutMut.mutate("pro")}
                    disabled={checkoutMut.isPending}
                  >
                    Upgrade to Pro
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={() => checkoutMut.mutate("team")}
                  disabled={checkoutMut.isPending}
                >
                  Upgrade to Team
                </Button>
              </div>
            )}
            {isOwner && billing.tier !== "free" && (
              <Button
                variant="outline"
                onClick={() => portalMut.mutate()}
                disabled={portalMut.isPending}
              >
                Manage billing
              </Button>
            )}
            {!isOwner && (
              <p className="text-sm text-muted-foreground">
                Only the team owner can change the plan.
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
