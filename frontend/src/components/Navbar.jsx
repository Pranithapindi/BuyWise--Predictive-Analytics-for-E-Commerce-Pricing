import { useNavigate, useLocation } from 'react-router-dom'
import { useState } from 'react'
import { HiSearch, HiBell, HiMoon, HiSun, HiRefresh } from 'react-icons/hi'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const routeTitles = {
  '/dashboard': 'Dashboard',
  '/products': 'My Products',
  '/search': 'Search Products',
  '/alerts': 'Price Alerts',
  '/profile': 'Profile',
  '/admin': 'Admin Panel',
}

export default function Navbar() {
  const { isDark, toggle } = useTheme()
  const { user } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const pageTitle = Object.entries(routeTitles).find(([path]) =>
    location.pathname.startsWith(path)
  )?.[1] || 'PriceTracker'

  const handleSearch = (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  return (
    <header className="h-16 flex items-center justify-between px-6 bg-surface-800/80 border-b border-slate-700/50 backdrop-blur-md shrink-0">
      {/* Page Title */}
      <h2 className="text-lg font-semibold text-white">{pageTitle}</h2>

      {/* Center: Search */}
      <form onSubmit={handleSearch} className="flex items-center gap-2 flex-1 max-w-md mx-6">
        <div className="relative flex-1">
          <HiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search products..."
            className="w-full pl-9 pr-4 py-2 rounded-xl bg-surface-700 border border-slate-600/50
                       text-sm text-slate-100 placeholder-slate-400
                       focus:outline-none focus:ring-1 focus:ring-primary-500/50 transition-all"
          />
        </div>
      </form>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-surface-700 transition-all"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? <HiSun className="w-5 h-5" /> : <HiMoon className="w-5 h-5" />}
        </button>

        {/* Alerts bell */}
        <button
          onClick={() => navigate('/alerts')}
          className="relative p-2 rounded-xl text-slate-400 hover:text-white hover:bg-surface-700 transition-all"
        >
          <HiBell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
        </button>

        {/* Avatar */}
        <button
          onClick={() => navigate('/profile')}
          className="w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white hover:scale-105 transition-transform"
        >
          {user?.username?.[0]?.toUpperCase() || 'U'}
        </button>
      </div>
    </header>
  )
}
