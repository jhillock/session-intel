# Enforcement Tracking

Creating skills is easy. Validating they **actually work** is hard.

Session Intelligence tracks skill effectiveness through **before/after comparison** and **usage detection**.

---

## The Enforcement Problem

Common workflow without enforcement:

1. Analyze sessions → find struggle pattern
2. Create skill to address pattern
3. ??? (assume it works)
4. Never validate

**Result:** Accumulate skills that:
- Never get used (Claude doesn't match trigger conditions)
- Get used but don't help (pattern more complex than skill addresses)
- Become stale (codebase evolves, skill outdated)

**Enforcement tracking solves this.**

---

## How It Works

### 1. Skill Creation Timestamp

When you apply a skill, Session Intelligence records:
```json
{
  "skill_name": "react-state-patterns",
  "created_at": "2026-02-04T10:30:00Z",
  "project": "my-project",
  "domain": "ui/design",
  "intent": "execution"
}
```

This timestamp divides sessions into **before** and **after** cohorts.

---

### 2. Session Matching

Find sessions that should have used the skill:

**Criteria:**
- Same project
- Matching domain (e.g., `ui/design`)
- Matching intent (e.g., `execution`)
- Created after skill creation

**Example query:**
```sql
SELECT * FROM sessions
WHERE project = 'my-project'
  AND domain = 'ui/design'
  AND intent = 'execution'
  AND created_at > '2026-02-04T10:30:00Z'
```

---

### 3. Before/After Comparison

**Before cohort:** 10+ sessions before skill creation (same domain/intent)  
**After cohort:** 10+ sessions after skill creation (same domain/intent)

**Metrics compared:**
- Average struggle score
- Error rate (errors per session)
- Retry rate
- Correction rate

**Statistical requirement:** Minimum 10 sessions per cohort for validity.

---

### 4. Usage Detection

Check if skill was actually used in **after** cohort sessions.

**Methods:**
1. **Skill mention:** Session messages contain skill name or trigger keywords
2. **CLAUDE.md reference:** Project's CLAUDE.md mentions the skill
3. **File presence:** Skill file exists in project or global skills directory

**Example:** Session text contains "using react-state-patterns skill" → skill was used.

---

### 5. Status Classification

Based on before/after comparison + usage detection:

**EFFECTIVE:**
- Skill used in matching sessions
- Struggle reduced by 20%+ (or error rate down 20%+)
- **Action:** Keep skill, consider expanding to other domains

**IGNORED:**
- Skill NOT used in matching sessions
- Struggle unchanged (or worse)
- **Action:** Make trigger conditions more explicit, add to CLAUDE.md

**INEFFECTIVE:**
- Skill used in matching sessions
- Struggle NOT reduced (or increased)
- **Action:** Update skill content, break into focused skills, review failures

**INSUFFICIENT_DATA:**
- Less than 10 sessions in before or after cohort
- **Action:** Wait for more sessions before validating

---

## Enforcement Command

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
Created: 2026-02-04 10:30:00
Project: my-project
Domain: ui/design
Intent: execution

Before (12 sessions):
  Avg struggle: 28.3
  Error rate: 4.2 per session
  Retry rate: 6.1 per session
  Correction rate: 1.8 per session

After (15 sessions):
  Avg struggle: 12.1  ✓ -57%
  Error rate: 1.8 per session  ✓ -57%
  Retry rate: 2.4 per session  ✓ -61%
  Correction rate: 0.9 per session  ✓ -50%

Usage: 12/15 sessions mention skill (80%)

Status: EFFECTIVE ✓

Recommendation: Skill is working. Consider expanding to similar patterns.
```

---

### Check All Skills

```bash
python3 src/enforcement.py PROJECT_NAME --check-all
```

**Output:**
```
Checking all skills for project: my-project

1. react-state-patterns
   Status: EFFECTIVE ✓
   Struggle: -57% (28.3 → 12.1)

2. api-error-handling
   Status: INEFFECTIVE ⚠️
   Struggle: +12% (15.2 → 17.0)
   Recommendation: Skill used but not helping. Review content.

3. dashboard-components
   Status: IGNORED ⚠️
   Struggle: -2% (22.1 → 21.7)
   Usage: 0/8 sessions mention skill
   Recommendation: Trigger conditions unclear. Add to CLAUDE.md.

4. sql-optimization
   Status: INSUFFICIENT_DATA
   Before: 12 sessions
   After: 3 sessions (need 7 more)

Summary:
  4 skills checked
  1 effective
  2 need attention
  1 needs more data
```

---

## Interpretation Guide

### EFFECTIVE Skills

**Characteristics:**
- Used in 60%+ of matching sessions
- Struggle reduced by 20%+ consistently
- Error/correction rates down

**Example:**
- Before: avg 25.3 struggle, 4.1 errors/session
- After: avg 10.2 struggle, 1.6 errors/session
- Usage: 85% of sessions

**Next steps:**
- **Keep it** - skill is working as designed
- **Expand** - apply pattern to related domains
- **Document** - add to skill marketplace (future feature)

---

### IGNORED Skills

**Characteristics:**
- Used in <20% of matching sessions
- Struggle unchanged (±5%)
- Claude not matching trigger conditions

**Common causes:**
1. **Trigger too vague:** "Use this for state management" → What type of state? When?
2. **Not in CLAUDE.md:** Claude doesn't see skill in checklist
3. **Skill name unclear:** Claude can't tell when to use it

**Example:**
```markdown
Before (BAD trigger):
---
name: state-patterns
description: Patterns for managing state
triggers: When working with state
---

After (GOOD trigger):
---
name: react-state-patterns
description: When to use useState vs useReducer vs Context in React
triggers: 
  - Building React components with complex state (3+ related values)
  - State updates depend on previous state
  - Multiple components need shared state
---
```

**Next steps:**
- **Make triggers specific:** Exact conditions when skill applies
- **Add to CLAUDE.md:** Include in project checklist
- **Rename if needed:** Skill name should match trigger
- **Add examples:** Show 2-3 concrete before/after snippets in skill

---

### INEFFECTIVE Skills

**Characteristics:**
- Used in 60%+ of matching sessions (Claude trying to use it)
- Struggle NOT reduced (or increased)
- Errors/corrections continue

**Common causes:**
1. **Skill too generic:** Covers pattern but misses edge cases
2. **Skill outdated:** Codebase changed, skill no longer applies
3. **Wrong diagnosis:** Pattern exists but different root cause
4. **Skill too complex:** Too many steps, Claude can't follow

**Example:**
```markdown
Skill created for: API error handling
Issue: Covers try/catch but misses validation, timeouts, retry logic
Result: Errors reduced (no more crashes) but retries increased (validation failures)
Struggle score: Unchanged (errors → retries)
```

**Next steps:**
- **Review failed sessions:** Read 3-5 sessions where skill was used but struggled
- **Identify gaps:** What did skill miss? What went wrong?
- **Update skill content:** Add missing patterns, edge cases
- **Break into focused skills:** If skill tries to do too much, split it
  - `api-error-handling` → `api-validation`, `api-retry-logic`, `api-timeout-handling`

---

### INSUFFICIENT_DATA

**Characteristics:**
- Less than 10 sessions in before or after cohort
- Can't draw statistical conclusions

**Why minimum 10:**
- Sample size for meaningful average
- Filters outliers (one terrible session skews avg of 3)
- Statistical significance (t-test needs data)

**Next steps:**
- **Wait** - keep using Claude in this domain/intent
- **Check back weekly** - re-run enforcement after more sessions
- **Don't delete** - skill might be effective, just not enough data yet

**Time to 10 sessions:**
- Active project (daily work): 1-2 weeks
- Side project (weekly work): 2-3 months

---

## Statistical Validation

### Why 20% Threshold?

**20% reduction** in struggle score is the minimum to consider a skill "effective."

**Why not 10%?**
- Session-to-session variance is ~15% (noise)
- 10% reduction could be random luck
- 20% is statistically significant with n=10

**Why not 50%?**
- Perfect skills (50%+ reduction) are rare
- 20-40% reduction is typical for good skills
- Higher bar would reject effective skills

---

### T-Test (Future Feature)

Current enforcement uses simple averages. **v0.2 will add t-tests:**

```python
from scipy import stats

# Before cohort struggle scores: [25, 28, 22, 30, 26, ...]
# After cohort struggle scores: [12, 15, 10, 14, 11, ...]

t_stat, p_value = stats.ttest_ind(before_scores, after_scores)

if p_value < 0.05:
    # Difference is statistically significant
    status = "EFFECTIVE"
else:
    # Could be random noise
    status = "INCONCLUSIVE"
```

**Why not yet?** Requires scipy dependency (keeping it minimal for now).

---

## Time Windows

### Before Cohort
**Default:** All matching sessions before skill creation

**Issue:** Very old sessions may not be comparable (codebase changed).

**Future:** Configurable lookback window (e.g., "only last 30 days before").

---

### After Cohort
**Default:** All matching sessions after skill creation

**Issue:** First few sessions after creation may still be adapting.

**Future:** Configurable warmup period (e.g., "ignore first 3 sessions after").

---

## Common Pitfalls

### 1. Comparing Different Domains

**Mistake:** Create skill for `ui/design`, compare to `data` sessions.

**Why it fails:** Different domains have different baseline struggle.

**Fix:** Enforcement automatically filters to same domain/intent.

---

### 2. Small Sample Size

**Mistake:** Validate after 3 sessions.

**Why it fails:** One bad session skews average.

**Fix:** Wait for 10+ sessions (enforcement flags INSUFFICIENT_DATA).

---

### 3. Codebase Changes

**Mistake:** Skill created in Feb, validated in June after major refactor.

**Why it fails:** Before/after cohorts not comparable (codebase changed).

**Fix:** Re-baseline after major changes (consider old skills stale).

---

### 4. Skill Overlap

**Mistake:** Create 3 skills for same domain/intent, all addressing similar patterns.

**Why it fails:** Can't attribute improvement to specific skill.

**Fix:** Create focused, non-overlapping skills. Use skill composition:
```markdown
See also: react-state-patterns (for basic state), react-context-patterns (for global state)
```

---

## Manual Validation

Enforcement stats are heuristics. Always manually review a few sessions.

### Pick 3 Sessions from After Cohort

```bash
# Get 3 random sessions after skill creation
sqlite3 ~/.session-intel/sessions.db "
SELECT session_id, struggle_score, first_message
FROM sessions
WHERE project='my-project'
  AND domain='ui/design'
  AND intent='execution'
  AND created_at > '2026-02-04'
ORDER BY RANDOM()
LIMIT 3
"
```

### Open Sessions in Claude Code History

```bash
# Find session JSONL (session_id from above)
ls ~/.claude/projects/my-project/sessions/ | grep SESSION_ID
```

### Review Each Session

**Questions to ask:**
1. Did skill get mentioned?
2. If yes, did Claude follow skill instructions?
3. If no, should it have been used? (trigger match?)
4. Did errors/retries happen in areas skill addresses?
5. Did user have to correct anything skill should have prevented?

**Example findings:**
- ✅ "Skill mentioned, Claude used useReducer as instructed, no state errors"
- ⚠️ "Skill NOT mentioned, but session was about state - trigger too vague"
- ❌ "Skill mentioned, Claude tried to follow it, but still made mistakes - skill incomplete"

---

## Iteration Workflow

Skills aren't "done" after creation. They evolve:

```
1. Analyze → Create skill
       ↓
2. Wait for 10+ sessions
       ↓
3. Check enforcement
       ↓
4a. EFFECTIVE → Keep, expand
4b. IGNORED → Update triggers, add to CLAUDE.md
4c. INEFFECTIVE → Update content, break into focused skills
       ↓
5. Wait for 10+ more sessions
       ↓
6. Re-check enforcement
       ↓
7. Repeat until EFFECTIVE or DELETE if never helps
```

**Healthy projects:** 70%+ skills EFFECTIVE after 2-3 iterations.

---

## Enforcement History (Future)

**v0.2 planned:** Track enforcement checks over time.

```sql
CREATE TABLE enforcement_history (
  id INTEGER PRIMARY KEY,
  skill_name TEXT,
  checked_at TIMESTAMP,
  before_avg_struggle REAL,
  after_avg_struggle REAL,
  reduction_pct REAL,
  status TEXT,
  notes TEXT
);
```

**Why useful:**
- See if skill was EFFECTIVE then became INEFFECTIVE (codebase drift)
- Track improvement over multiple iterations
- Graph skill effectiveness over time

---

## Related Documentation

- [WORKFLOW.md](WORKFLOW.md) - How to run enforcement checks
- [CLASSIFICATION.md](CLASSIFICATION.md) - How domain/intent matching works
- [SCORING.md](SCORING.md) - How struggle scores are calculated

---

*Enforcement is what makes Session Intelligence a **system**, not just an analysis tool.*
