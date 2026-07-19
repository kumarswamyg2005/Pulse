import { Navigate, Route, Routes } from "react-router-dom"

import AcceptInvite from "@/pages/AcceptInvite"
import Billing from "@/pages/Billing"
import Dashboard from "@/pages/Dashboard"
import ForgotPassword from "@/pages/ForgotPassword"
import Incidents from "@/pages/Incidents"
import Login from "@/pages/Login"
import MonitorDetail from "@/pages/MonitorDetail"
import ResetPassword from "@/pages/ResetPassword"
import Signup from "@/pages/Signup"
import StatusPage from "@/pages/StatusPage"
import TeamMembers from "@/pages/TeamMembers"
import { useAuth } from "@/lib/auth"

export default function App() {
  const { me, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen grid place-items-center text-muted-foreground">Loading…</div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={me ? <Navigate to="/" replace /> : <Login />} />
      <Route path="/signup" element={me ? <Navigate to="/" replace /> : <Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/invite/:token" element={<AcceptInvite />} />
      <Route path="/status/:slug" element={<StatusPage />} />
      <Route path="/team" element={me ? <TeamMembers /> : <Navigate to="/login" replace />} />
      <Route path="/incidents" element={me ? <Incidents /> : <Navigate to="/login" replace />} />
      <Route path="/billing" element={me ? <Billing /> : <Navigate to="/login" replace />} />
      <Route
        path="/monitors/:id"
        element={me ? <MonitorDetail /> : <Navigate to="/login" replace />}
      />
      <Route path="/" element={me ? <Dashboard /> : <Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
