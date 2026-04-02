import { safeJsonParse } from '../utils/helpers.js'

export class ArenaWebSocket {
  /**
   * @param {string} url
   * @param {(evt: any) => void} onEvent
   * @param {(status: 'connecting'|'open'|'closed'|'error') => void} onStatus
   */
  constructor(url, onEvent, onStatus) {
    this.url = url
    this.onEvent = onEvent
    this.onStatus = onStatus
    this.ws = null
    this.shouldRun = false
    this.reconnectAttempt = 0
    this.reconnectTimer = null
  }

  start() {
    if (this.shouldRun) return
    this.shouldRun = true
    this.#connect()
  }

  stop() {
    this.shouldRun = false
    this.reconnectAttempt = 0
    if (this.reconnectTimer) {
      window.clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      try {
        this.ws.close()
      } catch {
        // ignore
      }
      this.ws = null
    }
  }

  #scheduleReconnect() {
    if (!this.shouldRun) return
    const base = 350
    const max = 5000
    const delay = Math.min(max, base * 2 ** this.reconnectAttempt)
    this.reconnectAttempt = Math.min(this.reconnectAttempt + 1, 6)
    this.reconnectTimer = window.setTimeout(() => this.#connect(), delay)
  }

  #connect() {
    if (!this.shouldRun) return
    this.onStatus?.('connecting')

    try {
      this.ws = new WebSocket(this.url)
    } catch {
      this.onStatus?.('error')
      this.#scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      this.reconnectAttempt = 0
      this.onStatus?.('open')
    }

    this.ws.onerror = () => {
      this.onStatus?.('error')
    }

    this.ws.onclose = () => {
      this.onStatus?.('closed')
      this.#scheduleReconnect()
    }

    this.ws.onmessage = (msg) => {
      const raw = typeof msg?.data === 'string' ? msg.data : ''
      const parsed = safeJsonParse(raw)
      if (!parsed) return
      this.onEvent?.(parsed)
    }
  }
}

