---
name: analyze-project
description: Analyze current project's Claude Code sessions for skill gaps
triggers:
  - /analyze-project
  - analyze this project
  - find skill gaps
  - check my sessions
---

# Analyze Project Sessions

Analyzes Claude Code sessions for the current project to identify struggle patterns and generate skill recommendations.

## Usage

**From within a project directory:**
```
/analyze-project
```

Claude will:
1. Detect current project name
2. Run Session Intelligence analysis
3. Summarize top findings
4. Offer to apply recommended skills

## What It Does

### 1. Detect Current Project

```bash
# Get project name from current directory
PROJECT=$(basename "$PWD")
```

Or from `.claude/CLAUDE.md` if it exists:
```bash
grep "Project:" .claude/CLAUDE.md | cut -d: -f2 | xargs
```

### 2. Check If Sessions Exist

```bash
sqlite3 ~/.session-intel/sessions.db "SELECT COUNT(*) FROM sessions WHERE project='$PROJECT'"
```

If 0:
- Tell user: "No sessions found for this project. Use Claude Code here first, then run ingestion: `python3 ~/.session-intel/src/adapters/claude_code.py`"

### 3. Run Analysis

```bash
cd ~/.session-intel
python3 src/analyze.py "$PROJECT" --strategy=all
```

**This takes 2-3 minutes.** Tell user:
"Analyzing sessions for {project}... This will take 2-3 minutes."

Show progress:
- Extracting signals...
- Classifying patterns...
- Generating skill recommendations...

### 4. Summarize Findings

Read the generated report:
```bash
cat ~/.session-intel/reviews/$PROJECT-analysis-*.md
```

**Summarize for user:**

```markdown
## Session Intelligence Analysis: {project}

**Summary:**
- {total_sessions} sessions analyzed
- {high_struggle} high-struggle sessions found
- Top pain area: {top_domain} ({avg_struggle} avg struggle)

**Top 3 Struggle Patterns:**

1. **{pattern_1}** (Severity: {severity}/5)
   - Found in {count} sessions
   - Example: {preview}
   
2. **{pattern_2}** (Severity: {severity}/5)
   - Found in {count} sessions
   - Example: {preview}

3. **{pattern_3}** (Severity: {severity}/5)
   - Found in {count} sessions
   - Example: {preview}

**Skill Recommendations:**

- **CREATE: {skill_name_1}** - {brief_description}
- **CREATE: {skill_name_2}** - {brief_description}
- **UPDATE: {skill_name_3}** - {brief_description}

**Next Steps:**

Would you like me to:
1. Show full report details for any pattern
2. Apply recommended skills (I'll do dry-run first)
3. View the full analysis report
```

### 5. Offer Actions

**If user wants to apply skills:**
```bash
# Dry-run first
python3 ~/.session-intel/src/apply_skills.py ~/.session-intel/reviews/$PROJECT-analysis-*.md --dry-run

# Show what would be created/updated
# Ask: "Proceed with applying these skills? (yes/no)"

# If yes:
python3 ~/.session-intel/src/apply_skills.py ~/.session-intel/reviews/$PROJECT-analysis-*.md
```

**If user wants full report:**
```bash
cat ~/.session-intel/reviews/$PROJECT-analysis-*.md | less
```

## Strategy Options

**Default:** `--strategy=all` (all 4 extraction strategies)

**User can specify:**
- `/analyze-project --strategy=c` (corrections only, faster)
- `/analyze-project --strategy=a` (retry chains only)

Strategies:
- `a` - Retry chains (Claude stuck in loops)
- `b` - Error→resolution pairs
- `c` - User corrections (high signal)
- `d` - Tool repetition
- `all` - All strategies (most comprehensive)

## Example Session

```
User: /analyze-project

Claude:
Analyzing sessions for backend-api... This will take 2-3 minutes.

Extracting signals... ✓ Found 28 patterns
Classifying... ✓ 12 clusters identified
Generating recommendations... ✓ 4 skills recommended

## Session Intelligence Analysis: backend-api

**Summary:**
- 58 sessions analyzed
- 12 high-struggle sessions found
- Top pain area: infra/deploy (avg struggle: 24.3)

**Top 3 Struggle Patterns:**

1. **Salesforce Deployment Retries** (Severity: 5/5)
   - Found in 8 sessions
   - Pattern: Repeatedly deploying same metadata, hitting validation errors

2. **SOQL Query Optimization** (Severity: 4/5)
   - Found in 6 sessions
   - Pattern: Writing N+1 queries, user correcting to use joins

3. **Apex Test Coverage** (Severity: 3/5)
   - Found in 4 sessions
   - Pattern: Failing to meet 75% code coverage requirement

**Skill Recommendations:**

- **CREATE: salesforce-deployment-patterns** - Quick actions, metadata deploy validation
- **CREATE: soql-optimization** - Avoid N+1, proper joins, governor limits
- **UPDATE: apex-testing** - Add coverage strategies, test data factory patterns

Would you like me to apply these skills? I'll do a dry-run first to show what changes.
```

## When To Use

- After finishing work on a project (weekly/monthly review)
- When you notice Claude repeating mistakes
- Before starting similar work (see what gaps exist)
- After a frustrating session with lots of errors

## Related

- `/analyze-global` - Analyze all projects combined
- `python3 ~/.session-intel/src/enforcement.py PROJECT` - Check if skills are working