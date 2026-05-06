import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const path = request.nextUrl.pathname

  // Public paths that don't require authentication
  if (
    path === '/' || 
    path === '/login' || 
    path === '/signup' || 
    path.startsWith('/_next') || 
    path.startsWith('/api') ||
    path.endsWith('/login') // All role-specific login pages
  ) {
    return NextResponse.next()
  }

  // Helper to decode JWT without a library (Edge compatible)
  const parseJwt = (token: string) => {
    try {
      return JSON.parse(atob(token.split('.')[1]))
    } catch (e) {
      return null
    }
  }

  // 1. SuperAdmin Route Protection
  if (path.startsWith('/superadmin')) {
    // Note: Cookies aren't used currently, we use localStorage.
    // However, middleware CANNOT read localStorage.
    // If the SaaS relies on localStorage, middleware protection is limited.
    // For a true enterprise SaaS, we MUST move tokens to cookies.
    // But since this is a refactor based on existing localStorage logic,
    // we will pass the request through and rely on the layout.tsx to kick them out,
    // OR we can implement an edge-compatible solution.
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}
