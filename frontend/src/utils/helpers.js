export function safeJsonParse(raw) {
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export function nowMs() {
  return Date.now()
}

export function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n))
}

export function shortId(prefix = 'id') {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now().toString(16)}`
}

export function toText(value) {
  if (value == null) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export function actionToEdgeType(action) {
  if (action === 'attack' || action === 'disrupt') return 'critique'
  if (action === 'merge') return 'refinement'
  if (action === 'judge') return 'accepted'
  return 'refinement'
}

