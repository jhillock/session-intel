# Session Intelligence System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Claude Code Sessions                          │
│              ~/.claude/projects/*/sessions/*.jsonl               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INGEST LAYER (Python)                          │
│                 adapters/claude_code.py                          │
│                                                                   │
│  • Read JSONL sessions                                           │
│  • Detect intent (execution/planning/debug/config)               │
│  • Detect domain (ui/data/api/workflow/infra)                    │
│  • Flag signals (errors/retries/corrections/discoveries)         │
│  • Calculate struggle score (intent-adjusted)                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 SESSION DATABASE (SQLite)                        │
│                   ~/.session-intel/sessions.db                   │
│                                                                   │
│  Tables:                                                         │
│  • sessions - metadata, struggle scores, intent/domain           │
│  • messages - individual messages with flags                     │
│  • skill_signals - extracted patterns (future)                   │
│  • analysis_runs - history of analysis runs                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              EXTRACTION LAYER (Python)                           │
│                 strategies/extract.py                            │
│                                                                   │
│  Strategy A: Retry Chains                                        │
│    → Find 3+ consecutive retries (Claude stuck in loop)          │
│                                                                   │
│  Strategy B: Error→Resolution                                    │
│    → Find error messages followed by discoveries                 │
│                                                                   │
│  Strategy C: User Corrections                                    │
│    → Extract where user corrected Claude                         │
│                                                                   │
│  Strategy D: Tool Repetition                                     │
│    → Find same tool called 3+ times in sequence                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                REVIEW LAYER (Markdown)                           │
│                ~/.session-intel/reviews/                         │
│                                                                   │
│  • Project stats (struggle by intent/domain)                     │
│  • Top 10 struggle sessions                                      │
│  • Extracted signal clusters                                     │
│  • Manual review workflow                                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│            ANALYSIS LAYER (Future - LLM-Powered)                 │
│                                                                   │
│  1. Classify signals (Haiku)                                     │
│     → Category, severity, description                            │
│                                                                   │
│  2. Check existing skills                                        │
│     → Scan project/.claude/skills/                               │
│                                                                   │
│  3. Generate recommendations (Sonnet)                            │
│     → CREATE new skill                                           │
│     → UPDATE existing skill                                      │
│     → NONE (enforcement issue)                                   │
│                                                                   │
│  4. Wait for approval                                            │
│     → Log to analysis_runs                                       │
│     → Apply only if --auto-approve                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SKILL GENERATION                              │
│              ~/project/.claude/skills/                           │
│                                                                   │
│  • Create SKILL.md from template                                 │
│  • Include concrete examples from signals                        │
│  • Document common mistakes                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              ENFORCEMENT LAYER (Python)                          │
│                 enforcement.py                                   │
│                                                                   │
│  1. Track skill effectiveness                                    │
│     → Compare struggle before/after skill creation               │
│                                                                   │
│  2. Detect skill usage                                           │
│     → Check if Claude matched the skill                          │
│     → Flag: skill_exists_but_ignored                             │
│                                                                   │
│  3. Identify ineffective skills                                  │
│     → High struggle continues after skill creation               │
│     → Flag: skill_exists_but_ineffective                         │
│                                                                   │
│  4. Generate enforcement recommendations                         │
│     → Make trigger conditions more explicit                      │
│     → Add to CLAUDE.md checklist                                 │
│     → Break into multiple focused skills                         │
│     → Update with missing patterns                               │
└─────────────────────────────────────────────────────────────────┘
```

## Two-Axis Classification

Sessions classified by:

**INTENT (HOW):**
- `execution` - Building features, implementing plans
- `planning` - Designing architecture, writing specs
- `debug` - Fixing broken code
- `config` - Setting up tools, dependencies
- `research` - Exploring APIs, reading docs
- `review` - Code review, design critique
- `continuation` - Session resumed from prior context
- `startup` - Initial project setup
- `unknown` - Can't determine intent

**DOMAIN (WHAT):**
- `ui/design` - Frontend, components, layouts
- `data` - Database, queries, schemas
- `api` - Backend routes, endpoints
- `workflow/automation` - Scripts, cron, integrations
- `infra/deploy` - Deployment, CI/CD, hosting
- `config` - Configuration files, env setup
- `architecture` - System design, patterns
- `metadata` - Documentation, comments
- `test/qa` - Tests, validation
- `general` - Can't determine domain

## Intent-Adjusted Struggle Scoring

Different intents weight errors differently:

```python
execution:   errors*2 + retries*2 + corrections*3
planning:    corrections*3 + retries*0.25
debug:       retries*1 + corrections*3
config:      retries*2 + errors*1
research:    corrections*3
startup:     0  # setup struggles don't indicate skill gaps
```

**Why?**
- Execution errors = critical (building wrong thing)
- Planning retries = minor (thinking through options)
- Debug retries = expected (that's the job)
- Corrections = always valuable (user knows what's wrong)

## Signal Types

**Struggle:**
- High error/retry/correction rates
- Indicates skill gap or missing knowledge

**Success:**
- Low struggle, smooth execution
- Validates existing skills work

**Correction:**
- User corrected Claude's mistake
- Confirms knowledge gap

**Discovery:**
- Claude figured something out on its own
- Pattern worth codifying into a skill

## Current State

**✅ Built:**
- Ingest layer (497 sessions analyzed)
- Database schema
- Extraction strategies (4 types)
- Review workflow
- Enforcement layer (skill effectiveness tracking)

**🚧 In Progress:**
- Analysis layer (manual review for now)
- LLM-powered classification (future)

**📋 Not Built Yet:**
- Auto skill generation (LLM-powered classification)

## Usage

**Ingest sessions:**
```bash
cd ~/.session-intel
python3 adapters/claude_code.py
```

**Extract signals:**
```bash
python3 strategies/extract.py my-project c  # Strategy C (corrections)
python3 strategies/extract.py my-project all  # All strategies
```

**Generate review:**
```bash
python3 analyze.py my-project --strategy=c
cat ~/.session-intel/reviews/my-project-c-*.md
```

**Check skill enforcement:**
```bash
# Check specific skill
python3 enforcement.py my-project my-skill-name --domain=infra/deploy

# Check all skills in project
python3 enforcement.py my-project --check-all
```

**Query database directly:**
```bash
sqlite3 ~/.session-intel/sessions.db
```

## Key Insights

Example findings from analysis:
- **High-struggle sessions** (score > 5) indicate skill gaps
- **Common pain areas:** ui/design, infra/deploy, data modeling
- **Execution sessions struggle most** when patterns aren't documented
- **Low correction rate** = user can't catch mistakes (skill gap harder to detect)

**Critical Pattern:**
Correction rate is a proxy for user domain expertise, not Claude's quality. Projects where users know the domain well show higher correction rates, allowing Claude to learn faster. Low-expertise domains show high struggle with low corrections = undetected skill gaps (most dangerous).

## Enforcement Flags

**skill_exists_but_ignored:**
- Skill created to address a pattern
- Sessions matching skill domain continue
- Skill not mentioned/used in those sessions
- **Fix:** Make trigger conditions more explicit, add to CLAUDE.md checklist

**skill_exists_but_ineffective:**
- Skill created and used
- Struggle scores don't improve (or get worse)
- High error/retry rates continue
- **Fix:** Update skill with missing patterns, break into focused skills, review failed sessions

## Files

```
~/.session-intel/
├── sessions.db              # SQLite database
├── schema.sql               # DB schema definition
├── adapters/
│   └── claude_code.py       # Ingest Claude Code sessions
├── strategies/
│   └── extract.py           # 4 extraction strategies
├── reviews/                 # Generated review files
│   └── project-strategy-timestamp.md
├── analyze.py               # Main analysis script (WIP)
├── enforcement.py           # Skill effectiveness tracker
└── ARCHITECTURE.md          # This file
```
