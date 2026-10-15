import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { productsAPI, mlAPI } from '../services/api'
import { formatPrice, recommendationStyle } from '../utils/formatters'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend
} from 'recharts'
import { HiSparkles, HiShoppingBag, HiCalendar, HiBadgeCheck } from 'react-icons/hi'
import toast from 'react-hot-toast'

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

export default function Predictions() {
  const [searchParams] = useSearchParams()
  const initialId = searchParams.get('product') || ''

  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [selectedId, setSelectedId] = useState(initialId)
  const [loading, setLoading] = useState(true)
  const [prediction, setPrediction] = useState(null)
  const [recommendation, setRecommendation] = useState(null)

  useEffect(() => {
    loadProducts()
  }, [])

  useEffect(() => {
    if (selectedId) {
      loadMLData(selectedId)
    }
  }, [selectedId])

  const loadProducts = async () => {
    setLoading(true)
    try {
      const { data } = await productsAPI.list(0, 100)
      const list = data || []
      setProducts(list)

      if (initialId) {
        setSelectedId(initialId)
      } else if (list.length > 0) {
        setSelectedId(list[0].id)
      } else {
        setLoading(false)
      }
    } catch {
      setLoading(false)
    }
  }

  const loadMLData = async (productId) => {
    setLoading(true)
    setPrediction(null)
    setRecommendation(null)
    try {
      const [pRes, rRes] = await Promise.all([
        mlAPI.predict(productId, 30).catch(e => ({ data: { error: e?.response?.data?.detail || 'Failed to load predictions' } })),
        mlAPI.recommend(productId).catch(() => null),
      ])
      setPrediction(pRes.data)
      setRecommendation(rRes?.data)
    } catch {
      toast.error('Failed to load AI predictions')
    } finally {
      setLoading(false)
    }
  }

  const selectedProduct = products.find(p => p.id === selectedId)
  const recStyle = recommendation ? recommendationStyle(recommendation.recommendation) : null

  const chartData = prediction?.chart_data
    ? prediction.chart_data.prediction_labels.map((date, i) => ({
        date,
        predicted: prediction.chart_data.prediction_prices[i],
      }))
    : []

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <HiSparkles className="w-7 h-7 text-purple-400" />
            AI Price Predictions & Forecasting
          </h1>
          <p className="page-subtitle">Machine learning multi-model price trends and smart buying recommendations</p>
        </div>

        {/* Product selector dropdown */}
        {products.length > 0 && (
          <div className="w-full md:w-auto">
            <select
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              className="input-field w-full text-white bg-surface-800 border-slate-700"
            >
              {products.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name || 'Unnamed Product'} ({p.website}) — {formatPrice(p.current_price)}
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
          <p className="text-slate-500 text-sm mt-1">Track products to view AI price predictions and buying advice</p>
        </div>
      ) : loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="spinner" />
        </div>
      ) : (
        <>
          {/* Active Product Title Bar */}
          {selectedProduct && (
            <div className="glass-card p-4 flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-white line-clamp-1">{selectedProduct.name}</h2>
                <p className="text-xs text-slate-400 capitalize">{selectedProduct.website} • Current Price: {formatPrice(selectedProduct.current_price)}</p>
              </div>
              <button
                onClick={() => navigate(`/products/${selectedId}`)}
                className="btn-secondary text-xs"
              >
                View Product Details
              </button>
            </div>
          )}

          {/* AI Recommendation Banner */}
          {recommendation && recStyle && (
            <div className={`glass-card p-6 border ${recStyle.bg}`}>
              <div className="flex items-start gap-4">
                <div className="text-4xl">🤖</div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className={`text-xl font-bold ${recStyle.color}`}>{recStyle.label}</span>
                    <span className="badge badge-purple flex items-center gap-1">
                      <HiBadgeCheck className="w-3.5 h-3.5" />
                      {Math.round((recommendation.confidence || 0.85) * 100)}% confidence
                    </span>
                  </div>
                  <p className="text-slate-300 text-sm mt-1">{recommendation.reason}</p>

                  {recommendation.best_time_to_buy && recommendation.best_time_to_buy !== 'Now' && (
                    <p className="text-xs text-slate-300 mt-3 flex items-center gap-1">
                      <HiCalendar className="w-4 h-4 text-primary-400" />
                      Best time to buy: <span className="text-primary-400 font-semibold">{recommendation.best_time_to_buy}</span>
                      {recommendation.expected_price && (
                        <span> at estimated {formatPrice(recommendation.expected_price)}</span>
                      )}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ML Model Performance & Predictions */}
          {prediction && (
            <>
              {/* Model Comparison Grid */}
              {prediction.model_info?.model_comparison && (
                <div className="glass-card p-6">
                  <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                    <HiSparkles className="w-5 h-5 text-purple-400" />
                    AI Model Accuracy & Comparison
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(prediction.model_info.model_comparison).map(([name, metrics]) => (
                      <div
                        key={name}
                        className={`p-4 rounded-xl border ${
                          prediction.model_info.best_model === name
                            ? 'bg-primary-500/10 border-primary-500/30'
                            : 'bg-surface-700/50 border-slate-700/50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <p className="text-sm font-semibold text-slate-200">{name}</p>
                          {prediction.model_info.best_model === name && (
                            <span className="badge badge-purple text-xs">Best Model</span>
                          )}
                        </div>
                        <div className="space-y-1 text-xs text-slate-400">
                          <p>MAE (Mean Abs Error): <span className="text-slate-200 font-medium">₹{metrics.mae}</span></p>
                          <p>RMSE (Root Mean Sq Error): <span className="text-slate-200 font-medium">₹{metrics.rmse}</span></p>
                          <p>R² Score: <span className="text-slate-200 font-medium">{metrics.r2}</span></p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Prediction Chart */}
              <div className="glass-card p-6">
                <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
                  <HiSparkles className="w-5 h-5 text-purple-400" />
                  30-Day Price Trend Projection
                </h3>

                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                      <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 10 }} />
                      <YAxis stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend />
                      <Line type="monotone" dataKey="predicted" stroke="#a78bfa" strokeWidth={2} dot={false} name="Predicted Price" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                {prediction.expected_best_buy_date && (
                  <div className="mt-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <p className="text-sm text-emerald-400">
                      📅 Lowest predicted price date: <strong>{prediction.expected_best_buy_date}</strong>
                    </p>
                  </div>
                )}
              </div>

              {/* 30-Day Forecast Table */}
              {prediction.next_30_days?.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-base font-semibold text-white mb-4">30-Day Daily Price Forecast</h3>
                  <div className="overflow-x-auto">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>Forecast Date</th>
                          <th>Predicted Price</th>
                          <th>Trend Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {prediction.next_30_days.map((p, idx) => (
                          <tr key={idx}>
                            <td className="text-slate-300 font-medium">{p.date}</td>
                            <td className="font-bold text-purple-400">{formatPrice(p.predicted_price)}</td>
                            <td>
                              <span className="badge badge-purple">
                                {idx === 0 ? 'Start' : p.predicted_price <= (selectedProduct?.current_price || p.predicted_price) ? 'Price Drop' : 'Expected Spike'}
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
        </>
      )}
    </div>
  )
}
