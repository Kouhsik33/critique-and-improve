import { useEffect, useMemo, useRef, useState } from 'react'
import * as d3 from 'd3'
import { useApp } from '../context/AppContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'

const DARK_NODE_COLORS = {
  creator:     { fill: 'rgba(0, 212, 255, 0.12)',  stroke: '#00d4ff', glow: 'rgba(0, 212, 255, 0.45)' },
  critic:      { fill: 'rgba(255, 107, 107, 0.12)', stroke: '#ff6b6b', glow: 'rgba(255, 107, 107, 0.45)' },
  radical:     { fill: 'rgba(255, 179, 71, 0.12)',  stroke: '#ffb347', glow: 'rgba(255, 179, 71, 0.45)' },
  synthesizer: { fill: 'rgba(0, 229, 160, 0.12)',  stroke: '#00e5a0', glow: 'rgba(0, 229, 160, 0.45)' },
  judge:       { fill: 'rgba(167, 139, 255, 0.12)', stroke: '#a78bff', glow: 'rgba(167, 139, 255, 0.45)' },
}

const LIGHT_NODE_COLORS = {
  creator:     { fill: 'rgba(8, 145, 178, 0.10)',  stroke: '#0891b2', glow: 'rgba(8, 145, 178, 0.25)' },
  critic:      { fill: 'rgba(220, 38, 38, 0.10)',  stroke: '#dc2626', glow: 'rgba(220, 38, 38, 0.25)' },
  radical:     { fill: 'rgba(217, 119, 6, 0.10)',   stroke: '#d97706', glow: 'rgba(217, 119, 6, 0.25)' },
  synthesizer: { fill: 'rgba(5, 150, 105, 0.10)',  stroke: '#059669', glow: 'rgba(5, 150, 105, 0.25)' },
  judge:       { fill: 'rgba(124, 58, 237, 0.10)', stroke: '#7c3aed', glow: 'rgba(124, 58, 237, 0.25)' },
}

const DARK_EDGE = { critique: '#ff6b6b', refinement: '#6c63ff', accepted: '#00e5a0', default: '#6c63ff' }
const LIGHT_EDGE = { critique: '#dc2626', refinement: '#5046e5', accepted: '#059669', default: '#5046e5' }

const NODE_WIDTH = 120
const NODE_HEIGHT = 58
const ITERATION_PAD_X = 24
const ITERATION_PAD_Y = 22

function summarizeNodeText(text = '', maxLength = 42) {
  const compact = cleanNodeText(text)
  if (!compact) return ''
  if (compact.length <= maxLength) return compact
  return `${compact.slice(0, maxLength - 1).trimEnd()}...`
}

function cleanNodeText(text = '') {
  return String(text)
    .replace(/\s+/g, ' ')
    .replace(/^demo\s+(concept|critique|disruption|synthesis|judge)\s+\d+\s*:\s*/i, '')
    .trim()
}

function wrapNodeText(text = '', lineLength = 18, maxLines = 3) {
  const compact = summarizeNodeText(text, lineLength * maxLines)
  if (!compact) return []

  const words = compact.split(' ')
  const lines = []
  let current = ''

  for (const word of words) {
    const next = current ? `${current} ${word}` : word
    if (next.length <= lineLength) {
      current = next
      continue
    }

    if (current) lines.push(current)
    current = word
    if (lines.length === maxLines - 1) break
  }

  if (lines.length < maxLines && current) lines.push(current)
  const finalLines = lines.slice(0, maxLines)

  if (compact.endsWith('...') && finalLines.length > 0 && !finalLines[finalLines.length - 1].endsWith('...')) {
    finalLines[finalLines.length - 1] = `${finalLines[finalLines.length - 1].replace(/\.*$/, '')}...`
  }

  return finalLines
}

function paletteForNode(node, activeAgent, NODE_COLORS) {
  const palette = NODE_COLORS[node?.agent] || {
    fill: 'rgba(255,255,255,0.10)',
    stroke: 'rgba(255,255,255,0.35)',
    glow: 'rgba(255,255,255,0.16)',
  }
  const isActive = Boolean(activeAgent) && node?.agent === activeAgent
  return {
    ...palette,
    strokeWidth: isActive ? 2 : 1.2,
    glowSize: isActive ? 10 : 0,
  }
}

function rectAnchorPoint(fromNode, toNode) {
  const x1 = fromNode?.x ?? 0
  const y1 = fromNode?.y ?? 0
  const x2 = toNode?.x ?? x1
  const y2 = toNode?.y ?? y1
  const dx = x2 - x1
  const dy = y2 - y1

  if (!dx && !dy) {
    return { x: x1, y: y1 }
  }

  const halfW = NODE_WIDTH / 2
  const halfH = NODE_HEIGHT / 2
  const scaleX = dx === 0 ? Number.POSITIVE_INFINITY : halfW / Math.abs(dx)
  const scaleY = dy === 0 ? Number.POSITIVE_INFINITY : halfH / Math.abs(dy)
  const scale = Math.min(scaleX, scaleY)

  return {
    x: x1 + dx * scale,
    y: y1 + dy * scale,
  }
}

function computeIterationBox(items, fallbackX, fallbackY) {
  const validItems = items.filter((item) => Number.isFinite(item.x) && Number.isFinite(item.y))
  if (!validItems.length) {
    return {
      minX: fallbackX - 60,
      maxX: fallbackX + 60,
      minY: fallbackY - 45,
      maxY: fallbackY + 45,
    }
  }

  return {
    minX: d3.min(validItems, (item) => item.x) - NODE_WIDTH / 2 - ITERATION_PAD_X,
    maxX: d3.max(validItems, (item) => item.x) + NODE_WIDTH / 2 + ITERATION_PAD_X,
    minY: d3.min(validItems, (item) => item.y) - NODE_HEIGHT / 2 - ITERATION_PAD_Y,
    maxY: d3.max(validItems, (item) => item.y) + NODE_HEIGHT / 2 + ITERATION_PAD_Y,
  }
}

function nearestIterationAnchors(source, target) {
  const sourceCenterX = (source.minX + source.maxX) / 2
  const sourceCenterY = (source.minY + source.maxY) / 2
  const targetCenterX = (target.minX + target.maxX) / 2
  const targetCenterY = (target.minY + target.maxY) / 2
  const dx = targetCenterX - sourceCenterX
  const dy = targetCenterY - sourceCenterY

  if (Math.abs(dx) >= Math.abs(dy)) {
    if (dx >= 0) {
      return {
        x1: source.maxX,
        y1: sourceCenterY,
        x2: target.minX,
        y2: targetCenterY,
      }
    }
    return {
      x1: source.minX,
      y1: sourceCenterY,
      x2: target.maxX,
      y2: targetCenterY,
    }
  }

  if (dy >= 0) {
    return {
      x1: sourceCenterX,
      y1: source.maxY,
      x2: targetCenterX,
      y2: target.minY,
    }
  }

  return {
    x1: sourceCenterX,
    y1: source.minY,
    x2: targetCenterX,
    y2: target.maxY,
  }
}

export default function IdeaGraph() {
  const { state } = useApp()
  const { theme } = useTheme()
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const simRef = useRef(null)
  const zoomRef = useRef(null)
  const [hoveredNode, setHoveredNode] = useState(null)

  const NODE_COLORS = theme === 'dark' ? DARK_NODE_COLORS : LIGHT_NODE_COLORS
  const EDGE_COLORS = theme === 'dark' ? DARK_EDGE : LIGHT_EDGE

  const nodes = state.graph.nodes
  const links = useMemo(
    () =>
      state.graph.edges.map((e) => ({
        ...e,
        source: e.source,
        target: e.target,
      })),
    [state.graph.edges],
  )

  useEffect(() => {
    const svgEl = svgRef.current
    if (!svgEl) return

    const svg = d3.select(svgEl)
    const width = svgEl.clientWidth || 900
    const height = svgEl.clientHeight || 600
    const nodePadding = 46

    svg.attr('viewBox', `0 0 ${width} ${height}`)

    // layers
    let root = svg.select('g.root')
    if (root.empty()) {
      root = svg.append('g').attr('class', 'root')
      root.append('g').attr('class', 'iteration-links')
      root.append('g').attr('class', 'iterations')
      root.append('g').attr('class', 'links')
      root.append('g').attr('class', 'nodes')
    }

    // Enable pan/zoom for dense graphs.
    if (!zoomRef.current) {
      const zoom = d3
        .zoom()
        .scaleExtent([0.6, 2.4])
        .on('zoom', (event) => {
          root.attr('transform', event.transform)
        })
      svg.call(zoom)
      zoomRef.current = zoom
    }

    const linkSel = root
      .select('g.links')
      .selectAll('line.link')
      .data(links, (d) => d.id)

    linkSel
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', (d) => EDGE_COLORS[d.type] || EDGE_COLORS.default)
      .attr('stroke-width', 2)
      .attr('stroke-opacity', 0.8)
      .attr('x1', width / 2)
      .attr('y1', height / 2)
      .attr('x2', width / 2)
      .attr('y2', height / 2)
      .transition()
      .duration(260)
      .attr('stroke-opacity', 0.95)

    linkSel.exit().remove()

    const iterationEntries = Array.from(
      d3.group(
        nodes.filter((node) => node?.graphRole === 'agent-step'),
        (node) => node.iteration,
      ),
      ([iteration, items]) => ({
        id: `iter-${iteration}`,
        iteration,
        items,
      }),
    )

    const iterationBounds = iterationEntries.map((entry) => ({
      ...entry,
      ...computeIterationBox(entry.items, width / 2, height / 2),
    }))

    const iterationLinkData = iterationBounds
      .slice()
      .sort((a, b) => Number(a.iteration) - Number(b.iteration))
      .slice(1)
      .map((entry, index, arr) => {
        const previous = iterationBounds
          .slice()
          .sort((a, b) => Number(a.iteration) - Number(b.iteration))[index]
        return {
          id: `iter-link-${previous.iteration}-${entry.iteration}`,
          source: previous,
          target: entry,
        }
      })

    const iterationLinkSel = root
      .select('g.iteration-links')
      .selectAll('line.iteration-link')
      .data(iterationLinkData, (d) => d.id)

    iterationLinkSel
      .enter()
      .append('line')
      .attr('class', 'iteration-link')
      .attr('stroke', 'rgba(255,255,255,0.12)')
      .attr('stroke-width', 1)
      .attr('stroke-dasharray', '5 5')
      .attr('stroke-linecap', 'butt')
      .attr('x1', width / 2)
      .attr('y1', height / 2)
      .attr('x2', width / 2)
      .attr('y2', height / 2)
      .transition()
      .duration(260)
      .attr('stroke-opacity', 0.9)

    iterationLinkSel.exit().remove()

    const iterationSel = root
      .select('g.iterations')
      .selectAll('g.iteration-group')
      .data(iterationBounds, (d) => d.id)

    const iterationEnter = iterationSel
      .enter()
      .append('g')
      .attr('class', 'iteration-group')
      .attr('pointer-events', 'none')

    iterationEnter
      .append('rect')
      .attr('rx', 22) /* Reduced from 32 */
      .attr('ry', 22)
      .attr('fill', 'rgba(10, 15, 30, 0.22)')
      .attr('stroke', 'rgba(255,255,255,0.06)')
      .attr('stroke-width', 1)

    iterationEnter
      .append('text')
      .attr('fill', 'rgba(255, 255, 255, 0.4)')
      .attr('font-size', 9) /* Reduced from 10 */
      .attr('font-weight', 600)
      .attr('font-family', 'var(--mono)')
      .text((d) => `ITERation ${Number(d.iteration) + 1}`)

    iterationSel.exit().remove()

    const nodeSel = root
      .select('g.nodes')
      .selectAll('g.node')
      .data(nodes, (d) => d.id)

    const nodeEnter = nodeSel.enter().append('g').attr('class', 'node')

    function showNodeOverlay(event, datum) {
      const containerRect = containerRef.current?.getBoundingClientRect()
      if (!containerRect) return

      const maxLeft = Math.max(16, containerRect.width - 336)
      const maxTop = Math.max(16, containerRect.height - 236)
      const left = Math.min(Math.max(16, event.clientX - containerRect.left + 18), maxLeft)
      const top = Math.min(Math.max(16, event.clientY - containerRect.top + 18), maxTop)

      setHoveredNode({
        id: datum.id,
        agent: datum.agent,
        summary: cleanNodeText(datum.fullSummary || datum.summary || ''),
        left,
        top,
      })
    }

    function clearNodeOverlay() {
      setHoveredNode((current) => (current ? null : current))
    }

    nodeEnter
      .on('mouseenter', showNodeOverlay)
      .on('mousemove', showNodeOverlay)
      .on('mouseleave', clearNodeOverlay)

    nodeEnter
      .append('rect')
      .attr('x', -NODE_WIDTH / 2)
      .attr('y', -NODE_HEIGHT / 2)
      .attr('rx', 12)
      .attr('ry', 12)
      .attr('width', NODE_WIDTH)
      .attr('height', NODE_HEIGHT)
      .attr('fill', (d) => paletteForNode(d, state.activeAgent, NODE_COLORS).fill)
      .attr('stroke', (d) => paletteForNode(d, state.activeAgent, NODE_COLORS).stroke)
      .attr('stroke-width', (d) => paletteForNode(d, state.activeAgent, NODE_COLORS).strokeWidth)
      .attr('filter', (d) =>
        paletteForNode(d, state.activeAgent, NODE_COLORS).glowSize ? `drop-shadow(0 0 ${paletteForNode(d, state.activeAgent, NODE_COLORS).glowSize}px ${paletteForNode(d, state.activeAgent, NODE_COLORS).glow})` : null,
      )
      .attr('opacity', 0)
      .transition()
      .duration(320)
      .attr('opacity', 1)

    nodeEnter
      .append('text')
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', 'var(--text)')
      .attr('font-size', 10) /* Reduced from 11 */
      .attr('font-weight', 500)
      .attr('font-family', 'var(--sans)')
      .style('pointer-events', 'none')
      .attr('opacity', 0)
      .each(function renderSummary(d) {
        const text = d3.select(this)
        const lines = wrapNodeText(d.summary)
        const startDy = -((Math.max(lines.length, 1) - 1) * 12) / 2 /* Reduced from 13 */
        lines.forEach((line, index) => {
          text
            .append('tspan')
            .attr('x', 0)
            .attr('dy', index === 0 ? startDy : 12) /* Reduced from 13 */
            .text(line)
        })
      })
      .transition()
      .duration(360)
      .attr('opacity', 1)

    nodeSel
      .on('mouseenter', showNodeOverlay)
      .on('mousemove', showNodeOverlay)
      .on('mouseleave', clearNodeOverlay)
      .select('rect')
      .attr('fill', (d) => paletteForNode(d, state.activeAgent, NODE_COLORS).fill)
      .attr('stroke', (d) => paletteForNode(d, state.activeAgent, NODE_COLORS).stroke)
      .attr('stroke-width', (d) => paletteForNode(d, state.activeAgent, NODE_COLORS).strokeWidth)
      .attr('filter', (d) =>
        paletteForNode(d, state.activeAgent, NODE_COLORS).glowSize ? `drop-shadow(0 0 ${paletteForNode(d, state.activeAgent, NODE_COLORS).glowSize}px ${paletteForNode(d, state.activeAgent, NODE_COLORS).glow})` : null,
      )

    nodeSel.select('text').each(function updateSummary(d) {
      const text = d3.select(this)
      text.selectAll('tspan').remove()
      const lines = wrapNodeText(d.summary)
      const startDy = -((Math.max(lines.length, 1) - 1) * 13) / 2
      lines.forEach((line, index) => {
        text
          .append('tspan')
          .attr('x', 0)
          .attr('dy', index === 0 ? startDy : 13)
          .text(line)
      })
    })

    nodeSel.exit().remove()

    // simulation
    if (!simRef.current) {
      simRef.current = d3
        .forceSimulation()
        .force(
          'link',
          d3.forceLink().id((d) => d.id).distance(108).strength(0.82),
        )
        .force('charge', d3.forceManyBody().strength(-380))
        .force('collide', d3.forceCollide().radius(60))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .alphaDecay(0.05)
    }

    const sim = simRef.current
    const orderedIterations = Array.from(
      new Set(nodes.map((node) => node.iteration).filter((value) => typeof value === 'number')),
    ).sort((a, b) => a - b)

    const iterationSpacing = Math.min(360, Math.max(260, width / Math.max(orderedIterations.length, 2)))
    const totalSpan = iterationSpacing * Math.max(orderedIterations.length - 1, 0)
    const startX = width / 2 - totalSpan / 2

    sim.nodes(nodes)
    sim.force('link').links(links)
    sim.force('center', d3.forceCenter(width / 2, height / 2))
    sim.force(
      'iteration-x',
      d3
        .forceX((node) => {
          const index = orderedIterations.indexOf(node.iteration)
          if (index === -1) return width / 2
          return startX + index * iterationSpacing
        })
        .strength(0.22),
    )
    sim.alpha(0.7).restart()

    const allNodes = root.select('g.nodes').selectAll('g.node')
    const allLinks = root.select('g.links').selectAll('line.link')
    const allIterations = root.select('g.iterations').selectAll('g.iteration-group')
    const allIterationLinks = root.select('g.iteration-links').selectAll('line.iteration-link')

    sim.on('tick', () => {
      nodes.forEach((d) => {
        d.x = Math.max(nodePadding, Math.min(width - nodePadding, d.x ?? width / 2))
        d.y = Math.max(nodePadding, Math.min(height - nodePadding, d.y ?? height / 2))
      })

      allLinks
        .attr('x1', (d) => rectAnchorPoint(d.source, d.target).x)
        .attr('y1', (d) => rectAnchorPoint(d.source, d.target).y)
        .attr('x2', (d) => rectAnchorPoint(d.target, d.source).x)
        .attr('y2', (d) => rectAnchorPoint(d.target, d.source).y)

      allNodes.attr(
        'transform',
        (d) => `translate(${d.x ?? width / 2},${d.y ?? height / 2})`,
      )

      allIterations.each(function positionIterationGroup(group) {
        const { minX, maxX, minY, maxY } = computeIterationBox(group.items, width / 2, height / 2)
        group.minX = minX
        group.maxX = maxX
        group.minY = minY
        group.maxY = maxY

        const g = d3.select(this)
        g.select('rect')
          .attr('x', minX)
          .attr('y', minY)
          .attr('width', Math.max(120, maxX - minX))
          .attr('height', Math.max(90, maxY - minY))

        g.select('text')
          .attr('x', minX + 18)
          .attr('y', minY - 10)
      })

      allIterationLinks
        .attr('x1', (d) => nearestIterationAnchors(d.source, d.target).x1)
        .attr('y1', (d) => nearestIterationAnchors(d.source, d.target).y1)
        .attr('x2', (d) => nearestIterationAnchors(d.source, d.target).x2)
        .attr('y2', (d) => nearestIterationAnchors(d.source, d.target).y2)
    })

    return () => {
      sim.on('tick', null)
    }
  }, [nodes, links, state.activeAgent, theme])

  return (
    <div ref={containerRef} className="graph-stage">
      <svg
        ref={svgRef}
        style={{ width: '100%', height: '100%', display: 'block' }}
        aria-label="Idea graph"
      />
      {hoveredNode ? (
        <div
          className="graph-node-modal"
          style={{ left: hoveredNode.left, top: hoveredNode.top }}
          role="dialog"
          aria-label="Node details"
        >
          <div className="graph-node-modal-header">
            <span className={`dot ${agentColorClass(hoveredNode.agent)}`} />
            <span className="mono">{hoveredNode.agent || 'agent'}</span>
          </div>
          <div className="graph-node-modal-body">{hoveredNode.summary || 'No output available.'}</div>
        </div>
      ) : null}
    </div>
  )
}

function agentColorClass(agent) {
  if (agent === 'creator') return 'blue'
  if (agent === 'critic') return 'red'
  if (agent === 'radical') return 'amber'
  if (agent === 'synthesizer') return 'green'
  if (agent === 'judge') return 'purple'
  return ''
}
