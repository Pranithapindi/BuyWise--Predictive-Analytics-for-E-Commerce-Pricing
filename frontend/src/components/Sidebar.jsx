import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  HiHome, HiShoppingBag, HiChartBar, HiBell, HiSearch,
  HiUser, HiCog, HiLogout, HiSparkles, HiTrendingUp, HiDocumentReport
} from 'react-icons/hi'

const navItems = [
  { to: '/dashboard', icon: HiHome,        label: 'Dashboard' },
  { to: '/products',  icon: HiShoppingBag, label: 'Products' },
  { to: '/search',    icon: HiSearch,      label: 'Search' },
  { to: '/alerts',    icon: HiBell,        label: 'Alerts' },
  { to: '/profile',   icon: HiUser,        label: 'Profile' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 h-full flex flex-col bg-surface-800 border-r border-slate-700/50 shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-700/50">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center shadow-lg shadow-primary-500/30">
          <HiTrendingUp className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-base font-bold text-white">PriceTracker</h1>
          <p className="text-xs text-slate-400">AI Price Intelligence</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <p className="px-4 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Main</p>

        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'nav-item-active' : ''}`
            }
          >
            <Icon className="w-5 h-5" />
            <span>{label}</span>
          </NavLink>
        ))}

        {/* AI Features */}
        <p className="px-4 mt-6 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">AI & Analytics</p>
        <NavLink
          to="/analytics"
          className={({ isActive }) =>
            `nav-item ${isActive ? 'nav-item-active' : ''}`
          }
        >
          <HiChartBar className="w-5 h-5" />
          <span>Analytics</span>
        </NavLink>

        <NavLink
          to="/reports"
          className={({ isActive }) =>
            `nav-item ${isActive ? 'nav-item-active' : ''}`
          }
        >
          <HiDocumentReport className="w-5 h-5 text-emerald-400" />
          <span>Reports</span>
        </NavLink>

        <NavLink
          to="/predictions"
          className={({ isActive }) =>
            `nav-item ${isActive ? 'nav-item-active' : ''}`
          }
        >
          <HiSparkles className="w-5 h-5 text-purple-400" />
          <span>ML Predictions</span>
          <span className="ml-auto badge badge-purple">AI</span>
        </NavLink>

        {/* Admin only */}
        {user?.role === 'admin' && (
          <>
            <p className="px-4 mt-6 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Admin</p>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `nav-item ${isActive ? 'nav-item-active' : ''}`
              }
            >
              <HiCog className="w-5 h-5" />
              <span>Admin Panel</span>
            </NavLink>
          </>
        )}
      </nav>

      {/* User Info & Logout */}
      <div className="px-3 py-4 border-t border-slate-700/50">
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl mb-2">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white shrink-0">
            {user?.username?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.username}</p>
            <p className="text-xs text-slate-400 truncate">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="nav-item w-full text-red-400 hover:text-red-300 hover:bg-red-500/10"
        >
          <HiLogout className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  )
}
