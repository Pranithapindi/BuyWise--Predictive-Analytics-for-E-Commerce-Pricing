import { useEffect, useState } from 'react'
import { productsAPI } from '../services/api'
import ProductCard from '../components/ProductCard'
import toast from 'react-hot-toast'
import { HiPlus, HiSearch, HiX, HiRefresh } from 'react-icons/hi'

const INTERVALS = [
  { label: '30 min', value: 30 },
  { label: '1 hour', value: 60 },
  { label: '6 hours', value: 360 },
  { label: 'Daily', value: 1440 },
]

export default function Products() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [url, setUrl] = useState('')
  const [interval, setInterval_] = useState(60)
  const [adding, setAdding] = useState(false)
  const [filter, setFilter] = useState('')

  useEffect(() => { loadProducts() }, [])

  const loadProducts = async () => {
    setLoading(true)
    try {
      const { data } = await productsAPI.list()
      setProducts(data)
    } catch {} finally { setLoading(false) }
  }

  const handleAdd = async (e) => {
    e.preventDefault()
    let cleanUrl = url.trim()
    if (!cleanUrl) return
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = 'https://' + cleanUrl
    }
    setAdding(true)
    try {
      await productsAPI.track(cleanUrl, interval)
      toast.success('Product added! Scraping in background...')
      setUrl('')
      setShowAddModal(false)
      setTimeout(loadProducts, 1500)
    } catch {} finally { setAdding(false) }
  }

  const filtered = products.filter(p =>
    !filter ||
    p.name?.toLowerCase().includes(filter.toLowerCase()) ||
    p.website?.includes(filter.toLowerCase()) ||
    p.brand?.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">My Products</h1>
          <p className="page-subtitle">{products.length} products being tracked</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={loadProducts} className="btn-secondary">
            <HiRefresh className="w-4 h-4" />
            Refresh
          </button>
          <button
            id="track-product-btn"
            onClick={() => setShowAddModal(true)}
            className="btn-primary"
          >
            <HiPlus className="w-4 h-4" />
            Track Product
          </button>
        </div>
      </div>

      {/* Search filter */}
      <div className="relative max-w-md">
        <HiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          placeholder="Filter by name, brand, website..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="input-field pl-9"
        />
        {filter && (
          <button onClick={() => setFilter('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
            <HiX className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Products Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="spinner" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <div className="text-6xl mb-4">🛍️</div>
          <p className="text-xl font-semibold text-slate-300 mb-2">
            {filter ? 'No matching products' : 'No products tracked yet'}
          </p>
          <p className="text-slate-400 text-sm mb-6">
            {filter ? 'Try a different filter' : 'Paste an Amazon, Flipkart, Myntra or other supported URL to begin'}
          </p>
          {!filter && (
            <button onClick={() => setShowAddModal(true)} className="btn-primary mx-auto">
              <HiPlus className="w-4 h-4" />
              Add Your First Product
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map((p) => (
            <ProductCard
              key={p.id}
              product={p}
              onRefresh={loadProducts}
              onDelete={loadProducts}
            />
          ))}
        </div>
      )}

      {/* Add Product Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="glass-card w-full max-w-lg p-8 animate-slide-up">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-white">Track a Product</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-surface-700 transition-all"
              >
                <HiX className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAdd} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Product URL</label>
                <input
                  id="product-url-input"
                  type="text"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="reliancedigital.in/samsung-galaxy-s24-ultra/p/49435123"
                  className="input-field"
                  autoFocus
                />
                <p className="text-xs text-slate-500 mt-1.5">
                  Supported: Amazon, Flipkart, Myntra, AJIO, Reliance Digital, Croma, Snapdeal
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">Scrape Interval</label>
                <div className="grid grid-cols-4 gap-2">
                  {INTERVALS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setInterval_(opt.value)}
                      className={`py-2 px-3 rounded-xl text-sm font-medium border transition-all
                        ${interval === opt.value
                          ? 'bg-primary-500/20 border-primary-500/50 text-primary-400'
                          : 'bg-surface-700 border-slate-600/50 text-slate-400 hover:border-slate-500'
                        }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary flex-1 justify-center"
                >
                  Cancel
                </button>
                <button
                  id="confirm-track-btn"
                  type="submit"
                  disabled={adding}
                  className="btn-primary flex-1 justify-center"
                >
                  {adding ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Adding...
                    </span>
                  ) : (
                    <>
                      <HiPlus className="w-4 h-4" />
                      Start Tracking
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
