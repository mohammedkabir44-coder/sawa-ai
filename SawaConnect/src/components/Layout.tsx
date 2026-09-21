import { useNavigate, NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Dashboard', to: '/' },
  { label: 'Customers', to: '/customers' },
  { label: 'Leads', to: '/leads' },
  { label: 'Conversations', to: '/conversations' },
  { label: 'Products', to: '/products' },
  { label: 'WhatsApp', to: '/whatsapp' },
  { label: 'SMS', to: '/sms' },
  { label: 'Campaigns', to: '/campaigns' },
  { label: 'Automations', to: '/automations' },
  { label: 'AI Assistant', to: '/ai' },
  { label: 'Analytics', to: '/analytics' },
  { label: 'Team', to: '/team' },
  { label: 'Settings', to: '/settings' },
]

export default function Layout() {
  const { user, businesses, currentBusiness, setCurrentBusiness, logout } =
    useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="w-60 shrink-0 border-r border-gray-200 bg-gray-50">
        <div className="flex h-14 items-center border-b border-gray-200 px-4">
          <span className="text-lg font-semibold text-gray-900">SAWA AI</span>
        </div>
        <nav className="p-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm font-medium ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-700 hover:bg-gray-200'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col">
        {/* Topbar */}
        <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
          <div className="flex items-center gap-3">
            <h1 className="text-base font-semibold text-gray-900">
              {currentBusiness?.name ?? 'SAWA AI'}
            </h1>
            {businesses.length > 1 && (
              <select
                value={currentBusiness?.id ?? ''}
                onChange={(e) => {
                  const selected = businesses.find(
                    (b) => String(b.id) === e.target.value,
                  )
                  if (selected) setCurrentBusiness(selected)
                }}
                className="rounded-lg border border-gray-300 px-2 py-1 text-sm text-gray-700 focus:border-indigo-500 focus:outline-none"
                aria-label="Switch business"
              >
                {businesses.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          <div className="flex items-center gap-4">
            <div className="text-sm text-gray-500">
              {user?.full_name ?? 'User'}
            </div>
            <button
              onClick={handleLogout}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto bg-white p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}