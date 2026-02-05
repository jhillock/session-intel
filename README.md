# Session Intelligence

![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status: Beta](https://img.shields.io/badge/status-beta-orange.svg)

Automated skill gap detection for Claude Code. Analyzes your session history to find struggle patterns → generates targeted skills → validates effectiveness.

## What It Does

Claude Code is powerful but has no memory. You keep solving the same problems, making the same mistakes, and burning tokens on repeated patterns.

**Session Intelligence** watches your Claude Code sessions to:
1. **Detect struggle patterns** (errors, retries, corrections)
2. **Classify pain points** (Intent × Domain matrix)
3. **Generate targeted skills** (LLM-powered, with examples from your history)
4. **Validate effectiveness** (before/after struggle comparison)

### Two-Axis Classification

Sessions are classified by **Intent × Domain**:

**Intent (HOW you're working):**
- `execution` - Building features, implementing
- `planning` - Designing architecture, specs
- `debug` - Fixing broken code
- `config` - Setting up tools, dependencies
- `research` - Exploring APIs, reading docs

**Domain (WHAT you're working on):**
- `ui/design` - Frontend, components
- `data` - Database, queries, schemas
- `api` - Backend routes, endpoints
- `workflow` - Scripts, automation
- `infra` - Deployment, CI/CD

Each cell in the Intent × Domain matrix reveals specific skill gaps.

## Key Features

✅ **Intent-adjusted struggle scoring** - Different intents weight errors differently (execution errors are critical, planning retries are normal)

✅ **4 signal extraction strategies** - Retry chains, error→resolution, user corrections, tool repetition

✅ **LLM-powered analysis** - Uses Haiku for classification, Sonnet for skill generation

✅ **Enforcement tracking** - Validates whether skills actually reduce struggle

✅ **Zero manual tagging** - Automatic intent/domain detection from session content

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/jhillock/session-intel.git
cd session-intel

# 2. Initialize database
mkdir -p ~/.session-intel
sqlite3 ~/.session-intel/sessions.db < schema.sql

# 3. Verify Claude Code is installed
claude --version

# 4. Ingest your Claude Code sessions
python3 src/adapters/claude_code.py

# 5. Run analysis on a project
python3 src/analyze.py your-project-name --strategy=all

# 6. Review generated report
cat ~/.session-intel/reviews/your-project-analysis-*.md

# 7. Apply recommended skills (after manual review)
python3 src/apply_skills.py ~/.session-intel/reviews/your-project-analysis-*.md

# 8. Check if skills worked (after more sessions)
python3 src/enforcement.py your-project-name --check-all
```

## Installation

### Prerequisites

- **Python 3.8+** (standard library only, no pip packages required)
- **Claude Code CLI** installed and logged in
- **Claude Pro or Max subscription** (uses your existing subscription, no API costs)
- **Claude Code session history** (`~/.claude/projects/*/sessions/*.jsonl`)

### Claude Code Setup

Session Intelligence uses your local Claude Code installation for LLM-powered classification and skill generation.

1. Install Claude Code: https://www.anthropic.com/claude/code
2. Log in: `claude auth login`
3. Verify it works: `claude --version`

**No API costs** - Uses your existing Claude Pro/Max subscription through Claude Code.

### Install Session Intelligence

```bash
git clone https://github.com/jhillock/session-intel.git
cd session-intel
mkdir -p ~/.session-intel
sqlite3 ~/.session-intel/sessions.db < schema.sql

# Verify Claude Code is working
claude --version
```

**No pip dependencies required** - Uses Python standard library + your local Claude Code installation.

## Example Output

After running analysis, you get a report like this:

```markdown
# Project Analysis: your-project (2026-02-04)

## Summary
- 87 total sessions
- 23 high-struggle sessions (score > 5)
- Top pain: ui/design (15 sessions, avg 28.3)

## By Intent
| Intent     | Sessions | Avg Struggle |
|------------|----------|--------------|
| execution  | 45       | 32.1         |
| debug      | 18       | 15.2         |
| planning   | 12       | 3.4          |

## Top Struggle Sessions
1. abc12345 - execution/ui/design - Score: 45.2
   "Build dashboard with real-time updates..."

## Extracted Signals

### Strategy C: User Corrections (8 found)

#### Signal 1: React State Management
- Sessions: abc12345, def67890, ghi11223
- Pattern: Repeatedly correcting useState placement...
- Severity: 4/5

## Skill Recommendations

### CREATE: react-state-patterns
**Reason:** High struggle in ui/design execution
**Trigger:** React + useState + execution intent
**Content:** [Generated SKILL.md with examples from your sessions]
```

## How It Works

```
Claude Code Sessions (~/.claude/projects/*/sessions/*.jsonl)
        ↓
  Ingest & Classify
  (Intent + Domain detection, struggle scoring)
        ↓
  SQLite Database (~/.session-intel/sessions.db)
        ↓
  Extract Signals
  (4 strategies: retries, errors, corrections, repetition)
        ↓
  Classify with Haiku
  (Category, severity, description)
        ↓
  Generate Skills with Sonnet
  (CREATE/UPDATE/NONE decision, SKILL.md content)
        ↓
  Analysis Report (~/.session-intel/reviews/)
        ↓
  Manual Review & Apply
  (You approve, script writes skills)
        ↓
  Track Enforcement
  (Validate skills reduce struggle)
```

## Documentation

- **[Workflow Guide](docs/WORKFLOW.md)** - Step-by-step usage, from installation to enforcement
- **[Classification System](docs/CLASSIFICATION.md)** - Intent + domain taxonomy, detection heuristics
- **[Scoring Methodology](docs/SCORING.md)** - Intent-adjusted struggle scoring explained
- **[Enforcement Tracking](docs/ENFORCEMENT.md)** - How to validate skill effectiveness

## Project Structure

```
session-intel/
├── src/
│   ├── adapters/
│   │   └── claude_code.py      # Ingest Claude Code sessions
│   ├── strategies/
│   │   └── extract.py          # 4 signal extraction strategies
│   ├── classify.py             # Haiku classification
│   ├── generate_skill.py       # Sonnet skill generation
│   ├── analyze.py              # Full analysis workflow
│   ├── enforcement.py          # Skill effectiveness tracking
│   ├── apply_skills.py         # Apply recommendations
│   └── llm_helper.py           # Claude Code CLI wrapper
├── docs/                       # Detailed documentation
├── examples/                   # Sample reports, skills, configs
├── schema.sql                  # SQLite database schema
└── README.md                   # This file
```

## Key Insights

From real-world usage analyzing hundreds of sessions:

**Critical Pattern:** Correction rate is a proxy for the user's domain expertise, not Claude's quality.

- High corrections in familiar domains (e.g., Salesforce admin correcting Claude on Apex) = user can validate
- Low corrections in unfamiliar domains (e.g., learning React) = undetected mistakes accumulate

**This means:** High struggle + low corrections = most dangerous situation (you can't catch Claude's fumbles).

**Intent matters:** Execution errors are critical (building wrong thing), but planning retries are normal (thinking through options). Intent-adjusted scoring reflects this.

## Enforcement Tracking

After creating skills, Session Intelligence tracks whether they actually work:

**skill_exists_but_ignored:**
- Skill created to address a pattern
- New sessions match the domain/intent
- Skill never mentioned in those sessions
- **Fix:** Make trigger conditions more explicit, add to CLAUDE.md checklist

**skill_exists_but_ineffective:**
- Skill created and used
- Struggle scores don't improve
- Errors/retries continue at same rate
- **Fix:** Update skill content, break into focused skills, review failed sessions

## Examples

See the [examples/](examples/) directory for:
- Sample analysis report (sanitized)
- Sample generated skill
- Sample session JSONL structure
- Configuration file template

## Contributing

Contributions welcome! Areas of interest:

- **New extraction strategies** (current: 4, could add more signal types)
- **Classification accuracy** (refine intent/domain detection heuristics)
- **Skill templates** (generic patterns for common domains)
- **Enforcement validation** (statistical significance tests)
- **Web UI** (visualize session history + skills)

Please open an issue before starting major work.

## Roadmap

### v0.2 (Next)
- Statistical validation for enforcement
- Skill templates library
- Configuration file support
- Better error handling

### v0.3
- Web UI for reviewing signals
- Multi-project comparison
- Export to Obsidian/Notion
- OpenRouter API fallback (optional direct API access)

### v1.0
- VS Code extension
- Skill marketplace (share/discover skills)
- Real-time monitoring (watch sessions live)

## FAQ

**Q: Do I need Claude Pro or Max?**  
A: Yes. Session Intelligence uses Claude Code for LLM-powered analysis, which requires an active subscription. This keeps costs at $0 (uses your existing subscription).

**Q: Will this work with other coding assistants (Cursor, Cody, etc.)?**  
A: Not yet. Currently only supports Claude Code session format. Adapters for other tools are planned.

**Q: How much does analysis cost (LLM tokens)?**  
A: **Zero.** Session Intelligence uses your existing Claude Pro/Max subscription through Claude Code. No API costs, no additional fees.

**Q: Does this send my code to external servers?**  
A: Only session metadata (intent, domain, error patterns) is sent to Claude via your local Claude Code installation. Your actual code stays local. All processing happens through your existing Claude subscription.

**Q: Can I customize the classification system?**  
A: Not yet (hardcoded intent/domain taxonomy), but planned for v0.2.

**Q: How do I know if a skill is working?**  
A: Use `enforcement.py` to compare struggle scores before/after skill creation. Look for 20%+ reduction in matching sessions.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Created by [John Hillock](https://github.com/jhillock).

Built on top of:
- [Claude Code](https://www.anthropic.com/claude/code) by Anthropic

## Links

- **Documentation:** [docs/](docs/)
- **Examples:** [examples/](examples/)
- **Issues:** [GitHub Issues](https://github.com/jhillock/session-intel/issues)
- **Discussions:** [GitHub Discussions](https://github.com/jhillock/session-intel/discussions)
- **Claude Code:** https://www.anthropic.com/claude/code

---

*Help Claude Code remember what you taught it.*
