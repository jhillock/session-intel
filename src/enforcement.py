#!/usr/bin/env python3
"""
Session Intelligence Enforcement Layer

Tracks whether skills are actually being used and if they reduce struggle.

Workflow:
1. Identify sessions where a skill SHOULD have been used
2. Check if Claude actually matched/used the skill
3. Compare struggle scores before/after skill creation
4. Flag: skill_exists_but_ignored, skill_exists_but_ineffective
5. Generate enforcement recommendations

Usage:
    python enforcement.py <project> <skill-name>
    python enforcement.py my-project --check-all
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/.session-intel/sessions.db")


def get_db():
    return sqlite3.connect(DB_PATH)


def get_skill_metadata(project: str, skill_name: str) -> dict:
    """Get skill creation date and description from SKILL.md."""
    project_paths = {
        "my-project-1": "~/my-project-1/.claude/skills",
        "my-project-2": "~/my-project-2/.claude/skills",
        "my-project-3": "~/my-project-3/skills",
    }
    
    if project not in project_paths:
        return None
    
    skill_path = Path(os.path.expanduser(project_paths[project])) / skill_name / "SKILL.md"
    
    if not skill_path.exists():
        return None
    
    # Get file creation time
    created_at = datetime.fromtimestamp(skill_path.stat().st_birthtime).isoformat()
    
    # Extract description (first 10 lines)
    with open(skill_path) as f:
        header = "".join(f.readlines()[:10])
    
    # Try to extract "Use when:" line
    trigger = None
    for line in header.split("\n"):
        if "use when:" in line.lower() or "trigger:" in line.lower():
            trigger = line.split(":", 1)[1].strip()
            break
    
    return {
        "skill_name": skill_name,
        "created_at": created_at,
        "trigger": trigger,
        "description": header[:200],
    }


def find_matching_sessions(project: str, skill_metadata: dict, domain: str = None) -> list:
    """
    Find sessions that match the skill's domain/trigger.
    Returns sessions both before and after skill creation.
    """
    db = get_db()
    
    # Get all sessions for this project, filtered by domain if provided
    query = """
        SELECT session_id, created_at, struggle_score, intent, domain,
               error_count, retry_count, correction_count, first_message
        FROM sessions
        WHERE project = ?
    """
    params = [project]
    
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    
    query += " ORDER BY created_at"
    
    sessions = db.execute(query, params).fetchall()
    db.close()
    
    skill_created = skill_metadata['created_at']
    
    before = []
    after = []
    
    for sess_id, created, score, intent, dom, errs, retries, corrs, msg in sessions:
        session = {
            "session_id": sess_id[:12],
            "created_at": created,
            "struggle_score": round(score, 1) if score else 0,
            "intent": intent,
            "domain": dom,
            "error_count": errs,
            "retry_count": retries,
            "correction_count": corrs,
            "preview": msg[:100] if msg else "",
        }
        
        if created < skill_created:
            before.append(session)
        else:
            after.append(session)
    
    return before, after


def check_skill_usage(project: str, skill_name: str, session_ids: list) -> dict:
    """
    Check if Claude actually used this skill in the given sessions.
    (Requires reading session JSONLs for tool calls or mentions)
    """
    project_paths = {
        "my-project-1": "~/.claude/projects/my-project-1/sessions",
        "my-project-2": "~/.claude/projects/my-project-2/sessions",
        "my-project-3": "~/.claude/projects/my-project-3/sessions",
    }
    
    if project not in project_paths:
        return {}
    
    sessions_dir = Path(os.path.expanduser(project_paths[project]))
    
    usage = {}
    
    for sess_id in session_ids:
        # Find matching session file
        session_files = list(sessions_dir.glob(f"{sess_id}*.jsonl"))
        if not session_files:
            usage[sess_id] = "not_found"
            continue
        
        # Read JSONL and check for skill mentions
        skill_mentioned = False
        with open(session_files[0]) as f:
            for line in f:
                msg = json.loads(line)
                content = json.dumps(msg).lower()
                if skill_name.lower() in content or skill_name.replace("-", " ").lower() in content:
                    skill_mentioned = True
                    break
        
        usage[sess_id] = "used" if skill_mentioned else "ignored"
    
    return usage


def calculate_effectiveness(before_sessions: list, after_sessions: list) -> dict:
    """
    Compare struggle metrics before/after skill creation.
    """
    if not before_sessions or not after_sessions:
        return {"status": "insufficient_data"}
    
    # Calculate averages
    before_avg = sum(s['struggle_score'] for s in before_sessions) / len(before_sessions)
    after_avg = sum(s['struggle_score'] for s in after_sessions) / len(after_sessions)
    
    # Calculate retry/error rates
    before_retry_rate = sum(s['retry_count'] for s in before_sessions) / len(before_sessions)
    after_retry_rate = sum(s['retry_count'] for s in after_sessions) / len(after_sessions)
    
    before_error_rate = sum(s['error_count'] for s in before_sessions) / len(before_sessions)
    after_error_rate = sum(s['error_count'] for s in after_sessions) / len(after_sessions)
    
    improvement = before_avg - after_avg
    improvement_pct = (improvement / before_avg * 100) if before_avg > 0 else 0
    
    return {
        "status": "effective" if improvement > 0 else "ineffective",
        "before_avg_struggle": round(before_avg, 1),
        "after_avg_struggle": round(after_avg, 1),
        "improvement": round(improvement, 1),
        "improvement_pct": round(improvement_pct, 1),
        "before_sessions": len(before_sessions),
        "after_sessions": len(after_sessions),
        "before_retry_rate": round(before_retry_rate, 1),
        "after_retry_rate": round(after_retry_rate, 1),
        "before_error_rate": round(before_error_rate, 1),
        "after_error_rate": round(after_error_rate, 1),
    }


def generate_enforcement_report(project: str, skill_name: str, domain: str = None):
    """Generate full enforcement report for a skill."""
    
    # Get skill metadata
    skill_meta = get_skill_metadata(project, skill_name)
    if not skill_meta:
        print(f"❌ Skill not found: {skill_name}")
        return
    
    print(f"\n{'='*80}")
    print(f"  Enforcement Report: {project} / {skill_name}")
    print(f"{'='*80}\n")
    
    print(f"**Skill Created:** {skill_meta['created_at']}")
    print(f"**Trigger:** {skill_meta['trigger'] or '(not specified)'}\n")
    
    # Find matching sessions
    before, after = find_matching_sessions(project, skill_meta, domain)
    
    print(f"**Sessions in scope:**")
    print(f"  Before skill: {len(before)} sessions")
    print(f"  After skill:  {len(after)} sessions\n")
    
    if len(after) == 0:
        print("⚠️  No sessions since skill creation. Cannot measure effectiveness.\n")
        return
    
    # Calculate effectiveness
    effectiveness = calculate_effectiveness(before, after)
    
    if effectiveness['status'] == 'insufficient_data':
        print("⚠️  Insufficient data to measure effectiveness.\n")
        return
    
    print(f"**Effectiveness Analysis:**\n")
    print(f"  Status: {effectiveness['status'].upper()}")
    print(f"  Before skill: avg struggle {effectiveness['before_avg_struggle']}")
    print(f"  After skill:  avg struggle {effectiveness['after_avg_struggle']}")
    print(f"  Improvement:  {effectiveness['improvement']} ({effectiveness['improvement_pct']}%)\n")
    
    print(f"**Detailed Metrics:**")
    print(f"  Retry rate:  {effectiveness['before_retry_rate']} → {effectiveness['after_retry_rate']}")
    print(f"  Error rate:  {effectiveness['before_error_rate']} → {effectiveness['after_error_rate']}\n")
    
    # Check if skill was actually used
    if len(after) > 0:
        after_ids = [s['session_id'] for s in after[:10]]  # Check up to 10 recent sessions
        usage = check_skill_usage(project, skill_name, after_ids)
        
        used_count = sum(1 for v in usage.values() if v == "used")
        ignored_count = sum(1 for v in usage.values() if v == "ignored")
        
        print(f"**Skill Usage (last {len(after_ids)} sessions):**")
        print(f"  Used:    {used_count}")
        print(f"  Ignored: {ignored_count}\n")
        
        if ignored_count > used_count:
            print("⚠️  **ENFORCEMENT ISSUE:** Skill exists but is frequently ignored.")
            print("   Recommendations:")
            print("   1. Make trigger conditions more explicit in SKILL.md")
            print("   2. Add skill to CLAUDE.md 'Before you start' checklist")
            print("   3. Update skill description to match actual work patterns\n")
    
    # Show high-struggle sessions after skill creation (skill failed to help)
    high_struggle_after = [s for s in after if s['struggle_score'] > 10]
    if high_struggle_after and effectiveness['status'] == 'ineffective':
        print(f"**High-struggle sessions AFTER skill creation:**\n")
        for s in high_struggle_after[:5]:
            print(f"  [{s['session_id']}] score={s['struggle_score']}, {s['intent']} × {s['domain']}")
            print(f"    {s['preview']}\n")
        
        print("⚠️  **SKILL INEFFECTIVE:** High struggle continues despite skill existence.")
        print("   Recommendations:")
        print("   1. Review sessions above to understand what's still going wrong")
        print("   2. Update skill with missing patterns")
        print("   3. Consider breaking into multiple focused skills\n")


def check_all_skills(project: str):
    """Check enforcement for all skills in a project."""
    project_paths = {
        "my-project-1": "~/my-project-1/.claude/skills",
        "my-project-2": "~/my-project-2/.claude/skills",
        "my-project-3": "~/my-project-3/skills",
    }
    
    if project not in project_paths:
        print(f"Unknown project: {project}")
        return
    
    skills_dir = Path(os.path.expanduser(project_paths[project]))
    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}")
        return
    
    skills = [d.name for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    
    print(f"\n{'='*80}")
    print(f"  Checking {len(skills)} skills in {project}")
    print(f"{'='*80}\n")
    
    for skill_name in sorted(skills):
        generate_enforcement_report(project, skill_name)
        print()


def main():
    parser = argparse.ArgumentParser(description="Check skill enforcement and effectiveness")
    parser.add_argument("project", help="Project name (my-project-1, my-project-2, my-project-3)")
    parser.add_argument("skill", nargs="?", help="Skill name (optional if --check-all)")
    parser.add_argument("--domain", help="Filter to specific domain (ui/design, data, api, etc.)")
    parser.add_argument("--check-all", action="store_true", help="Check all skills in project")
    args = parser.parse_args()
    
    if args.check_all:
        check_all_skills(args.project)
    elif args.skill:
        generate_enforcement_report(args.project, args.skill, args.domain)
    else:
        print("Error: Must specify skill name or use --check-all")
        parser.print_help()


if __name__ == "__main__":
    main()
