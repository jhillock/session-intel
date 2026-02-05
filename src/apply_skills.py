#!/usr/bin/env python3
"""
Apply skill recommendations from an analysis report.

Reads a generated analysis markdown file and applies the recommended
skill creates/updates.

Usage:
    python apply_skills.py <analysis-report.md> [--dry-run]
"""

import argparse
import json
import re
from pathlib import Path


def extract_recommendations(report_path: Path) -> list:
    """Parse recommendations from markdown report."""
    with open(report_path) as f:
        content = f.read()
    
    # Find recommendations section
    if "## Skill Recommendations" not in content:
        return []
    
    rec_section = content.split("## Skill Recommendations")[1].split("## Raw Signals")[0]
    
    recommendations = []
    
    # Parse each recommendation (format: ### N. [ACTION] skill-name)
    for block in rec_section.split("###")[1:]:
        lines = block.strip().split("\n")
        if not lines:
            continue
        
        # Parse header: "1. [CREATE] skill-name"
        header = lines[0]
        match = re.search(r'\[(\w+)\]\s+(.+)', header)
        if not match:
            continue
        
        action = match.group(1).lower()
        skill_name = match.group(2).strip()
        
        # Extract category, description
        category = None
        description = None
        skill_content = None
        
        for line in lines[1:]:
            if line.startswith("**Category:**"):
                category = line.split("**Category:**")[1].strip()
            elif line.startswith("**Description:**"):
                description = line.split("**Description:**")[1].strip()
        
        # Extract skill content (in code block)
        if "```markdown" in block:
            skill_content = block.split("```markdown")[1].split("```")[0].strip()
        
        if action in ('create', 'update') and skill_content:
            recommendations.append({
                "action": action,
                "skill_name": skill_name,
                "category": category,
                "description": description,
                "skill_content": skill_content,
            })
    
    return recommendations


def apply_recommendation(project: str, rec: dict, dry_run: bool = False):
    """Create or update a skill file."""
    project_paths = {
        "my-project-1": "~/my-project-1/.claude/skills",
        "my-project-2": "~/my-project-2/.claude/skills",
        "my-project-3": "~/my-project-3/skills",
    }
    
    if project not in project_paths:
        print(f"  ❌ Unknown project: {project}")
        return False
    
    skills_dir = Path(os.path.expanduser(project_paths[project]))
    skill_path = skills_dir / rec['skill_name'] / "SKILL.md"
    
    if dry_run:
        print(f"  [DRY RUN] Would {rec['action'].upper()}: {skill_path}")
        return True
    
    # Create directory
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write skill file
    with open(skill_path, 'w') as f:
        f.write(rec['skill_content'])
    
    print(f"  ✓ {rec['action'].upper()}: {skill_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Apply skill recommendations from analysis report")
    parser.add_argument("report", help="Path to analysis report (.md file)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without applying")
    args = parser.parse_args()
    
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"Error: Report not found: {report_path}")
        return
    
    # Extract project name from filename (format: project-analysis-strategy-timestamp.md)
    project = report_path.stem.split("-")[0]
    
    print(f"\n{'='*80}")
    print(f"  Applying Skills: {project}")
    if args.dry_run:
        print(f"  [DRY RUN MODE]")
    print(f"{'='*80}\n")
    
    recommendations = extract_recommendations(report_path)
    
    if not recommendations:
        print("No actionable recommendations found in report.\n")
        return
    
    print(f"Found {len(recommendations)} recommendations:\n")
    
    applied = 0
    for rec in recommendations:
        print(f"[{rec['action'].upper()}] {rec['skill_name']}")
        print(f"  Category: {rec['category']}")
        print(f"  {rec['description']}")
        
        if apply_recommendation(project, rec, dry_run=args.dry_run):
            applied += 1
        
        print()
    
    print(f"{'='*80}")
    if args.dry_run:
        print(f"  {applied} skills would be applied (run without --dry-run to apply)")
    else:
        print(f"  {applied} skills applied successfully!")
        print(f"\n  Next: Check enforcement to see if they reduce struggle:")
        print(f"  python3 ~/.session-intel/enforcement.py {project} --check-all")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
