import { createContext, useContext, useMemo, useReducer } from 'react'
import { actionToEdgeType, nowMs, shortId, toText } from '../utils/helpers.js'

const AppContext = createContext(null)

const initialState = {
  requestId: null,
  workflowStatus: 'idle',
  isDemoMode: false,
  demoCompleted: false,
  demoPlannedIterations: null,
  ideas: [],
  critiques: [],
  radicalIdeas: [],
  refinedOutput: '',
  metrics: {},
  metricsHistory: [],
  agentEvents: [],
  activeAgent: null,
  iteration: 0,
  tokens: {},

  graph: {
    nodes: [],
    edges: [],
  },
  agentStatus: {},
  connectionStatus: 'closed',
  lastError: null,
}

function normalizeMetricsPayload(payload) {
  const ideaMetric = payload?.idea_metrics?.[payload.idea_metrics.length - 1] || {}

  const rawSystem = payload?.system_metrics || {}
  const system = Array.isArray(rawSystem)
    ? rawSystem[rawSystem.length - 1] || {}
    : rawSystem

  const rawAgent = payload?.agent_metrics || {}
  const agentMetrics = Array.isArray(rawAgent)
    ? rawAgent.reduce((acc, m) => {
        if (!m || !m.agent) return acc
        acc[m.agent] = acc[m.agent] || []
        acc[m.agent].push(m)
        return acc
      }, {})
    : rawAgent

  const flat = {
    ideaFitness: ideaMetric.fitness_score,
    novelty: ideaMetric.novelty,
    feasibility: ideaMetric.feasibility,
    clarity: ideaMetric.clarity,
    impact: ideaMetric.impact,
    conflictIntensity: system.conflict_intensity,
    iterationGain: system.convergence_speed,
    totalTokenUsage: system.total_token_usage,
    tokenEfficiency: system.token_efficiency,
    iterationCount: system.iteration_count,
  }

  const tokensByAgent = {}
  let totalFromAgents = 0
  for (const [agent, arr] of Object.entries(agentMetrics)) {
    const last = Array.isArray(arr) ? arr[arr.length - 1] : null
    if (last && typeof last.token_count === 'number') {
      tokensByAgent[agent] = last.token_count
      totalFromAgents += last.token_count
    }
  }

  if (typeof flat.totalTokenUsage !== 'number' && totalFromAgents > 0) {
    flat.totalTokenUsage = totalFromAgents
  }

  return { flat, tokensByAgent, raw: payload }
}

function normalizeIdea(data) {
  if (!data) return null
  if (typeof data === 'string') {
    return { id: shortId('idea'), text: data }
  }
  if (typeof data === 'object') {
    const id = data.id || data.ideaId || data.nodeId || shortId('idea')
    const text = data.text || data.idea || data.content || data.output || toText(data)
    return { ...data, id, text }
  }
  return { id: shortId('idea'), text: String(data) }
}

function pickIdeaIdsFromData(data) {
  if (!data || typeof data !== 'object') return { from: null, to: null }
  const from =
    data.fromId || data.sourceId || data.parentId || data.ideaFromId || data.from || null
  const to = data.toId || data.targetId || data.ideaId || data.nodeId || data.to || null
  return { from, to }
}

function latestIdeaNodeId(nodes) {
  for (let i = nodes.length - 1; i >= 0; i -= 1) {
    if (nodes[i]?.kind === 'idea') return nodes[i].id
  }
  return null
}

function latestGraphNodeId(nodes) {
  for (let i = nodes.length - 1; i >= 0; i -= 1) {
    if (nodes[i]?.graphRole === 'agent-step') return nodes[i].id
  }
  return null
}

function actionStepNumber(actionName) {
  const order = {
    generate: 1,
    attack: 2,
    disrupt: 3,
    merge: 4,
    judge: 5,
  }
  return order[actionName] || 0
}

function buildGraphNodeLabel(actionName, iteration) {
  const stepNumber = actionStepNumber(actionName)
  return `Node${stepNumber}`
}

function reducer(state, action) {
  switch (action.type) {
    case 'RESET_RUN': {
      return {
        ...initialState,
        connectionStatus: state.connectionStatus,
        lastError: null,
      }
    }
    case 'RUN_STARTED': {
      const requestId = action.payload?.requestId || null
      return {
        ...state,
        requestId,
        workflowStatus: 'running',
        isDemoMode: false,
        demoCompleted: false,
        demoPlannedIterations: null,
        lastError: null,
      }
    }
    case 'RUN_ERROR': {
      return {
        ...state,
        lastError: action.payload?.message || 'Run error',
        isDemoMode: true, // Fallback: enable demo indicators if run fails
      }
    }
    case 'WS_STATUS': {
      const status = action.payload?.status || 'closed'
      return { ...state, connectionStatus: status }
    }
    case 'METRICS_UPDATE': {
      const normalized = normalizeMetricsPayload(action.payload || {})
      const metrics = normalized.flat
      const point = { t: nowMs(), iteration: state.iteration, ...metrics }
      const nextHistory = [...state.metricsHistory, point].slice(-240)
      const total =
        typeof metrics.totalTokenUsage === 'number' ? metrics.totalTokenUsage : state.tokens.total
      return {
        ...state,
        metrics,
        metricsHistory: nextHistory,
        tokens: {
          ...state.tokens,
          ...normalized.tokensByAgent,
          ...(typeof total === 'number' ? { total } : null),
        },
      }
    }
    case 'STATUS_UPDATE': {
      const payload = action.payload || {}
      const status = payload.status || state.workflowStatus
      const iter =
        typeof payload.iteration === 'number' ? payload.iteration : state.iteration
      return {
        ...state,
        workflowStatus: status,
        iteration: iter,
      }
    }
    case 'SET_DEMO_MODE': {
      return { ...state, isDemoMode: Boolean(action.payload?.enabled) }
    }
    case 'SET_DEMO_PLAN': {
      return {
        ...state,
        demoPlannedIterations:
          typeof action.payload?.iterations === 'number' ? action.payload.iterations : null,
      }
    }
    case 'DEMO_COMPLETE': {
      return {
        ...state,
        isDemoMode: false,
        demoCompleted: true,
        demoPlannedIterations: null,
        activeAgent: null,
        workflowStatus: 'idle',
      }
    }
    case 'STREAM_EVENT': {
      const evt = action.payload
      if (!evt || typeof evt !== 'object') return state

      const eventType = evt.type || 'agent_action'
      const agent = evt.agent || null
      const actionName = evt.action || null
      const iteration =
        typeof evt.iteration === 'number' ? evt.iteration : state.iteration || 0
      const data = evt.data

      const agentEvents = [...state.agentEvents, { ...evt, ts: nowMs() }].slice(-1200)

      const agentStatus = {
        ...state.agentStatus,
        ...(agent ? { [agent]: actionName || 'idle' } : null),
      }

      let ideas = state.ideas
      let critiques = state.critiques
      let radicalIdeas = state.radicalIdeas
      let refinedOutput = state.refinedOutput
      let tokens = state.tokens

      let nodes = state.graph.nodes
      let edges = state.graph.edges

      if (eventType === 'iteration_complete') {
        nodes = nodes.map((node) => {
          if (node?.graphRole !== 'agent-step' || node.iteration !== iteration) return node
          return {
            ...node,
            label: buildGraphNodeLabel(node.action, iteration),
          }
        })
      }

      const maybeIdea =
        data?.idea ?? data?.node ?? data?.proposal ?? data?.output ?? data?.text ?? null

      if (eventType === 'agent_action' && actionName === 'generate') {
        const idea = normalizeIdea(maybeIdea ?? data)
        if (idea) {
          ideas = [...ideas, idea]
          nodes = [
            ...nodes,
            {
              id: idea.id,
              label: '',
              summary: idea.text,
              fullSummary: idea.text,
              kind: 'idea',
              agent: agent || 'creator',
              action: actionName,
              graphRole: 'agent-step',
              iteration,
            },
          ]
          if (nodes.length > 250) nodes = nodes.slice(-250)
        }
      }

      if (eventType === 'agent_action' && (actionName === 'attack' || actionName === 'disrupt')) {
        const critiqueText =
          data?.issue || data?.critique || data?.message || data?.text || toText(data)
        critiques = [
          ...critiques,
          {
            id: shortId('crit'),
            agent,
            iteration,
            action: actionName,
            text: critiqueText,
            raw: data,
            ts: nowMs(),
          },
        ].slice(-400)
      }

      if (eventType === 'agent_action' && actionName === 'merge') {
        const refinementText =
          data?.refinement || data?.merge || data?.message || data?.text || toText(data)
        refinedOutput = refinementText || refinedOutput
      }

      if (eventType === 'feedback') {
        const feedbackText = data?.message || data?.feedback || evt.message || toText(data)
        critiques = [
          ...critiques,
          {
            id: shortId('fb'),
            agent: agent || 'judge',
            iteration,
            action: 'feedback',
            text: feedbackText,
            raw: data,
            ts: nowMs(),
          },
        ].slice(-400)
      }

      if (eventType === 'agent_action' && actionName === 'judge') {
        if (typeof data?.accepted !== 'undefined') {
          // keep raw metrics or acceptance signals in state.metrics, but don't invent structure
        }
        const judgedText = data?.verdict || data?.decision || data?.text || null
        if (judgedText) refinedOutput = judgedText
      }

      if (eventType === 'agent_action' && actionName === 'disrupt' && (data?.radical || data?.radicalIdea)) {
        const rad = data.radicalIdea ?? data.radical
        radicalIdeas = [
          ...radicalIdeas,
          { id: shortId('rad'), agent, iteration, text: toText(rad), raw: rad, ts: nowMs() },
        ].slice(-250)
      } else if (data?.radicalIdea) {
        radicalIdeas = [
          ...radicalIdeas,
          {
            id: shortId('rad'),
            agent,
            iteration,
            text: toText(data.radicalIdea),
            raw: data.radicalIdea,
            ts: nowMs(),
          },
        ].slice(-250)
      }

      if (data?.tokens || data?.tokenUsage) {
        const t = data.tokens || data.tokenUsage
        if (typeof t === 'object' && t) {
          tokens = { ...tokens, ...t }
        }
      }

      const edgeType = actionToEdgeType(actionName)
      let edgeAdded = false

      // Add compact per-step nodes so each iteration stays readable.
      if (eventType === 'agent_action' && actionName && actionName !== 'generate') {
        const summaryByAction = {
          attack: data?.issue || data?.critique || 'Critique',
          disrupt: data?.radicalIdea || data?.radical || 'Radical',
          merge: data?.refinement || data?.merge || 'Synthesis',
          judge: data?.verdict || data?.decision || 'Judgement',
        }
        const nodeId = shortId(actionName)
        const summary = toText(summaryByAction[actionName] || actionName)
        nodes = [
          ...nodes,
          {
            id: nodeId,
            label: '',
            summary: summary.slice(0, 120),
            fullSummary: summary,
            kind: actionName,
            agent: agent || actionName,
            action: actionName,
            graphRole: 'agent-step',
            iteration,
          },
        ].slice(-250)

        const parent = latestGraphNodeId(nodes.slice(0, -1)) || latestIdeaNodeId(nodes.slice(0, -1)) || null
        if (parent) {
          edges = [
            ...edges,
            {
              id: shortId('e'),
              source: parent,
              target: nodeId,
              type: edgeType,
              iteration,
            },
          ].slice(-400)
          edgeAdded = true
        }
      }

      // Build/extend edges when the backend provides IDs; otherwise, connect the last two graph steps.
      const { from, to } = pickIdeaIdsFromData(data)
      if (eventType === 'agent_action' && from && to && !edgeAdded) {
        edges = [
          ...edges,
          { id: shortId('e'), source: String(from), target: String(to), type: edgeType, iteration },
        ].slice(-400)
      } else if (
        eventType === 'agent_action' &&
        nodes.length >= 2 &&
        actionName &&
        actionName !== 'generate' &&
        !edgeAdded
      ) {
        const a = nodes[nodes.length - 2]?.id
        const b = nodes[nodes.length - 1]?.id
        if (a && b) {
          edges = [
            ...edges,
            { id: shortId('e'), source: a, target: b, type: edgeType, iteration },
          ].slice(-400)
        }
      }

      return {
        ...state,
        ideas,
        critiques,
        radicalIdeas,
        refinedOutput,
        tokens,
        graph: { nodes, edges },
        agentEvents,
        agentStatus,
        workflowStatus:
          eventType === 'workflow_complete'
            ? 'completed'
            : eventType === 'iteration_complete'
              ? 'running'
              : state.workflowStatus,
        activeAgent: eventType === 'workflow_complete' ? null : agent,
        iteration,
      }
    }
    default:
      return state
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const value = useMemo(() => ({ state, dispatch }), [state])
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
