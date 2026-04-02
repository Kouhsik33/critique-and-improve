import { useMemo } from 'react'
import { useApp } from '../context/AppContext.jsx'

/* ── Agent type → colour / glow mapping ─────── */
const AGENT_META = {
  creator:     { color: '#00d4ff', border: 'rgba(0,212,255,0.55)',   icon: '✦', action: 'generate'  },
  critic:      { color: '#ff6b6b', border: 'rgba(255,107,107,0.55)', icon: '✸', action: 'attack'    },
  radical:     { color: '#ffb347', border: 'rgba(255,179,71,0.55)',  icon: '✺', action: 'disrupt'   },
  synthesizer: { color: '#00e5a0', border: 'rgba(0,229,160,0.55)',   icon: '⟳', action: 'merge'     },
  judge:       { color: '#a78bff', border: 'rgba(167,139,255,0.55)', icon: '⚖', action: 'judge'     },
}

function stateDot(status) {
  if (status === 'generate') return 'blue'
  if (status === 'attack')   return 'red'
  if (status === 'disrupt')  return 'amber'
  if (status === 'merge')    return 'green'
  if (status === 'judge')    return 'purple'
  return ''
}

export default function AgentStatus() {
  const { state } = useApp()

  const agents = useMemo(
    () => ['creator', 'critic', 'radical', 'synthesizer', 'judge'],
    [],
  )

  const activeAgent = state.activeAgent || null

  return (
    <div>
      <div className="panel-title" style={{ marginBottom: 12 }}>
        ⬡ Agent Status
      </div>
      <div className="status-grid">
        {agents.map((agent) => {
          const status   = state.agentStatus?.[agent] || 'idle'
          const isActive = activeAgent === agent
          const meta     = AGENT_META[agent] || {}
          const dotColor = stateDot(status)

          return (
            <div
              key={agent}
              className={`status-card${isActive ? ' active' : ''}`}
              aria-label={`Agent ${agent} — ${status}`}
              style={isActive ? {
                borderColor: meta.border,
                boxShadow: `0 0 0 2px ${meta.border}40, 0 0 24px ${meta.color}22`,
              } : {}}
            >
              <div className="status-agent">
                <span
                  className={`dot ${dotColor}${isActive ? ' pulse' : ''}`}
                  style={isActive ? { boxShadow: `0 0 6px ${meta.color}` } : {}}
                />
                <span style={{ color: isActive ? meta.color : 'var(--text)', fontWeight: isActive ? 600 : 400 }}>
                  {meta.icon && <span style={{ marginRight: 5 }}>{meta.icon}</span>}
                  {agent}
                </span>
              </div>
              <div
                className="status-state"
                style={{ color: isActive ? meta.color : 'var(--muted)', fontWeight: isActive ? 500 : 400 }}
              >
                {status}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
