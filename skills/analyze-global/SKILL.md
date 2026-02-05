---
name: analyze-global
description: Analyze all Claude Code sessions across all projects for cross-cutting skill gaps
triggers:
  - /analyze-global
  - analyze all projects
  - global session analysis
  - find common patterns
---

# Analyze Global Sessions

Analyzes Claude Code sessions across **all projects** to identify cross-cutting patterns and universal skill gaps.

## Usage

**From anywhere:**
```
/analyze-global
```

Claude will:
1. Analyze all sessions in database
2. Identify patterns that appear across multiple projects
3. Generate global skills (not project-specific)
4. Summarize cross-cutting themes

## What It Does

### 1. Get All Projects

```bash
sqlite3 ~/.session-intel/sessions.db "SELECT DISTINCT project, COUNT(*) as sessions FROM sessions GROUP BY project ORDER BY sessions DESC"
```

Show user:
"Analyzing sessions across {N} projects: {project1} ({X} sessions), {project2} ({Y} sessions), ..."

### 2. Run Global Analysis

**Option A: Analyze Each Project Separately**
```bash
for project in $(sqlite3 ~/.session-intel/sessions.db "SELECT DISTINCT project FROM sessions"); do
    python3 ~/.session-intel/src/analyze.py "$project" --strategy=c
done
```

Then aggregate common patterns.

**Option B: Create Synthetic "global" Project**
```bash
# Treat all sessions as one mega-project
python3 ~/.session-intel/src/analyze.py --all-projects --strategy=c
```

(Need to implement `--all-projects` flag)

### 3. Identify Cross-Cutting Patterns

Look for patterns that appear in 3+ projects:
- Same error types
- Same correction patterns
- Same domains struggling (e.g., all projects struggle with ui/design)

### 4. Summarize Global Findings

```markdown
## Global Session Intelligence Analysis

**Coverage:**
- {N} projects analyzed
- {total_sessions} sessions total
- {total_high_struggle} high-struggle sessions

**Cross-Cutting Patterns:**

### 1. React State Management (Found in 4/5 projects)
- Pattern: Repeatedly correcting useState/useReducer usage
- Severity: 5/5
- Projects: my-project, personal-site, dashboard-app, frontend-app

### 2. API Error Handling (Found in 3/5 projects)
- Pattern: Missing try/catch, unclear error messages
- Severity: 4/5  
- Projects: my-project, api-server, api-server

### 3. Database Query Optimization (Found in 3/5 projects)
- Pattern: N+1 queries, missing indexes
- Severity: 4/5
- Projects: my-project, api-server, analytics-tool

**Universal Skill Recommendations:**

- **CREATE: react-state-patterns** (applies to 4 projects)
- **CREATE: api-error-handling-universal** (applies to 3 projects)
- **CREATE: database-query-patterns** (applies to 3 projects)

These skills will be installed globally and help across all projects.
```

### 5. Apply Global Skills

Skills go to `~/.claude/skills/` (not project-specific):

```bash
python3 ~/.session-intel/src/apply_skills.py --global ~/.session-intel/reviews/global-analysis-*.md
```

## Use Cases

### Find Universal Patterns
You make the same mistakes across projects (e.g., always forgetting error handling).

### Skill Reuse
Generate skills once, apply everywhere.

### Team Patterns
If multiple people use same Claude Code account, see team-wide gaps.

### Language/Framework Patterns
If you work in React across 5 projects, see React-specific patterns.

## Strategy Options

**Default:** `--strategy=c` (corrections only, high signal)

Global analysis with `--strategy=all` can take 10-20 minutes for 500+ sessions.

**Recommended:**
- Start with `-c` (user corrections, 2-3 min)
- If patterns found, run `-a` or `-all` for deeper analysis

## Example Session

```
User: /analyze-global

Claude:
Analyzing sessions across all projects... This will take 3-5 minutes.

Found 5 projects:
- my-project (195 sessions)
- backend-api (58 sessions)
- automation-scripts (129 sessions)
- personal-site (42 sessions)
- api-server (38 sessions)

Extracting signals across 462 sessions...
Identifying cross-cutting patterns...

## Global Session Intelligence Analysis

**Coverage:**
- 5 projects, 462 sessions total
- 78 high-struggle sessions
- 124 correction events

**Top Cross-Cutting Patterns:**

1. **React Component Patterns** (Found in 4/5 projects)
   - useState misuse, missing useCallback
   - 32 correction events
   - Severity: 5/5

2. **TypeScript Type Errors** (Found in 4/5 projects)
   - Missing type annotations, 'any' usage
   - 28 correction events
   - Severity: 4/5

3. **API Error Handling** (Found in 3/5 projects)
   - No try/catch, unclear errors
   - 18 correction events
   - Severity: 4/5

**Recommended Universal Skills:**

- **react-component-patterns** (helps 4 projects)
- **typescript-best-practices** (helps 4 projects)  
- **api-error-handling** (helps 3 projects)

Apply these globally? They'll be available in all Claude Code sessions.
```

## Frequency

**Recommended:**
- Monthly global analysis (see trends)
- After learning new framework (see if old habits persist)
- Before code reviews (catch recurring issues)

## Differences from Project Analysis

| Aspect | Project Analysis | Global Analysis |
|--------|------------------|-----------------|
| Scope | Single project | All projects |
| Skills | Project-specific | Universal |
| Time | 2-3 min | 5-10 min |
| When | After project work | Monthly review |
| Finds | Project pain points | Cross-cutting themes |

## Related

- `/analyze-project` - Analyze current project only
- `python3 ~/.session-intel/src/enforcement.py --check-all` - Check all skills across projects
