"use client"
import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { LogOut, LayoutDashboard, Users, Hotel, CreditCard } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function TenantLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const isLoginPage = pathname === '/tenant/login'
  const [authorized, setAuthorized] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    if (pathname === '/tenant/login') return
    const token = localStorage.getItem('tenant_token')
    if (!token) {
      router.push('/tenant/login')
      return
    }
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.role !== 'tenant_admin') throw new Error()
      setAuthorized(true)
    } catch {
      localStorage.removeItem('tenant_token')
      router.push('/tenant/login')
    }
  }, [router, pathname])

  const handleLogout = () => {
    localStorage.removeItem('tenant_token')
    router.push('/tenant/login')
  }

  // Login page: skip auth guard, just render the form
  if (isLoginPage) return <>{children}</>

  // Before mount: render nothing — server + client match (no hydration mismatch)
  if (!mounted) return null

  // Mounted but not yet authorized: blank dark screen while redirect happens
  if (!authorized) return <div className="min-h-screen bg-zinc-950" />

  const links = [
    { name: 'Hotel Dashboard', href: '/tenant/dashboard', icon: LayoutDashboard },
    { name: 'My Properties', href: '/tenant/properties', icon: Hotel },
    { name: 'Manage Agents', href: '/tenant/agents', icon: Users },
    { name: 'Billing', href: '/tenant/billing', icon: CreditCard },
  ]

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100 font-sans">
      <motion.aside 
        initial={{ x: -250 }}
        animate={{ x: 0 }}
        className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col"
      >
        <div className="p-6 border-b border-zinc-800">
          <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">HotelBot SaaS</h2>
          <p className="text-xs text-zinc-500 uppercase mt-1">Tenant Admin</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {links.map((link) => {
            const Icon = link.icon
            const isActive = pathname === link.href
            return (
              <Link key={link.name} href={link.href}>
                <div className={cn(
                  "flex items-center space-x-3 px-4 py-3 rounded-xl transition-all",
                  isActive 
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" 
                    : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800"
                )}>
                  <Icon className="w-5 h-5" />
                  <span className="font-medium text-sm">{link.name}</span>
                </div>
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-zinc-800">
          <button 
            onClick={handleLogout}
            className="flex items-center space-x-3 px-4 py-3 rounded-xl w-full text-zinc-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium text-sm">Log out</span>
          </button>
        </div>
      </motion.aside>

      <main className="flex-1 overflow-y-auto bg-zinc-950">
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-8"
        >
          {children}
        </motion.div>
      </main>
    </div>
  )
}
