import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { productsAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { formatPrice, formatDiscount, formatDate } from '../utils/formatters'
import {
  HiShoppingBag, HiChartBar, HiBell, HiTrendingUp, HiTrendingDown,
  HiSparkles, HiPlus, HiRefresh, HiClock, HiDocumentReport
} from 'react-icons/hi'

function StatCard({ icon: Icon, label, value, sub, color = 'primary', trend }) {
  const colors = {
    primary: 'from-primary-500/20 to-primary-600/5 border-primary-500/20',
    green:   'from-emerald-500/20 to-emerald-600/5 border-emerald-500/20',
    red:     'from-red-500/20 to-red-600/5 border-red-500/20',
    yellow:  'from-yellow-500/20 to-yellow-600/5 border-yellow-500/20',
    purple:  'from-purple-500/20 to-purple-600/5 border-purple-500/20',
  }
  const iconColors = {
    primary: 'text-primary-400 bg-primary-500/10',
    green:   'text-emerald-400 bg-emerald-500/10',
    red:     'text-red-400 bg-red-500/10',
    yellow:  'text-yellow-400 bg-yellow-500/10',
    purple:  'text-purple-400 bg-purple-500/10',
  }

  return (
    <div className={`stat-card bg-gradient-to-br border ${colors[color]}`}>
      <div className="flex items-start justify-between">
        <div className={`p-2.5 rounded-xl ${iconColors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <span className={`text-xs font-medium ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-sm font-medium text-slate-300">{label}</p>
        {sub && <p className="text-xs text-slate-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadProducts()
  }, [])

  const loadProducts = async () => {
    setLoading(true)
    try {
      const { data } = await productsAPI.list(0, 100)
      setProducts(data)
    } catch {}
    finally { setLoading(false) }
  }

  // Aggregate stats
  const totalProducts = products.length
  const activeProducts = products.filter(p => p.is_active).length
  const totalSavings = products.reduce((acc, p) => {
    if (p.original_price && p.current_price) {
      return acc + (p.original_price - p.current_price)
    }
    return acc
  }, 0)
  const avgDiscount = products.filter(p => p.current_discount > 0).length > 0
    ? products.reduce((acc, p) => acc + (p.current_discount || 0), 0) / products.filter(p => p.current_discount > 0).length
    : 0

  const recentProducts = [...products]
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5)

  const topDiscounts = [...products]
    .filter(p => p.current_discount > 0)
    .sort((a, b) => b.current_discount - a.current_discount)
    .slice(0, 5)

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">
            Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'},{' '}
            <span className="gradient-text">{user?.username}!</span>
          </h1>
          <p className="page-subtitle">Here's your price intelligence overview</p>
        </div>
        <button
          id="add-product-btn"
          onClick={() => navigate('/products')}
          className="btn-primary"
        >
          <HiPlus className="w-4 h-4" />
          Track Product
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={HiShoppingBag}
          label="Products Tracked"
          value={totalProducts}
          sub={`${activeProducts} active`}
          color="primary"
        />
        <StatCard
          icon={HiTrendingDown}
          label="Total Savings"
          value={formatPrice(totalSavings)}
          sub="vs original prices"
          color="green"
        />
        <StatCard
          icon={HiChartBar}
          label="Avg Discount"
          value={`${avgDiscount.toFixed(0)}%`}
          sub="across tracked products"
          color="yellow"
        />
        <StatCard
          icon={HiSparkles}
          label="AI Predictions"
          value={totalProducts}
          sub="ML models trained"
          color="purple"
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Products */}
        <div className="lg:col-span-2 glass-card p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <HiClock className="w-5 h-5 text-primary-400" />
              Recently Added
            </h2>
            <button onClick={() => navigate('/products')} className="text-sm text-primary-400 hover:text-primary-300 transition-colors">
              View all →
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="spinner" />
            </div>
          ) : recentProducts.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-5xl mb-3">🛍️</div>
              <p className="text-slate-400 font-medium">No products tracked yet</p>
              <p className="text-slate-500 text-sm mt-1">Paste a product URL to start tracking prices</p>
              <button onClick={() => navigate('/products')} className="btn-primary mt-4 mx-auto">
                <HiPlus className="w-4 h-4" />
                Track Your First Product
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {recentProducts.map((p) => (
                <div
                  key={p.id}
                  onClick={() => navigate(`/products/${p.id}`)}
                  className="flex items-center gap-3 p-3 rounded-xl bg-surface-700/50 hover:bg-surface-700 cursor-pointer transition-all group"
                >
                  <div className="w-10 h-10 rounded-lg bg-surface-600 flex items-center justify-center shrink-0 overflow-hidden">
                    {p.image_url ? (
                      <img
                        src={p.image_url}
                        alt=""
                        className="w-full h-full object-contain p-1"
                        onError={(e) => {
                          e.target.onerror = null
                          e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300'
                        }}
                      />
                    ) : (
                      <span className="text-xl">🛍️</span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate group-hover:text-primary-400 transition-colors">
                      {p.name || 'Loading...'}
                    </p>
                    <p className="text-xs text-slate-500">{p.website} • {formatDate(p.created_at)}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-bold text-emerald-400">{formatPrice(p.current_price)}</p>
                    {p.current_discount > 0 && (
                      <p className="text-xs text-emerald-500">{formatDiscount(p.current_discount)}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Deals */}
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-5">
            <HiTrendingDown className="w-5 h-5 text-emerald-400" />
            Top Deals
          </h2>

          {topDiscounts.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-slate-400 text-sm">No deals yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {topDiscounts.map((p, idx) => (
                <div
                  key={p.id}
                  onClick={() => navigate(`/products/${p.id}`)}
                  className="flex items-center gap-3 cursor-pointer group"
                >
                  <span className="text-lg font-bold text-slate-500 w-6 shrink-0">
                    {idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-300 truncate group-hover:text-white transition-colors">
                      {p.name?.substring(0, 30)}...
                    </p>
                    <p className="text-xs text-slate-500">{p.website}</p>
                  </div>
                  <span className="badge badge-green shrink-0">
                    -{formatDiscount(p.current_discount)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Quick actions */}
          <div className="mt-6 pt-4 border-t border-slate-700/50 space-y-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Quick Actions</p>
            <button onClick={() => navigate('/analytics')} className="btn-secondary w-full text-sm justify-center">
              <HiChartBar className="w-4 h-4 text-primary-400" />
              View Analytics
            </button>
            <button onClick={() => navigate('/reports')} className="btn-secondary w-full text-sm justify-center">
              <HiDocumentReport className="w-4 h-4 text-emerald-400" />
              Export Reports
            </button>
            <button onClick={() => navigate('/alerts')} className="btn-secondary w-full text-sm justify-center">
              <HiBell className="w-4 h-4 text-yellow-400" />
              Manage Alerts
            </button>
            <button onClick={loadProducts} className="btn-secondary w-full text-sm justify-center">
              <HiRefresh className="w-4 h-4" />
              Refresh Data
            </button>
          </div>
        </div>
      </div>

      {/* Website Distribution */}
      {products.length > 0 && (
        <div className="glass-card p-6">
          <h2 className="text-lg font-semibold text-white mb-5 flex items-center gap-2">
            <HiChartBar className="w-5 h-5 text-primary-400" />
            Products by Website
          </h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(
              products.reduce((acc, p) => {
                acc[p.website] = (acc[p.website] || 0) + 1
                return acc
              }, {})
            ).map(([site, count]) => (
              <div key={site} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-700/50 border border-slate-700/50">
                <span className="text-sm font-medium text-slate-300 capitalize">{site}</span>
                <span className="badge badge-blue">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
