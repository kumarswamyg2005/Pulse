export function StatusDot({ up }: { up: boolean | null }) {
  const color = up === null ? "bg-muted-foreground" : up ? "bg-green-500" : "bg-destructive"
  const label = up === null ? "pending" : up ? "up" : "down"
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`h-2.5 w-2.5 rounded-full ${color}`} />
      {label}
    </span>
  )
}
