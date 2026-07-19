import { useState, type FormEvent } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { Header } from "@/components/Header"
import { WebhooksSection } from "@/components/WebhooksSection"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useAuth, type Role } from "@/lib/auth"
import { changeRole, invite, listMembers, removeMember } from "@/lib/teams"

export default function TeamMembers() {
  const { me } = useAuth()
  const qc = useQueryClient()
  const team = me?.current_team
  const canManage = team?.role === "owner" || team?.role === "admin"

  const { data: members } = useQuery({
    queryKey: ["members", team?.id],
    queryFn: () => listMembers(team!.id),
    enabled: !!team,
  })

  const [email, setEmail] = useState("")
  const [role, setRole] = useState<Role>("member")
  const [msg, setMsg] = useState<string | null>(null)

  const refetch = () => qc.invalidateQueries({ queryKey: ["members", team?.id] })
  const inviteMut = useMutation({
    mutationFn: () => invite(team!.id, email, role),
    onSuccess: () => {
      setMsg(`Invite sent to ${email}`)
      setEmail("")
    },
    onError: (e) => setMsg(e instanceof Error ? e.message : "Invite failed"),
  })
  const roleMut = useMutation({
    mutationFn: (v: { userId: string; role: Role }) => changeRole(team!.id, v.userId, v.role),
    onSuccess: refetch,
  })
  const removeMut = useMutation({
    mutationFn: (userId: string) => removeMember(team!.id, userId),
    onSuccess: refetch,
  })

  const onInvite = (e: FormEvent) => {
    e.preventDefault()
    setMsg(null)
    inviteMut.mutate()
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="mx-auto max-w-3xl space-y-6 p-6">
        <h1 className="text-2xl font-bold">Team — {team?.name}</h1>

        {canManage && (
          <form onSubmit={onInvite} className="flex flex-wrap items-center gap-2">
            <Input
              type="email"
              placeholder="teammate@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="max-w-xs"
              required
            />
            <select
              className="h-9 rounded-md border border-input bg-background px-2 text-sm"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
            >
              <option value="member">Member</option>
              <option value="admin">Admin</option>
            </select>
            <Button type="submit" disabled={inviteMut.isPending}>
              Invite
            </Button>
            {msg && <span className="text-sm text-muted-foreground">{msg}</span>}
          </form>
        )}

        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-muted-foreground">
              <th className="py-2">Email</th>
              <th className="py-2">Role</th>
              {canManage && <th className="py-2"></th>}
            </tr>
          </thead>
          <tbody>
            {members?.map((m) => (
              <tr key={m.user_id} className="border-b">
                <td className="py-2">{m.email}</td>
                <td className="py-2">
                  {canManage && m.role !== "owner" ? (
                    <select
                      className="rounded-md border border-input bg-background px-2 py-1"
                      value={m.role}
                      onChange={(e) =>
                        roleMut.mutate({ userId: m.user_id, role: e.target.value as Role })
                      }
                    >
                      <option value="member">member</option>
                      <option value="admin">admin</option>
                    </select>
                  ) : (
                    m.role
                  )}
                </td>
                {canManage && (
                  <td className="py-2 text-right">
                    {m.role !== "owner" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeMut.mutate(m.user_id)}
                      >
                        Remove
                      </Button>
                    )}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>

        {canManage && team && <WebhooksSection teamId={team.id} />}
      </main>
    </div>
  )
}
