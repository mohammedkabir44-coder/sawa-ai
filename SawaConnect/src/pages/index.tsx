import { useEffect, useState } from 'react'
import Placeholder from '../components/Placeholder'
import { useAuth } from '../context/AuthContext'
import { analyticsApi, type DashboardResponse } from '../lib/api'

export { default as Campaigns } from './Campaigns'
export { default as Automations } from './Automations'
export { default as Analytics } from './Analytics'

export function Dashboard() {
  const { user, currentBusiness } = useAuth()
  const [dash, setDash] = useState<DashboardResponse | null>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await analyticsApi.dashboard()
        if (!cancelled) setDash(data)
      } catch {
        /* non-fatal for the landing page */
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const metrics = [
    {
      label: 'Messages (30d)',
      value: dash ? String(dash.stats.total_messages_30d) : '0',
      hint: 'WhatsApp + SMS',
    },
    {
      label: 'Active Automations',
      value: dash ? String(dash.stats.active_automations) : '0',
      hint: 'Running workflows',
    },
    {
      label: 'Won Leads',
      value: dash ? String(dash.stats.won_leads) : '0',
      hint: 'Closed deals',
    },
    {
      label: 'Delivery Rate',
      value: dash ? `${dash.stats.campaign_delivery_rate}%` : '0%',
      hint: 'Campaign delivery',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900">
          Welcome back, {user?.full_name?.split(' ')[0] ?? 'there'} 👋
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          {currentBusiness
            ? `Working in ${currentBusiness.name}`
            : 'Select a business to continue'}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <div
            key={m.label}
            className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm"
          >
            <div className="text-sm font-medium text-gray-500">{m.label}</div>
            <div className="mt-2 text-3xl font-bold text-gray-900">{m.value}</div>
            <div className="mt-1 text-xs text-gray-400">{m.hint}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function Customers() {
  return <Placeholder title="Customers" />
}

export function Leads() {
  return <Placeholder title="Leads" />
}

export function Conversations() {
  return <Placeholder title="Conversations" />
}

export function Products() {
  return <Placeholder title="Products" />
}

export function WhatsApp() {
  return <Placeholder title="WhatsApp" />
}

export function SMS() {
  return <Placeholder title="SMS" />
}

export function AIAssistant() {
  return <Placeholder title="AI Assistant" />
}

export function Team() {
  return <Placeholder title="Team" />
}

export function Settings() {
  return <Placeholder title="Settings" />
}