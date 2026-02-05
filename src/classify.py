#!/usr/bin/env python3
"""
Format classification task for sub-agent execution.
The actual LLM call happens via sessions_spawn in analyze.py.
"""

import json
import sys


def format_classification_task(signals_text: str) -> str:
    """Format signals into a classification task for sub-agent."""
    
    return f"""Analyze these Claude Code session struggle signals and classify the pain points.

For each distinct pain point, provide:
- category: one of (ui/design, data, api, workflow, infra, config, architecture, metadata, test)
- severity: 1-5 (where 5 = critical skill gap, 1 = minor issue)
- description: one sentence describing what goes wrong
- sessions: list of session IDs mentioned in the signals (just the first 7-12 chars)

Return ONLY valid JSON with this exact structure (no explanatory text before or after):
{{
  "pain_points": [
    {{
      "category": "ui/design",
      "severity": 4,
      "description": "Claude doesn't follow COMPONENTS.md patterns",
      "sessions": ["b4a5af7", "645372a"]
    }}
  ],
  "summary": "Brief overview of what the signals show"
}}

SIGNALS:
{signals_text}
"""


def parse_classification_response(response: str) -> dict:
    """Extract JSON from sub-agent response."""
    
    output = response.strip()
    
    # Extract JSON (handle markdown code blocks)
    if "```json" in output:
        output = output.split("```json")[1].split("```")[0].strip()
    elif "```" in output:
        output = output.split("```")[1].split("```")[0].strip()
    
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from sub-agent: {e}\nOutput:\n{output}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python classify.py <signals-file>")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        signals = f.read()
    
    task = format_classification_task(signals)
    print(task)
