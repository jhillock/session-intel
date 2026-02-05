---
name: session-intel-setup
description: One-time setup for Session Intelligence
triggers: 
  - /setup-session-intel
  - set up session intelligence
  - install session intel
---

# Session Intelligence Setup

Run this once after cloning the repo to set up Session Intelligence for your environment.

## What This Does

1. Initializes SQLite database
2. Ingests your existing Claude Code sessions
3. Installs analysis skills globally
4. Verifies everything works

## Steps

### 1. Initialize Database

```bash
mkdir -p ~/.session-intel
sqlite3 ~/.session-intel/sessions.db < schema.sql
```

Verify it worked:
```bash
sqlite3 ~/.session-intel/sessions.db ".tables"
# Should show: analysis_runs  messages  sessions
```

### 2. Test LLM Integration

```bash
python3 src/llm_helper.py
```

Should output:
```
✓ Claude Code is installed
✓ LLM integration working correctly
```

### 3. Ingest Your Sessions

```bash
python3 src/adapters/claude_code.py
```

This scans `~/.claude/projects/*/sessions/*.jsonl` and populates the database.

Takes 30-60 seconds for 100 sessions.

Output shows: `Total: X sessions, Y messages`

### 4. Install Analysis Skills Globally

```bash
# Copy skills to global Claude Code skills directory
cp -r skills/* ~/.claude/skills/
```

Or create symlinks (so updates propagate):
```bash
ln -s $(pwd)/skills/analyze-project ~/.claude/skills/
ln -s $(pwd)/skills/analyze-global ~/.claude/skills/
```

### 5. Verify Setup

Check available projects:
```bash
sqlite3 ~/.session-intel/sessions.db "SELECT DISTINCT project FROM sessions ORDER BY project"
```

You should see your Claude Code projects listed.

## Done!

Setup complete. You can now use:
- `/analyze-project` - Analyze current project's sessions
- `/analyze-global` - Analyze all sessions across projects

## Troubleshooting

**No sessions found:**
- Use Claude Code for a few hours to generate session history
- Then re-run: `python3 src/adapters/claude_code.py`

**Database locked error:**
- Another process is using it
- Find with: `lsof ~/.session-intel/sessions.db`
- Kill or wait for it to finish

**LLM test fails:**
- Verify Claude Code installed: `claude --version`
- Verify logged in: `claude auth status`
- If not: `claude auth login`

## Re-running Setup

Safe to run multiple times. Ingestion is incremental (only adds new sessions).

To reset completely:
```bash
rm ~/.session-intel/sessions.db
# Then run setup again
```
