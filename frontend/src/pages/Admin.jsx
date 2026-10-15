import { useEffect, useState } from 'react'
import { adminAPI } from '../services/api'
import { formatDate } from '../utils/formatters'
import {
  HiUsers, HiDatabase, HiExclamationCircle, HiCheckCircle,
  HiChartBar, HiShoppingBag
} from 'react-icons/hi'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

export default function Admin() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('overview')

  useEffect(() => { loadAll() }, [])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [s, u, l] = await Promise.all([
        adminAPI.stats(),
        adminAPI.users(),
        adminAPI.logs(50),
      ])
      setStats(s.data)
      setUsers(u.data)
      setLogs(l.data.logs)
    } catch {} finally { setLoading(false) }
  }

  const websiteChartData = stats
    ? Object.entries(stats.website_statistics).map(([name, count]) => ({ name, count }))
    : []

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Admin Dashboard</h1>
        <p className="page-subtitle">System overview and management</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : (
        <>
          {/* Stats */}
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Total Users', value: stats.total_users, icon: HiUsers, color: 'text-primary-400', bg: 'bg-primary-500/10' },
                { label: 'Total Products', value: stats.total_products, icon: HiShoppingBag, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
                { label: 'Scrapes Today', value: stats.total_scrapes_today, icon: HiDatabase, color: 'text-blue-400', bg: 'bg-blue-500/10' },
                { label: 'Failed Scrapes', value: stats.failed_scrapes_today, icon: HiExclamationCircle, color: 'text-red-400', bg: 'bg-red-500/10' },
              ].map(({ label, value, icon: Icon, color, bg }) => (
                <div key={label} className="glass-card p-5">
                  <div className={`inline-flex p-2.5 rounded-xl ${bg} mb-3`}>
                    <Icon className={`w-5 h-5 ${color}`} />
                  </div>
                  <p className="text-2xl font-bold text-white">{value}</p>
                  <p className="text-sm text-slate-400">{label}</p>
                </div>
              ))}
            </div>
          )}

          {/* Tabs */}
          <div className="flex gap-1 border-b border-slate-700/50">
            {['overview', 'users', 'logs'].map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2.5 text-sm font-medium capitalize transition-all border-b-2 -mb-px
                  ${tab === t ? 'border-primary-500 text-primary-400' : 'border-transparent text-slate-400 hover:text-white'}`}
              >
                {t}
              </button>
            ))}
          </div>

          {tab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Website distribution */}
              {websiteChartData.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                    <HiChartBar className="w-5 h-5 text-primary-400" />
                    Products by Website
                  </h3>
                  <div className="h-48">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={websiteChartData}>
                        <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} />
                        <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                        <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }} />
                        <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )}

              {/* Most Tracked */}
              {stats?.most_tracked_products?.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-base font-semibold text-white mb-4">Most Tracked Products</h3>
                  <div className="space-y-3">
                    {stats.most_tracked_products.slice(0, 5).map((p, i) => (
                      <div key={i} className="flex items-center gap-3">
                        <span className="text-lg font-bold text-slate-500 w-6">{i + 1}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-slate-300 truncate">{p.name || 'Unknown'}</p>
                          <p className="text-xs text-slate-500">{p.website}</p>
                        </div>
                        <span className="badge badge-blue">{p.track_count} tracked</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === 'users' && (
            <div className="glass-card overflow-hidden">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td className="font-medium text-slate-200">{u.username}</td>
                      <td className="text-slate-400">{u.email}</td>
                      <td><span className={`badge ${u.role === 'admin' ? 'badge-purple' : 'badge-blue'}`}>{u.role}</span></td>
                      <td><span className={`badge ${u.is_active ? 'badge-green' : 'badge-red'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                      <td className="text-xs text-slate-400">{formatDate(u.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === 'logs' && (
            <div className="glass-card overflow-hidden">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Product ID</th>
                    <th>Status</th>
                    <th>Response Time</th>
                    <th>Error</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((l) => (
                    <tr key={l.id}>
                      <td className="text-xs text-slate-400">{formatDate(l.scraped_at)}</td>
                      <td className="font-mono text-xs text-slate-400">{l.product_id.substring(0, 8)}...</td>
                      <td>
                        <span className={`badge ${
                          l.status === 'success' ? 'badge-green'
                          : l.status === 'captcha' ? 'badge-yellow'
                          : 'badge-red'
                        }`}>
                          {l.status === 'success' ? (
                            <span className="flex items-center gap-1"><HiCheckCircle className="w-3 h-3" /> Success</span>
                          ) : (
                            <span className="flex items-center gap-1"><HiExclamationCircle className="w-3 h-3" /> {l.status}</span>
                          )}
                        </span>
                      </td>
                      <td className="text-sm text-slate-300">{l.response_time_ms ? `${l.response_time_ms}ms` : '—'}</td>
                      <td className="text-xs text-red-400 max-w-xs truncate">{l.error_message || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  )
}
