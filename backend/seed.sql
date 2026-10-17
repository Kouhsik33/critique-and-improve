-- ============================================================================
-- IDEA ARENA - Database Schema & Seed Data for PostgreSQL / Neon
-- ============================================================================

-- 1. Create Tables
CREATE TABLE IF NOT EXISTS workflow_logs (
    id VARCHAR PRIMARY KEY,
    request_id VARCHAR,
    iteration INTEGER,
    initial_prompt TEXT,
    final_output TEXT,
    status VARCHAR,
    total_iterations INTEGER,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    data JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_workflow_logs_request_id ON workflow_logs (request_id);
CREATE INDEX IF NOT EXISTS ix_workflow_logs_created_at ON workflow_logs (created_at);

CREATE TABLE IF NOT EXISTS agent_metrics (
    id VARCHAR PRIMARY KEY,
    workflow_id VARCHAR,
    agent VARCHAR,
    iteration INTEGER,
    action VARCHAR,
    token_count INTEGER DEFAULT 0,
    quality_score FLOAT DEFAULT 0.0,
    diversity_score FLOAT,
    confidence FLOAT DEFAULT 0.5,
    latency_ms FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    output TEXT,
    data JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_agent_metrics_workflow_id ON agent_metrics (workflow_id);
CREATE INDEX IF NOT EXISTS ix_agent_metrics_agent ON agent_metrics (agent);
CREATE INDEX IF NOT EXISTS ix_agent_metrics_created_at ON agent_metrics (created_at);

CREATE TABLE IF NOT EXISTS idea_metrics (
    id VARCHAR PRIMARY KEY,
    workflow_id VARCHAR,
    iteration INTEGER,
    idea TEXT,
    novelty FLOAT DEFAULT 0.0,
    feasibility FLOAT DEFAULT 0.0,
    clarity FLOAT DEFAULT 0.0,
    impact FLOAT DEFAULT 0.0,
    fitness_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_idea_metrics_workflow_id ON idea_metrics (workflow_id);
CREATE INDEX IF NOT EXISTS ix_idea_metrics_created_at ON idea_metrics (created_at);

CREATE TABLE IF NOT EXISTS system_metrics (
    id VARCHAR PRIMARY KEY,
    workflow_id VARCHAR,
    iteration_count INTEGER DEFAULT 0,
    convergence_speed FLOAT,
    total_token_usage INTEGER DEFAULT 0,
    conflict_intensity FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS ix_system_metrics_workflow_id ON system_metrics (workflow_id);
CREATE INDEX IF NOT EXISTS ix_system_metrics_created_at ON system_metrics (created_at);

-- ============================================================================
-- 2. Seed Initial Sample Data (Demonstration Workflow)
-- ============================================================================

INSERT INTO workflow_logs (
    id, request_id, iteration, initial_prompt, final_output, status, total_iterations, total_tokens, created_at, completed_at, data
) VALUES (
    'seed_demo_run',
    'seed_demo_run',
    3,
    'Design an autonomous decentralized mesh solar grid for rural communities.',
    'A modular peer-to-peer solar microgrid utilizing dynamic smart contracts and local battery clustering with automated load balancing.',
    'completed',
    3,
    2840,
    NOW() - INTERVAL '1 hour',
    NOW() - INTERVAL '55 minutes',
    '{"max_iterations": 3, "temperature": 0.7}'::jsonb
) ON CONFLICT (id) DO NOTHING;

INSERT INTO agent_metrics (
    id, workflow_id, agent, iteration, action, token_count, quality_score, diversity_score, confidence, latency_ms, created_at, output
) VALUES 
(
    'seed_metric_1',
    'seed_demo_run',
    'creator',
    1,
    'generate',
    420,
    0.85,
    0.78,
    0.88,
    1240.5,
    NOW() - INTERVAL '59 minutes',
    'Proposed decentralized rooftop solar microgrid sharing surplus energy via local tokens.'
),
(
    'seed_metric_2',
    'seed_demo_run',
    'critic',
    1,
    'attack',
    380,
    0.80,
    0.70,
    0.82,
    1100.2,
    NOW() - INTERVAL '58 minutes',
    'Identified single-point-of-failure in power storage and variable weather risk.'
),
(
    'seed_metric_3',
    'seed_demo_run',
    'radical',
    1,
    'disrupt',
    410,
    0.92,
    0.91,
    0.86,
    1350.0,
    NOW() - INTERVAL '57 minutes',
    'Suggested mobile battery swarms that dynamically re-route energy to high-demand nodes.'
),
(
    'seed_metric_4',
    'seed_demo_run',
    'synthesizer',
    1,
    'merge',
    520,
    0.89,
    0.84,
    0.90,
    1420.8,
    NOW() - INTERVAL '56 minutes',
    'Integrated fixed storage buffer with localized peer arbitration for stability.'
),
(
    'seed_metric_5',
    'seed_demo_run',
    'judge',
    1,
    'judge',
    310,
    0.93,
    0.88,
    0.95,
    980.4,
    NOW() - INTERVAL '55 minutes',
    'High viability and novelty achieved. Approved final specification.'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO idea_metrics (
    id, workflow_id, iteration, idea, novelty, feasibility, clarity, impact, fitness_score, created_at
) VALUES (
    'seed_idea_1',
    'seed_demo_run',
    1,
    'Modular peer-to-peer solar microgrid with automated load balancing and tokenized incentives.',
    0.88,
    0.82,
    0.90,
    0.87,
    0.8675,
    NOW() - INTERVAL '55 minutes'
) ON CONFLICT (id) DO NOTHING;

INSERT INTO system_metrics (
    id, workflow_id, iteration_count, convergence_speed, total_token_usage, conflict_intensity, created_at
) VALUES (
    'seed_sys_1',
    'seed_demo_run',
    3,
    0.85,
    2840,
    0.42,
    NOW() - INTERVAL '55 minutes'
) ON CONFLICT (id) DO NOTHING;
