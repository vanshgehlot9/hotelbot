"use client"
import Link from 'next/link'
import { motion } from 'framer-motion'
import { Building2, Bot, CalendarCheck, ArrowRight, ShieldCheck } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-zinc-950 font-sans text-zinc-100 overflow-hidden">
      {/* Navigation */}
      <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto relative z-10">
        <div className="flex items-center gap-2">
          <Building2 className="w-8 h-8 text-indigo-500" />
          <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-rose-400">HotelBot SaaS</span>
        </div>
        <div className="flex items-center gap-6 text-sm font-medium">
          <Link href="/login" className="text-zinc-400 hover:text-zinc-100 transition-colors">Customer Login</Link>
          <Link href="/signup" className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full transition-all hover:shadow-[0_0_20px_rgba(79,70,229,0.3)]">Get Started</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative max-w-7xl mx-auto px-6 pt-20 pb-32 flex flex-col items-center text-center">
        {/* Background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-600/20 rounded-full blur-[120px] -z-10 pointer-events-none" />
        
        <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, ease: "easeOut" }} className="max-w-4xl">
          <span className="px-4 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 text-sm font-medium mb-6 inline-block">
            Enterprise-Grade Hotel Automation
          </span>
          <h1 className="text-6xl md:text-8xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-white via-zinc-200 to-zinc-600 mb-8 leading-tight">
            The Future of <br className="hidden md:block" />Hotel Bookings.
          </h1>
          <p className="text-xl text-zinc-400 max-w-2xl mx-auto mb-12">
            Automate your front desk with our AI-powered WhatsApp bot, manage staff seamlessly, and skyrocket your direct bookings without paying OTA commissions.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/signup" className="w-full sm:w-auto px-8 py-4 bg-zinc-100 text-zinc-950 hover:bg-white font-semibold rounded-full flex items-center justify-center gap-2 transition-transform hover:scale-105">
              Start Free Trial <ArrowRight className="w-5 h-5" />
            </Link>
            <Link href="#features" className="w-full sm:w-auto px-8 py-4 bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white hover:bg-zinc-800 font-semibold rounded-full transition-colors">
              View Portals
            </Link>
          </div>
        </motion.div>

        {/* Feature Cards / Portals */}
        <motion.div id="features" initial={{ opacity: 0, y: 40 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.2 }} className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-32 w-full text-left">
          <div className="bg-gradient-to-b from-zinc-900 to-zinc-950 p-8 rounded-3xl border border-zinc-800/50 hover:border-emerald-500/30 transition-colors group">
            <div className="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-emerald-500/20 transition-colors">
              <Building2 className="w-7 h-7 text-emerald-400" />
            </div>
            <h3 className="text-xl font-bold text-zinc-100 mb-2">Business Owners</h3>
            <p className="text-zinc-400 mb-6 line-clamp-2">Manage your properties, oversee your staff, and track real-time revenue analytics across all your hotels.</p>
            <Link href="/tenant/login" className="text-emerald-400 font-medium flex items-center gap-1 hover:text-emerald-300">Tenant Portal →</Link>
          </div>

          <div className="bg-gradient-to-b from-zinc-900 to-zinc-950 p-8 rounded-3xl border border-zinc-800/50 hover:border-blue-500/30 transition-colors group">
            <div className="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-blue-500/20 transition-colors">
              <CalendarCheck className="w-7 h-7 text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-zinc-100 mb-2">Hotel Staff</h3>
            <p className="text-zinc-400 mb-6 line-clamp-2">Access daily booking itineraries, manage guest check-ins, and override bot interactions seamlessly.</p>
            <Link href="/staff/login" className="text-blue-400 font-medium flex items-center gap-1 hover:text-blue-300">Staff Portal →</Link>
          </div>

          <div className="bg-gradient-to-b from-zinc-900 to-zinc-950 p-8 rounded-3xl border border-zinc-800/50 hover:border-indigo-500/30 transition-colors group">
            <div className="w-14 h-14 bg-indigo-500/10 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-indigo-500/20 transition-colors">
              <ShieldCheck className="w-7 h-7 text-indigo-400" />
            </div>
            <h3 className="text-xl font-bold text-zinc-100 mb-2">Platform Admin</h3>
            <p className="text-zinc-400 mb-6 line-clamp-2">Global God-mode. Manage subscriptions, on-board new tenants, and view cross-platform health metrics.</p>
            <Link href="/superadmin/login" className="text-indigo-400 font-medium flex items-center gap-1 hover:text-indigo-300">Admin Portal →</Link>
          </div>
        </motion.div>
      </main>
    </div>
  )
}
