import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts'
import { useMemo } from 'react'
import { useApp } from '../context/AppContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'

/* ── Colour maps per theme ── */
const DARK_COLORS = {
  ideaFitness:       '#00d4ff',
  agentPerformance:  '#a78bff',
  conflictIntensity: '#ff6b6b',
  iterationGain:     '#00e5a0',
}
const LIGHT_COLORS = {
  ideaFitness:       '#0891b2',
  agentPerformance:  '#7c3aed',
  conflictIntensity: '#dc2626',
  iterationGain:     '#059669',
}

const KPI_META = [
  { key: 'ideaFitness',       label: 'Idea Fitness',      icon: '◎' },
  { key: 'conflictIntensity', label: 'Conflict Intensity', icon: '⚡' },
]

function toSeries(history) {
  return history.map((p, idx) => ({
    idx,
    iteration:         p.iteration         ?? 0,
    ideaFitness:       p.ideaFitness       ?? p.fitness       ?? p.idea_fitness ?? null,
    agentPerformance:  p.agentPerformance  ?? p.performance   ?? null,
    conflictIntensity: p.conflictIntensity ?? p.conflict      ?? null,
    iterationGain:     p.iterationGain     ?? p.gain          ?? null,
  }))
}

function fmt(v) {
  if (v == null || v === '') return '—'
  if (typeof v === 'number') return Number.isFinite(v) ? v.toFixed(2) : '—'
  return v
}

export default function MetricsPanel() {
  const { state } = useApp()
  const { theme } = useTheme()
  const data = useMemo(() => toSeries(state.metricsHistory), [state.metricsHistory])

  const COLORS = theme === 'dark' ? DARK_COLORS : LIGHT_COLORS
  const isDark = theme === 'dark'

  const gridColor = isDark ? 'rgba(108,99,255,0.08)' : 'rgba(80,70,229,0.06)'
  const axisColor = isDark ? 'rgba(108,99,255,0.12)' : 'rgba(80,70,229,0.10)'
  const tickColor = isDark ? 'rgba(140,155,200,0.50)' : 'rgba(71,85,105,0.50)'
  const tooltipBg = isDark ? 'rgba(9, 13, 28, 0.96)'  : 'rgba(255,255,255,0.97)'
  const tooltipBorder = isDark ? 'rgba(108,99,255,0.30)' : 'rgba(80,70,229,0.15)'
  const tooltipLabel = isDark ? 'rgba(200,210,255,0.75)' : 'rgba(51,65,85,0.70)'
  const tooltipItem  = isDark ? 'rgba(200,210,255,0.90)' : 'rgba(15,23,42,0.85)'
  const legendColor  = isDark ? 'rgba(140,155,200,0.70)' : 'rgba(71,85,105,0.65)'

  return (
    <div style={{ width: '100%', minHeight: 260 }}>
      {/* ── KPI cards ── */}
      <div className="kpi" style={{ marginBottom: 14 }}>
        {KPI_META.map(({ key, label, icon }) => {
          const raw = state.metrics?.[key] ?? state.metrics?.fitness ?? null
          const color = COLORS[key] || COLORS.ideaFitness
          return (
            <div className="kpi-card" key={key}>
              <div className="kpi-label">
                <span style={{ marginRight: 5, color }}>{icon}</span>
                {label}
              </div>
              <div className="kpi-value" style={{ color }}>
                {fmt(raw)}
              </div>
            </div>
          )
        })}
      </div>

      {/* ── Chart ── */}
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 14, left: -14, bottom: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="4 4" />
          <XAxis
            dataKey="idx"
            tick={{ fill: tickColor, fontSize: 10, fontFamily: 'Fira Code, monospace' }}
            axisLine={{ stroke: axisColor }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: tickColor, fontSize: 10, fontFamily: 'Fira Code, monospace' }}
            axisLine={{ stroke: axisColor }}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: tooltipBg,
              border: `1px solid ${tooltipBorder}`,
              borderRadius: 10,
              boxShadow: '0 8px 32px rgba(0,0,0,0.20)',
              fontFamily: 'Fira Code, monospace',
              fontSize: 12,
            }}
            labelStyle={{ color: tooltipLabel, marginBottom: 4 }}
            itemStyle={{ color: tooltipItem }}
            cursor={{ stroke: axisColor, strokeWidth: 1 }}
          />
          <Legend
            wrapperStyle={{
              color: legendColor,
              fontSize: 11,
              fontFamily: 'Fira Code, monospace',
            }}
          />
          <Line type="monotone" dataKey="ideaFitness"       stroke={COLORS.ideaFitness}       strokeWidth={2} dot={false} isAnimationActive={false} strokeLinecap="round" />
          <Line type="monotone" dataKey="agentPerformance"  stroke={COLORS.agentPerformance}  strokeWidth={2} dot={false} isAnimationActive={false} strokeLinecap="round" />
          <Line type="monotone" dataKey="conflictIntensity" stroke={COLORS.conflictIntensity} strokeWidth={2} dot={false} isAnimationActive={false} strokeLinecap="round" />
          <Line type="monotone" dataKey="iterationGain"     stroke={COLORS.iterationGain}     strokeWidth={2} dot={false} isAnimationActive={false} strokeLinecap="round" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
