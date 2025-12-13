-- Initialize database schema
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    agent_id VARCHAR(100),
    task_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message TEXT,
    data JSONB,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_sessions (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    event_count INTEGER DEFAULT 0,
    info JSONB
);

-- Clipboard Events Table
CREATE TABLE IF NOT EXISTS clipboard_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    content_type VARCHAR(50),
    raw_content TEXT,
    source_app VARCHAR(255),
    source_url VARCHAR(500),
    processed_summary TEXT,
    tags JSONB,
    image_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activity/Window Events Table
CREATE TABLE IF NOT EXISTS activity_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    window_title VARCHAR(500),
    application VARCHAR(255),
    url VARCHAR(500),
    event_metadata VARCHAR(2000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shell Command Events Table
CREATE TABLE IF NOT EXISTS command_events (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    command TEXT,
    user_name VARCHAR(100),
    working_directory VARCHAR(500),
    exit_code INTEGER,
    event_metadata VARCHAR(2000),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OCR Results Table
CREATE TABLE IF NOT EXISTS ocr_results (
    id SERIAL PRIMARY KEY,
    clipboard_event_id INTEGER REFERENCES clipboard_events(id) ON DELETE CASCADE,
    extracted_text TEXT,
    confidence FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_agent_id ON events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_task_id ON events(task_id);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_sessions_agent_id ON agent_sessions(agent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_clipboard_timestamp ON clipboard_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_clipboard_app ON clipboard_events(source_app);
CREATE INDEX IF NOT EXISTS idx_clipboard_type ON clipboard_events(content_type);
CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_activity_app ON activity_events(application);
CREATE INDEX IF NOT EXISTS idx_command_timestamp ON command_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_command_user ON command_events(user_name);
