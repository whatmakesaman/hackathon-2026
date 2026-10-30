import { mockApi } from './mocks/sample'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export async function api(path, options) {
  if (USE_MOCK) return mockApi(path, options)
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw Object.assign(new Error('api error'), { status: res.status })
  return res.json()
}
