"use client"
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Lock, Mail, ArrowRight } from 'lucide-react'
import api from '@/lib/api'
import { parseApiError } from '@/lib/parseApiError'

export default function SuperAdminLogin() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const res = await api.post('/auth/superadmin/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      localStorage.setItem('superadmin_token', res.data.access_token)
      router.push('/superadmin/dashboard')
    } catch (err: any) {
      setError(parseApiError(err, 'Invalid super admin credentials'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center">
          <div className="mx-auto w-16 h-16 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl flex items-center justify-center mb-6">
            <Lock className="w-8 h-8 text-indigo-400" />
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-zinc-100">Super Admin</h2>
          <p className="mt-2 text-sm text-zinc-400">Platform Management Portal</p>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-zinc-900 py-8 px-4 shadow sm:rounded-2xl sm:px-10 border border-zinc-800">
            <form className="space-y-6" onSubmit={handleLogin}>
              <div>
                <label className="block text-sm font-medium text-zinc-300">Email address</label>
                <div className="mt-2 relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-zinc-700 rounded-xl bg-zinc-950 text-zinc-100 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="admin@hotelbot.com" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-300">Password</label>
                <div className="mt-2 relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <input type="password" required value={password} onChange={e => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-zinc-700 rounded-xl bg-zinc-950 text-zinc-100 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                    placeholder="••••••••" />
                </div>
              </div>

              {error && <div className="text-rose-400 text-sm bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg">{error}</div>}

              <button type="submit" disabled={loading}
                className="w-full flex justify-center items-center gap-2 py-2.5 px-4 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-zinc-900 focus:ring-indigo-500 disabled:opacity-50 transition-colors">
                {loading ? 'Authenticating...' : 'Enter System'} <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
