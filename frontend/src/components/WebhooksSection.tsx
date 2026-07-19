import { useState, type FormEvent } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { createWebhook, deleteWebhook, listWebhooks } from "@/lib/webhooks"

export function WebhooksSection({ teamId }: { teamId: string }) {
  const qc = useQueryClient()
  const key = ["webhooks", teamId]
  const { data: hooks } = useQuery({ queryKey: key, queryFn: listWebhooks })
  const [url, setUrl] = useState("")
  const [err, setErr] = useState<string | null>(null)

  const addMut = useMutation({
    mutationFn: () => createWebhook(url),
    onSuccess: () => {
      setUrl("")
      setErr(null)
      qc.invalidateQueries({ queryKey: key })
    },
    onError: (e) => setErr(e instanceof Error ? e.message : "Could not add webhook"),
  })
  const delMut = useMutation({
    mutationFn: (id: string) => deleteWebhook(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
  })

  const onAdd = (e: FormEvent) => {
    e.preventDefault()
    addMut.mutate()
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Webhooks</h2>
      <p className="text-sm text-muted-foreground">
        Receive a JSON POST when incidents open or resolve.
      </p>
      <form onSubmit={onAdd} className="flex gap-2">
        <Input
          placeholder="https://hooks.example.com/…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="max-w-md"
          required
        />
        <Button type="submit" disabled={addMut.isPending}>
          Add
        </Button>
      </form>
      {err && <p className="text-sm text-destructive">{err}</p>}
      <ul className="text-sm">
        {hooks?.map((h) => (
          <li key={h.id} className="flex items-center justify-between border-b py-2">
            <span className="truncate">{h.url}</span>
            <Button size="sm" variant="ghost" onClick={() => delMut.mutate(h.id)}>
              Remove
            </Button>
          </li>
        ))}
      </ul>
    </section>
  )
}
