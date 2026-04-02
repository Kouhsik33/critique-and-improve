import { useMemo } from 'react'
import { useApp } from '../context/AppContext.jsx'

/* ── Per-agent colour / icon ──────────────────── */
const AGENT_META = {
  creator:     { color: '#00d4ff', icon: '✦' },
  critic:      { color: '#ff6b6b', icon: '✸' },
  radical:     { color: '#ffb347', icon: '✺' },
  synthesizer: { color: '#00e5a0', icon: '⟳' },
  judge:       { color: '#a78bff', icon: '⚖' },
}

const KPI_META = [
  { key: 'total',      label: 'Total Tokens',    icon: '∑' },
  { key: 'cost',       label: 'Est. Cost (USD)',  icon: '◈' },
  { key: 'efficiency', label: 'Tokens / Iter',    icon: '◉' },
  { key: 'agent',      label: 'Active Agent',     icon: '⬡' },
]

function usd(n) {
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString(undefined, { style: 'currency', currency: 'USD', minimumFractionDigits: 4 })
}

export default function TokenPanel() {
  const { state } = useApp()
  const tokens = state.tokens || {}

  const perAgent = useMemo(() => {
    const entries = Object.entries(tokens).filter(([k]) => k !== 'total')
    return entries
      .map(([agent, count]) => ({ agent, count: Number(count) || 0 }))
      .sort((a, b) => b.count - a.count)
  }, [tokens])

  const total      = Number(tokens.total) || perAgent.reduce((sum, x) => sum + x.count, 0)
  const USD_PER_1K = 0.002
  const cost       = (total / 1000) * USD_PER_1K
  const efficiency = state.iteration >= 0 ? total / (state.iteration + 1) : null
  const maxCount   = perAgent[0]?.count || 1

  const kpiValues = {
    total:      total || '—',
    cost:       usd(cost),
    efficiency: efficiency == null ? '—' : Math.round(efficiency),
    agent:      state.activeAgent || '—',
  }

  return (
    <div>
      {/* ── KPI cards ── */}
      <div className="kpi" style={{ marginBottom: 14 }}>
        {KPI_META.map(({ key, label, icon }) => {
          const meta = key === 'agent' ? AGENT_META[state.activeAgent] : null
          return (
            <div className="kpi-card" key={key}>
              <div className="kpi-label">
                <span style={{ marginRight: 5, color: 'var(--accent-lavender)' }}>{icon}</span>
                {label}
              </div>
              <div
                className="kpi-value"
                style={{ color: meta?.color || 'var(--text)', fontSize: key === 'agent' ? 14 : undefined }}
              >
                {meta && (
                  <span style={{ marginRight: 5 }}>{meta.icon}</span>
                )}
                {kpiValues[key]}
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Per-agent token bars ── */}
      {perAgent.length === 0 ? (
        <div className="muted" style={{ fontSize: 'var(--text-sm)', paddingTop: 4 }}>
          No token events yet.
        </div>
      ) : (
        <div className="token-bar-wrap">
          {perAgent.slice(0, 12).map((row) => {
            const meta  = AGENT_META[row.agent] || { color: '#6c63ff', icon: '·' }
            const pct   = Math.max(2, Math.round((row.count / maxCount) * 100))
            return (
              <div key={row.agent} className="token-bar-row">
                <div className="token-bar-label" title={row.agent}>
                  <span style={{ color: meta.color, marginRight: 5 }}>{meta.icon}</span>
                  {row.agent}
                </div>
                <div className="token-bar-track">
                  <div
                    className="token-bar-fill"
                    style={{
                      '--bar-w': `${pct}%`,
                      width: `${pct}%`,
                      background: `linear-gradient(90deg, ${meta.color}cc, ${meta.color})`,
                    }}
                  />
                </div>
                <div className="token-bar-count">{row.count.toLocaleString()}</div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
