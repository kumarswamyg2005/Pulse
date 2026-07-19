import { useQuery } from "@tanstack/react-query"

import { buttonVariants } from "@/components/ui/button"
import { api, API_URL } from "@/lib/api"

export function GoogleButton() {
  const { data } = useQuery({
    queryKey: ["providers"],
    queryFn: () => api<{ google: boolean }>("/auth/providers"),
    staleTime: Infinity,
  })

  // Only show the button when Google OAuth is actually configured on the server.
  if (!data?.google) return null

  return (
    <a
      href={`${API_URL}/auth/google/login`}
      className={buttonVariants({ variant: "outline" }) + " w-full"}
    >
      Continue with Google
    </a>
  )
}
