"use client"
import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, KeyRound, Users, RefreshCw, X } from 'lucide-react'
import api from '@/lib/api'

interface Tenant {
  email: string
  role: string
  tenant_id: string
}

export default function ManageTenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [loading, setLoading] = useState(true)

  // Create modal state
  const [showCreate, setShowCreate] = useState(false)
  const [createEmail, setCreateEmail] = useState('')
  const [createPass, setCreatePass] = useState('')
  const [createLoading, setCreateLoading] = useState(false)
  const [createMsg, setCreateMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  // Change password modal state
  const [showChangePw, setShowChangePw] = useState(false)
  const [selectedEmail, setSelectedEmail] = useState('')
  const [newPass, setNewPass] = useState('')
  const [pwLoading, setPwLoading] = useState(false)
  const [pwMsg, setPwMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  const fetchTenants = async () => {
    setLoading(true)
    try {
      const res = await api.get('/users/tenants')
      setTenants(res.data.tenants)
    } catch { } finally { setLoading(false) }
  }

  useEffect(() => { fetchTenants() }, [])

  const handleCreateTenant = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreateLoading(true)
    setCreateMsg(null)
    try {
      const res = await api.post('/users/tenant', { email: createEmail, password: createPass })
      setCreateMsg({ text: `✅ Created! Tenant ID: ${res.data.tenant_id}`, type: 'success' })
      setCreateEmail(''); setCreatePass('')
      fetchTenants()
    } catch (err: any) {
      setCreateMsg({ text: err.response?.data?.detail || 'Failed', type: 'error' })
    } finally { setCreateLoading(false) }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwLoading(true)
    setPwMsg(null)
    try {
      await api.put('/users/change-password', { email: selectedEmail, new_password: newPass })
      setPwMsg({ text: '✅ Password updated successfully!', type: 'success' })
      setNewPass('')
    } catch (err: any) {
      setPwMsg({ text: err.response?.data?.detail || 'Failed', type: 'error' })
    } finally { setPwLoading(false) }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-zinc-100">Manage Tenants</h1>
          <p className="text-zinc-400 mt-1">Create and manage hotel owner accounts.</p>
        </div>
        <div className="flex gap-3">
          <button onClick={fetchTenants} className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-lg text-sm transition-colors">
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors">
            <Plus className="w-4 h-4" /> New Tenant
          </button>
        </div>
      </div>

      {/* Tenants Table */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-zinc-800 flex items-center gap-2">
          <Users className="w-5 h-5 text-zinc-400" />
          <span className="text-zinc-300 font-medium">All Tenant Admins ({tenants.length})</span>
        </div>
        {loading ? (
          <div className="space-y-2 p-4">
            {[1,2,3].map(i => <div key={i} className="h-14 bg-zinc-800 rounded-lg animate-pulse" />)}
          </div>
        ) : tenants.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-zinc-500 text-sm">No tenants yet. Create one!</div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {tenants.map((t, i) => (
              <motion.div key={t.email} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
                className="flex items-center justify-between p-4 hover:bg-zinc-800/40 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-9 h-9 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-sm font-bold">
                    {t.email.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-zinc-200 font-medium text-sm">{t.email}</p>
                    <p className="text-xs text-zinc-500 font-mono">Tenant ID: {t.tenant_id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="px-2 py-1 text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-full">{t.role}</span>
                  <button
                    onClick={() => { setSelectedEmail(t.email); setShowChangePw(true); setPwMsg(null); setNewPass('') }}
                    className="flex items-center gap-1 px-3 py-1.5 bg-amber-500/10 text-amber-400 border border-amber-500/20 rounded-lg text-xs hover:bg-amber-500/20 transition-colors"
                  >
                    <KeyRound className="w-3.5 h-3.5" /> Change Password
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Create Tenant Modal */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 w-full max-w-md">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold text-zinc-100">Create Tenant Admin</h2>
                <button onClick={() => { setShowCreate(false); setCreateMsg(null) }} className="text-zinc-500 hover:text-zinc-300"><X className="w-5 h-5" /></button>
              </div>
              <form onSubmit={handleCreateTenant} className="space-y-4">
                {createMsg && <div className={`p-3 rounded-lg text-sm border ${createMsg.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}`}>{createMsg.text}</div>}
                <div><label className="text-xs text-zinc-400 uppercase">Email</label><input value={createEmail} onChange={e => setCreateEmail(e.target.value)} type="email" required className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-zinc-200 outline-none focus:ring-2 focus:ring-indigo-500" placeholder="owner@hotel.com" /></div>
                <div><label className="text-xs text-zinc-400 uppercase">Password</label><input value={createPass} onChange={e => setCreatePass(e.target.value)} type="password" required className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-zinc-200 outline-none focus:ring-2 focus:ring-indigo-500" placeholder="••••••••" /></div>
                <button type="submit" disabled={createLoading} className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-2 rounded-lg font-medium transition-colors">
                  {createLoading ? 'Creating...' : 'Create Account'}
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Change Password Modal */}
      <AnimatePresence>
        {showChangePw && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.95, opacity: 0 }}
              className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 w-full max-w-md">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-semibold text-zinc-100">Change Password</h2>
                <button onClick={() => { setShowChangePw(false); setPwMsg(null) }} className="text-zinc-500 hover:text-zinc-300"><X className="w-5 h-5" /></button>
              </div>
              <p className="text-zinc-500 text-sm mb-4">Changing password for: <span className="text-indigo-400 font-mono">{selectedEmail}</span></p>
              <form onSubmit={handleChangePassword} className="space-y-4">
                {pwMsg && <div className={`p-3 rounded-lg text-sm border ${pwMsg.type === 'success' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'}`}>{pwMsg.text}</div>}
                <div><label className="text-xs text-zinc-400 uppercase">New Password</label><input value={newPass} onChange={e => setNewPass(e.target.value)} type="password" required minLength={6} className="w-full mt-1 bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-zinc-200 outline-none focus:ring-2 focus:ring-amber-500" placeholder="New password (min 6 chars)" /></div>
                <button type="submit" disabled={pwLoading} className="w-full bg-amber-600 hover:bg-amber-500 text-white py-2 rounded-lg font-medium transition-colors">
                  {pwLoading ? 'Updating...' : 'Update Password'}
                </button>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
