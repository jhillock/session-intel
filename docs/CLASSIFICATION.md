# Classification System

Session Intelligence uses a **two-axis classification system** to precisely identify skill gaps.

## Why Two Axes?

A single "struggle score" isn't enough. Consider these scenarios:

- **High struggle in execution/ui** = Missing React patterns
- **High struggle in debug/data** = SQL troubleshooting gaps
- **High struggle in planning/architecture** = Design framework needed

**Intent × Domain** creates a matrix where each cell represents a specific type of work, revealing precise skill gaps.

---

## Intent Axis (HOW You're Working)

Intent describes **how** you're approaching the work in a session.

### 1. Execution
**Definition:** Building features, implementing plans, writing code.

**Keywords:**
- "implement", "build", "create", "add feature"
- "write code for", "make it work"
- Tool usage: heavy write, exec

**Example session starts:**
- "Build a dashboard component with real-time updates"
- "Implement user authentication with JWT"
- "Add dark mode toggle to settings"

**Struggle signals:**
- Errors in code execution (syntax, runtime)
- Failed tests
- Repeated rewrites
- User corrections on logic

**Scoring weight:** Errors × 2, Retries × 2, Corrections × 3

**Why:** Execution errors are critical - building the wrong thing wastes time/money.

---

### 2. Planning
**Definition:** Designing architecture, writing specs, thinking through approach.

**Keywords:**
- "design", "architecture", "plan", "spec"
- "how should we", "what's the best way"
- "outline", "structure"
- Tool usage: heavy read, minimal write

**Example session starts:**
- "Design the database schema for multi-tenancy"
- "Plan the API structure for the notification system"
- "How should we architect the caching layer?"

**Struggle signals:**
- Many conversation turns (back-and-forth)
- Changing directions
- User corrections on approach

**Scoring weight:** Corrections × 3, Retries × 0.25

**Why:** Planning retries are normal (exploring options). Only corrections matter (wrong assumptions).

---

### 3. Debug
**Definition:** Fixing broken code, investigating errors, troubleshooting.

**Keywords:**
- "fix", "debug", "broken", "error", "not working"
- "why is", "figure out"
- Tool usage: lots of read (logs, error output)

**Example session starts:**
- "Fix the API timeout error in production"
- "Debug why the tests are failing on CI"
- "Figure out why the component isn't re-rendering"

**Struggle signals:**
- Long chains of investigation
- Dead ends
- Trial and error
- User corrections on diagnosis

**Scoring weight:** Retries × 1, Corrections × 3

**Why:** Debug retries are expected (that's the job). High corrections = wrong mental model.

---

### 4. Config
**Definition:** Setting up tools, configuring dependencies, environment setup.

**Keywords:**
- "setup", "configure", "install", "environment"
- "add dependency", "update package"
- Tool usage: exec (npm, pip, etc.), write (config files)

**Example session starts:**
- "Set up TypeScript in the project"
- "Configure ESLint with Prettier"
- "Add Tailwind CSS to Next.js app"

**Struggle signals:**
- Version conflicts
- Dependency resolution failures
- Path/environment issues
- User corrections on config format

**Scoring weight:** Retries × 2, Errors × 1

**Why:** Config retries are painful (trial and error). Errors often cryptic.

---

### 5. Research
**Definition:** Exploring APIs, reading documentation, learning how something works.

**Keywords:**
- "how to", "learn", "explore", "research"
- "what is", "how does X work"
- Tool usage: heavy web_search, read docs

**Example session starts:**
- "How do I use React Server Components?"
- "Learn how Stripe webhooks work"
- "Explore the best way to handle WebSocket reconnection"

**Struggle signals:**
- Many searches
- Reading same docs multiple times
- User corrections on understanding

**Scoring weight:** Corrections × 3

**Why:** Research doesn't have errors/retries (just reading). Corrections = misunderstanding.

---

### 6. Review
**Definition:** Code review, design critique, evaluating work.

**Keywords:**
- "review", "evaluate", "assess", "check"
- "does this look good", "is this correct"
- Tool usage: read only

**Example session starts:**
- "Review this PR for security issues"
- "Evaluate the performance of this SQL query"
- "Check if this component follows best practices"

**Struggle signals:**
- Missing issues in review
- User corrections on assessment

**Scoring weight:** Corrections × 3

**Why:** Review is knowledge work. Corrections = blind spots.

---

### 7. Continuation
**Definition:** Resuming previous work, picking up where you left off.

**Keywords:**
- "continue", "resume", "pick up where"
- Tool usage: read previous work first

**Example session starts:**
- "Continue implementing the user profile page"
- "Resume the API migration from v1 to v2"

**Struggle signals:**
- Lost context
- Re-doing previous work
- User corrections on previous decisions

**Scoring:** Same as underlying intent (execution, debug, etc.)

**Why:** Continuation inherits intent from what's being continued.

---

### 8. Startup
**Definition:** Initial project setup, scaffolding, boilerplate.

**Keywords:**
- "create new project", "scaffold", "initialize"
- "set up fresh", "start from scratch"
- Tool usage: create-next-app, npx, etc.

**Example session starts:**
- "Create a new Next.js app with TypeScript"
- "Initialize a Python project with Poetry"

**Struggle signals:**
- Boilerplate errors
- Template issues

**Scoring weight:** 0 (setup struggles don't indicate skill gaps)

**Why:** Initial setup issues are environmental, not skill-related.

---

### 9. Unknown
**Definition:** Can't determine intent from session content.

**When it happens:**
- Very short sessions (1-2 messages)
- Generic prompts ("help with this")
- Mixed intents in single session

**Scoring:** Default formula (Errors × 1 + Retries × 1 + Corrections × 2)

---

## Domain Axis (WHAT You're Working On)

Domain describes **what** part of the codebase you're working in.

### 1. UI/Design
**Definition:** Frontend, user interface, visual components.

**Technologies:**
- React, Vue, Svelte, Angular
- HTML, CSS, Tailwind, styled-components
- Component libraries (MUI, Radix, shadcn)

**Keywords:**
- "component", "page", "layout", "UI", "frontend"
- "style", "CSS", "design", "responsive"
- "button", "form", "modal", "navigation"

**Example files:**
- `src/components/`, `pages/`, `app/`
- `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`
- `styles/`, `*.css`, `*.scss`

**Common struggles:**
- State management (useState, useEffect)
- Event handling
- Styling bugs (CSS specificity, responsive)
- Component composition

---

### 2. Data
**Definition:** Databases, queries, schemas, data modeling.

**Technologies:**
- SQL (PostgreSQL, MySQL, SQLite)
- ORMs (Prisma, Sequelize, SQLAlchemy)
- NoSQL (MongoDB, Redis, DynamoDB)

**Keywords:**
- "database", "query", "schema", "table", "model"
- "SQL", "migration", "data", "records"
- "fetch", "insert", "update", "delete"

**Example files:**
- `schema.prisma`, `migrations/`, `models/`
- `*.sql`, `db/`, `database/`

**Common struggles:**
- Query performance
- Schema design (normalization, relationships)
- ORM usage
- Data validation

---

### 3. API
**Definition:** Backend routes, endpoints, server logic.

**Technologies:**
- REST APIs (Express, FastAPI, Rails)
- GraphQL (Apollo, Hasura)
- tRPC, gRPC

**Keywords:**
- "API", "endpoint", "route", "handler"
- "request", "response", "middleware"
- "GET", "POST", "fetch", "axios"

**Example files:**
- `api/`, `routes/`, `controllers/`
- `pages/api/` (Next.js)
- `*.route.ts`, `*.controller.py`

**Common struggles:**
- Request validation
- Error handling
- Authentication/authorization
- Rate limiting

---

### 4. Workflow/Automation
**Definition:** Scripts, cron jobs, background tasks, integrations.

**Technologies:**
- Bash scripts, Python scripts
- Cron, GitHub Actions, Zapier
- Task queues (Bull, Celery)

**Keywords:**
- "script", "automation", "cron", "task"
- "workflow", "pipeline", "job"
- "integrate", "sync", "webhook"

**Example files:**
- `scripts/`, `cron/`, `.github/workflows/`
- `*.sh`, `*.py` (standalone scripts)
- `Makefile`, `package.json` (scripts section)

**Common struggles:**
- Environment variables
- Error handling in scripts
- Scheduling/timing
- Idempotency

---

### 5. Infra/Deploy
**Definition:** Deployment, CI/CD, hosting, infrastructure.

**Technologies:**
- Vercel, Netlify, Railway, Fly.io
- Docker, Kubernetes
- CI/CD (GitHub Actions, CircleCI)
- Cloud (AWS, GCP, Azure)

**Keywords:**
- "deploy", "deployment", "CI/CD", "pipeline"
- "docker", "container", "kubernetes"
- "hosting", "environment", "production"

**Example files:**
- `Dockerfile`, `docker-compose.yml`
- `.github/workflows/`, `vercel.json`
- `terraform/`, `k8s/`

**Common struggles:**
- Build configuration
- Environment variables
- Deployment failures
- Performance/scaling

---

### 6. Config
**Definition:** Configuration files, tool setup, project settings.

**Technologies:**
- ESLint, Prettier, TypeScript
- Webpack, Vite, Rollup
- Package managers (npm, yarn, pnpm)

**Keywords:**
- "config", "configuration", "settings"
- "eslint", "prettier", "tsconfig"
- "package.json", ".env"

**Example files:**
- `.eslintrc.js`, `tsconfig.json`, `prettier.config.js`
- `package.json`, `.env`, `.env.local`
- `next.config.js`, `vite.config.ts`

**Common struggles:**
- TypeScript errors
- Linting conflicts
- Dependency versions
- Path aliases

---

### 7. Architecture
**Definition:** System design, patterns, high-level structure.

**Keywords:**
- "architecture", "design pattern", "structure"
- "monolith", "microservices", "modular"
- "separation of concerns", "abstraction"

**Example sessions:**
- "Design the folder structure for a monorepo"
- "Refactor to use repository pattern"
- "Plan the migration from REST to GraphQL"

**Common struggles:**
- Over-engineering
- Inconsistent patterns
- Tight coupling
- Missing abstractions

---

### 8. Metadata
**Definition:** Documentation, comments, types, annotations.

**Keywords:**
- "documentation", "comments", "README"
- "types", "interfaces", "JSDoc"
- "OpenAPI", "swagger"

**Example files:**
- `README.md`, `CONTRIBUTING.md`, `docs/`
- Type definition files (`*.d.ts`)
- OpenAPI specs (`openapi.yaml`)

**Common struggles:**
- Outdated docs
- Missing types
- Inconsistent comments

---

### 9. Test/QA
**Definition:** Tests, validation, quality assurance.

**Technologies:**
- Jest, Vitest, Pytest
- Playwright, Cypress
- Testing Library

**Keywords:**
- "test", "spec", "unit test", "integration test"
- "coverage", "mock", "fixture"
- "e2e", "end-to-end"

**Example files:**
- `*.test.ts`, `*.spec.js`, `__tests__/`
- `tests/`, `e2e/`
- `vitest.config.ts`, `jest.config.js`

**Common struggles:**
- Flaky tests
- Low coverage
- Mocking complexity
- Test setup

---

### 10. General
**Definition:** Can't determine specific domain (or multiple domains).

**When it happens:**
- Cross-cutting concerns (logging, error handling)
- Multiple files across domains
- Generic discussions

---

## Detection Heuristics

### How Intent Is Detected

Session Intelligence analyzes:
1. **First user message** (keywords, phrasing)
2. **Tool usage patterns** (read vs. write vs. exec)
3. **Error/retry/correction patterns**
4. **Session metadata** (short vs. long, tool distribution)

**Example logic:**
```python
if "fix" in first_message or "debug" in first_message:
    intent = "debug"
elif write_count > read_count * 2:
    intent = "execution"
elif read_count > write_count * 2 and "how" in first_message:
    intent = "research"
```

### How Domain Is Detected

Session Intelligence analyzes:
1. **File paths** (inferred from tool usage)
2. **Keywords in messages**
3. **Technologies mentioned**

**Example logic:**
```python
if any("component" in path or ".tsx" in path for path in files):
    domain = "ui/design"
elif any(".sql" in path or "schema" in path for path in files):
    domain = "data"
elif "api/" in files or "route" in first_message:
    domain = "api"
```

---

## Edge Cases

### Multiple Intents in One Session

**Scenario:** Session starts with planning, then switches to execution.

**Handling:** First intent wins (usually planning).

**Why:** Intent typically set in opening messages, rarely changes mid-session.

**Better approach:** Split into separate sessions if possible.

---

### Multiple Domains in One Session

**Scenario:** Working on API + database in same session.

**Handling:** Dominant domain wins (most tool usage).

**Example:** If 80% of writes are in `api/`, domain = `api`.

**Edge case:** If truly 50/50, marked as `general`.

---

### Ambiguous Keywords

**Scenario:** "Build a test for the API"

**Conflict:** "Build" = execution? "test" = test/qa?

**Handling:** Intent from verb ("build" = execution), domain from noun ("test" = test/qa).

**Result:** Intent = execution, domain = test/qa.

---

### Short Sessions (1-2 messages)

**Scenario:** User asks quick question, Claude answers.

**Handling:** Often marked `unknown` intent, `general` domain.

**Why:** Not enough signal to classify accurately.

**Impact:** Low struggle score (few messages = few errors).

---

## Customization (Future)

Currently, intent/domain taxonomy is hardcoded in `src/adapters/claude_code.py`.

**Planned for v0.2:**
- Configuration file (`~/.session-intel/config.json`)
- Custom intent/domain definitions
- Custom keywords/heuristics
- Project-specific overrides

**Example config (future):**
```json
{
  "classification": {
    "intents": {
      "execution": {
        "keywords": ["build", "implement", "create"],
        "tool_pattern": "write_heavy"
      }
    },
    "domains": {
      "salesforce": {
        "keywords": ["apex", "sobject", "salesforce"],
        "file_patterns": ["*.cls", "*.trigger"]
      }
    }
  }
}
```

---

## Validation

### How to Check Classification Accuracy

Manually review some sessions:

```bash
# Get 10 random sessions with classification
sqlite3 ~/.session-intel/sessions.db "
SELECT session_id, intent, domain, first_message 
FROM sessions 
WHERE project='yourproject' 
ORDER BY RANDOM() 
LIMIT 10
"
```

For each session:
1. Open the session JSONL in `~/.claude/projects/yourproject/sessions/`
2. Read first few messages
3. Check if intent/domain match your assessment

If accuracy < 80%, open an issue with examples.

---

## Impact on Skill Generation

Classification directly affects skill recommendations:

**Precise classification** = Precise skills
- "execution/ui" struggle → "React component patterns" skill
- "debug/data" struggle → "SQL troubleshooting" skill

**Vague classification** = Generic skills
- "unknown/general" struggle → "General coding practices" (not useful)

**This is why two axes matter:** Narrows down exactly what skill is needed.

---

## Related Documentation

- [SCORING.md](SCORING.md) - Intent-adjusted struggle scoring formulas
- [ENFORCEMENT.md](ENFORCEMENT.md) - How classification affects skill matching
- [WORKFLOW.md](WORKFLOW.md) - Full analysis workflow

---

*Classification is the foundation of Session Intelligence. Feedback on accuracy welcome!*
