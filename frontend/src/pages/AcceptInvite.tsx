import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link, useNavigate, useParams } from "react-router-dom"

import { AuthShell } from "@/components/AuthShell"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth"
import { acceptInvite, getInvite } from "@/lib/teams"

export default function AcceptInvite() {
  const { token = "" } = useParams()
  const { me } = useAuth()
  const qc = useQueryClient()
  const nav = useNavigate()

  const { data: info, isLoading, isError } = useQuery({
    queryKey: ["invite", token],
    queryFn: () => getInvite(token),
    retry: false,
  })

  const accept = useMutation({
    mutationFn: () => acceptInvite(token),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["me"] })
      nav("/team")
    },
  })

  if (isLoading) return <AuthShell title="Loading invite…">{null}</AuthShell>
  if (isError || !info)
    return (
      <AuthShell title="Invite not found">
        <p className="text-center text-sm text-muted-foreground">
          This invite is invalid or expired.
        </p>
      </AuthShell>
    )

  return (
    <AuthShell title={`Join ${info.team_name}`}>
      <p className="text-center text-sm text-muted-foreground">
        You've been invited as <strong>{info.role}</strong> ({info.email}).
      </p>
      {me ? (
        <>
          {me.user.email.toLowerCase() !== info.email.toLowerCase() && (
            <p className="text-center text-sm text-destructive">
              You're signed in as {me.user.email}. This invite is for {info.email}.
            </p>
          )}
          <Button className="w-full" onClick={() => accept.mutate()} disabled={accept.isPending}>
            Accept invite
          </Button>
          {accept.isError && (
            <p className="text-center text-sm text-destructive">
              {accept.error instanceof Error ? accept.error.message : "Could not accept"}
            </p>
          )}
        </>
      ) : (
        <p className="text-center text-sm">
          <Link className="underline" to="/login">
            Sign in
          </Link>{" "}
          or{" "}
          <Link className="underline" to="/signup">
            create an account
          </Link>{" "}
          with {info.email} to accept.
        </p>
      )}
    </AuthShell>
  )
}
