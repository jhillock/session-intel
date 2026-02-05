#!/usr/bin/env python3
"""
Session Intelligence Analysis Layer - Uses Claude Code CLI

Full workflow:
1. Extract signals from session DB  
2. Classify with Claude Code CLI (via llm_helper)
3. Generate skill recommendations with Claude Code CLI
4. Save to review file

Usage:
    python analyze.py <project> [--strategy=<a|b|c|d|all>]
"""

import argparse
import json
import os
import requests
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/.session-intel/sessions.db")
STRATEGIES_DIR = os.path.expanduser("~/.session-intel/src/strategies")
REVIEW_DIR = os.path.expanduser("~/.session-intel/reviews")

# Import LLM helper (uses Claude Code CLI)
sys.path.insert(0, os.path.dirname(__file__))
from llm_helper import call_claude


def get_db():
    return sqlite3.connect(DB_PATH)


def extract_signals(project: str, strategy: str) -> str:
    """Run extraction strategy and return signal text."""
    result = subprocess.run(
        ["python3", f"{STRATEGIES_DIR}/extract.py", project, strategy],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Extract failed: {result.stderr}")
    return result.stdout


def get_project_stats(project: str) -> dict:
    """Get basic stats about this project's sessions."""
    db = get_db()
    stats = {}
    
    stats['total_sessions'] = db.execute(
        "SELECT COUNT(*) FROM sessions WHERE project = ?", (project,)
    ).fetchone()[0]
    
    stats['high_struggle'] = db.execute(
        "SELECT COUNT(*) FROM sessions WHERE project = ? AND struggle_score > 5",
        (project,)
    ).fetchone()[0]
    
    intent_counts = db.execute("""
        SELECT intent, COUNT(*), AVG(struggle_score)
        FROM sessions
        WHERE project = ? AND intent IS NOT NULL
        GROUP BY intent
        ORDER BY AVG(struggle_score) DESC
    """, (project,)).fetchall()
    stats['by_intent'] = [{"intent": i, "count": c, "avg_struggle": round(s, 1)} for i, c, s in intent_counts]
    
    domain_counts = db.execute("""
        SELECT domain, COUNT(*), AVG(struggle_score)
        FROM sessions
        WHERE project = ? AND domain IS NOT NULL
        GROUP BY domain
        ORDER BY AVG(struggle_score) DESC
    """, (project,)).fetchall()
    stats['by_domain'] = [{"domain": d, "count": c, "avg_struggle": round(s, 1)} for d, c, s in domain_counts]
    
    top_struggle = db.execute("""
        SELECT session_id, intent, domain, struggle_score, first_message
        FROM sessions
        WHERE project = ?
        ORDER BY struggle_score DESC
        LIMIT 10
    """, (project,)).fetchall()
    stats['top_struggle'] = [{
        "session_id": s[:12],
        "intent": i,
        "domain": d,
        "score": round(sc, 1),
        "preview": msg[:100] if msg else "(no message)"
    } for s, i, d, sc, msg in top_struggle]
    
    db.close()
    return stats


def classify_signals_via_claude(signals: str) -> dict:
    """Use Claude Code CLI to classify signals."""
    
    prompt = f"""Analyze these Claude Code session struggle signals and classify the pain points.

For each distinct pain point, provide:
- category: one of (ui/design, data, api, workflow, infra, config, architecture, metadata, test)
- severity: 1-5 (where 5 = critical skill gap, 1 = minor issue)
- description: one sentence describing what goes wrong
- sessions: list of session IDs mentioned in the signals (just first 7-12 chars)

Return ONLY valid JSON with this exact structure (no explanatory text before or after):
{{
  "pain_points": [
    {{
      "category": "workflow",
      "severity": 4,
      "description": "Claude doesn't respect branch isolation",
      "sessions": ["766aaac"]
    }}
  ],
  "summary": "Brief overview of what the signals show"
}}

SIGNALS:
{signals[:8000]}
"""
    
    # Call Claude Code CLI
    response_text = call_claude(prompt, timeout=120)
    
    # Extract JSON from response (handle markdown code blocks)
    output = response_text
    if "```json" in output:
        output = output.split("```json")[1].split("```")[0].strip()
    elif "```" in output:
        output = output.split("```")[1].split("```")[0].strip()
    
    return json.loads(output)


def generate_skill_recommendation_via_claude(project: str, pain_point: dict) -> dict:
    """Use Claude Code CLI to generate skill recommendation."""
    
    # Check if skill already exists
    skills_dir = Path.home() / project / ".claude" / "skills"
    existing_skills = []
    if skills_dir.exists():
        existing_skills = [f.stem for f in skills_dir.glob("**/SKILL.md")]
    
    task = f"""Based on this pain point, recommend a skill for {project}.

PAIN POINT:
- Category: {pain_point['category']}
- Severity: {pain_point['severity']}/5
- Description: {pain_point['description']}
- Affected sessions: {pain_point['sessions']}

EXISTING SKILLS:
{chr(10).join(f"- {s}" for s in existing_skills) if existing_skills else "(none)"}

Return ONLY valid JSON:
{{
  "action": "create|update|none",
  "skill_name": "skill-folder-name",
  "reasoning": "why this skill is needed or why existing skill should be updated",
  "skill_content": "full SKILL.md content (if action=create/update, else null)"
}}

If creating/updating, generate a complete SKILL.md with:
- Frontmatter (name, description)
- Clear trigger conditions
- Concrete examples from the pain point
- Anti-patterns to avoid
"""
    
    # Call Claude Code CLI
    response_text = call_claude(task, timeout=180)
    
    # Extract JSON from response
    output = response_text
    if "```json" in output:
        json_start = output.find("```json") + 7
        json_end = output.find("```", json_start)
        output = output[json_start:json_end].strip()
    elif "```" in output:
        json_start = output.find("```") + 3
        json_end = output.find("```", json_start)
        output = output[json_start:json_end].strip()
    
    return json.loads(output)


def save_analysis_report(project: str, strategy: str, stats: dict, signals: str, 
                         classification: dict, recommendations: list) -> Path:
    """Save full analysis report."""
    Path(REVIEW_DIR).mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{project}-analysis-{strategy}-{timestamp}.md"
    filepath = Path(REVIEW_DIR) / filename
    
    # Build recommendations section
    rec_text = ""
    for i, rec in enumerate(recommendations, 1):
        action = rec['action'].upper()
        rec_text += f"\n### {i}. [{action}] {rec['skill_name']}\n\n"
        rec_text += f"**Category:** {rec['pain_point']['category']}\n"
        rec_text += f"**Severity:** {rec['pain_point']['severity']}/5\n"
        rec_text += f"**Description:** {rec['pain_point']['description']}\n\n"
        rec_text += f"**Reasoning:** {rec['reasoning']}\n\n"
        
        if rec.get('skill_content'):
            rec_text += f"**Proposed SKILL.md:**\n\n```markdown\n{rec['skill_content']}\n```\n\n"
    
    content = f"""# Session Intelligence Analysis: {project}

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Strategy:** {strategy}

---

## Project Stats

- **Total sessions:** {stats['total_sessions']}
- **High struggle (>5):** {stats['high_struggle']}

### By Intent
{chr(10).join(f"- {row['intent']}: {row['count']} sessions, avg struggle {row['avg_struggle']}" for row in stats['by_intent'])}

### By Domain
{chr(10).join(f"- {row['domain']}: {row['count']} sessions, avg struggle {row['avg_struggle']}" for row in stats['by_domain'])}

---

## Classification Summary

{classification.get('summary', '(no summary)')}

**Pain Points Found:** {len(classification.get('pain_points', []))}

---

## Skill Recommendations

{rec_text if rec_text else '(no recommendations generated)'}

---

## Raw Signals

{signals}

---

## Next Steps

**To apply recommendations:**

```bash
# Review recommendations above, then run:
python3 ~/.session-intel/apply_skills.py {filepath}

# Or manually create/update skills in:
ls ~/{project}/.claude/skills/
```

**To check enforcement after creating skills:**

```bash
python3 ~/.session-intel/enforcement.py {project} <skill-name>
```
"""
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    return filepath


def main():
    parser = argparse.ArgumentParser(description="Analyze sessions and generate skill recommendations")
    parser.add_argument("project", help="Project name (my-project-1, my-project-2, my-project-3)")
    parser.add_argument("--strategy", default="all", choices=["a", "b", "c", "d", "all"],
                       help="Extraction strategy (default: all)")
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f"  Session Intelligence Analysis: {args.project}")
    print(f"  Strategy: {args.strategy}")
    print(f"{'='*80}\n")
    
    # Step 1: Get stats
    print("Step 1: Loading project stats...")
    stats = get_project_stats(args.project)
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  High struggle: {stats['high_struggle']}\n")
    
    if stats['high_struggle'] == 0:
        print("✓ No high-struggle sessions found. All clear!\n")
        return
    
    # Step 2: Extract signals
    print(f"Step 2: Extracting signals (strategy: {args.strategy})...")
    signals = extract_signals(args.project, args.strategy)
    
    if "(no " in signals and signals.count("\n") < 5:
        print("  No significant signals found.\n")
        return
    
    signal_count = signals.count("SESSION")
    print(f"  Found {signal_count} signal clusters\n")
    
    # Step 3: Classify with Haiku (via Gateway)
    print("Step 3: Classifying pain points (Haiku via Gateway)...")
    
    try:
        classification = classify_signals_via_claude(signals)
        print(f"  {classification.get('summary', '(no summary)')}")
        print(f"  Pain points: {len(classification.get('pain_points', []))}\n")
    except Exception as e:
        print(f"  ❌ Classification failed: {e}\n")
        print("  Saving raw signals for manual review...\n")
        classification = {"pain_points": [], "summary": f"Classification failed: {e}"}
    
    # Step 4: Generate recommendations with Sonnet (via Gateway)
    recommendations = []
    if classification.get('pain_points'):
        print("Step 4: Generating skill recommendations (Sonnet via Gateway)...")
        for pain_point in classification['pain_points']:
            try:
                rec = generate_skill_recommendation_via_claude(args.project, pain_point)
                rec['pain_point'] = pain_point
                recommendations.append(rec)
                print(f"  [{rec['action'].upper()}] {rec['skill_name']}")
            except Exception as e:
                print(f"  ⚠️  Failed for {pain_point['category']}: {e}")
        print()
    
    # Step 5: Save report
    filepath = save_analysis_report(args.project, args.strategy, stats, signals,
                                   classification, recommendations)
    
    print(f"\n{'='*80}")
    print(f"  Analysis complete!")
    print(f"  Report: {filepath}")
    print(f"{'='*80}\n")
    
    # Show summary
    if recommendations:
        print("Recommendations:\n")
        for rec in recommendations:
            action = rec['action'].upper()
            print(f"  [{action}] {rec['skill_name']}")
            print(f"    → {rec['reasoning'][:100]}...\n")
        
        print(f"Review the full report:\n")
        print(f"  cat {filepath}\n")


if __name__ == "__main__":
    main()
