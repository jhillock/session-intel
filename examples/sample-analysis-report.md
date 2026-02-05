# Session Intelligence Analysis: my-project

**Generated:** 2026-02-04 11:00:00  
**Strategy:** all

---

## Project Stats

- **Total sessions:** 87
- **High struggle (>5):** 23

### By Intent
- execution: 45 sessions, avg struggle 32.1
- planning: 12 sessions, avg struggle 8.3
- debug: 18 sessions, avg struggle 15.2
- config: 8 sessions, avg struggle 18.7
- research: 4 sessions, avg struggle 4.1

### By Domain
- ui/design: 28 sessions, avg struggle 28.6
- data: 22 sessions, avg struggle 12.4
- api: 15 sessions, avg struggle 14.3
- workflow/automation: 12 sessions, avg struggle 16.8
- config: 8 sessions, avg struggle 18.7
- test/qa: 2 sessions, avg struggle 8.5

---

## Top 10 Struggle Sessions

| Session ID | Intent | Domain | Score | Preview |
|------------|--------|--------|-------|---------|
| abc12345 | execution | ui/design | 52.0 | "Build dashboard component with real-time updates" |
| def67890 | execution | ui/design | 48.3 | "Implement user profile page with form validation" |
| ghi11223 | config | config | 42.1 | "Set up TypeScript with ESLint and Prettier" |
| jkl44556 | debug | api | 38.5 | "Fix API timeout error in production" |
| mno77889 | execution | data | 35.2 | "Create database migration for user preferences" |
| pqr00112 | execution | ui/design | 32.8 | "Add dark mode toggle to settings page" |
| stu33445 | debug | data | 30.1 | "Debug slow query on dashboard" |
| vwx66778 | execution | api | 28.9 | "Implement authentication with JWT" |
| yza99001 | config | workflow | 27.4 | "Configure GitHub Actions CI/CD pipeline" |
| bcd22334 | execution | ui/design | 25.6 | "Build modal component library" |

---

## Extracted Signals

### Strategy A: Retry Chains

Found **5 retry chains** (3+ consecutive retries indicating Claude stuck in loops).

#### Signal 1: React State Management Loop
**Sessions:** abc12345, def67890, pqr00112  
**Pattern:** Claude repeatedly rewrites useState logic, trying different approaches  
**Retry count:** 6 messages in a row trying to fix re-render issues  
**Example:**
```
[msg 45] Let me update the state handling...
[msg 48] That didn't work. Let me try using useEffect...
[msg 51] Still not rendering. Let me check the dependency array...
[msg 54] Actually, let me use useReducer instead...
[msg 57] Wait, the problem might be closure. Let me rewrite...
[msg 60] Found it! The issue was stale closure. Fixed.
```

#### Signal 2: TypeScript Configuration Trial-and-Error
**Sessions:** ghi11223  
**Pattern:** 8 consecutive config changes trying to resolve build errors  
**Retry count:** 8 messages adjusting tsconfig.json, ESLint, Prettier  
**Example:**
```
[msg 12] Let me update tsconfig.json...
[msg 15] Still errors. Let me add @typescript-eslint...
[msg 18] Conflict with Prettier. Let me adjust ESLint config...
[msg 21] Path alias not resolving. Let me update baseUrl...
[msg 24] Still broken. Let me check if tsconfig extends properly...
[msg 27] Found it - needed both tsconfig.json AND vite.config.ts updates.
```

---

### Strategy B: Error→Resolution Pairs

Found **8 error→resolution sequences** (learning moments).

#### Signal 1: Database Connection Pooling
**Session:** mno77889  
**Error:** Connection timeout errors under load  
**Resolution:** Added connection pooling, reduced max connections  
**Learning captured:** "Database was creating new connection per request instead of using pool"

#### Signal 2: API CORS Issues
**Session:** vwx66778  
**Error:** CORS errors blocking frontend API calls  
**Resolution:** Added CORS middleware with proper origin config  
**Learning captured:** "CORS must be configured before route handlers in Express"

---

### Strategy C: User Corrections

Found **12 user corrections** (knowledge gaps confirmed by user).

#### Signal 1: React useEffect Misunderstanding
**Sessions:** abc12345, def67890, pqr00112  
**Pattern:** Claude consistently places useEffect incorrectly  
**Severity:** 4/5  

**Example correction:**
```
Claude: "I'll use useEffect to update state on every render..."
User: "No, that creates an infinite loop. Only trigger on mount or when props change."
Claude: "You're right, adding dependency array..."
```

**Frequency:** 3 sessions, same mistake each time

---

#### Signal 2: SQL Query Optimization
**Sessions:** stu33445  
**Pattern:** Claude writes N+1 queries instead of joins  
**Severity:** 3/5  

**Example correction:**
```
Claude: "I'll fetch users then loop through to get their posts..."
User: "That's N+1 queries. Use a JOIN instead."
Claude: "Right, let me write a proper join query..."
```

---

### Strategy D: Tool Repetition

Found **3 tool repetition patterns** (same tool called 3+ times indicating missing context).

#### Signal 1: File Read Loop
**Session:** abc12345  
**Pattern:** Read same component file 5 times in 10 minutes  
**Cause:** Claude forgot file structure, kept re-reading

#### Signal 2: Database Query Repetition
**Session:** stu33445  
**Pattern:** Ran same SELECT query 4 times  
**Cause:** Didn't save query results in context

---

## Classification Results

Classified 12 signal clusters into skill recommendations.

### Category Breakdown
- **ui/design**: 5 signals (high severity)
- **data**: 3 signals (medium severity)
- **api**: 2 signals (medium severity)
- **config**: 2 signals (high severity)

---

## Skill Recommendations

### 1. CREATE: react-state-patterns

**Reason:** High struggle in ui/design execution sessions with React state  
**Severity:** 5/5  
**Sessions affected:** abc12345, def67890, pqr00112 (3 sessions, 32% of ui/design execution)

**Trigger Conditions:**
- Building React components with complex state (3+ related values)
- State updates depend on previous state
- Multiple components need shared state

**Skill Content:**

```markdown
---
name: react-state-patterns
description: When to use useState vs useReducer vs Context in React
tags: [react, state, hooks]
---

# React State Management Patterns

## When to Use Each Pattern

### useState (Simple State)
**Use for:**
- Single primitive values (string, number, boolean)
- Independent values (updating one doesn't affect others)
- No complex update logic

**Example:**
\`\`\`typescript
const [count, setCount] = useState(0);
const [isOpen, setIsOpen] = useState(false);
\`\`\`

### useReducer (Complex State)
**Use for:**
- Multiple related values that update together
- Complex update logic with many cases
- State transitions that follow patterns

**Example:**
\`\`\`typescript
type State = {
  user: User | null;
  loading: boolean;
  error: string | null;
};

type Action =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; user: User }
  | { type: 'FETCH_ERROR'; error: string };

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    case 'FETCH_SUCCESS':
      return { user: action.user, loading: false, error: null };
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.error };
  }
};

const [state, dispatch] = useReducer(reducer, initialState);
\`\`\`

### Context (Shared State)
**Use for:**
- State needed by many deeply nested components
- Avoiding prop drilling (passing props through many levels)
- Theme, auth, localization

**Example:**
\`\`\`typescript
const ThemeContext = createContext<Theme>(defaultTheme);

// Provider at top level
<ThemeContext.Provider value={theme}>
  <App />
</ThemeContext.Provider>

// Consume anywhere
const theme = useContext(ThemeContext);
\`\`\`

## Common Mistakes

### Stale Closures
❌ **Wrong:**
\`\`\`typescript
useEffect(() => {
  setInterval(() => {
    setCount(count + 1); // Uses stale count
  }, 1000);
}, []); // Only runs once, captures initial count
\`\`\`

✅ **Right:**
\`\`\`typescript
useEffect(() => {
  const id = setInterval(() => {
    setCount(c => c + 1); // Functional update, always fresh
  }, 1000);
  return () => clearInterval(id);
}, []);
\`\`\`

### Unnecessary useEffect
❌ **Wrong:**
\`\`\`typescript
const [total, setTotal] = useState(0);
useEffect(() => {
  setTotal(price * quantity); // Runs after every render
}, [price, quantity]);
\`\`\`

✅ **Right:**
\`\`\`typescript
const total = price * quantity; // Compute during render
\`\`\`

## Decision Tree

1. **Is it a single primitive value with simple updates?**  
   → useState

2. **Is it multiple related values or complex update logic?**  
   → useReducer

3. **Does it need to be shared across many components?**  
   → Context + useState/useReducer

## Related Patterns
- See `react-hooks-patterns.md` for useEffect, useMemo, useCallback
- See `component-composition.md` for prop drilling alternatives
```

---

### 2. CREATE: sql-query-optimization

**Reason:** High struggle in data domain with slow queries  
**Severity:** 4/5  
**Sessions affected:** stu33445, mno77889 (2 sessions)

**Trigger Conditions:**
- Writing SQL queries
- Performance issues mentioned
- Database domain

**Skill Content:**

```markdown
---
name: sql-query-optimization
description: Common SQL performance pitfalls and how to fix them
tags: [sql, performance, database]
---

# SQL Query Optimization

## N+1 Query Problem

### The Problem
Fetching data in loops creates N+1 queries (1 for parent, N for children).

❌ **Bad (N+1):**
\`\`\`typescript
const users = await db.query('SELECT * FROM users');
for (const user of users) {
  const posts = await db.query('SELECT * FROM posts WHERE user_id = ?', [user.id]);
  user.posts = posts;
}
\`\`\`

✅ **Good (Single Query with JOIN):**
\`\`\`sql
SELECT 
  users.*,
  posts.id as post_id,
  posts.title as post_title
FROM users
LEFT JOIN posts ON posts.user_id = users.id
\`\`\`

## Use Indexes

### When to Index
- Foreign keys (user_id, project_id, etc.)
- Columns in WHERE clauses
- Columns in ORDER BY
- Columns in JOIN conditions

\`\`\`sql
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_posts_created_at ON posts(created_at);
\`\`\`

## Avoid SELECT *

❌ **Bad:**
\`\`\`sql
SELECT * FROM users WHERE email = 'user@example.com';
\`\`\`

✅ **Good:**
\`\`\`sql
SELECT id, email, name FROM users WHERE email = 'user@example.com';
\`\`\`

Fetches only needed columns, reduces data transfer.

## Use LIMIT

Always limit query results when possible:

\`\`\`sql
SELECT * FROM posts ORDER BY created_at DESC LIMIT 20;
\`\`\`
```

---

### 3. UPDATE: api-error-handling

**Reason:** Existing skill missing validation and retry patterns  
**Severity:** 3/5  
**Sessions showing gaps:** vwx66778, jkl44556

**Add to existing skill:**

\`\`\`markdown
## Request Validation

Always validate input before processing:

\`\`\`typescript
import { z } from 'zod';

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(13).optional(),
});

app.post('/users', async (req, res) => {
  const result = createUserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ errors: result.error.issues });
  }
  
  const user = await createUser(result.data);
  res.status(201).json(user);
});
\`\`\`

## Retry Logic for External APIs

\`\`\`typescript
async function fetchWithRetry(url: string, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, { timeout: 5000 });
      if (response.ok) return response;
      if (response.status < 500) throw new Error('Client error');
    } catch (err) {
      if (i === maxRetries - 1) throw err;
      await sleep(1000 * (i + 1)); // Exponential backoff
    }
  }
}
\`\`\`
\`\`\`

---

### 4. CREATE: typescript-config-setup

**Reason:** High struggle in config domain with TypeScript setup  
**Severity:** 5/5  
**Sessions affected:** ghi11223

**Trigger Conditions:**
- Setting up TypeScript in new project
- TypeScript + ESLint + Prettier integration
- Path alias configuration

**Skill Content:**

```markdown
---
name: typescript-config-setup
description: How to set up TypeScript with modern tools (Vite, ESLint, Prettier)
tags: [typescript, config, eslint, prettier]
---

# TypeScript Configuration Setup

## Base tsconfig.json

\`\`\`json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "jsx": "react-jsx",
    
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
\`\`\`

## Path Aliases

### tsconfig.json
\`\`\`json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"]
    }
  }
}
\`\`\`

### vite.config.ts (must match tsconfig)
\`\`\`typescript
import { defineConfig } from 'vite';
import path from 'path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
    },
  },
});
\`\`\`

## ESLint + Prettier Integration

### .eslintrc.cjs
\`\`\`javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'prettier', // MUST be last to override conflicting rules
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint'],
};
\`\`\`

### .prettierrc
\`\`\`json
{
  "semi": true,
  "singleQuote": true,
  "trailingComma": "es5"
}
\`\`\`

**Order matters:** Prettier config must be last in ESLint extends to avoid conflicts.
```

---

## Summary

- **4 skills recommended** (3 CREATE, 1 UPDATE)
- **2 critical severity** (React state, TypeScript config)
- **23 high-struggle sessions** addressed by these skills
- **Estimated impact:** 40-60% reduction in ui/design and config struggle

---

## Next Steps

1. Review skill content above
2. Apply skills with:
   ```bash
   python3 src/apply_skills.py ~/.session-intel/reviews/my-project-analysis-20260204.md
   ```
3. Wait for 10+ new sessions in each domain
4. Check enforcement:
   ```bash
   python3 src/enforcement.py my-project --check-all
   ```

---

*Generated by Session Intelligence v0.1 - https://github.com/jhillock/session-intel*
