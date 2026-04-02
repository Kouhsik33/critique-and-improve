import { motion, AnimatePresence } from 'framer-motion'
import { useMemo } from 'react'
import { useApp } from '../context/AppContext.jsx'

const STEPS = [
  { key: 'generate', label: 'Creator',     icon: '✦', agent: 'creator',     color: 'blue' },
  { key: 'attack',   label: 'Critic',      icon: '✸', agent: 'critic',      color: 'red'  },
  { key: 'disrupt',  label: 'Radical',     icon: '✺', agent: 'radical',     color: 'amber'},
  { key: 'merge',    label: 'Synthesizer', icon: '⟳', agent: 'synthesizer', color: 'green'},
  { key: 'judge',    label: 'Judge',       icon: '⚖', agent: 'judge',       color: 'purple'},
]

export default function AgentTimeline() {
  const { state } = useApp()

  const lastAgentAction = useMemo(() => {
    for (let i = state.agentEvents.length - 1; i >= 0; i -= 1) {
      const event = state.agentEvents[i]
      if (event?.type === 'agent_action' && event?.action) return event
    }
    return null
  }, [state.agentEvents])

  const activeAction = lastAgentAction?.action || null
  const activeStep   = STEPS.find((step) => step.key === activeAction) || null

  const cycle = useMemo(() => {
    const iter = (state.iteration ?? 0) + 1
    return `Iteration ${iter}`
  }, [state.iteration])

  return (
    <div className="agent-stack">
      {/* ── Vertical agent bars ── */}
      <div className="agent-stack-list" role="list" aria-label="Agent action timeline">
        {STEPS.map((s) => {
          const isActive = s.key === activeAction
          return (
            <motion.div
              key={s.key}
              className={`agent-bar ${s.key}${isActive ? ' active' : ''}`}
              role="listitem"
              aria-current={isActive ? 'step' : undefined}
              layout
              transition={{ type: 'spring', stiffness: 480, damping: 32 }}
            >
              <span className="agent-bar-icon">{s.icon}</span>
              <span className="agent-bar-label">{s.label}</span>
              <span className="agent-bar-node">N{STEPS.indexOf(s) + 1}</span>
            </motion.div>
          )
        })}
      </div>

    </div>
  )
}

function stepLabel(actionName) {
  const map = { generate: 'N1·Creator', attack: 'N2·Critic', disrupt: 'N3·Radical', merge: 'N4·Synth', judge: 'N5·Judge' }
  return map[actionName] || actionName || '—'
}

function stepEdgeColor(key) {
  const map = {
    generate: 'rgba(0, 212, 255, 0.40)',
    attack:   'rgba(255, 107, 107, 0.40)',
    disrupt:  'rgba(255, 179, 71, 0.40)',
    merge:    'rgba(0, 229, 160, 0.40)',
    judge:    'rgba(167, 139, 255, 0.40)',
  }
  return map[key] || 'rgba(255,255,255,0.10)'
}
