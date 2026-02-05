#!/usr/bin/env python3
"""
Generate skill recommendations using Sonnet.

Takes a classified pain point and:
1. Checks if skills exist in the project
2. Decides: CREATE, UPDATE, or NONE
3. Generates SKILL.md content
"""

import json
import os
import sys
from pathlib import Path

# Add current directory to path for llm_helper import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_helper import call_claude


def check_existing_skills(project: str, category: str) -> list[str]:
    """Find existing skills that might address this category."""
    project_paths = {
        "my-project-1": "~/my-project-1/.claude/skills",
        "my-project-2": "~/my-project-2/.claude/skills",
        "my-project-3": "~/my-project-3/skills",
    }
    
    if project not in project_paths:
        return []
    
    skills_dir = Path(os.path.expanduser(project_paths[project]))
    if not skills_dir.exists():
        return []
    
    matches = []
    category_words = category.lower().replace("/", " ").replace("-", " ").split()
    
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            continue
        
        # Read skill content
        with open(skill_file) as f:
            content = f.read().lower()
        
        # Check if any category words appear in the skill
        if any(word in content for word in category_words):
            matches.append(skill_dir.name)
    
    return matches


def generate_skill_recommendation(pain_point: dict, project: str, existing_skills: list[str]) -> dict:
    """Use Sonnet to generate skill recommendation."""
    
    existing_list = "\n".join(f"- {s}" for s in existing_skills) if existing_skills else "(none)"
    
    prompt = f"""You are analyzing a skill gap in the {project} project.

PAIN POINT:
- Category: {pain_point['category']}
- Severity: {pain_point['severity']}/5
- Description: {pain_point['description']}
- Sessions affected: {', '.join(pain_point['sessions'])}

EXISTING SKILLS IN THIS CATEGORY:
{existing_list}

Decide:
1. CREATE - New skill needed (no existing skill covers this)
2. UPDATE - Existing skill needs enhancement
3. NONE - Existing skills should work (enforcement issue, not skill gap)

Return JSON:
{{
  "action": "create|update|none",
  "skill_name": "proposed-skill-name" or "existing-skill-name",
  "reasoning": "why this action (2-3 sentences)",
  "skill_content": "SKILL.md markdown content" or null
}}

For SKILL.md content, use this format:

# Skill Name

**Use when:** [specific trigger conditions - be explicit]

**Problem:** [what goes wrong without this skill]

**Solution:** [concrete steps to fix it]

**Key Patterns:**
- [Pattern 1]
- [Pattern 2]

**Common Mistakes:**
- [What Claude did wrong that this prevents]

**Examples:**
[Reference the session signals if helpful]

Make it actionable and specific. Claude should know exactly when to use this skill.
"""
    
    try:
        output = call_claude(prompt, model="claude-3-5-sonnet-20241022", max_tokens=8192)
        
        # Extract JSON
        if "```json" in output:
            output = output.split("```json")[1].split("```")[0].strip()
        elif "```" in output:
            output = output.split("```")[1].split("```")[0].strip()
        
        return json.loads(output)
        
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from Sonnet: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_skill.py <project> <pain-point-json>")
        sys.exit(1)
    
    project = sys.argv[1]
    pain_point = json.loads(sys.argv[2])
    
    existing = check_existing_skills(project, pain_point['category'])
    result = generate_skill_recommendation(pain_point, project, existing)
    
    print(json.dumps(result, indent=2))
