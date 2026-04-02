import { motion, useScroll, useTransform } from 'framer-motion'
import { useCallback, useMemo, useRef, useState } from 'react'
import { AppProvider, useApp } from './context/AppContext.jsx'
import { ThemeProvider, useTheme } from './context/ThemeContext.jsx'
import IdeaGraph from './components/IdeaGraph.jsx'
import AgentTimeline from './components/AgentTimeline.jsx'
import MetricsPanel from './components/MetricsPanel.jsx'
import TokenPanel from './components/TokenPanel.jsx'
import AgentOutputs from './components/AgentOutputs.jsx'
import { API_BASE_URL, WS_BASE_URL, runArena } from './services/api.js'
import { useAgentStream } from './hooks/useAgentStream.js'
import { useDemoStream } from './hooks/useDemoStream.js'

function Shell() {
  const { state, dispatch } = useApp()
  const { theme, toggleTheme } = useTheme()
  const [prompt, setPrompt] = useState('')
  const [isStarting, setIsStarting] = useState(false)
  const titleRef = useRef(null)

  // ── Scroll-driven card transitions ──
  const { scrollY } = useScroll()

  // Pivot from stack to row (spread over a longer scroll duration)
  const x1 = useTransform(scrollY, [0, 900], [-10, -600])
  const x2 = useTransform(scrollY, [0, 900], [12,  -300])
  const x3 = useTransform(scrollY, [0, 900], [-8,   0])
  const x4 = useTransform(scrollY, [0, 900], [15,   300])
  const x5 = useTransform(scrollY, [0, 900], [-20,  600])

  const r1 = useTransform(scrollY, [0, 600], [-8,  0])
  const r2 = useTransform(scrollY, [0, 600], [6,   0])
  const r3 = useTransform(scrollY, [0, 600], [-4,  0])
  const r4 = useTransform(scrollY, [0, 600], [9,   0])
  const r5 = useTransform(scrollY, [0, 600], [-12, 0])

  const yPos = useTransform(scrollY, [0, 900], [0, -50])

  const wsUrl = useMemo(() => {
    if (!state.requestId) return null
    return `${WS_BASE_URL}/stream/${state.requestId}`
  }, [state.requestId])

  useAgentStream(wsUrl, state.requestId)
  useDemoStream()

  const agentStateLabel = state.activeAgent ? 'Active' : 'Idle'
  const isConnected = state.connectionStatus === 'connected'
  const isRunning   = state.workflowStatus === 'running'
  const isThinking  = isRunning && state.agentEvents.length === 0

  const handleThemeToggle = useCallback(() => {
    const el = titleRef.current
    if (el) {
      el.classList.add('flipping')
      setTimeout(() => el.classList.remove('flipping'), 500)
    }
    toggleTheme()
  }, [toggleTheme])

  async function onStart() {
    const trimmed = prompt.trim()
    if (!trimmed || isStarting) return

    setIsStarting(true)
    dispatch({ type: 'RESET_RUN', payload: { prompt: trimmed } })

    try {
      const res = await runArena({ prompt: trimmed, max_iterations: 5, temperature: 0.7 })
      dispatch({ type: 'RUN_STARTED', payload: { requestId: res?.request_id || null } })
    } catch (err) {
      console.error("Critical: Arena run API failed, falling back to demo simulation.", err)
      dispatch({
        type: 'RUN_ERROR',
        payload: { message: err?.message || 'Ngrok tunnel/Backend failed to start run' },
      })
    } finally {
      setIsStarting(false)
    }
  }

  return (
    <div className="app">
      {/* ════════ NAVBAR — overlaid on hero, fades in after 2s ════════ */}
      <motion.header
        className="topbar"
        role="banner"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 2, duration: 0.8, ease: 'easeOut' }}
      >
        <div className="topbar-inner">
          <div className="brand" aria-label="Idea Arena" onClick={handleThemeToggle}>
            <div className="brand-title" ref={titleRef}>Idea Arena</div>
            <span className="theme-hint" aria-label="Toggle theme">
              {theme === 'dark' ? '☀' : '☽'}
            </span>
            <div className="brand-sub">Multi-agent debate · live</div>
          </div>
        </div>
      </motion.header>

      {/* ── Hero Section ── */}
      <section className="hero">
        <div className="hero-overlay" />

        {/* Floating card stack — scroll-driven unstack into a row */}
        <div className="hero-card-stack">
          <motion.div className="hero-card" style={{ x: x1, rotate: r1, y: yPos }}><img src="/red-agent.png" alt="Agent Logic 1" /></motion.div>
          <motion.div className="hero-card" style={{ x: x2, rotate: r2, y: yPos }}><img src="/blue-agent.png" alt="Agent Logic 2" /></motion.div>
          <motion.div className="hero-card" style={{ x: x3, rotate: r3, y: yPos }}><img src="/violet-agent.png" alt="Agent Logic 3" /></motion.div>
          <motion.div className="hero-card" style={{ x: x4, rotate: r4, y: yPos }}><img src="/gold-agent.png" alt="Agent Logic 4" /></motion.div>
          <motion.div className="hero-card" style={{ x: x5, rotate: r5, y: yPos }}><img src="/green-agent.png" alt="Agent Logic 5" /></motion.div>
        </div>

        <div className="hero-content">
          <h1>Idea Arena</h1>
          <p>The arena of minds where ideas go to battle.</p>
        </div>

        <div className="scroll-indicator">
          <span className="mouse" />
          <span className="arrow" />
        </div>
      </section>

      {/* ── Main content fades in on scroll ── */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-120px" }}
        transition={{ duration: 0.85, ease: 'easeOut' }}
      >
        <main className="layout" role="main">

          {/* ── Command Center: prompt + actions ── */}
          <section className="command-center" aria-label="Arena controls">
            <div className="command-prompt">
              <input
                id="arena-prompt"
                className="input"
                value={prompt}
                placeholder="Enter a prompt to spark the arena…"
                aria-label="Arena prompt"
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') onStart() }}
              />
              <div className="command-actions">
                <button
                  id="arena-start-btn"
                  className="btn btn-primary"
                  onClick={onStart}
                  disabled={isStarting}
                  aria-label={isStarting ? 'Starting arena run' : 'Start arena run'}
                >
                  {isStarting ? '⏳ Starting…' : '▶ Start'}
                </button>

                {!state.activeAgent && !state.requestId && !state.isDemoMode && (
                  <button
                    className="btn btn-simulation"
                    onClick={() => dispatch({ type: 'SET_DEMO_MODE', payload: { enabled: true } })}
                  >
                    ✦ Start Simulation
                  </button>
                )}
              </div>
            </div>

            {/* Error ribbon — from upstream */}
            {state.lastError && (
              <div className="status-ribbon">
                <div
                  className="pill"
                  style={{
                    borderColor: 'color-mix(in srgb, var(--accent-coral) 50%, transparent)',
                    color: 'var(--accent-coral)',
                  }}
                  title="Last error"
                >
                  <span className="mono">error</span>&thinsp;—&thinsp;{state.lastError}
                </div>
                <div className="pill" title="API base URL">
                  api&thinsp;<span className="mono">{API_BASE_URL}</span>
                </div>
              </div>
            )}

            {/* Status ribbon */}
            <div className="status-ribbon">
              <div className="pill" title="Current iteration">
                iter <span className="mono">{state.iteration}</span>
              </div>
              <div className="pill" title="Event count">
                ⚡ <span className="mono">{state.agentEvents.length}</span>
              </div>
              {(isStarting || isThinking) && (
                <div
                  className="pill"
                  title={isStarting ? 'Starting run' : 'Agent is thinking'}
                  style={{
                    borderColor: 'color-mix(in srgb, var(--accent-emerald) 35%, transparent)',
                    color: 'var(--accent-emerald)',
                  }}
                >
                  <span className="mono">{isStarting ? 'starting…' : 'agent thinking…'}</span>
                </div>
              )}
              <div
                className="pill"
                title="WebSocket / workflow status"
                style={{
                  borderColor: isConnected
                    ? 'color-mix(in srgb, var(--accent-emerald) 35%, transparent)'
                    : 'color-mix(in srgb, var(--accent-coral) 28%, transparent)',
                  color: isConnected
                    ? 'var(--accent-emerald)'
                    : 'var(--accent-coral)',
                }}
              >
                <span
                  className={`dot ${isConnected ? 'green' : 'red'}${isRunning ? ' pulse' : ''}`}
                  style={{ display: 'inline-block', marginRight: 6 }}
                />
                <span className="mono">{state.workflowStatus}</span>
              </div>
              <div className="pill" title="Agent state">
                <span
                  className={`dot ${state.activeAgent ? 'purple' : ''}`}
                  style={{ display: 'inline-block', marginRight: 6 }}
                />
                <span className="mono">{agentStateLabel}{state.isDemoMode ? ' · demo' : ''}</span>
              </div>
              {state.isDemoMode && (
                <div className="pill pill-demo" title="Demo simulation active">
                  ✦ demo
                  {typeof state.demoPlannedIterations === 'number'
                    ? ` · ${state.demoPlannedIterations} iter`
                    : ''}
                </div>
              )}
            </div>
          </section>

          {/* ── Arena Stage: Agents (left) + IdeaGraph (right) ── */}
          <div className="arena-stage">
            <div className="arena-agents">
              <AgentTimeline />
            </div>

            <section className="arena-graph" aria-label="Idea graph">
              <div className="arena-graph-header">
                <div className="panel-title">◈ Idea Graph</div>
                <div className="arena-graph-controls">
                  <div className="tag">
                    <span className={`dot blue${state.activeAgent ? ' pulse' : ''}`} />
                    <span className="mono">Iteration {(state.iteration ?? 0) + 1}</span>
                  </div>
                  <div className="tag">
                    <span className={`dot ${state.activeAgent ? 'green pulse' : 'red'}`} />
                    <span className="mono">{state.activeAgent || 'no active agent'}</span>
                  </div>
                </div>
              </div>
              <div className="arena-graph-body">
                <IdeaGraph />
              </div>
            </section>
          </div>

          {/* ── Agent Outputs — from upstream ── */}
          <section className="panel" aria-label="Agent outputs">
            <div className="panel-header">
              <div className="panel-title">◆ Agent Outputs</div>
              <div className="pill">
                live&thinsp;<span className="mono">{state.agentEvents.length}</span>
              </div>
            </div>
            <div className="panel-body">
              <AgentOutputs />
            </div>
          </section>

          {/* ── Metrics ── */}
          <section className="panel metrics-panel" aria-label="Metrics and tokens">
            <div className="panel-header">
              <div className="panel-title">◉ Metrics &amp; Tokens</div>
              <div className="pill">
                ∑&thinsp;<span className="mono">{state.tokens?.total ?? 0}</span>&thinsp;tokens
              </div>
            </div>
            <div className="panel-body grid-two">
              <MetricsPanel />
              <TokenPanel />
            </div>
          </section>

        </main>
      </motion.div>
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AppProvider>
        <Shell />
      </AppProvider>
    </ThemeProvider>
  )
}
