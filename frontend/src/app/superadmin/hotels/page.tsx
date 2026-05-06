"use client"
import { useEffect, useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { Building2, MapPin, Star, IndianRupee, RefreshCw, Search, Filter, Trash2 } from 'lucide-react'
import api from '@/lib/api'

interface Hotel {
  id: string
  name: string
  city: string
  state?: string
  price_per_night: number
  rating: number
  tenant_id: string
  available: boolean
}

export default function ManageHotelsPage() {
  const [hotels, setHotels] = useState<Hotel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filter States
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedState, setSelectedState] = useState('All')
  const [selectedCity, setSelectedCity] = useState('All')

  const fetchHotels = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/hotels/')
      setHotels(res.data.hotels)
    } catch (err: any) {
      setError('Failed to fetch hotels')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete ${name}? This action cannot be undone.`)) return
    try {
      await api.delete(`/hotels/${id}`)
      setHotels(prev => prev.filter(h => h.id !== id))
    } catch (err: any) {
      alert('Failed to delete hotel')
    }
  }

  useEffect(() => {
    fetchHotels()
  }, [])

  // Get unique states and cities for the dropdowns
  const uniqueStates = useMemo(() => {
    const states = hotels.map(h => h.state || 'Unknown').filter(Boolean)
    return ['All', ...Array.from(new Set(states)).sort()]
  }, [hotels])

  const uniqueCities = useMemo(() => {
    let filteredHotels = hotels
    if (selectedState !== 'All') {
      filteredHotels = hotels.filter(h => (h.state || 'Unknown') === selectedState)
    }
    const cities = filteredHotels.map(h => h.city).filter(Boolean)
    return ['All', ...Array.from(new Set(cities)).sort()]
  }, [hotels, selectedState])

  // If state changes, reset city if it's no longer valid
  useEffect(() => {
    if (selectedCity !== 'All' && !uniqueCities.includes(selectedCity)) {
      setSelectedCity('All')
    }
  }, [uniqueCities, selectedCity])

  // Apply filters
  const filteredHotels = useMemo(() => {
    return hotels.filter(h => {
      const matchState = selectedState === 'All' || (h.state || 'Unknown') === selectedState
      const matchCity = selectedCity === 'All' || h.city === selectedCity
      const matchSearch = h.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          h.city.toLowerCase().includes(searchQuery.toLowerCase())
      return matchState && matchCity && matchSearch
    })
  }, [hotels, selectedState, selectedCity, searchQuery])

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Global Hotel Inventory</h1>
          <p className="text-zinc-400 mt-1">View and filter all hotels across states and districts.</p>
        </div>
        <button onClick={fetchHotels} className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-sm transition-colors">
          <RefreshCw className="w-4 h-4" /> Refresh List
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-4 flex flex-col md:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-500" />
          <input 
            type="text" 
            placeholder="Search hotels by name..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-zinc-200 text-sm"
          />
        </div>

        {/* State Filter */}
        <div className="w-full md:w-48 relative">
          <Filter className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-500" />
          <select 
            value={selectedState}
            onChange={(e) => setSelectedState(e.target.value)}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-2.5 pl-9 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-zinc-200 text-sm appearance-none cursor-pointer"
          >
            {uniqueStates.map(state => (
              <option key={state} value={state}>{state === 'All' ? 'All States' : state}</option>
            ))}
          </select>
        </div>

        {/* City Filter */}
        <div className="w-full md:w-48 relative">
          <MapPin className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-zinc-500" />
          <select 
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            disabled={uniqueCities.length <= 1}
            className="w-full bg-zinc-950 border border-zinc-800 rounded-xl py-2.5 pl-9 pr-8 focus:outline-none focus:ring-2 focus:ring-indigo-500 text-zinc-200 text-sm appearance-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uniqueCities.map(city => (
              <option key={city} value={city}>{city === 'All' ? 'All Districts' : city}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Building2 className="w-5 h-5 text-indigo-400" />
            <span className="text-zinc-300 font-medium">Platform Hotels ({filteredHotels.length})</span>
          </div>
        </div>

        {loading ? (
          <div className="p-4 space-y-3">
            {[1,2,3,4,5].map(i => <div key={i} className="h-16 bg-zinc-800 rounded-xl animate-pulse" />)}
          </div>
        ) : error ? (
          <div className="p-6 text-center text-rose-400">{error}</div>
        ) : filteredHotels.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-zinc-500">
            <Building2 className="w-12 h-12 mb-3 opacity-20" />
            <p>No hotels match your filters.</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {filteredHotels.map((h, i) => (
              <motion.div key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}
                className="flex items-center justify-between p-4 hover:bg-zinc-800/40 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                    <Building2 className="w-6 h-6" />
                  </div>
                  <div>
                    <p className="text-zinc-200 font-medium text-base">{h.name}</p>
                    <div className="flex flex-wrap items-center gap-3 mt-1 text-xs text-zinc-500">
                      <span className="flex items-center gap-1 bg-zinc-800 px-2 py-0.5 rounded-md text-zinc-300">
                        <MapPin className="w-3 h-3" /> {h.state || 'Unknown'} → {h.city}
                      </span>
                      <span className="flex items-center gap-1 text-amber-400"><Star className="w-3 h-3 fill-amber-400" /> {h.rating}</span>
                      <span>Tenant ID: <span className="font-mono text-zinc-400">{h.tenant_id}</span></span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="flex items-center justify-end gap-0.5 text-sm font-medium text-emerald-400">
                      <IndianRupee className="w-3.5 h-3.5" />{h.price_per_night}
                    </p>
                    <p className="text-xs text-zinc-500">per night</p>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium border hidden sm:block ${h.available ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}`}>
                    {h.available ? 'Available' : 'Unavailable'}
                  </span>
                  <button onClick={() => handleDelete(h.id, h.name)} className="p-2 ml-2 bg-rose-500/10 text-rose-400 hover:bg-rose-500 hover:text-white rounded-lg transition-colors" title="Delete Hotel">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
