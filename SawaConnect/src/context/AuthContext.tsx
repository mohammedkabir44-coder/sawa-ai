import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'
import {
  authApi,
  getStoredBusinessId,
  getToken,
  setStoredBusinessId,
  setToken,
  type BusinessOut,
  type MeResponse,
  type RegisterRequest,
  type UserOut,
} from '../lib/api'

interface AuthContextValue {
  user: UserOut | null
  businesses: BusinessOut[]
  currentBusiness: BusinessOut | null
  loading: boolean
  initializing: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => void
  setCurrentBusiness: (business: BusinessOut) => void
  refreshMe: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [businesses, setBusinesses] = useState<BusinessOut[]>([])
  const [currentBusiness, setCurrentBusinessState] = useState<BusinessOut | null>(
    null,
  )
  const [loading, setLoading] = useState(false)
  const [initializing, setInitializing] = useState(true)

  const refreshMe = useCallback(async () => {
    const data: MeResponse = await authApi.me()
    setUser(data.user)
    setBusinesses(data.memberships.map((m) => m.business))

    // Restore the saved business selection, or fall back to the first one.
    const storedId = getStoredBusinessId()
    const selected =
      data.memberships.find((m) => String(m.business.id) === storedId)?.business ??
      data.memberships[0]?.business ??
      null
    setCurrentBusinessState(selected)
    if (selected) setStoredBusinessId(String(selected.id))
    else setStoredBusinessId(null)
  }, [])

  // On page refresh, restore the session from the stored token.
  useEffect(() => {
    async function bootstrap() {
      if (!getToken()) {
        setInitializing(false)
        return
      }
      try {
        await refreshMe()
      } catch {
        // Token invalid/expired — cleared by apiFetch.
        setUser(null)
        setBusinesses([])
        setCurrentBusinessState(null)
      } finally {
        setInitializing(false)
      }
    }
    bootstrap()
  }, [refreshMe])

  const login = useCallback(
    async (email: string, password: string) => {
      setLoading(true)
      try {
        const data = await authApi.login(email, password)
        setToken(data.access_token)
        await refreshMe()
      } finally {
        setLoading(false)
      }
    },
    [refreshMe],
  )

  const register = useCallback(
    async (data: RegisterRequest) => {
      setLoading(true)
      try {
        const token = await authApi.register(data)
        setToken(token.access_token)
        await refreshMe()
      } finally {
        setLoading(false)
      }
    },
    [refreshMe],
  )

  const logout = useCallback(() => {
    setToken(null)
    setStoredBusinessId(null)
    setUser(null)
    setBusinesses([])
    setCurrentBusinessState(null)
  }, [])

  const setCurrentBusiness = useCallback(
    (business: BusinessOut) => {
      setCurrentBusinessState(business)
      setStoredBusinessId(String(business.id))
    },
    [],
  )

  return (
    <AuthContext.Provider
      value={{
        user,
        businesses,
        currentBusiness,
        loading,
        initializing,
        login,
        register,
        logout,
        setCurrentBusiness,
        refreshMe,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside an AuthProvider')
  }
  return ctx
}