import { useMemo } from 'react'
import { useApp } from '../context/AppContext.jsx'

const SECTIONS = [
  {
    key:        'critiques',
    stateKey:   'critiques',
    title:      'Critic Issues',
    icon:       '✸',
    colorClass: 'red',
    edgeClass:  'red-edge',
    color:      '#ff6b6b',
  },
  {
    key:        'radical',
    stateKey:   'radicalIdeas',
    title:      'Radical Ideas',
    icon:       '✺',
    colorClass: 'amber',
    edgeClass:  'amber-edge',
    color:      '#ffb347',
  },
  {
    key:        'refinement',
    stateKey:   null,         // derived
    title:      'Synthesizer Output',
    icon:       '⟳',
    colorClass: 'green',
    edgeClass:  'green-edge',
    color:      '#00e5a0',
  },
]

function Section({ title, icon, colorClass, edgeClass, color, items }) {
  return (
    <div className="feedback-column">
      <div
        className="panel-title"
        style={{ marginBottom: 10, color, display: 'flex', alignItems: 'center', gap: 6 }}
      >
        <span>{icon}</span>
        {title}
      </div>
      {items.length === 0 ? (
        <div className="muted" style={{ fontSize: 'var(--text-sm)' }}>
          Waiting for events…
        </div>
      ) : (
        <ul className="list feedback-list">
          {items.map((it) => (
            <li key={it.id} className={`list-item ${edgeClass}`}>
              <div className="list-item-header">
                <div className="list-item-title">
                  <span className={`dot ${colorClass}`} />
                  {it.agent || 'agent'}
                </div>
                <div className="list-item-meta" title="iteration">
                  iter&thinsp;<span className="mono">{it.iteration ?? 0}</span>
                </div>
              </div>
              <div className="list-item-body">{it.text}</div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function FeedbackPanel() {
  const { state } = useApp()

  const critiques = useMemo(
    () => state.critiques.slice().reverse().slice(0, 25),
    [state.critiques],
  )
  const radical = useMemo(
    () => state.radicalIdeas.slice().reverse().slice(0, 18),
    [state.radicalIdeas],
  )
  const refinement = useMemo(() => {
    if (!state.refinedOutput) return []
    return [
      {
        id:        'refined',
        agent:     state.activeAgent,
        iteration: state.iteration,
        text:      state.refinedOutput,
      },
    ]
  }, [state.refinedOutput, state.activeAgent, state.iteration])

  const itemsMap = { critiques, radical, refinement }

  return (
    <div className="feedback-grid">
      {SECTIONS.map((s) => (
        <Section
          key={s.key}
          title={s.title}
          icon={s.icon}
          colorClass={s.colorClass}
          edgeClass={s.edgeClass}
          color={s.color}
          items={itemsMap[s.key]}
        />
      ))}
    </div>
  )
}
