# Contributing to Session Intelligence

Thank you for considering contributing! This document outlines how to get started.

## Ways to Contribute

### 1. Bug Reports
Found a bug? Open an issue with:
- Steps to reproduce
- Expected behavior
- Actual behavior
- System info (OS, Python version, Claude Code version)
- Relevant logs or error messages

### 2. Feature Requests
Have an idea? Open an issue with:
- Problem you're trying to solve
- Proposed solution (if you have one)
- Example use case

### 3. Documentation Improvements
Docs unclear? Submit a PR with:
- What was confusing
- Your improved version
- Why it's clearer

### 4. Code Contributions
Want to add a feature or fix a bug? See below.

---

## Development Setup

### Prerequisites
- Python 3.8+
- Claude Code installed and logged in
- Claude Code with session history

### Clone and Install
```bash
git clone https://github.com/jhillock/session-intel.git
cd session-intel
# No pip dependencies required!
```

### Initialize Database
```bash
mkdir -p ~/.session-intel
sqlite3 ~/.session-intel/sessions.db < schema.sql
```

### Verify Claude Code
```bash
claude --version
claude auth status
```

### Test Your Setup
```bash
# Ingest sessions
python3 src/adapters/claude_code.py

# Check database
sqlite3 ~/.session-intel/sessions.db "SELECT COUNT(*) FROM sessions"
```

---

## Making Changes

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes
- Follow existing code style (PEP 8 for Python)
- Add docstrings to new functions
- Update docs if behavior changes
- Add examples if adding new features

### 3. Test Locally
```bash
# Run on your own sessions
python3 src/analyze.py your-project --strategy=all

# Check for errors
python3 -m py_compile src/**/*.py
```

### 4. Commit
```bash
git add .
git commit -m "feat: add X feature"
```

**Commit message format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `refactor:` - Code restructuring (no behavior change)
- `test:` - Adding tests

### 5. Push and Open PR
```bash
git push origin feature/your-feature-name
```

Open a Pull Request on GitHub with:
- Description of changes
- Why the change is needed
- Testing you've done
- Related issues (if any)

---

## Code Style

### Python
- Follow PEP 8
- Use type hints where possible
- Docstrings for all public functions
- Max line length: 100 chars

**Example:**
```python
def extract_signals(project: str, strategy: str) -> List[Dict]:
    """
    Extract struggle signals from session database.
    
    Args:
        project: Project name (e.g., "my-project")
        strategy: Extraction strategy (a/b/c/d/all)
    
    Returns:
        List of signal dicts with session_id, pattern, severity
    """
    # Implementation
```

### Documentation
- Use markdown
- Clear headings
- Code examples with syntax highlighting
- Link to related docs

---

## Areas We Need Help

### High Priority
- [ ] Statistical validation for enforcement (t-tests)
- [ ] Skill templates library
- [ ] Configuration file support
- [ ] Better error handling

### Medium Priority
- [ ] Web UI for reviewing signals
- [ ] Export to Obsidian/Notion
- [ ] OpenRouter API fallback
- [ ] Multi-project comparison

### Low Priority
- [ ] VS Code extension
- [ ] Real-time monitoring
- [ ] Skill marketplace

---

## Review Process

1. **Automated checks** (if we add CI):
   - Python syntax check
   - Lint check
   - Basic smoke tests

2. **Maintainer review:**
   - Code quality
   - Documentation
   - Breaking changes
   - Alignment with project goals

3. **Merge:**
   - Squash and merge (keep history clean)
   - Update CHANGELOG
   - Tag release if needed

---

## Questions?

- **General questions:** Open a discussion
- **Bug reports:** Open an issue
- **Feature requests:** Open an issue (label: enhancement)
- **Security issues:** Email directly (see SECURITY.md)

---

## License

By contributing, you agree your contributions will be licensed under MIT License (same as project).

---

*Thank you for helping make Session Intelligence better!*
