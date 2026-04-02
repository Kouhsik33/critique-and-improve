import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'

/* ── Modular CSS imports (order matters) ── */
import './styles/tokens.css'
import './styles/animations.css'
import './styles/base.css'
import './styles/shell.css'
import './styles/panel.css'
import './styles/components/timeline.css'
import './styles/components/arena-stage.css'
import './styles/components/graph.css'
import './styles/components/metrics.css'
import './styles/components/token-bars.css'
import './styles/components/status.css'
import './styles/components/feedback.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
