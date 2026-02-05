CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                -- source:session_id
    source TEXT NOT NULL,               -- claude-code | clawdbot
    project TEXT,                       -- casechek-salesforce | johnOS | clawd | null
    session_id TEXT NOT NULL,           -- original session UUID
    first_message TEXT,                 -- first user message (300 char preview)
    message_count INTEGER DEFAULT 0,
    user_message_count INTEGER DEFAULT 0,
    assistant_message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,      -- messages containing error signals
    retry_count INTEGER DEFAULT 0,      -- "let me try" / repeated operations
    correction_count INTEGER DEFAULT 0, -- user corrections ("actually", "no", "you can't")
    unique_tools TEXT,                  -- JSON array of distinct tool names used
    size_bytes INTEGER,
    created_at TEXT,                    -- session file birthtime
    modified_at TEXT,                   -- session file mtime
    duration_minutes REAL,             -- modified - created
    raw_path TEXT,                      -- path to original JSONL
    ingested_at TEXT DEFAULT (datetime('now')),
    analyzed_at TEXT                    -- null until analysis run covers it
, intent TEXT, struggle_score REAL DEFAULT 0, domain TEXT);
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    seq INTEGER NOT NULL,               -- message sequence number
    role TEXT NOT NULL,                  -- user | assistant | system
    timestamp TEXT,
    content_preview TEXT,               -- first 300 chars
    tool_names TEXT,                     -- JSON array of tools used in this message
    tool_call_count INTEGER DEFAULT 0,
    has_error INTEGER DEFAULT 0,        -- contains error/failure signal
    is_retry INTEGER DEFAULT 0,         -- follows a failed attempt
    is_correction INTEGER DEFAULT 0,    -- user correcting claude
    is_discovery INTEGER DEFAULT 0,     -- claude figured something out
    UNIQUE(session_id, seq)
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE skill_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    project TEXT,
    category TEXT,                       -- deploy, metadata, flows, config, etc.
    signal_type TEXT NOT NULL,           -- struggle | success | correction | discovery
    description TEXT,
    severity TEXT,                       -- high | medium | low
    message_seq_start INTEGER,
    message_seq_end INTEGER,
    matched_skill TEXT,                  -- path to existing skill if found
    outcome TEXT,                        -- gap_confirmed | gap_resolved | new_pattern | skill_validated
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date TEXT DEFAULT (datetime('now')),
    source TEXT,                         -- which source was analyzed
    sessions_scanned INTEGER DEFAULT 0,
    signals_found INTEGER DEFAULT 0,
    skills_proposed INTEGER DEFAULT 0,
    skills_created INTEGER DEFAULT 0
, project TEXT, strategy TEXT, findings_json TEXT);
CREATE INDEX idx_sessions_project ON sessions(project);
CREATE INDEX idx_sessions_source ON sessions(source);
CREATE INDEX idx_sessions_modified ON sessions(modified_at DESC);
CREATE INDEX idx_sessions_errors ON sessions(error_count DESC);
CREATE INDEX idx_messages_session ON messages(session_id, seq);
CREATE INDEX idx_signals_project ON skill_signals(project, category);
CREATE INDEX idx_signals_type ON skill_signals(signal_type);
