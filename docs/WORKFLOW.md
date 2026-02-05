# Session Intelligence - Workflow Guide

Complete step-by-step guide from installation to enforcement tracking.

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Ingesting Sessions](#ingesting-sessions)
4. [Running Analysis](#running-analysis)
5. [Reviewing Reports](#reviewing-reports)
6. [Applying Skills](#applying-skills)
7. [Tracking Enforcement](#tracking-enforcement)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Step 1: Prerequisites

Verify you have the required components:

```bash
# Check Python version (need 3.8+)
python3 --version

# Check if Claude Code is installed
claude --version

# Check if Claude Code sessions exist
ls ~/.claude/projects/*/sessions/*.jsonl | head -5
```

If Claude Code sessions don't exist, you need to use Claude Code first to generate session history.

### Step 2: Verify Claude Code Setup

```bash
# Check Claude Code is logged in
claude auth status

# If not logged in:
claude auth login

# Test it works
echo "Say hello" | claude
```

**Note:** Session Intelligence uses your existing Claude Pro/Max subscription through Claude Code. No API costs, no additional setup needed.

### Step 4: Clone Session Intelligence

```bash
cd ~
git clone https://github.com/jhillock/session-intel.git
cd session-intel
```

### Step 5: Check Dependencies

```bash
# No pip dependencies required!
# Session Intelligence uses Python standard library only
python3 --version  # Just verify Python 3.8+
```

Session Intelligence has **zero external Python dependencies**. It uses your local Claude Code installation for LLM calls.

### Step 6: Initialize Database

```bash
# Create data directory
mkdir -p ~/.session-intel

# Initialize SQLite database from schema
sqlite3 ~/.session-intel/sessions.db < schema.sql

# Verify tables were created
sqlite3 ~/.session-intel/sessions.db ".tables"
# Should show: sessions, messages, analysis_runs
```

---

## Configuration

### Verify Claude Code

Make sure Claude Code is working:

```bash
# Check version
claude --version

# Check auth status
claude auth status

# Test it works
echo "Say hello" | claude
```

**No environment variables needed** - Claude Code handles authentication automatically.

### Optional: Custom Paths

By default, Session Intelligence looks for:
- Sessions: `~/.claude/projects/*/sessions/*.jsonl`
- Database: `~/.session-intel/sessions.db`
- Skills: `~/.claude/skills/`

To customize, edit `src/adapters/claude_code.py` (configuration file support coming in v0.2).

---

## Ingesting Sessions

Ingestion reads your Claude Code session JSONLs and populates the SQLite database.

### First Ingest

```bash
cd ~/session-intel
python3 src/adapters/claude_code.py
```

**Output:**
```
Scanning ~/.claude/projects/...
Found 3 projects: my-app, backend-api, automation-scripts
Ingesting sessions...
  my-app: 170 sessions (0 new)
  backend-api: 105 sessions (0 new)
  automation-scripts: 67 sessions (0 new)
Total: 342 sessions (0 new, 342 existing)
```

### Re-Ingest (After New Sessions)

Run the same command to pick up new sessions:

```bash
python3 src/adapters/claude_code.py
```

Only new/modified sessions are processed (incremental).

### What Gets Extracted

For each session:
- **Metadata:** Project name, created/modified times
- **Classification:** Intent (execution/planning/debug/etc.), domain (ui/data/api/etc.)
- **Counts:** Messages, errors, retries, corrections, discoveries
- **Struggle score:** Intent-adjusted scoring based on error/retry/correction counts
- **First message:** Preview of what the session was about

For each message:
- **Role:** User vs. assistant
- **Content preview:** First 200 chars
- **Tools used:** Read, write, exec, etc.
- **Flags:** has_error, is_retry, is_correction, is_discovery

### Manual Database Queries

Explore the data:

```bash
# Open database
sqlite3 ~/.session-intel/sessions.db

# Count sessions by project
SELECT project, COUNT(*) FROM sessions GROUP BY project;

# High-struggle sessions
SELECT session_id, intent, domain, struggle_score, first_message 
FROM sessions 
WHERE struggle_score > 5 
ORDER BY struggle_score DESC 
LIMIT 10;

# Sessions by intent
SELECT intent, COUNT(*), AVG(struggle_score) 
FROM sessions 
WHERE intent IS NOT NULL 
GROUP BY intent 
ORDER BY AVG(struggle_score) DESC;
```

---

## Running Analysis

Analysis extracts signals, classifies them with Haiku, and generates skill recommendations with Sonnet.

### Basic Analysis

```bash
python3 src/analyze.py YOUR_PROJECT_NAME --strategy=all
```

Replace `YOUR_PROJECT_NAME` with one of your Claude Code projects (e.g., `my-app`, `backend-api`).

### Strategy Selection

Choose which signal extraction strategies to use:

- **`a`** - Retry chains (Claude stuck in loops, 3+ consecutive retries)
- **`b`** - Error→resolution (errors followed by discoveries)
- **`c`** - User corrections (user fixed Claude's mistake)
- **`d`** - Tool repetition (same tool called 3+ times in a row)
- **`all`** - All strategies combined (recommended)

**Examples:**
```bash
# Just user corrections (fastest, high signal)
python3 src/analyze.py my-app --strategy=c

# Retry chains + corrections
python3 src/analyze.py my-app --strategy=a,c

# All strategies (most comprehensive)
python3 src/analyze.py my-app --strategy=all
```

### What Happens During Analysis

1. **Extract signals** from SQLite database using chosen strategy
2. **Classify signals** with Haiku (category, severity, description) via Claude Code
3. **Check existing skills** in `~/.claude/skills/` and project `.claude/skills/`
4. **Generate recommendations** with Sonnet (CREATE/UPDATE/NONE) via Claude Code
5. **Write report** to `~/.session-intel/reviews/PROJECT-STRATEGY-TIMESTAMP.md`

**Time:** 2-3 minutes for 100 sessions with `--strategy=all`.

**Cost:** $0 - Uses your existing Claude Pro/Max subscription through Claude Code.

### Output

Analysis creates a report file:
```
~/.session-intel/reviews/my-project-all-20260204.md
```

The script prints the path when complete.

---

## Reviewing Reports

Open the generated report:

```bash
cat ~/.session-intel/reviews/my-project-all-20260204.md
```

### Report Structure

```markdown
# Project Analysis: my-project (2026-02-04)

## Summary
[Total sessions, high-struggle count, top pain areas]

## By Intent
[Table of session counts + avg struggle per intent]

## By Domain
[Table of session counts + avg struggle per domain]

## Top 10 Struggle Sessions
[Highest struggle sessions with session ID, intent/domain, score, preview]

## Extracted Signals
[Each strategy shows signals found]

### Strategy A: Retry Chains (5 found)
[List of retry chain signals with sessions, patterns, severity]

### Strategy C: User Corrections (12 found)
[List of correction signals with sessions, patterns, severity]

## Skill Recommendations

### 1. CREATE: skill-name
**Reason:** Why this skill is needed
**Trigger:** When should Claude use this skill
**Sessions:** Which sessions show this pattern
**Content:** [Full SKILL.md content generated by Sonnet]

### 2. UPDATE: existing-skill-name
**Reason:** Why existing skill needs updating
**Add:** What to add to existing skill
**Sessions:** Which sessions show gaps
```

### Interpretation Guide

**High struggle (score > 20):**
- Critical skill gap
- Recurring pattern across multiple sessions
- High error/correction rate
- Prioritize addressing these first

**Medium struggle (score 5-20):**
- Moderate friction
- May be normal for the domain (e.g., debugging always has retries)
- Consider skill if pattern repeats

**Low struggle (score < 5):**
- Minor issues or normal workflow
- Usually not worth a skill

**Correction rate:**
- High corrections in your specialty = good (you're catching mistakes)
- Low corrections in unfamiliar domain = dangerous (mistakes going undetected)

---

## Applying Skills

After reviewing the report, apply recommended skills.

### Dry Run First (Recommended)

```bash
python3 src/apply_skills.py ~/.session-intel/reviews/my-project-all-20260204.md --dry-run
```

**Output:**
```
[DRY RUN] Would create: ~/.claude/skills/react-state-patterns/SKILL.md
[DRY RUN] Would update: ~/.claude/skills/my-app-dashboard/SKILL.md
[DRY RUN] 2 skills would be modified
```

### Apply for Real

```bash
python3 src/apply_skills.py ~/.session-intel/reviews/my-project-all-20260204.md
```

**Output:**
```
Created: ~/.claude/skills/react-state-patterns/SKILL.md
Updated: ~/.claude/skills/my-app-dashboard/SKILL.md
Applied 2 skills
```

### Manual Review Before Applying

**Best practice:** Read the recommended SKILL.md content in the report before applying.

Check for:
- ✅ Trigger conditions make sense
- ✅ Examples are relevant
- ✅ Instructions are actionable
- ✅ No overly specific patterns (won't generalize)

### Selective Application

If you only want to apply some skills:

1. Copy the SKILL.md content from the report
2. Manually create the skill file:
   ```bash
   mkdir -p ~/.claude/skills/skill-name
   nano ~/.claude/skills/skill-name/SKILL.md
   # Paste content, edit as needed
   ```

### Where Skills Go

- **Global skills:** `~/.claude/skills/` (used by all projects)
- **Project skills:** `~/your-project/.claude/skills/` (project-specific)

Apply script writes to global skills by default. Move to project-specific if needed.

---

## Tracking Enforcement

After applying skills, track whether they actually reduce struggle.

### Wait for New Sessions

Skills need sessions **after** creation to validate effectiveness. Wait for:
- 10+ new sessions in matching domain/intent (minimum)
- 1-2 weeks of normal work (recommended)

### Check Specific Skill

```bash
python3 src/enforcement.py PROJECT_NAME SKILL_NAME
```

**Example:**
```bash
python3 src/enforcement.py my-project react-state-patterns
```

**Output:**
```
Skill: react-state-patterns
Created: 2026-02-04
Domain: ui/design
Intent: execution

Before (10 sessions):
  Avg struggle: 28.3
  Error rate: 4.2 per session

After (12 sessions):
  Avg struggle: 12.1  ✓ -57%
  Error rate: 1.8 per session  ✓ -57%

Status: EFFECTIVE
```

### Check All Skills

```bash
python3 src/enforcement.py PROJECT_NAME --check-all
```

Checks all skills created for that project.

### Enforcement Flags

**EFFECTIVE:**
- Struggle reduced by 20%+ in matching sessions
- Skill is working as intended

**IGNORED:**
- Skill exists but never mentioned in matching sessions
- **Fix:** Make trigger conditions more explicit in SKILL.md, add to project CLAUDE.md

**INEFFECTIVE:**
- Skill used but struggle not reduced (or increased)
- **Fix:** Review failed sessions, update skill content, break into focused skills

**INSUFFICIENT_DATA:**
- Not enough sessions after skill creation (need 10+)
- **Fix:** Wait for more sessions

### Manual Validation

Check specific sessions where skill should have applied:

```bash
# Find sessions matching skill domain/intent after skill creation
sqlite3 ~/.session-intel/sessions.db "
SELECT session_id, struggle_score, first_message 
FROM sessions 
WHERE project='my-project' 
  AND domain='ui/design' 
  AND intent='execution'
  AND created_at > '2026-02-04'
ORDER BY created_at DESC
LIMIT 10
"
```

Open those Claude Code sessions and verify:
- Was the skill mentioned?
- Did Claude follow the skill instructions?
- Did struggle actually decrease?

---

## Troubleshooting

### Claude Code Not Installed

**Error:**
```
RuntimeError: Claude Code not found in PATH
```

**Fix:**
```bash
# Install Claude Code
# Download from: https://www.anthropic.com/claude/code

# Verify installation
claude --version
```

### Claude Code Not Authenticated

**Error:**
```
RuntimeError: Claude Code authentication failed
```

**Fix:**
```bash
# Log in to Claude Code
claude auth login

# Verify
claude auth status
```

### No Sessions Found

**Error:**
```
Found 0 projects
```

**Causes:**
1. Claude Code never used (no session history)
2. Sessions in non-standard location

**Fix:**
```bash
# Check if sessions exist
ls -la ~/.claude/projects/*/sessions/*.jsonl | head

# If empty, use Claude Code first to generate sessions
```

### Database Locked

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Cause:** Another process is using the database.

**Fix:**
```bash
# Find process using database
lsof ~/.session-intel/sessions.db

# Kill if needed (or wait for it to finish)
```

### Classification Fails

**Error:**
```
Classification failed: Rate limit exceeded
```

**Cause:** Claude Pro/Max usage limits hit.

**Fix:**
- Wait 60 minutes and retry
- Reduce number of signals (use `--strategy=c` instead of `--strategy=all`)
- Check Claude Code rate limits: https://www.anthropic.com/pricing

### Skill Generation Fails

**Error:**
```
Skill generation failed: Context length exceeded
```

**Cause:** Too many signals sent to Sonnet at once.

**Fix:**
- Break analysis into smaller chunks
- Use specific strategies instead of `--strategy=all`
- Manually create skill from report content

### Empty Analysis Report

**Issue:** Report generated but says "No signals found"

**Causes:**
1. No high-struggle sessions in project
2. Strategy threshold too strict
3. Sessions too old (no errors flagged)

**Debug:**
```bash
# Check if high-struggle sessions exist
sqlite3 ~/.session-intel/sessions.db "
SELECT COUNT(*) FROM sessions 
WHERE project='YOUR_PROJECT' AND struggle_score > 5
"

# If 0, project may have low struggle (good thing!)
```

### Skills Not Applied

**Issue:** `apply_skills.py` runs but no files created

**Debug:**
```bash
# Check report file exists and has recommendations
grep -A 10 "CREATE:" ~/.session-intel/reviews/PROJECT-*.md

# Check permissions
ls -la ~/.claude/skills/
mkdir -p ~/.claude/skills/  # Create if missing
```

---

## Best Practices

### 1. Incremental Analysis

Don't analyze all projects at once. Start with one:

```bash
python3 src/analyze.py your-main-project --strategy=c
```

Review, apply, validate. Then move to next project.

### 2. Regular Ingestion

Set up a cron job to re-ingest weekly:

```bash
# Add to crontab
0 9 * * 1 cd ~/session-intel && python3 src/adapters/claude_code.py
```

### 3. Selective Skill Application

Not every recommendation needs a skill. Apply:
- ✅ High-severity patterns (score > 20)
- ✅ Recurring across 5+ sessions
- ✅ Clear, actionable patterns

Skip:
- ❌ One-off mistakes
- ❌ Overly specific to single session
- ❌ Normal domain friction (debugging always has retries)

### 4. Skill Iteration

Skills are living documents. After applying:
1. Wait 1-2 weeks for new sessions
2. Check enforcement
3. Update if ineffective
4. Delete if never used

### 5. Backup Before Applying

```bash
# Backup existing skills before mass application
cp -r ~/.claude/skills ~/.claude/skills.backup.$(date +%Y%m%d)
```

---

## Advanced Usage

### Query Database Directly

```bash
sqlite3 ~/.session-intel/sessions.db

# Most common errors
SELECT content_preview, COUNT(*) as count
FROM messages
WHERE has_error = 1
GROUP BY content_preview
ORDER BY count DESC
LIMIT 10;

# Struggle by hour of day
SELECT strftime('%H', created_at) as hour, AVG(struggle_score)
FROM sessions
GROUP BY hour
ORDER BY hour;
```

### Custom Extraction

Edit `src/strategies/extract.py` to add new signal types:

```python
def extract_strategy_e(project: str) -> List[Dict]:
    """Extract discovery patterns (Claude figured something out)."""
    # Your custom logic
```

### Batch Analysis

Analyze multiple projects:

```bash
for project in my-app backend-api automation-scripts; do
    python3 src/analyze.py $project --strategy=all
done
```

### Export to Other Formats

```bash
# Convert report to JSON
python3 -c "
import json
import sys
# Parse markdown report, convert to JSON
# (not implemented yet - future feature)
"
```

---

## Next Steps

After your first successful workflow:

1. **Read the other docs:**
   - [CLASSIFICATION.md](CLASSIFICATION.md) - Understand intent/domain taxonomy
   - [SCORING.md](SCORING.md) - Deep dive on struggle scoring
   - [ENFORCEMENT.md](ENFORCEMENT.md) - Statistical validation methods

2. **Experiment with strategies:**
   - Try each strategy individually to see what signals it finds
   - Compare `--strategy=c` (corrections) vs `--strategy=a` (retries)

3. **Contribute back:**
   - Share effective skills in discussions
   - Report bugs or unclear docs
   - Suggest new extraction strategies

---

*This guide is living documentation. Feedback welcome!*
