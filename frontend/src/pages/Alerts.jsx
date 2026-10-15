import { useEffect, useState } from 'react'
import { alertsAPI } from '../services/api'
import { formatPrice, formatDate } from '../utils/formatters'
import toast from 'react-hot-toast'
import { HiBell, HiTrash, HiCheckCircle, HiClock } from 'react-icons/hi'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadAlerts() }, [])

  const loadAlerts = async () => {
    setLoading(true)
    try {
      const { data } = await alertsAPI.list()
      setAlerts(data)
    } catch {} finally { setLoading(false) }
  }

  const handleDelete = async (id) => {
    try {
      await alertsAPI.delete(id)
      toast.success('Alert deleted')
      setAlerts(prev => prev.filter(a => a.id !== id))
    } catch {}
  }

  const handleToggle = async (alert) => {
    try {
      await alertsAPI.update(alert.id, { is_active: !alert.is_active })
      setAlerts(prev => prev.map(a => a.id === alert.id ? { ...a, is_active: !a.is_active } : a))
      toast.success(alert.is_active ? 'Alert paused' : 'Alert activated')
    } catch {}
  }

  const active = alerts.filter(a => a.is_active && !a.is_triggered)
  const triggered = alerts.filter(a => a.is_triggered)
  const paused = alerts.filter(a => !a.is_active && !a.is_triggered)

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Price Alerts</h1>
        <p className="page-subtitle">{active.length} active · {triggered.length} triggered</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="glass-card p-5 text-center">
          <p className="text-3xl font-bold text-emerald-400">{active.length}</p>
          <p className="text-sm text-slate-400 mt-1">Active Alerts</p>
        </div>
        <div className="glass-card p-5 text-center">
          <p className="text-3xl font-bold text-yellow-400">{triggered.length}</p>
          <p className="text-sm text-slate-400 mt-1">Triggered</p>
        </div>
        <div className="glass-card p-5 text-center">
          <p className="text-3xl font-bold text-slate-400">{paused.length}</p>
          <p className="text-sm text-slate-400 mt-1">Paused</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : alerts.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <div className="text-6xl mb-4">🔔</div>
          <p className="text-xl font-semibold text-slate-300 mb-2">No alerts set</p>
          <p className="text-slate-400 text-sm">Go to a product page and click "Alert" to create a price alert.</p>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="data-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Product</th>
                <th>Target Price</th>
                <th>Notifications</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alert) => (
                <tr key={alert.id}>
                  <td>
                    {alert.is_triggered ? (
                      <span className="badge badge-green flex items-center gap-1 w-fit">
                        <HiCheckCircle className="w-3 h-3" /> Triggered
                      </span>
                    ) : alert.is_active ? (
                      <span className="badge badge-blue flex items-center gap-1 w-fit">
                        <HiBell className="w-3 h-3" /> Active
                      </span>
                    ) : (
                      <span className="badge badge-yellow flex items-center gap-1 w-fit">
                        <HiClock className="w-3 h-3" /> Paused
                      </span>
                    )}
                  </td>
                  <td className="text-xs text-slate-400 font-mono">{alert.product_id.substring(0, 8)}...</td>
                  <td className="font-semibold text-emerald-400">
                    {alert.target_price ? formatPrice(alert.target_price) : '—'}
                  </td>
                  <td>
                    <div className="flex gap-1">
                      {alert.notify_email && <span className="badge badge-blue text-xs">📧</span>}
                      {alert.notify_sms && <span className="badge badge-yellow text-xs">📱</span>}
                      {alert.notify_browser && <span className="badge badge-purple text-xs">🔔</span>}
                    </div>
                  </td>
                  <td className="text-xs text-slate-400">{formatDate(alert.created_at)}</td>
                  <td>
                    <div className="flex items-center gap-2">
                      {!alert.is_triggered && (
                        <button
                          onClick={() => handleToggle(alert)}
                          className={`text-xs px-2 py-1 rounded-lg border transition-all
                            ${alert.is_active
                              ? 'border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10'
                              : 'border-green-500/30 text-green-400 hover:bg-green-500/10'
                            }`}
                        >
                          {alert.is_active ? 'Pause' : 'Resume'}
                        </button>
                      )}
                      <button
                        onClick={() => handleDelete(alert.id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
                      >
                        <HiTrash className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
