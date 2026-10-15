/**
 * Utility formatters for display.
 */

/** Format Indian Rupee price */
export function formatPrice(price) {
  if (price == null) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(price)
}

/** Format discount percentage */
export function formatDiscount(pct) {
  if (pct == null) return ''
  return `${Math.round(pct)}% off`
}

/** Relative date like "2 hours ago" */
export function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`
  return `${Math.floor(diffMins / 1440)}d ago`
}

/** Full date format */
export function formatFullDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

/** Trend direction → label + color */
export function trendInfo(trend) {
  switch (trend) {
    case 'up':   return { label: '↑ Rising',   color: 'text-red-400' }
    case 'down': return { label: '↓ Falling',  color: 'text-emerald-400' }
    default:     return { label: '→ Stable',   color: 'text-yellow-400' }
  }
}

/** Website name → badge color classes */
export function websiteBadgeColor(website) {
  const map = {
    amazon:         'bg-orange-500/20 text-orange-400',
    flipkart:       'bg-blue-500/20 text-blue-400',
    myntra:         'bg-pink-500/20 text-pink-400',
    ajio:           'bg-red-500/20 text-red-400',
    reliancedigital:'bg-indigo-500/20 text-indigo-400',
    croma:          'bg-green-500/20 text-green-400',
    snapdeal:       'bg-yellow-500/20 text-yellow-400',
  }
  return map[website] || 'bg-slate-500/20 text-slate-400'
}

/** Recommendation → style info */
export function recommendationStyle(rec) {
  switch (rec) {
    case 'BUY_NOW':
      return { label: '🛒 Buy Now', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' }
    case 'WAIT':
      return { label: '⏳ Wait', color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30' }
    case 'PRICE_LIKELY_DECREASE':
      return { label: '📉 Price Dropping', color: 'text-blue-400', bg: 'bg-blue-500/10 border-blue-500/30' }
    case 'PRICE_LIKELY_INCREASE':
      return { label: '📈 Price Rising', color: 'text-red-400', bg: 'bg-red-500/10 border-red-500/30' }
    default:
      return { label: '🔍 Analyzing...', color: 'text-slate-400', bg: 'bg-slate-500/10 border-slate-500/30' }
  }
}

/** Number abbreviation: 1200000 → 12L */
export function abbreviateNumber(num) {
  if (num == null) return '—'
  if (num >= 10000000) return `${(num / 10000000).toFixed(1)}Cr`
  if (num >= 100000) return `${(num / 100000).toFixed(1)}L`
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`
  return num.toString()
}
