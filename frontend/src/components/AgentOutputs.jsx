import { useMemo } from 'react'
import { useApp } from '../context/AppContext.jsx'

const AGENTS = [
  { key: 'creator',      label: 'Creator',      icon: '✦', color: '#38bdf8' },
  { key: 'critic',       label: 'Critic',       icon: '✸', color: '#ff6b6b' },
  { key: 'radical',      label: 'Radical',      icon: '✺', color: '#ffb347' },
  { key: 'synthesizer',  label: 'Synthesizer',  icon: '⟳', color: '#00e5a0' },
  { key: 'judge',        label: 'Judge',        icon: '⚖', color: '#a78bff' },
]

function extractOutput(evt) {
  if (!evt || typeof evt !== 'object') return null
  const data = evt.data || {}
  return (
    data.output ||
    data.idea ||
    data.ideas ||
    data.issue ||
    data.critique ||
    data.radicalIdea ||
    data.radical ||
    data.refinement ||
    data.merge_result ||
    data.verdict ||
    data.decision ||
    data.message ||
    data.text ||
    null
  )
}

export default function AgentOutputs() {
  const { state } = useApp()

  const latestByAgent = useMemo(() => {
    const map = {}
    for (let i = state.agentEvents.length - 1; i >= 0; i -= 1) {
      const evt = state.agentEvents[i]
      if (!evt || evt.type !== 'agent_action') continue
      const agent = evt.agent
      if (!agent || map[agent]) continue
      const output = extractOutput(evt)
      if (!output) continue
      map[agent] = {
        output: typeof output === 'string' ? output : JSON.stringify(output),
        iteration: evt.iteration ?? 0,
      }
      if (Object.keys(map).length >= AGENTS.length) break
    }
    return map
  }, [state.agentEvents])

  return (
    <div className="feedback-grid">
      {AGENTS.map((agent) => {
        const data = latestByAgent[agent.key]
        return (
          <div key={agent.key} className="feedback-column">
            <div
              className="panel-title"
              style={{ marginBottom: 10, color: agent.color, display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <span>{agent.icon}</span>
              {agent.label}
            </div>
            {!data ? (
              <div className="muted" style={{ fontSize: 'var(--text-sm)' }}>
                Waiting for output…
              </div>
            ) : (
              <ul className="list feedback-list">
                <li
                  className="list-item"
                  style={{ borderLeft: `3px solid ${agent.color}` }}
                >
                  <div className="list-item-header">
                    <div className="list-item-title">
                      <span className="dot" style={{ background: agent.color }} />
                      {agent.label}
                    </div>
                    <div className="list-item-meta" title="iteration">
                      iter&thinsp;<span className="mono">{data.iteration}</span>
                    </div>
                  </div>
                  <div className="list-item-body">{data.output}</div>
                </li>
              </ul>
            )}
          </div>
        )
      })}
    </div>
  )
}
