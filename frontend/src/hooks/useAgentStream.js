import { useEffect, useRef } from 'react'
import { ArenaWebSocket } from '../services/websocket.js'
import { getMetrics, getStatus } from '../services/api.js'
import { useApp } from '../context/AppContext.jsx'

export function useAgentStream(wsUrl, requestId) {
  const { dispatch } = useApp()
  const socketRef = useRef(null)

  useEffect(() => {
    if (!requestId || !wsUrl) {
      dispatch({ type: 'WS_STATUS', payload: { status: 'closed' } })
      return undefined
    }

    const socket = new ArenaWebSocket(
      wsUrl,
      (evt) => dispatch({ type: 'STREAM_EVENT', payload: evt }),
      (status) => {
        const mapped =
          status === 'connecting'
            ? 'connecting'
            : status === 'open'
              ? 'open'
              : status === 'error'
                ? 'error'
                : 'closed'
        dispatch({ type: 'WS_STATUS', payload: { status: mapped } })
      },
    )
    socketRef.current = socket
    socket.start()

    // Pull request-scoped metrics and status while workflow is running.
    const timer = window.setInterval(async () => {
      try {
        const metrics = await getMetrics(requestId)
        dispatch({ type: 'METRICS_UPDATE', payload: metrics })
      } catch {
        // ignore transient metrics fetch errors
      }

      try {
        const status = await getStatus(requestId)
        dispatch({ type: 'STATUS_UPDATE', payload: status })
      } catch {
        // ignore transient status fetch errors
      }
    }, 2000)

    return () => {
      window.clearInterval(timer)
      socket.stop()
      socketRef.current = null
    }
  }, [wsUrl, requestId, dispatch])
}

