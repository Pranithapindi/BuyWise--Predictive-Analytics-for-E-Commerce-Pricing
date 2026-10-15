import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { productsAPI, analyticsAPI, mlAPI, alertsAPI, exportAPI } from '../services/api'
import { formatPrice, formatDiscount, formatDate, recommendationStyle, trendInfo, websiteBadgeColor } from '../utils/formatters'
import {
  Line, LineChart, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, ReferenceLine
} from 'recharts'
import toast from 'react-hot-toast'
import {
  HiArrowLeft, HiExternalLink, HiRefresh, HiDownload, HiSparkles, HiBell,
  HiChartBar, HiTrendingUp, HiTrendingDown, HiStar
} from 'react-icons/hi'

// Custom tooltip for the price chart
function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card p-3 border border-slate-700/50 text-xs">
      <p className="text-slate-300 mb-1">{label}</p>
      {payload.map((entry, i) => (
        <p key={i} style={{ color: entry.color }} className="font-semibold">
          {entry.name}: ₹{Number(entry.value).toLocaleString('en-IN')}
        </p>
      ))}
    </div>
  )
}

export default function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [summary, setSummary] = useState(null)
  const [chart, setChart] = useState(null)
  const [prediction, setPrediction] = useState(null)
  const [recommendation, setRecommendation] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')
  const [showAlertModal, setShowAlertModal] = useState(false)
  const [alertForm, setAlertForm] = useState({ target_price: '', notify_email: true, notify_browser: true })

  useEffect(() => { loadAll() }, [id])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [pRes, sRes, cRes] = await Promise.all([
        productsAPI.get(id),
        analyticsAPI.summary(id).catch(() => null),
        analyticsAPI.chart(id).catch(() => null),
      ])
      setProduct(pRes.data)
      setSummary(sRes?.data)
      setChart(cRes?.data)

      // Load recommendation & predictions asynchronously
      loadPredictions()
      mlAPI.recommend(id).then(r => setRecommendation(r.data)).catch(() => {})
    } catch {
      toast.error('Product not found')
      navigate('/products')
    } finally {
      setLoading(false)
    }
  }

  const loadPredictions = async () => {
    try {
      const { data } = await mlAPI.predict(id, 30)
      setPrediction(data)
    } catch (e) {
      // Show a friendly error state instead of navigating away
      const detail = e?.response?.data?.detail || 'Need more price history for ML predictions'
      setPrediction({ error: detail })
    }
  }

  const handleScrapeNow = async () => {
    try {
      await productsAPI.scrapeNow(id)
      toast.success('Scrape triggered!')
    } catch {}
  }

  const handleExport = async (format) => {
    try {
      const { data } = await exportAPI.export(id, format)
      const url = window.URL.createObjectURL(new Blob([data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `price_history.${format === 'excel' ? 'xlsx' : format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      toast.success(`Exported as ${format.toUpperCase()}`)
    } catch {}
  }

  const handleCreateAlert = async (e) => {
    e.preventDefault()
    try {
      await alertsAPI.create({
        product_id: id,
        target_price: alertForm.target_price ? Number(alertForm.target_price) : null,
        notify_email: alertForm.notify_email,
        notify_browser: alertForm.notify_browser,
      })
      toast.success('Alert created!')
      setShowAlertModal(false)
    } catch {}
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  if (!product) return null

  const recStyle = recommendation ? recommendationStyle(recommendation.recommendation) : null
  const chartData = chart ? chart.labels.map((label, i) => ({
    date: label,
    price: chart.prices[i],
    ma: chart.moving_average[i],
  })) : []

  // Merge predictions
  const predChartData = prediction
    ? [
        ...chartData.slice(-14),
        ...prediction.next_30_days.map(p => ({
          date: p.date,
          predicted: p.predicted_price,
        })),
      ]
    : []

  const TABS = ['overview', 'history', 'predictions', 'export']

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button
          onClick={() => navigate('/products')}
          className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-surface-700 mt-1 transition-all"
        >
          <HiArrowLeft className="w-5 h-5" />
        </button>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`badge ${websiteBadgeColor(product.website)}`}>{product.website}</span>
            {product.availability && (
              <span className={`badge ${product.availability.includes('Stock') ? 'badge-green' : 'badge-red'}`}>
                {product.availability}
              </span>
            )}
          </div>
          <h1 className="text-2xl font-bold text-white leading-tight">{product.name}</h1>
          {product.brand && <p className="text-slate-400 mt-0.5">{product.brand}</p>}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <button onClick={handleScrapeNow} className="btn-secondary text-sm">
            <HiRefresh className="w-4 h-4" />
            Refresh
          </button>
          <button onClick={() => setShowAlertModal(true)} className="btn-secondary text-sm">
            <HiBell className="w-4 h-4" />
            Alert
          </button>
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary text-sm"
          >
            <HiExternalLink className="w-4 h-4" />
            View on {product.website}
          </a>
        </div>
      </div>

      {/* Product Hero */}
      <div className="glass-card p-6">
        <div className="flex gap-6">
          {/* Image */}
          <div className="w-40 h-40 rounded-2xl bg-surface-700 flex items-center justify-center overflow-hidden shrink-0">
            {product.image_url ? (
              <img
                src={product.image_url}
                alt={product.name}
                className="w-full h-full object-contain p-2"
                onError={(e) => {
                  e.target.onerror = null
                  e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300'
                }}
              />
            ) : (
              <span className="text-5xl">🛍️</span>
            )}
          </div>

          {/* Details */}
          <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-slate-500 mb-1">Current Price</p>
              <p className="text-3xl font-bold text-emerald-400">{formatPrice(product.current_price)}</p>
              {product.current_discount > 0 && (
                <span className="badge badge-green mt-1">{formatDiscount(product.current_discount)}</span>
              )}
            </div>
            {summary && (
              <>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Lowest Ever</p>
                  <p className="text-xl font-bold text-blue-400">{formatPrice(summary.lowest_price)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Highest Ever</p>
                  <p className="text-xl font-bold text-red-400">{formatPrice(summary.highest_price)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-1">Average</p>
                  <p className="text-xl font-bold text-slate-200">{formatPrice(summary.average_price)}</p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Additional info row */}
        <div className="flex flex-wrap gap-4 mt-5 pt-5 border-t border-slate-700/50">
          {product.seller && (
            <div className="text-sm"><span className="text-slate-500">Seller: </span><span className="text-slate-300">{product.seller}</span></div>
          )}
          {product.current_rating && (
            <div className="flex items-center gap-1 text-sm">
              <HiStar className="w-4 h-4 text-yellow-400" />
              <span className="text-slate-300">{product.current_rating}</span>
              {product.review_count && (
                <span className="text-slate-500">({product.review_count?.toLocaleString()} reviews)</span>
              )}
            </div>
          )}
          {product.delivery_charges !== null && (
            <div className="text-sm">
              <span className="text-slate-500">Delivery: </span>
              <span className="text-slate-300">{product.delivery_charges === 0 ? 'FREE' : formatPrice(product.delivery_charges)}</span>
            </div>
          )}
          <div className="text-sm ml-auto">
            <span className="text-slate-500">Last updated: </span>
            <span className="text-slate-300">{formatDate(product.last_scraped_at)}</span>
          </div>
        </div>
      </div>

      {/* AI Recommendation */}
      {recommendation && recStyle && (
        <div className={`glass-card p-5 border ${recStyle.bg}`}>
          <div className="flex items-start gap-4">
            <div className="text-3xl">🤖</div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <span className={`text-lg font-bold ${recStyle.color}`}>{recStyle.label}</span>
                <span className="badge badge-purple">
                  {Math.round(recommendation.confidence * 100)}% confidence
                </span>
              </div>
              <p className="text-slate-300 text-sm">{recommendation.reason}</p>
              {recommendation.best_time_to_buy && recommendation.best_time_to_buy !== 'Now' && (
                <p className="text-xs text-slate-400 mt-2">
                  📅 Best time to buy: <span className="text-primary-400">{recommendation.best_time_to_buy}</span>
                  {recommendation.expected_price && (
                    <span> at estimated {formatPrice(recommendation.expected_price)}</span>
                  )}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex border-b border-slate-700/50 gap-1">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => {
              setActiveTab(tab)
              if (tab === 'predictions' && !prediction) loadPredictions()
            }}
            className={`px-4 py-2.5 text-sm font-medium capitalize transition-all border-b-2 -mb-px
              ${activeTab === tab
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-slate-400 hover:text-white'
              }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <HiChartBar className="w-5 h-5 text-primary-400" />
            Price History
          </h3>
          {chartData.length > 1 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                  <YAxis
                    stroke="#64748b"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="price"
                    stroke="#22c55e"
                    strokeWidth={2}
                    dot={false}
                    name="Price"
                  />
                  <Line
                    type="monotone"
                    dataKey="ma"
                    stroke="#6366f1"
                    strokeWidth={1.5}
                    dot={false}
                    strokeDasharray="5 5"
                    name="7d MA"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex flex-col items-center justify-center text-center gap-3">
              <span className="text-4xl">📊</span>
              <div>
                <p className="text-slate-300 font-medium">Price history chart will appear here</p>
                <p className="text-slate-500 text-sm mt-1">
                  {chartData.length === 0
                    ? 'No price data recorded yet. The scraper will collect data on the configured interval.'
                    : 'Only 1 data point so far. The chart will populate as more prices are recorded over time.'}
                </p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'predictions' && (
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <HiSparkles className="w-5 h-5 text-purple-400" />
            ML Price Predictions (Next 30 Days)
          </h3>
          {!prediction ? (
            <div className="text-center py-12">
              <div className="spinner mx-auto mb-4" />
              <p className="text-slate-400">Training AI models on price history...</p>
            </div>
          ) : prediction.error ? (
            <div className="text-center py-8">
              <p className="text-slate-400">{prediction.error}</p>
            </div>
          ) : (
            <>
              {/* Model comparison */}
              {prediction.model_info?.model_comparison && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
                  {Object.entries(prediction.model_info.model_comparison).map(([name, metrics]) => (
                    <div key={name} className={`p-4 rounded-xl border
                      ${prediction.model_info.best_model === name
                        ? 'bg-primary-500/10 border-primary-500/30'
                        : 'bg-surface-700/50 border-slate-700/50'
                      }`}>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-semibold text-slate-200">{name}</p>
                        {prediction.model_info.best_model === name && (
                          <span className="badge badge-purple text-xs">Best</span>
                        )}
                      </div>
                      <div className="space-y-1 text-xs text-slate-400">
                        <p>MAE: <span className="text-slate-200">₹{metrics.mae}</span></p>
                        <p>RMSE: <span className="text-slate-200">₹{metrics.rmse}</span></p>
                        <p>R²: <span className="text-slate-200">{metrics.r2}</span></p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Prediction chart */}
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={[
                    ...(chartData || []).slice(-14).map(d => ({ ...d, type: 'history' })),
                    ...(prediction?.next_30_days || []).map(p => ({
                      date: p.date,
                      predicted: p.predicted_price,
                      type: 'prediction',
                    }))
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend />
                    <Line type="monotone" dataKey="price" stroke="#22c55e" strokeWidth={2} dot={false} name="Actual" />
                    <Line type="monotone" dataKey="predicted" stroke="#a78bfa" strokeWidth={2} dot={false} strokeDasharray="6 3" name="Predicted" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {prediction.expected_best_buy_date && (
                <div className="mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                  <p className="text-sm text-emerald-400">
                    📅 Expected best buying date: <strong>{prediction.expected_best_buy_date}</strong>
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-white mb-4">Price History Table</h3>
          <p className="text-slate-400 text-sm">
            View detailed price history in the Analytics section for full statistics.
          </p>
          <button
            onClick={() => navigate(`/analytics/${id}`)}
            className="btn-primary mt-4"
          >
            <HiChartBar className="w-4 h-4" />
            Open Full Analytics
          </button>
        </div>
      )}

      {activeTab === 'export' && (
        <div className="glass-card p-6">
          <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
            <HiDownload className="w-5 h-5 text-primary-400" />
            Export Price History
          </h3>
          <div className="grid grid-cols-3 gap-4">
            {['csv', 'excel', 'pdf'].map((fmt) => (
              <button
                key={fmt}
                onClick={() => handleExport(fmt)}
                className="btn-secondary flex-col items-center gap-3 py-6 uppercase"
              >
                <span className="text-3xl">{fmt === 'csv' ? '📄' : fmt === 'excel' ? '📊' : '📕'}</span>
                <span className="text-sm font-semibold">{fmt.toUpperCase()}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Alert Modal */}
      {showAlertModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card w-full max-w-md p-8 animate-slide-up">
            <h2 className="text-xl font-bold text-white mb-5 flex items-center gap-2">
              <HiBell className="w-5 h-5 text-primary-400" />
              Set Price Alert
            </h2>
            <form onSubmit={handleCreateAlert} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Target Price (₹)
                </label>
                <input
                  type="number"
                  value={alertForm.target_price}
                  onChange={(e) => setAlertForm({ ...alertForm, target_price: e.target.value })}
                  placeholder={`Current: ${formatPrice(product.current_price)}`}
                  className="input-field"
                />
              </div>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={alertForm.notify_email}
                    onChange={(e) => setAlertForm({ ...alertForm, notify_email: e.target.checked })}
                    className="rounded"
                  />
                  Email
                </label>
                <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={alertForm.notify_browser}
                    onChange={(e) => setAlertForm({ ...alertForm, notify_browser: e.target.checked })}
                    className="rounded"
                  />
                  Browser
                </label>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowAlertModal(false)} className="btn-secondary flex-1 justify-center">
                  Cancel
                </button>
                <button type="submit" className="btn-primary flex-1 justify-center">
                  Create Alert
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
