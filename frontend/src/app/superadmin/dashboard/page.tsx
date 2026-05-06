"use client"
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Users, TrendingUp, Hotel, CalendarCheck } from 'lucide-react'
import api from '@/lib/api'

interface PlatformStats {
  total_tenants: number
  total_hotels: number
  total_bookings: number
  total_revenue: number
  total_users: number
}

export default function SuperAdminDashboard() {
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [health, setHealth] = useState<Record<string, string> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api.get('/stats/superadmin'),
      api.get('/health')
    ])
      .then(([statsRes, healthRes]) => {
        setStats(statsRes.data)
        setHealth(healthRes.data)
      })
      .catch(() => setError('Failed to load dashboard data'))
      .finally(() => setLoading(false))
  }, [])

  const cards = stats
    ? [
        { label: 'Total Tenants', value: String(stats.total_tenants), icon: Users, color: 'text-blue-400', bg: 'bg-blue-400/10' },
        { label: 'Active Hotels', value: String(stats.total_hotels), icon: Hotel, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
        { label: 'Total Revenue', value: `₹${stats.total_revenue.toLocaleString('en-IN')}`, icon: TrendingUp, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
        { label: 'Total Bookings', value: String(stats.total_bookings), icon: CalendarCheck, color: 'text-rose-400', bg: 'bg-rose-400/10' },
      ]
    : []

  const healthData = health ? [
    { label: 'Firebase Firestore', status: health.firebase },
    { label: 'Redis Cache', status: health.redis },
    { label: 'WhatsApp Bot', status: health.whatsapp },
    { label: 'Gemini AI', status: health.gemini },
    { label: 'Razorpay', status: health.razorpay },
  ] : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-zinc-100">Platform Overview</h1>
        <p className="text-zinc-400 mt-1">Monitor the global health of HotelBot SaaS.</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1,2,3,4].map(i => (
            <div key={i} className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex items-center space-x-4 animate-pulse">
              <div className="p-4 rounded-xl bg-zinc-800 w-14 h-14" />
              <div className="space-y-2 flex-1"><div className="h-3 bg-zinc-800 rounded w-3/4" /><div className="h-6 bg-zinc-800 rounded w-1/2" /></div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="text-rose-400 bg-rose-500/10 border border-rose-500/20 p-4 rounded-xl">{error}</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {cards.map((card, i) => {
            const Icon = card.icon
            return (
              <motion.div key={card.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex items-center space-x-4">
                <div className={`p-4 rounded-xl ${card.bg} ${card.color}`}><Icon className="w-6 h-6" /></div>
                <div><p className="text-zinc-400 text-sm">{card.label}</p><p className="text-2xl font-bold text-zinc-100">{card.value}</p></div>
              </motion.div>
            )
          })}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
          <h3 className="font-semibold text-zinc-200 mb-2">Quick Actions</h3>
          <p className="text-zinc-500 text-sm mb-4">Use the sidebar to manage tenants, upload hotels, or handle billing.</p>
          <div className="flex flex-wrap gap-3">
            <a href="/superadmin/tenants" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg transition-colors">Manage Tenants →</a>
            <a href="/superadmin/billing" className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm rounded-lg transition-colors">Billing & Hotels →</a>
          </div>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
          <h3 className="font-semibold text-zinc-200 mb-2">System Status</h3>
          <div className="space-y-3 mt-2">
            {loading ? (
               <div className="animate-pulse space-y-3">
                 {[1,2,3].map(i => <div key={i} className="h-6 bg-zinc-800 rounded w-full" />)}
               </div>
            ) : healthData.map(s => {
               const isOk = s.status === 'Connected' || s.status === 'Running' || s.status === 'Configured'
               const isWarn = s.status === 'Test Mode'
               return (
                 <div key={s.label} className="flex justify-between items-center">
                   <span className="text-zinc-400 text-sm">{s.label}</span>
                   <span className={`text-xs px-2 py-1 border rounded-full ${isOk ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : isWarn ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}`}>
                     {s.status}
                   </span>
                 </div>
               )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
