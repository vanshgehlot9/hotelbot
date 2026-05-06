"use client"
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle, Download } from 'lucide-react'
import api from '@/lib/api'

export default function BillingPage() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<{ hotels_added: number; errors: string[] } | null>(null)
  const [uploadError, setUploadError] = useState('')
  const [dragging, setDragging] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) { setFile(e.target.files[0]); setResult(null); setUploadError('') }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped?.name.match(/\.(xlsx|xls)$/)) { setFile(dropped); setResult(null); setUploadError('') }
    else setUploadError('Only .xlsx or .xls files are accepted')
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true); setResult(null); setUploadError('')
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await api.post('/hotels/upload-excel', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(res.data)
    } catch (err: any) {
      setUploadError(err.response?.data?.detail || 'Upload failed')
    } finally { setUploading(false) }
  }

  const downloadTemplate = () => {
    const csv = "name,city,price_per_night,rating,amenities,description,tenant_id\nTaj Hotel Mumbai,Mumbai,15000,4.8,\"Pool, Spa, WiFi\",Luxury hotel at Gateway,tenant_abc123"
    const blob = new Blob([csv], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
    a.download = 'hotel_upload_template.csv'; a.click()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-100">Billing & Hotel Data</h1>
        <p className="text-zinc-400 mt-1">Manage subscriptions and bulk-upload hotel inventory.</p>
      </div>

      {/* Subscription Plans */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { name: 'Free', price: '₹0/mo', features: ['1 Hotel', '100 Bookings/mo', 'Basic Bot', 'Email Support'], color: 'border-zinc-700', badge: '' },
          { name: 'Pro', price: '₹2,999/mo', features: ['10 Hotels', '2,000 Bookings/mo', 'AI Bot + Gemini', 'Priority Support', 'Custom Branding'], color: 'border-indigo-500', badge: 'Popular' },
          { name: 'Enterprise', price: 'Custom', features: ['Unlimited Hotels', 'Unlimited Bookings', 'Dedicated AI', 'SLA + 24/7 Support', 'White Label'], color: 'border-rose-500', badge: '' },
        ].map((plan, i) => (
          <motion.div key={plan.name} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
            className={`bg-zinc-900 border-2 ${plan.color} rounded-2xl p-6 relative`}>
            {plan.badge && <span className="absolute top-4 right-4 text-xs bg-indigo-500 text-white px-2 py-0.5 rounded-full">{plan.badge}</span>}
            <h3 className="text-lg font-bold text-zinc-100">{plan.name}</h3>
            <p className="text-2xl font-bold text-indigo-400 my-2">{plan.price}</p>
            <ul className="space-y-2 mt-4">
              {plan.features.map(f => (
                <li key={f} className="flex items-center gap-2 text-sm text-zinc-400">
                  <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" /> {f}
                </li>
              ))}
            </ul>
          </motion.div>
        ))}
      </div>

      {/* Excel Upload */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
            <div>
              <h3 className="font-semibold text-zinc-200">Bulk Upload Hotels via Excel</h3>
              <p className="text-xs text-zinc-500">Upload an .xlsx file to add multiple hotels at once.</p>
            </div>
          </div>
          <button onClick={downloadTemplate} className="flex items-center gap-2 px-3 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs rounded-lg transition-colors">
            <Download className="w-4 h-4" /> Download Template
          </button>
        </div>

        {/* Drag & Drop Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => document.getElementById('excel-input')?.click()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all
            ${dragging ? 'border-indigo-500 bg-indigo-500/10' : 'border-zinc-700 hover:border-zinc-500 bg-zinc-950/50'}`}
        >
          <Upload className="w-10 h-10 mx-auto mb-3 text-zinc-500" />
          <p className="text-zinc-400 text-sm">{file ? file.name : 'Drag & drop your .xlsx file here, or click to select'}</p>
          <p className="text-zinc-600 text-xs mt-1">Supported: .xlsx, .xls</p>
          <input id="excel-input" type="file" accept=".xlsx,.xls" className="hidden" onChange={handleFileChange} />
        </div>

        {/* Required Columns */}
        <div className="mt-4 bg-zinc-950/50 border border-zinc-800 rounded-lg p-4">
          <p className="text-xs text-zinc-500 mb-2 font-medium uppercase">Required Excel Columns:</p>
          <div className="flex flex-wrap gap-2">
            {['name', 'city', 'price_per_night', 'rating', 'amenities', 'description', 'tenant_id'].map(col => (
              <span key={col} className="px-2 py-1 bg-zinc-800 text-zinc-300 rounded text-xs font-mono">{col}</span>
            ))}
          </div>
        </div>

        {uploadError && (
          <div className="mt-4 flex items-center gap-2 p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400 text-sm">
            <AlertCircle className="w-4 h-4 flex-shrink-0" /> {uploadError}
          </div>
        )}

        {result && (
          <motion.div initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} className="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
            <p className="text-emerald-400 font-medium">✅ Upload Complete</p>
            <p className="text-emerald-300 text-sm mt-1">{result.hotels_added} hotel(s) added successfully.</p>
            {result.errors?.length > 0 && (
              <div className="mt-2"><p className="text-amber-400 text-xs font-medium">Warnings:</p>
                {result.errors.map((e, i) => <p key={i} className="text-amber-300 text-xs">{e}</p>)}
              </div>
            )}
          </motion.div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="mt-4 w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white py-2.5 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
        >
          <Upload className="w-4 h-4" />
          {uploading ? 'Uploading...' : 'Upload Hotels'}
        </button>
      </div>
    </div>
  )
}
