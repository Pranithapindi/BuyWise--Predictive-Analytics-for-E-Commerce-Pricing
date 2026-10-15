import { useNavigate } from 'react-router-dom'
import { HiExternalLink, HiRefresh, HiTrash, HiChartBar, HiSparkles } from 'react-icons/hi'
import { productsAPI } from '../services/api'
import toast from 'react-hot-toast'
import { formatPrice, formatDiscount, formatDate, websiteBadgeColor } from '../utils/formatters'

export default function ProductCard({ product, onRefresh, onDelete }) {
  const navigate = useNavigate()

  const handleScrapeNow = async (e) => {
    e.stopPropagation()
    try {
      await productsAPI.scrapeNow(product.id)
      toast.success('Scrape triggered! Check back in a moment.')
      onRefresh?.()
    } catch {}
  }

  const handleDelete = async (e) => {
    e.stopPropagation()
    if (!confirm('Stop tracking this product?')) return
    try {
      await productsAPI.delete(product.id)
      toast.success('Product removed from tracking')
      onDelete?.()
    } catch {}
  }

  return (
    <div
      onClick={() => navigate(`/products/${product.id}`)}
      className="glass-card p-4 cursor-pointer group hover:border-primary-500/40 transition-all duration-300
                 hover:shadow-xl hover:shadow-primary-500/10 hover:-translate-y-1 animate-fade-in"
    >
      <div className="flex gap-4">
        {/* Product Image */}
        <div className="w-20 h-20 rounded-xl overflow-hidden bg-surface-700 shrink-0 flex items-center justify-center">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name || ''}
              className="w-full h-full object-contain p-1"
              onError={(e) => {
                e.target.onerror = null
                e.target.src = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=300'
              }}
            />
          ) : (
            <div className="text-slate-500 text-3xl">🛍️</div>
          )}
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          {/* Website Badge */}
          <div className="flex items-center gap-2 mb-1">
            <span className={`badge text-xs ${websiteBadgeColor(product.website)}`}>
              {product.website}
            </span>
            {product.availability && (
              <span className={`badge text-xs ${product.availability?.toLowerCase().includes('stock') ? 'badge-green' : 'badge-red'}`}>
                {product.availability?.toLowerCase().includes('in stock') ? 'In Stock' : 'Out of Stock'}
              </span>
            )}
          </div>

          {/* Name */}
          <h3 className="text-sm font-semibold text-white line-clamp-2 group-hover:text-primary-400 transition-colors">
            {product.name || 'Loading product info...'}
          </h3>

          {/* Brand */}
          {product.brand && (
            <p className="text-xs text-slate-400 mt-0.5">{product.brand}</p>
          )}

          {/* Price Row */}
          <div className="flex items-center gap-3 mt-2">
            {product.current_price ? (
              <>
                <span className="text-lg font-bold text-emerald-400">
                  {formatPrice(product.current_price)}
                </span>
                {product.original_price && product.original_price > product.current_price && (
                  <span className="text-sm text-slate-500 line-through">
                    {formatPrice(product.original_price)}
                  </span>
                )}
                {product.current_discount > 0 && (
                  <span className="badge badge-green text-xs">
                    -{formatDiscount(product.current_discount)}
                  </span>
                )}
              </>
            ) : (
              <span className="text-sm text-slate-400 italic">Fetching price...</span>
            )}
          </div>

          {/* Rating */}
          {product.current_rating && (
            <div className="flex items-center gap-1 mt-1">
              <span className="text-yellow-400 text-xs">★</span>
              <span className="text-xs text-slate-300">{product.current_rating}</span>
              {product.review_count && (
                <span className="text-xs text-slate-500">({product.review_count.toLocaleString()})</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-700/50">
        <span className="text-xs text-slate-500">
          {product.last_scraped_at ? `Updated ${formatDate(product.last_scraped_at)}` : 'Not yet scraped'}
        </span>

        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => { navigate(`/analytics/${product.id}`) }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-primary-400 hover:bg-primary-500/10 transition-all"
            title="Analytics"
            data-testid={`analytics-btn-${product.id}`}
          >
            <HiChartBar className="w-4 h-4" />
          </button>
          <button
            onClick={handleScrapeNow}
            className="p-1.5 rounded-lg text-slate-400 hover:text-blue-400 hover:bg-blue-500/10 transition-all"
            title="Scrape Now"
          >
            <HiRefresh className="w-4 h-4" />
          </button>
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
            title="Open product"
          >
            <HiExternalLink className="w-4 h-4" />
          </a>
          <button
            onClick={handleDelete}
            className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-all"
            title="Stop tracking"
          >
            <HiTrash className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
