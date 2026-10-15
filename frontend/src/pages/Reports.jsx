import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { productsAPI, analyticsAPI, exportAPI } from '../services/api'
import { formatPrice, formatDate } from '../utils/formatters'
import {
  HiDocumentReport, HiDownload, HiTable, HiDocumentText,
  HiShoppingBag, HiCheckCircle, HiRefresh, HiClock
} from 'react-icons/hi'
import toast from 'react-hot-toast'

export default function Reports() {
  const [searchParams] = useSearchParams()
  const initialProductId = searchParams.get('product') || ''

  const [products, setProducts] = useState([])
  const [selectedProductId, setSelectedProductId] = useState(initialProductId)
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generatingFormat, setGeneratingFormat] = useState(null)
  const [recentReports, setRecentReports] = useState([])

  useEffect(() => {
    loadProducts()
  }, [])

  useEffect(() => {
    if (selectedProductId) {
      loadSummary(selectedProductId)
    } else {
      setSummary(null)
    }
  }, [selectedProductId])

  const loadProducts = async () => {
    setLoading(true)
    try {
      const { data } = await productsAPI.list(0, 100)
      const list = data || []
      setProducts(list)
      if (list.length > 0 && !selectedProductId) {
        setSelectedProductId(list[0].id)
      }
    } catch {
      toast.error('Failed to load products')
    } finally {
      setLoading(false)
    }
  }

  const loadSummary = async (productId) => {
    try {
      const { data } = await analyticsAPI.summary(productId)
      setSummary(data)
    } catch {
      setSummary(null)
    }
  }

  const handleGenerateReport = async (format) => {
    if (!selectedProductId) {
      toast.error('Please select a product first')
      return
    }
    setGeneratingFormat(format)
    try {
      const selectedProduct = products.find((p) => p.id === selectedProductId)
      const productName = selectedProduct?.name || 'Product'

      // Pre-fetch the report blob data to ensure it's generated successfully
      const response = await exportAPI.export(selectedProductId, format)

      const newReport = {
        id: 'rep_' + Date.now(),
        productName,
        productId: selectedProductId,
        format,
        createdAt: new Date().toISOString(),
        blobData: response.data,
      }

      setRecentReports((prev) => [newReport, ...prev])
      toast.success(`${format.toUpperCase()} report generated! Download it below.`)
    } catch {
      toast.error(`Failed to generate ${format.toUpperCase()} report`)
    } finally {
      setGeneratingFormat(null)
    }
  }

  const triggerDownload = (report) => {
    try {
      const productNameClean = report.productName.substring(0, 25).replace(/[^a-zA-Z0-9]/g, '_')
      const mimeTypes = {
        csv: 'text/csv',
        excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        pdf: 'application/pdf',
      }

      const blob = new Blob([report.blobData], { type: mimeTypes[report.format] || 'application/octet-stream' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      const ext = report.format === 'excel' ? 'xlsx' : report.format
      link.setAttribute('download', `price_report_${productNameClean}.${ext}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast.success(`Downloaded ${report.format.toUpperCase()} report!`)
    } catch {
      toast.error('Failed to download report')
    }
  }

  const selectedProduct = products.find((p) => p.id === selectedProductId)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title flex items-center gap-2">
            <HiDocumentReport className="w-7 h-7 text-primary-400" />
            Price History Reports
          </h1>
          <p className="page-subtitle">Generate statistical reports and download them to your PC from recent reports</p>
        </div>
      </div>

      {products.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <HiShoppingBag className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-300 font-medium">No tracked products found</p>
          <p className="text-slate-500 text-sm mt-1">Track products to generate detailed price reports</p>
        </div>
      ) : (
        <>
          {/* Product selector */}
          <div className="glass-card p-6">
            <label className="block text-sm font-medium text-slate-300 mb-2">Select Tracked Product</label>
            <select
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(e.target.value)}
              className="input-field w-full md:w-1/2 text-white bg-surface-800 border-slate-700"
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name || 'Unnamed Product'} ({p.website}) — {formatPrice(p.current_price)}
                </option>
              ))}
            </select>
          </div>

          {/* Product summary preview */}
          {selectedProduct && (
            <div className="glass-card p-6">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-700/50">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-surface-700 flex items-center justify-center overflow-hidden shrink-0">
                    {selectedProduct.image_url ? (
                      <img src={selectedProduct.image_url} alt="" className="w-full h-full object-contain p-1" />
                    ) : (
                      <HiShoppingBag className="w-6 h-6 text-primary-400" />
                    )}
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-white line-clamp-1">{selectedProduct.name}</h2>
                    <p className="text-xs text-slate-400 capitalize">{selectedProduct.website} • Tracked since {formatDate(selectedProduct.created_at)}</p>
                  </div>
                </div>

                <div className="text-right">
                  <p className="text-xs text-slate-400">Current Price</p>
                  <p className="text-xl font-bold text-emerald-400">{formatPrice(selectedProduct.current_price)}</p>
                </div>
              </div>

              {summary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div className="bg-surface-700/40 p-3 rounded-xl">
                    <p className="text-xs text-slate-400">Lowest Price</p>
                    <p className="text-base font-bold text-emerald-400">{formatPrice(summary.lowest_price)}</p>
                  </div>
                  <div className="bg-surface-700/40 p-3 rounded-xl">
                    <p className="text-xs text-slate-400">Highest Price</p>
                    <p className="text-base font-bold text-red-400">{formatPrice(summary.highest_price)}</p>
                  </div>
                  <div className="bg-surface-700/40 p-3 rounded-xl">
                    <p className="text-xs text-slate-400">Average Price</p>
                    <p className="text-base font-bold text-slate-200">{formatPrice(summary.average_price)}</p>
                  </div>
                  <div className="bg-surface-700/40 p-3 rounded-xl">
                    <p className="text-xs text-slate-400">Price Drop %</p>
                    <p className="text-base font-bold text-primary-400">{summary.price_drop_pct}%</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Export formats grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* CSV */}
            <div className="glass-card p-6 flex flex-col justify-between hover:border-emerald-500/40 transition-all">
              <div>
                <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-4">
                  <HiTable className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white mb-1">CSV Raw Data</h3>
                <p className="text-xs text-slate-400">Comma-separated raw price history logs, ideal for custom data analysis and importing into database tools.</p>
              </div>
              <button
                onClick={() => handleGenerateReport('csv')}
                disabled={generatingFormat === 'csv'}
                className="btn-secondary w-full mt-6 justify-center text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/10"
              >
                {generatingFormat === 'csv' ? <HiRefresh className="w-4 h-4 animate-spin" /> : <HiDocumentReport className="w-4 h-4" />}
                Generate CSV Report
              </button>
            </div>

            {/* Excel */}
            <div className="glass-card p-6 flex flex-col justify-between hover:border-primary-500/40 transition-all">
              <div>
                <div className="w-12 h-12 rounded-xl bg-primary-500/10 text-primary-400 flex items-center justify-center mb-4">
                  <HiDocumentReport className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white mb-1">Excel Spreadsheet</h3>
                <p className="text-xs text-slate-400">Formatted Microsoft Excel (.xlsx) file with styled headers, formatted currency cells, and full audit column dimensions.</p>
              </div>
              <button
                onClick={() => handleGenerateReport('excel')}
                disabled={generatingFormat === 'excel'}
                className="btn-primary w-full mt-6 justify-center"
              >
                {generatingFormat === 'excel' ? <HiRefresh className="w-4 h-4 animate-spin" /> : <HiDocumentReport className="w-4 h-4" />}
                Generate Excel Report (.xlsx)
              </button>
            </div>

            {/* PDF */}
            <div className="glass-card p-6 flex flex-col justify-between hover:border-purple-500/40 transition-all">
              <div>
                <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center mb-4">
                  <HiDocumentText className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-white mb-1">PDF Report</h3>
                <p className="text-xs text-slate-400">Print-ready landscape PDF document with clean styled tables, metadata headers, and price history metrics.</p>
              </div>
              <button
                onClick={() => handleGenerateReport('pdf')}
                disabled={generatingFormat === 'pdf'}
                className="btn-secondary w-full mt-6 justify-center text-purple-400 border-purple-500/30 hover:bg-purple-500/10"
              >
                {generatingFormat === 'pdf' ? <HiRefresh className="w-4 h-4 animate-spin" /> : <HiDocumentReport className="w-4 h-4" />}
                Generate PDF Report
              </button>
            </div>
          </div>

          {/* Recent Reports Table */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              <HiClock className="w-5 h-5 text-primary-400" />
              Recent Reports
            </h2>

            {recentReports.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <HiDocumentText className="w-10 h-10 mx-auto mb-2 opacity-40" />
                <p className="text-sm font-medium">No reports generated yet</p>
                <p className="text-xs text-slate-600 mt-1">Click any button above to generate a report, then download it below</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Product</th>
                      <th>Generated At</th>
                      <th className="text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentReports.map((r) => (
                      <tr key={r.id}>
                        <td>
                          <span className={`badge ${r.format === 'csv' ? 'badge-green' : r.format === 'excel' ? 'badge-blue' : 'badge-purple'}`}>
                            {r.format.toUpperCase()}
                          </span>
                        </td>
                        <td className="font-medium text-slate-200">{r.productName}</td>
                        <td className="text-slate-400 text-xs">{formatDate(r.createdAt)}</td>
                        <td className="text-right">
                          <button
                            onClick={() => triggerDownload(r)}
                            className="btn-primary text-xs py-1.5 px-3 inline-flex items-center gap-1"
                          >
                            <HiDownload className="w-3.5 h-3.5" />
                            Download
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
