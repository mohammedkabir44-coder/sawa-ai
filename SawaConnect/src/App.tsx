import type { ReactNode } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import CreateBusiness from './pages/auth/CreateBusiness'
import {
  AIAssistant,
  Analytics,
  Automations,
  Campaigns,
  Conversations,
  Customers,
  Dashboard,
  Leads,
  Products,
  Settings,
  SMS,
  Team,
  WhatsApp,
} from './pages'

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, initializing } = useAuth()

  if (initializing) {
    return (
      <div className="flex min-h-full items-center justify-center bg-gray-50">
        <div className="text-sm text-gray-500">Loading workspace...</div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function AppRoutes() {
  const { user, businesses } = useAuth()

  // If signed in but has no business, force the Create Business page.
  if (user && businesses.length === 0) {
    return (
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route
          path="*"
          element={
            <ProtectedRoute>
              <CreateBusiness />
            </ProtectedRoute>
          }
        />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/leads" element={<Leads />} />
        <Route path="/conversations" element={<Conversations />} />
        <Route path="/products" element={<Products />} />
        <Route path="/whatsapp" element={<WhatsApp />} />
        <Route path="/sms" element={<SMS />} />
        <Route path="/campaigns" element={<Campaigns />} />
        <Route path="/automations" element={<Automations />} />
        <Route path="/ai" element={<AIAssistant />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/team" element={<Team />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}