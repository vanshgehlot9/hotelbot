/**
 * Parses FastAPI error responses into a human-readable string.
 * FastAPI can return detail as:
 *   - A string: "Not authenticated"
 *   - An array of Pydantic validation objects: [{type, loc, msg, input}]
 */
export function parseApiError(err: any, fallback = 'An error occurred'): string {
  const detail = err?.response?.data?.detail
  if (!detail) return fallback
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d: any) => d?.msg || JSON.stringify(d)).join(', ')
  }
  return fallback
}
