import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { searchAPI } from '../services/api'
import { formatPrice, formatDiscount, websiteBadgeColor } from '../utils/formatters'
import { HiSearch, HiX, HiFilter } from 'react-icons/hi'

const WEBSITES = ['amazon', 'flipkart', 'myntra', 'ajio', 'reliancedigital', 'croma', 'snapdeal']

export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({
    q: searchParams.get('q') || '',
    website: '',
    min_price: '',
    max_price: '',
    min_rating: '',
    min_discount: '',
    page: 1,
  })

  useEffect(() => {
    if (filters.q) doSearch()
  }, [filters.q])

  const doSearch = async (overrides = {}) => {
    const params = { ...filters, ...overrides }
    setLoading(true)
    try {
      const { data } = await searchAPI.search({
        ...params,
        min_price: params.min_price || undefined,
        max_price: params.max_price || undefined,
        min_rating: params.min_rating || undefined,
        min_discount: params.min_discount || undefined,
        website: params.website || undefined,
      })
      setResults(data.items)
      setTotal(data.total)
    } catch {} finally { setLoading(false) }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setSearchParams({ q: filters.q })
    doSearch()
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Search Products</h1>
        <p className="page-subtitle">Filter tracked products by name, website, price, and more</p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <div className="relative flex-1">
          <HiSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            id="search-input"
            type="text"
            value={filters.q}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            placeholder="Search products by name, brand..."
            className="input-field pl-10 text-base py-3.5"
          />
          {filters.q && (
            <button type="button" onClick={() => { setFilters({ ...filters, q: '' }); setResults([]) }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
            >
              <HiX className="w-5 h-5" />
            </button>
          )}
        </div>
        <button type="submit" className="btn-primary px-8">Search</button>
      </form>

      {/* Filters */}
      <div className="glass-card p-5">
        <div className="flex items-center gap-2 mb-4">
          <HiFilter className="w-4 h-4 text-primary-400" />
          <p className="text-sm font-semibold text-slate-300">Filters</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {/* Website */}
          <select
            value={filters.website}
            onChange={(e) => { setFilters({ ...filters, website: e.target.value }); doSearch({ website: e.target.value }) }}
            className="input-field text-sm col-span-2"
          >
            <option value="">All Websites</option>
            {WEBSITES.map(w => <option key={w} value={w}>{w.charAt(0).toUpperCase() + w.slice(1)}</option>)}
          </select>

          <input
            type="number"
            placeholder="Min Price ₹"
            value={filters.min_price}
            onChange={(e) => setFilters({ ...filters, min_price: e.target.value })}
            className="input-field text-sm"
          />
          <input
            type="number"
            placeholder="Max Price ₹"
            value={filters.max_price}
            onChange={(e) => setFilters({ ...filters, max_price: e.target.value })}
            className="input-field text-sm"
          />
          <input
            type="number"
            placeholder="Min Rating"
            min="0" max="5" step="0.5"
            value={filters.min_rating}
            onChange={(e) => setFilters({ ...filters, min_rating: e.target.value })}
            className="input-field text-sm"
          />
          <input
            type="number"
            placeholder="Min Discount %"
            min="0" max="100"
            value={filters.min_discount}
            onChange={(e) => setFilters({ ...filters, min_discount: e.target.value })}
            className="input-field text-sm"
          />
        </div>
        <button onClick={() => doSearch()} className="btn-secondary mt-3 text-sm">Apply Filters</button>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-20"><div className="spinner" /></div>
      ) : results.length > 0 ? (
        <>
          <p className="text-sm text-slate-400">{total} results found</p>
          <div className="glass-card overflow-hidden">
            <table className="data-table">
              <thead>
                <tr>
                  <th></th>
                  <th>Product</th>
                  <th>Website</th>
                  <th>Price</th>
                  <th>Discount</th>
                  <th>Rating</th>
                  <th>Availability</th>
                </tr>
              </thead>
              <tbody>
                {results.map((p) => (
                  <tr
                    key={p.id}
                    className="cursor-pointer hover:bg-surface-700/30"
                    onClick={() => navigate(`/products/${p.id}`)}
                  >
                    <td>
                      <div className="w-10 h-10 rounded-lg bg-surface-700 flex items-center justify-center overflow-hidden">
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
                          <span>🛍️</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div>
                        <p className="font-medium text-slate-200 line-clamp-1">{p.name}</p>
                        {p.brand && <p className="text-xs text-slate-500">{p.brand}</p>}
                      </div>
                    </td>
                    <td><span className={`badge ${websiteBadgeColor(p.website)}`}>{p.website}</span></td>
                    <td className="font-bold text-emerald-400">{formatPrice(p.current_price)}</td>
                    <td>
                      {p.current_discount ? (
                        <span className="badge badge-green">{formatDiscount(p.current_discount)}</span>
                      ) : '—'}
                    </td>
                    <td>
                      {p.current_rating
                        ? <span className="flex items-center gap-1 text-yellow-400 text-xs">★ {p.current_rating}</span>
                        : '—'}
                    </td>
                    <td>
                      {p.availability && (
                        <span className={`badge ${p.availability.includes('Stock') ? 'badge-green' : 'badge-red'}`}>
                          {p.availability}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : filters.q ? (
        <div className="glass-card p-16 text-center">
          <div className="text-5xl mb-3">🔍</div>
          <p className="text-slate-400 text-lg">No results found for "{filters.q}"</p>
        </div>
      ) : null}
    </div>
  )
}
