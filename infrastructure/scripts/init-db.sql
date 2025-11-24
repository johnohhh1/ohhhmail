-- ChiliHead OpsManager v2.1 - Database Initialization

-- PostgreSQL: Check if database exists, create if not
SELECT 'CREATE DATABASE chilihead'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chilihead')\gexec

-- Connect to chilihead database
\c chilihead;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS aubs;
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS events;

-- Set search path
SET search_path TO aubs, agents, events, public;

-- ========== AUBS Tables ==========

CREATE TABLE IF NOT EXISTS aubs.executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id VARCHAR(255) NOT NULL,
    dag_id VARCHAR(255) NOT NULL,
    dolphin_execution_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_executions_email ON aubs.executions(email_id);
CREATE INDEX idx_executions_status ON aubs.executions(status);
CREATE INDEX idx_executions_started ON aubs.executions(started_at DESC);

CREATE TABLE IF NOT EXISTS aubs.actions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES aubs.executions(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    result JSONB,
    confidence FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    executed_at TIMESTAMP
);

CREATE INDEX idx_actions_execution ON aubs.actions(execution_id);
CREATE INDEX idx_actions_type ON aubs.actions(action_type);
CREATE INDEX idx_actions_status ON aubs.actions(status);

-- ========== Agent Tables ==========

CREATE TABLE IF NOT EXISTS agents.agent_outputs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES aubs.executions(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    input_data JSONB NOT NULL,
    output_data JSONB NOT NULL,
    confidence FLOAT,
    model_used VARCHAR(100),
    execution_time_ms INTEGER,
    checkpoints JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_outputs_execution ON agents.agent_outputs(execution_id);
CREATE INDEX idx_agent_outputs_agent ON agents.agent_outputs(agent_type);
CREATE INDEX idx_agent_outputs_created ON agents.agent_outputs(created_at DESC);

CREATE TABLE IF NOT EXISTS agents.agent_errors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID REFERENCES aubs.executions(id) ON DELETE CASCADE,
    agent_type VARCHAR(50) NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_errors_execution ON agents.agent_errors(execution_id);
CREATE INDEX idx_agent_errors_type ON agents.agent_errors(error_type);

-- ========== Event Tables ==========

CREATE TABLE IF NOT EXISTS events.email_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id VARCHAR(255) NOT NULL UNIQUE,
    subject TEXT,
    sender VARCHAR(255),
    recipient VARCHAR(255),
    body TEXT,
    attachments JSONB,
    received_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_email_events_email ON events.email_events(email_id);
CREATE INDEX idx_email_events_status ON events.email_events(status);
CREATE INDEX idx_email_events_received ON events.email_events(received_at DESC);
CREATE INDEX idx_email_events_sender ON events.email_events(sender);

CREATE TABLE IF NOT EXISTS events.event_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    correlation_id UUID,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_event_log_type ON events.event_log(event_type);
CREATE INDEX idx_event_log_source ON events.event_log(event_source);
CREATE INDEX idx_event_log_correlation ON events.event_log(correlation_id);
CREATE INDEX idx_event_log_created ON events.event_log(created_at DESC);

-- ========== Context/Memory Tables ==========

CREATE TABLE IF NOT EXISTS agents.context_memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_id VARCHAR(255) NOT NULL,
    context_type VARCHAR(100) NOT NULL,
    context_data JSONB NOT NULL,
    embedding_id VARCHAR(255),  -- Reference to Qdrant vector
    relevance_score FLOAT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_context_memory_email ON agents.context_memory(email_id);
CREATE INDEX idx_context_memory_type ON agents.context_memory(context_type);
CREATE INDEX idx_context_memory_created ON agents.context_memory(created_at DESC);

-- ========== Helper Functions ==========

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_executions_updated_at
    BEFORE UPDATE ON aubs.executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========== Initial Data ==========

-- Insert sample agent types for reference
INSERT INTO agents.agent_outputs (id, execution_id, agent_type, input_data, output_data, confidence, model_used, execution_time_ms)
VALUES
    ('00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000', 'system', '{}', '{"status": "initialized"}', 1.0, 'system', 0)
ON CONFLICT DO NOTHING;

-- Grant permissions (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA aubs TO dolphin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agents TO dolphin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA events TO dolphin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA aubs TO dolphin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agents TO dolphin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA events TO dolphin;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'ChiliHead OpsManager database initialized successfully';
END $$;
