import { useEffect, useRef } from 'react'
import { useApp } from '../context/AppContext.jsx'

const DEMO_SEQUENCE = [
  { agent: 'creator', action: 'generate' },
  { agent: 'critic', action: 'attack' },
  { agent: 'radical', action: 'disrupt' },
  { agent: 'synthesizer', action: 'merge' },
  { agent: 'judge', action: 'judge' },
]

function demoData(stepIndex, action) {
  const n = stepIndex + 1
  if (action === 'generate') {
    return { 
      idea: { 
        id: `demo_idea_${n}`, 
        text: `Demo concept ${n}: An adaptive multi-agent strategy that dynamically reconfigures agent roles based on real-time performance metrics and debate outcomes, enabling emergent specialization and more efficient convergence.` 
      } 
    }
  }
  if (action === 'attack') {
    return { 
      critique: `Demo critique ${n}: The proposed approach has significant feasibility concerns regarding implementation complexity, scope management across distributed agents, and scalability limitations when handling multiple concurrent debate threads. Tightening required in all three areas.` 
    }
  }
  if (action === 'disrupt') {
    return { 
      radicalIdea: `Demo disruption ${n}: Invert core constraints by allowing agents to temporarily abandon their specialized roles, test opposite assumptions about debate structure, and explore counter-intuitive solution spaces that traditional approaches would filter out prematurely.` 
    }
  }
  if (action === 'merge') {
    return { 
      refinement: `Demo synthesis ${n}: Integrates critical feedback with radical reframing to produce a hybrid solution that maintains structural integrity while incorporating novel perspectives, resulting in improved adaptability without sacrificing coherence.` 
    }
  }
  return { 
    verdict: `Demo judge ${n}: Overall solution quality shows measurable improvement. Key metrics indicate 67% convergence toward optimal solution. Continue iterating with focus on edge cases and performance optimization.` 
  }
}

export function useDemoStream() {
  const { state, dispatch } = useApp()
  const timerRef = useRef(null)
  const startedRef = useRef(false)

  // Track fake metrics for the simulation
  const metricsStateRef = useRef({
    totalTokens: 0,
    agentTokens: { creator: 0, critic: 0, radical: 0, synthesizer: 0, judge: 0 },
    fitnessScore: 0.35,
  })

  useEffect(() => {
    // Demo should only run if explicitly requested (isDemoMode is true)
    // and no real workflow is active.
    if (state.requestId || state.demoCompleted || !state.isDemoMode) return undefined
    if (startedRef.current) return undefined

    startedRef.current = true

    const maxIterations = Math.random() < 0.5 ? 2 : 3
    dispatch({ type: 'SET_DEMO_PLAN', payload: { iterations: maxIterations } })

    const actionsPerIteration = DEMO_SEQUENCE.length
    const totalSteps = maxIterations * actionsPerIteration
    const stepDelayMs = 1800
    let idx = 0

    const tick = () => {
      const step = DEMO_SEQUENCE[idx % DEMO_SEQUENCE.length]
      const iteration = Math.floor(idx / actionsPerIteration)

      // Update fake metrics
      const currentMetrics = metricsStateRef.current
      const newTokens = Math.floor(Math.random() * 200) + 100
      
      currentMetrics.agentTokens[step.agent] = (currentMetrics.agentTokens[step.agent] || 0) + newTokens
      currentMetrics.totalTokens += newTokens
      
      // Gradually increase fitness score
      currentMetrics.fitnessScore = Math.min(0.96, currentMetrics.fitnessScore + (Math.random() * 0.05))

      dispatch({
        type: 'STREAM_EVENT',
        payload: {
          type: 'agent_action',
          agent: step.agent,
          action: step.action,
          data: demoData(idx, step.action),
          iteration,
          timestamp: new Date().toISOString(),
        },
      })

      // Fake metrics payload mimicking the backend
      dispatch({
        type: 'METRICS_UPDATE',
        payload: {
          idea_metrics: [
            {
              fitness_score: currentMetrics.fitnessScore,
              novelty: Math.min(1.0, currentMetrics.fitnessScore * 1.1),
              feasibility: Math.min(1.0, currentMetrics.fitnessScore * 0.95),
              clarity: Math.min(1.0, currentMetrics.fitnessScore * 1.05),
              impact: Math.min(1.0, currentMetrics.fitnessScore * 1.15),
            }
          ],
          system_metrics: {
            conflict_intensity: 0.2 + (Math.random() * 0.5),
            convergence_speed: 0.15 + (Math.random() * 0.1),
            total_token_usage: currentMetrics.totalTokens,
            token_efficiency: 185.5,
            iteration_count: iteration + 1
          },
          agent_metrics: {
            creator: [{ token_count: currentMetrics.agentTokens.creator }],
            critic: [{ token_count: currentMetrics.agentTokens.critic }],
            radical: [{ token_count: currentMetrics.agentTokens.radical }],
            synthesizer: [{ token_count: currentMetrics.agentTokens.synthesizer }],
            judge: [{ token_count: currentMetrics.agentTokens.judge }]
          }
        }
      })

      // Signal iteration boundaries to mimic backend semantics.
      if ((idx + 1) % actionsPerIteration === 0) {
        dispatch({
          type: 'STREAM_EVENT',
          payload: {
            type: 'iteration_complete',
            iteration,
            data: { completed: true },
            timestamp: new Date().toISOString(),
          },
        })
      }

      idx += 1

      if (idx >= totalSteps) {
        dispatch({
          type: 'STREAM_EVENT',
          payload: {
            type: 'workflow_complete',
            iteration: maxIterations - 1,
            data: { status: 'completed', mode: 'demo' },
            timestamp: new Date().toISOString(),
          },
        })
        dispatch({ type: 'DEMO_COMPLETE' })
        timerRef.current = null
        startedRef.current = false
        return
      }

      timerRef.current = window.setTimeout(tick, stepDelayMs)
    }

    timerRef.current = window.setTimeout(tick, stepDelayMs)

    return () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
      // Cleanup may happen if requestId changes to a real run.
      startedRef.current = false
      dispatch({ type: 'SET_DEMO_MODE', payload: { enabled: false } })
    }
  }, [state.requestId, state.demoCompleted, state.isDemoMode, dispatch])
}

