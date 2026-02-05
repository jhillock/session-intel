# Struggle Scoring Methodology

Session Intelligence uses **intent-adjusted scoring** to measure how much friction occurred in each session.

## Why Intent Matters

Not all errors are created equal. Consider:

- **Execution error:** Built wrong feature → Critical (wasted time/money)
- **Debug retry:** Tried 5 approaches to fix bug → Expected (that's debugging)
- **Planning retry:** Explored 3 architecture options → Normal (thinking process)

**A single "struggle score" that treats all sessions equally misses this nuance.**

Intent-adjusted scoring weights errors, retries, and corrections based on **what type of work you're doing**.

---

## Core Metrics

### 1. Error Count
**Definition:** Messages flagged as containing errors.

**Detection:**
- Exception traces (Python, JavaScript, etc.)
- Tool failures (file not found, permission denied)
- Build errors (TypeScript, linting)
- Keywords: "Error:", "Exception:", "Failed:", "Cannot"

**Example:**
```
AssistantMessage: Let's update the component...
ToolResult: Error: Cannot find module 'react-query'
```
→ `error_count += 1`

---

### 2. Retry Count
**Definition:** Messages that repeat a previous action (Claude trying again).

**Detection:**
- Same tool called with similar arguments within 3 messages
- Keywords: "let me try", "actually", "instead"
- Pattern: read → modify → write → (fails) → read again

**Example:**
```
AssistantMessage: I'll update the database schema...
ToolResult: (writes schema)
UserMessage: That broke migrations
AssistantMessage: Let me fix that...  ← Retry
ToolResult: (writes schema again)
```
→ `retry_count += 1`

---

### 3. Correction Count
**Definition:** User corrected Claude's mistake.

**Detection:**
- User message starts with: "No", "Actually", "That's wrong", "Don't"
- User provides corrected information
- Pattern: assistant → (wrong) → user → (correction) → assistant → (fixed)

**Example:**
```
AssistantMessage: I'll use useState for this...
UserMessage: No, use useReducer instead. useState won't work for complex state.  ← Correction
AssistantMessage: You're right, let me use useReducer...
```
→ `correction_count += 1`

---

### 4. Discovery Count (Positive Signal)
**Definition:** Claude figured something out on their own.

**Detection:**
- Keywords: "I see", "Ah", "Now I understand", "The issue is"
- Pattern: error → investigation → resolution

**Example:**
```
AssistantMessage: Hmm, getting CORS error...
ToolResult: (reads logs)
AssistantMessage: Ah, I see - the API is missing the Access-Control-Allow-Origin header.  ← Discovery
```
→ `discovery_count += 1`

**Note:** Discovery is a **positive signal** (learning happened), not counted in struggle score.

---

## Intent-Adjusted Formulas

Different intents weight the core metrics differently.

### Execution
```
struggle_score = (error_count × 2) + (retry_count × 2) + (correction_count × 3)
```

**Why:**
- **Errors matter most** (building wrong thing)
- **Retries are painful** (wasted effort)
- **Corrections are critical** (user knows what's right, Claude got it wrong)

**Example:**
- 3 errors, 2 retries, 1 correction
- Score: (3×2) + (2×2) + (1×3) = 6 + 4 + 3 = **13**

---

### Planning
```
struggle_score = (correction_count × 3) + (retry_count × 0.25)
```

**Why:**
- **Retries are normal** (exploring options, thinking through trade-offs)
- **Corrections matter** (user knows the domain, Claude misunderstood requirements)
- **Errors rare** (planning is conversation, not code)

**Example:**
- 0 errors, 8 retries (exploring options), 2 corrections
- Score: (2×3) + (8×0.25) = 6 + 2 = **8**

**Without intent adjustment:** 8 retries would look terrible. With adjustment: it's normal planning.

---

### Debug
```
struggle_score = (retry_count × 1) + (correction_count × 3)
```

**Why:**
- **Retries are expected** (that's debugging - try, fail, try again)
- **Corrections matter** (wrong diagnosis, user had to redirect)
- **Errors less important** (debugging inherently deals with errors)

**Example:**
- 5 errors (trying fixes), 10 retries, 1 correction
- Score: (10×1) + (1×3) = 10 + 3 = **13**

**Without intent adjustment:** 5 errors would dominate the score. With adjustment: expected part of debugging.

---

### Config
```
struggle_score = (retry_count × 2) + (error_count × 1)
```

**Why:**
- **Retries are painful** (config trial-and-error is frustrating)
- **Errors are common** (cryptic dependency/version issues)
- **Corrections less common** (config errors show up as failures, not logic mistakes)

**Example:**
- 4 errors (dependency conflicts), 6 retries, 0 corrections
- Score: (6×2) + (4×1) = 12 + 4 = **16**

---

### Research
```
struggle_score = (correction_count × 3)
```

**Why:**
- **Only corrections matter** (research is reading - no retries or errors)
- **User corrects misunderstandings** (Claude misread docs, user clarifies)

**Example:**
- 0 errors, 0 retries, 3 corrections (user clarifying API behavior)
- Score: (3×3) = **9**

---

### Review
```
struggle_score = (correction_count × 3)
```

**Why:**
- **Only corrections matter** (user points out missed issues)
- **No retries/errors** (review is evaluation, not execution)

**Example:**
- 0 errors, 0 retries, 2 corrections (user caught security issue)
- Score: (2×3) = **6**

---

### Startup
```
struggle_score = 0
```

**Why:**
- **Initial setup struggles don't indicate skill gaps** (environmental issues, boilerplate quirks)
- **Errors/retries expected** (first-time project setup)

**Impact:** Startup sessions excluded from skill gap analysis.

---

### Unknown Intent
```
struggle_score = (error_count × 1) + (retry_count × 1) + (correction_count × 2)
```

**Why:**
- **Neutral weighting** when intent can't be determined
- **Corrections weighted slightly higher** (always valuable signal)

---

## Thresholds

### High Struggle (Score > 20)
**Interpretation:** Critical skill gap or systemic issue.

**Characteristics:**
- 10+ errors, or 5+ corrections
- Long sessions with repeated failures
- User frustration visible in messages

**Action:** Prioritize addressing this pattern with a skill.

**Example sessions:**
- 15 errors, 8 retries, 3 corrections → Score: 47 (execution)
- 12 corrections → Score: 36 (planning)

---

### Medium Struggle (Score 5-20)
**Interpretation:** Moderate friction, may be normal for domain.

**Characteristics:**
- 3-5 errors or 2-3 corrections
- Some back-and-forth but eventually resolved
- Not a disaster but not smooth

**Action:** Consider skill if pattern repeats across 5+ sessions.

**Example sessions:**
- 4 errors, 3 retries, 1 correction → Score: 17 (execution)
- 6 corrections → Score: 18 (planning)

---

### Low Struggle (Score < 5)
**Interpretation:** Smooth session, minimal friction.

**Characteristics:**
- 0-2 errors
- 0-1 corrections
- Session went as expected

**Action:** No skill needed. Validate existing skills work.

**Example sessions:**
- 1 error, 0 retries, 0 corrections → Score: 2 (execution)
- 4 retries (planning exploration), 0 corrections → Score: 1 (planning)

---

## Interpretation Examples

### Example 1: High Execution Struggle

**Session:** Building a checkout flow with Stripe

**Metrics:**
- 12 errors (Stripe API failures)
- 8 retries (trying different approaches)
- 4 corrections (user fixed API key, webhook setup, currency format)

**Intent:** Execution  
**Formula:** (12×2) + (8×2) + (4×3) = 24 + 16 + 12 = **52**

**Interpretation:**
- **CRITICAL** - User had to correct Stripe fundamentals 4 times
- Claude doesn't understand Stripe API patterns
- **Skill needed:** "Stripe integration patterns"

---

### Example 2: Normal Planning Struggle

**Session:** Designing database schema for multi-tenancy

**Metrics:**
- 0 errors (no code yet)
- 15 retries (exploring 3 different schema approaches)
- 1 correction (user clarified tenant isolation requirements)

**Intent:** Planning  
**Formula:** (1×3) + (15×0.25) = 3 + 3.75 = **6.75**

**Interpretation:**
- **NORMAL** - Planning inherently iterative
- 15 retries look bad, but weighted low (exploration)
- 1 correction is minor clarification
- **No skill needed** - expected friction

---

### Example 3: Debug with High Correction

**Session:** Fixing production API timeout

**Metrics:**
- 8 errors (logs, traces)
- 20 retries (trying fixes)
- 5 corrections (user kept redirecting Claude's diagnosis)

**Intent:** Debug  
**Formula:** (20×1) + (5×3) = 20 + 15 = **35**

**Interpretation:**
- **HIGH STRUGGLE** - Despite retries being weighted low
- 5 corrections = Claude had wrong mental model
- Retries alone weren't the issue (expected in debug)
- **Skill needed:** "API performance debugging" or domain-specific troubleshooting

---

### Example 4: Config Hell

**Session:** Setting up TypeScript with Vite + Tailwind

**Metrics:**
- 6 errors (build failures)
- 12 retries (config tweaks)
- 1 correction (user fixed path alias)

**Intent:** Config  
**Formula:** (12×2) + (6×1) = 24 + 6 = **30**

**Interpretation:**
- **HIGH STRUGGLE** - Config is painful
- 12 retries = trial-and-error frustration
- Only 1 correction (errors show up as build failures, not logic)
- **Skill needed:** "Vite + Tailwind setup"

---

## Why Corrections Are Weighted Highest

Corrections are the **strongest signal** of a skill gap:

1. **User knows the right answer** (domain expertise)
2. **Claude had wrong assumption** (knowledge gap)
3. **Wasted tokens/time** (Claude went down wrong path)

**Example:**
```
AssistantMessage: I'll use localStorage for session management.
UserMessage: No, use httpOnly cookies. localStorage is vulnerable to XSS.  ← HIGH VALUE CORRECTION
AssistantMessage: You're right, let me use cookies instead.
```

This single correction (score: 3 for execution) signals:
- Claude lacks security knowledge
- User had to teach a fundamental concept
- Wasted time implementing wrong approach first

**Errors/retries can be environmental. Corrections are always knowledge gaps.**

---

## Correction Rate = Domain Expertise Proxy

**Key insight from 500+ sessions analyzed:**

**Correction rate correlates with USER's domain expertise, not Claude's quality.**

### High Corrections in Familiar Domain
**Example:** Salesforce admin using Claude for Apex code

- User catches mistakes immediately (knows Apex)
- High correction count
- Struggle score stays medium (corrections prevent disasters)
- **Outcome:** Claude improves via feedback loop

### Low Corrections in Unfamiliar Domain
**Example:** Backend dev using Claude for React

- User can't validate Claude's React decisions
- Low correction count (not because Claude is perfect)
- Errors accumulate undetected
- **Outcome:** Building wrong thing, only discovered later

**This means:** High struggle + low corrections = MOST DANGEROUS situation.

---

## Adjusting Thresholds

Thresholds (5, 20) are defaults. Adjust based on your projects:

### Lower Threshold (Stricter)
**When:** You have high domain expertise, can catch most mistakes

**Set:** High struggle = 10, medium = 3

**Why:** You'll correct Claude often, so scores trend higher.

### Higher Threshold (Looser)
**When:** Learning new domain, exploring unfamiliar territory

**Set:** High struggle = 30, medium = 10

**Why:** Struggle is expected when learning. Focus on repeated patterns.

---

## Limitations

### 1. Short Sessions
**Issue:** 1-2 message sessions have low scores by default.

**Impact:** May miss skill gaps in quick interactions.

**Mitigation:** Focus on medium+ length sessions (5+ messages).

### 2. Context Loss
**Issue:** Session restarts (continuation intent) lose context.

**Impact:** May re-solve same problem, inflating score.

**Mitigation:** Continuation sessions inherit previous session's intent/domain.

### 3. Mixed Intents
**Issue:** Session switches from planning → execution mid-way.

**Impact:** Score uses first intent (planning), but later execution errors weighted wrong.

**Mitigation:** Split long sessions into separate analyses (future feature).

### 4. Environmental Issues
**Issue:** Network failures, API downtime, local system issues inflate error count.

**Impact:** High score from non-skill-gap causes.

**Mitigation:** Manual review of high-struggle sessions to filter environmental noise.

---

## Future Improvements

### v0.2 Planned
- Configurable formulas per project
- Custom thresholds
- Session splitting (detect intent changes)

### v0.3 Planned
- Time-weighted scoring (recent sessions matter more)
- Comparative scoring (project A vs. project B)
- Environmental error detection (filter network/system issues)

---

## Related Documentation

- [CLASSIFICATION.md](CLASSIFICATION.md) - Intent/domain taxonomy
- [ENFORCEMENT.md](ENFORCEMENT.md) - Using scores to validate skills
- [WORKFLOW.md](WORKFLOW.md) - Running analysis and interpreting reports

---

*Scoring is heuristic, not perfect. Use as a starting point, validate with manual review.*
