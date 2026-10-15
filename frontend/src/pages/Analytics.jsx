import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { analyticsAPI, productsAPI } from '../services/api'
import { formatPrice, trendInfo } from '../utils/formatters'
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend
} from 'recharts'
import { HiArrowLeft, HiChartBar, HiShoppingBag, HiDocumentReport } from 'react-icons/hi'

function StatBox({ label, value, unit }) {
  return (
    <div className="glass-card p-4 text-center">
      <p className="text-2xl font-bold text-white">{value ?? '—'}{unit || ''}</p>
      <p className="text-xs text-slate-400 mt-1">{label}</p>
    </div>
  )
}

export default function Analytics() {
  const { id: paramId } = useParams()
  const navigate = useNavigate()
  
  const [products, setProducts] = useState([])
  const [selectedId, setSelectedId] = useState(paramId || '')
  const [loading, setLoading] = useState(true)
  const [summary, setSummary] = useState(null)
  const [stats, setStats] = useState(null)
  const [trends, setTrends] = useState(null)
  const [chart, setChart] = useState(null)
  const [monthly, setMonthly] = useState(null)
  const [history, setHistory] = useState(null)

  useEffect(() => {
    loadProducts()
  }, [paramId])

  useEffect(() => {
    if (selectedId) {
      loadAnalytics(selectedId)
    }
  }, [selectedId])

  const loadProducts = async () => {
    try {
      const { data } = await productsAPI.list(0, 100)
      const list = data || []
      setProducts(list)

      if (paramId) {
        setSelectedId(paramId)
      } else if (list.length > 0) {
        setSelectedId(list[0].id)
      } else {
        setLoading(false)
      }
    } catch {
      setLoading(false)
    }
  }

  const loadAnalytics = async (productId) => {
    setLoading(true)
    // Reset all state before loading new product
    setSummary(null)
    setStats(null)
    setTrends(null)
    setChart(null)
    setMonthly(null)
    setHistory(null)
    try {
      const [s, st, tr, ch, mo, hi] = await Promise.all([
        analyticsAPI.summary(productId).catch(() => null),
        analyticsAPI.stats(productId).catch(() => null),
        analyticsAPI.trends(productId).catch(() => null),
        analyticsAPI.chart(productId).catch(() => null),
        analyticsAPI.monthly(productId).catch(() => null),
        analyticsAPI.history(productId, 50).catch(() => null),
      ])
      setSummary(s?.data)
      // Only set stats if we have actual stats (not the insufficient_data flag)
      setStats(st?.data?.insufficient_data ? null : st?.data)
      setTrends(tr?.data)
      setChart(ch?.data)
      setMonthly(mo?.data)
      setHistory(hi?.data)
    } catch {}
    finally { setLoading(false) }
  }

  const handleProductChange = (newId) => {
    setSelectedId(newId)
    navigate(`/analytics/${newId}`, { replace: true })
  }

  const chartData = chart
    ? chart.labels.map((l, i) => ({ date: l, price: chart.prices[i], ma: chart.moving_average[i] }))
    : []

  const monthlyData = monthly?.monthly || []
  const historyRows = history?.history?.slice(0, 20) || []
  const selectedProduct = products.find(p => p.id === selectedId)

  if (loading) {
    return <div className="flex items-center justify-center h-64"><div className="spinner" /></div>
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/dashboard')} className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-surface-700 transition-all">
            <HiArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="page-title flex items-center gap-2">
              <HiChartBar className="w-7 h-7 text-primary-400" />
              Price Analytics
            </h1>
            <p className="page-subtitle">Detailed statistical analysis and price history metrics</p>
          </div>
        </div>

        {/* Product selector dropdown */}
        {products.length > 0 && (
          <div className="w-full md:w-auto">
            <select
              value={selectedId}
              onChange={(e) => handleProductChange(e.target.value)}
              className="input-field w-full text-white bg-surface-800 border-slate-700"
            >
              {products.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name || 'Unnamed Product'} ({p.website})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {products.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <HiShoppingBag className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-300 font-medium">No tracked products found</p>
          <p className="text-slate-500 text-sm mt-1">Track products to view detailed price analytics</p>
        </div>
      ) : (
        <>
          {/* Active Product Title Bar */}
          {selectedProduct && (
            <div className="glass-card p-4 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white line-clamp-1">{selectedProduct.name}</h2>
                <p className="text-xs text-slate-400 capitalize">{selectedProduct.website} • Current: {formatPrice(selectedProduct.current_price)}</p>
              </div>
              <button
                onClick={() => navigate(`/reports?product=${selectedId}`)}
                className="btn-secondary text-xs flex items-center gap-1.5"
              >
                <HiDocumentReport className="w-4 h-4 text-primary-400" />
                Export Report
              </button>
            </div>
          )}

          {/* Summary Stats */}
          {summary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatBox label="Current Price" value={formatPrice(summary.current_price)} />
              <StatBox label="Lowest Ever" value={formatPrice(summary.lowest_price)} />
              <StatBox label="Highest Ever" value={formatPrice(summary.highest_price)} />
              <StatBox label="Average Price" value={formatPrice(summary.average_price)} />
              <StatBox label="Price Drop" value={summary.price_drop_pct?.toFixed(1)} unit="%" />
              <StatBox label="Price Increase" value={summary.price_increase_pct?.toFixed(1)} unit="%" />
              <StatBox label="Volatility (σ)" value={formatPrice(summary.volatility)} />
              <StatBox label="Data Points" value={summary.total_data_points} />
            </div>
          )}

          {/* Not enough data notice */}
          {summary && summary.total_data_points < 2 && (
            <div className="glass-card p-4 border border-amber-500/30 bg-amber-500/5">
              <p className="text-amber-400 text-sm font-medium">📊 Collecting price data...</p>
              <p className="text-slate-400 text-xs mt-1">
                Only {summary.total_data_points} data point recorded so far. Statistical analysis (trends, moving averages, outliers) will appear once more price history is collected. Prices update on the configured scrape interval.
              </p>
            </div>
          )}

          {/* Statistical Measures */}
          {stats && (
            <div className="glass-card p-6">
              <h2 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                <HiChartBar className="w-5 h-5 text-primary-400" />
                Statistical Measures
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatBox label="Mean" value={formatPrice(stats.mean)} />
                <StatBox label="Median" value={formatPrice(stats.median)} />
                <StatBox label="Std Dev" value={formatPrice(stats.std_dev)} />
                <StatBox label="Variance" value={formatPrice(stats.variance)} />
                <StatBox label="7d Moving Avg" value={formatPrice(stats.moving_average_7d)} />
                <StatBox label="30d Rolling Mean" value={formatPrice(stats.rolling_mean_30d)} />
                <div className="col-span-2 glass-card p-4">
                  <p className="text-xs text-slate-400 mb-2">Outlier Prices (IQR Method)</p>
                  {stats.outliers?.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {stats.outliers.map((o, i) => (
                        <span key={i} className="badge badge-yellow">{formatPrice(o)}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-400">No outliers detected</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Trends */}
          {trends && (
            <div className="glass-card p-6">
              <h2 className="text-base font-semibold text-white mb-4">Price Trends</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { label: 'Weekly Trend', value: trends.weekly_trend },
                  { label: 'Monthly Trend', value: trends.monthly_trend },
                  { label: 'Seasonal', value: trends.seasonal_trend || 'stable' },
                ].map(({ label, value }) => {
                  const info = trendInfo(value)
                  return (
                    <div key={label} className="glass-card p-4 text-center">
                      <p className={`text-xl font-bold ${info.color}`}>{info.label}</p>
                      <p className="text-xs text-slate-400 mt-1">{label}</p>
                    </div>
                  )
                })}
              </div>

              {trends.festival_comparison && Object.keys(trends.festival_comparison).length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-700/50">
                  <p className="text-sm font-medium text-slate-300 mb-3">Festival Price Comparison</p>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(trends.festival_comparison).map(([fest, price]) => (
                      <div key={fest} className="glass-card px-4 py-3 text-center">
                        <p className="text-sm font-bold text-primary-400">{formatPrice(price)}</p>
                        <p className="text-xs text-slate-400">{fest}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Price Chart */}
          {chartData.length > 0 && (
            <div className="glass-card p-6">
              <h2 className="text-base font-semibold text-white mb-4">Price Timeline</h2>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                      formatter={(v) => [formatPrice(v)]}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="price" stroke="#22c55e" strokeWidth={2} dot={false} name="Price" />
                    <Line type="monotone" dataKey="ma" stroke="#6366f1" strokeWidth={1.5} dot={false} strokeDasharray="5 5" name="7d MA" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Monthly Bar Chart */}
          {monthlyData.length > 0 && (
            <div className="glass-card p-6">
              <h2 className="text-base font-semibold text-white mb-4">Monthly Average Prices</h2>
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="month" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
                    <Tooltip
                      contentStyle={{ background: '#1e293b', border: '1px solid #475569', borderRadius: 8 }}
                      formatter={(v) => [formatPrice(v)]}
                    />
                    <Bar dataKey="avg_price" fill="#6366f1" radius={[4, 4, 0, 0]} name="Avg Price" />
                    <Bar dataKey="min_price" fill="#22c55e" radius={[4, 4, 0, 0]} name="Min Price" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Recent history table */}
          {historyRows.length > 0 && (
            <div className="glass-card p-6">
              <h2 className="text-base font-semibold text-white mb-4">Recent Price Records</h2>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Price</th>
                      <th>Original</th>
                      <th>Discount</th>
                      <th>Rating</th>
                      <th>Availability</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyRows.map((r) => (
                      <tr key={r.id}>
                        <td>{new Date(r.scraped_at).toLocaleDateString()}</td>
                        <td className="font-semibold text-emerald-400">{formatPrice(r.price)}</td>
                        <td className="text-slate-500 line-through">{r.original_price ? formatPrice(r.original_price) : '—'}</td>
                        <td>{r.discount_pct ? <span className="badge badge-green">{r.discount_pct.toFixed(0)}%</span> : '—'}</td>
                        <td>{r.rating ? <span className="flex items-center gap-1"><span className="text-yellow-400">★</span>{r.rating}</span> : '—'}</td>
                        <td>
                          <span className={`badge ${r.availability?.includes('Stock') ? 'badge-green' : 'badge-red'}`}>
                            {r.availability || '—'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
