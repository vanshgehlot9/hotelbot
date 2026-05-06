"use client"
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { CheckSquare, LogIn, LogOut, Clock } from 'lucide-react'
import api from '@/lib/api'

interface AgentStats {
  arrivals_today: number
  departures_today: number
  pending_bookings: number
  total_confirmed: number
  todays_arrivals: Booking[]
}

interface Booking {
  booking_id: string
  guest_name: string
  hotel_name: string
  checkin: string
  checkout: string
  rooms: number
  status: string
  phone?: string
}

export default function AgentDashboard() {
  const [stats, setStats] = useState<AgentStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await api.get('/stats/agent')
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
        { label: 'Arrivals Today', value: String(stats.arrivals_today), icon: LogIn, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
        { label: 'Departures Today', value: String(stats.departures_today), icon: LogOut, color: 'text-rose-400', bg: 'bg-rose-400/10' },
        { label: 'Upcoming Bookings', value: String(stats.pending_bookings), icon: Clock, color: 'text-amber-400', bg: 'bg-amber-400/10' },
        { label: 'Total Confirmed', value: String(stats.total_confirmed), icon: CheckSquare, color: 'text-blue-400', bg: 'bg-blue-400/10' },
      ]
    : []

  const getInitials = (name: string) =>
    name ? name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2) : 'NA'

  const getNights = (checkin: string, checkout: string) => {
    try {
      const d1 = new Date(checkin), d2 = new Date(checkout)
      return Math.max(Math.round((d2.getTime() - d1.getTime()) / 86400000), 1)
    } catch { return 1 }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Daily Operations</h1>
          <p className="text-zinc-400 mt-1">Manage today's arrivals and active guests.</p>
        </div>
        <div className="text-sm text-zinc-500">
          {new Date().toLocaleDateString('en-IN', { weekday: 'long', month: 'long', day: 'numeric' })}
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

      {/* Today's Arrivals Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
        <h3 className="font-semibold text-lg mb-6 text-zinc-200">Today's Arrivals</h3>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-zinc-800 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : stats?.todays_arrivals?.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-zinc-500 text-sm">
            No arrivals scheduled for today.
          </div>
        ) : (
          <div className="space-y-3">
            {stats?.todays_arrivals?.map((booking) => (
              <motion.div
                key={booking.booking_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center justify-between p-4 bg-zinc-950 rounded-xl border border-zinc-800/50"
              >
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-indigo-500/20 text-indigo-400 rounded-full flex items-center justify-center font-bold text-sm">
                    {getInitials(booking.guest_name)}
                  </div>
                  <div>
                    <p className="font-medium text-zinc-200">{booking.guest_name}</p>
                    <p className="text-xs text-zinc-500">#{booking.booking_id} · {booking.phone || 'N/A'}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right hidden sm:block">
                    <p className="text-sm font-medium text-zinc-300">{booking.hotel_name}</p>
                    <p className="text-xs text-zinc-500">
                      {getNights(booking.checkin, booking.checkout)} Night(s) · {booking.rooms} Room(s)
                    </p>
                  </div>
                  <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded-lg text-xs font-medium">
                    {booking.status}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
