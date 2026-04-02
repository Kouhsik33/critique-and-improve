import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
export const WS_BASE_URL =
  import.meta.env.VITE_WS_BASE_URL || API_BASE_URL.replace(/^http/i, 'ws')

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
})

export async function runArena(payload) {
  const res = await client.post('/run', payload)
  return res.data
}

export async function getMetrics(requestId) {
  if (!requestId) throw new Error('requestId is required for metrics')
  const res = await client.get(`/metrics/${requestId}`)
  return res.data
}

export async function getStatus(requestId) {
  if (!requestId) throw new Error('requestId is required for status')
  const res = await client.get(`/status/${requestId}`)
  return res.data
}
