"use client"
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { CalendarCheck, DollarSign, Hotel, Users } from 'lucide-react'
import api from '@/lib/api'

interface TenantStats {
  total_hotels: number
  total_bookings: number
  total_revenue: number
  total_agents: number
}

export default function TenantDashboard() {
  const [stats, setStats] = useState<TenantStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get('/stats/tenant')
        setStats(res.data)
      } catch (err: any) {
        setError('Failed to load stats')
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [])

  const cards = stats
    ? [
        { label: 'Total Revenue', value: `₹${stats.total_revenue.toLocaleString('en-IN')}`, icon: DollarSign, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
        { label: 'My Hotels', value: String(stats.total_hotels), icon: Hotel, color: 'text-blue-400', bg: 'bg-blue-400/10' },
        { label: 'Total Bookings', value: String(stats.total_bookings), icon: CalendarCheck, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
        { label: 'Staff / Agents', value: String(stats.total_agents), icon: Users, color: 'text-rose-400', bg: 'bg-rose-400/10' },
      ]
    : []

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Hotel Dashboard</h1>
          <p className="text-zinc-400 mt-1">Overview of your properties and bookings.</p>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex items-center space-x-4 animate-pulse">
              <div className="p-4 rounded-xl bg-zinc-800 w-14 h-14" />
              <div className="space-y-2 flex-1">
                <div className="h-3 bg-zinc-800 rounded w-3/4" />
                <div className="h-6 bg-zinc-800 rounded w-1/2" />
              </div>
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
              <motion.div
                key={card.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex items-center space-x-4"
              >
                <div className={`p-4 rounded-xl ${card.bg} ${card.color}`}>
                  <Icon className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-zinc-400 text-sm">{card.label}</p>
                  <p className="text-2xl font-bold text-zinc-100">{card.value}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Bookings — real data placeholder for table */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col min-h-[320px]">
          <h3 className="font-semibold text-lg mb-4 text-zinc-200">Recent Bookings</h3>
          <div className="flex-1 flex items-center justify-center text-zinc-500 text-sm">
            No bookings yet for this tenant.
          </div>
        </div>

        {/* Create Agent Form */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 flex flex-col">
          <h3 className="font-semibold text-lg mb-4 text-zinc-200">Create Staff / Agent</h3>
          <form
            className="flex flex-col gap-4 flex-1"
            onSubmit={async (e) => {
              e.preventDefault()
              const form = e.target as HTMLFormElement
              const email = (form.elements.namedItem('email') as HTMLInputElement).value
              const password = (form.elements.namedItem('password') as HTMLInputElement).value
              try {
                await api.post('/users/agent', { email, password })
                alert('Agent created successfully!')
                form.reset()
                // Refresh stats
                const res = await api.get('/stats/tenant')
                setStats(res.data)
              } catch (err: any) {
                alert(err.response?.data?.detail || 'Failed to create agent')
              }
            }}
          >
            <div className="flex-1 space-y-4">
              <div>
                <label className="text-xs text-zinc-400 uppercase">Agent Email</label>
                <input name="email" type="email" required className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none text-zinc-200" placeholder="reception@hotel.com" />
              </div>
              <div>
                <label className="text-xs text-zinc-400 uppercase">Temporary Password</label>
                <input name="password" type="password" required className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500 outline-none text-zinc-200" placeholder="••••••••" />
              </div>
            </div>
            <button type="submit" className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg font-medium transition-colors w-full mt-auto">
              Create Agent Account
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
