import type { ReactNode } from "react"

export function AuthShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="min-h-screen grid place-items-center bg-background text-foreground p-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg border p-6 shadow-sm">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">Pulse</h1>
          <p className="text-sm text-muted-foreground">{title}</p>
        </div>
        {children}
      </div>
    </div>
  )
}
