#!/usr/bin/env python3
"""
LLM helper - calls Claude via local Claude Code CLI.

Uses your existing Claude Pro/Max subscription through Claude Code.
No API costs, no additional setup needed.
"""

import subprocess
import tempfile
import os
from pathlib import Path


def call_claude(
    prompt: str,
    model: str = "sonnet",
    max_tokens: int = 4096,
    timeout: int = 120
) -> str:
    """
    Call Claude Code to generate a response.
    
    Args:
        prompt: Text prompt to send to Claude
        model: Model to use ("haiku" or "sonnet", ignored - uses account default)
        max_tokens: Max response length (ignored by Claude Code)
        timeout: Seconds to wait for response
    
    Returns:
        Claude's response text
    
    Raises:
        RuntimeError: If Claude Code is not installed or fails
        subprocess.TimeoutExpired: If response takes longer than timeout
    """
    
    # Check if Claude Code is available
    try:
        result = subprocess.run(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise RuntimeError(
                "Claude Code not found or not working.\n"
                "Install from: https://www.anthropic.com/claude/code\n"
                "Then verify: claude --version"
            )
    except FileNotFoundError:
        raise RuntimeError(
            "Claude Code not found in PATH.\n"
            "Install from: https://www.anthropic.com/claude/code\n"
            "Then verify: claude --version"
        )
    
    try:
        # Call Claude Code with prompt via stdin
        # This matches what works in the terminal: echo "prompt" | claude --print
        result = subprocess.run(
            ['claude', '--print'],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode != 0:
            raise RuntimeError(
                f"Claude Code failed (exit {result.returncode}):\n"
                f"stderr: {result.stderr}\n"
                f"stdout: {result.stdout}"
            )
        
        # Return response
        response = result.stdout.strip()
        
        if not response:
            raise RuntimeError("Claude Code returned empty response")
        
        return response
        
    except subprocess.TimeoutExpired:
        raise RuntimeError(
            f"Claude Code timed out after {timeout}s.\n"
            "The prompt might be too complex or Claude is rate-limited.\n"
            "Try again in a few minutes."
        )


def check_claude_available() -> bool:
    """
    Check if Claude Code is installed and working.
    
    Returns:
        True if Claude Code is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['claude', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


if __name__ == "__main__":
    # Test the helper
    print("Testing Claude Code integration...")
    
    if not check_claude_available():
        print("❌ Claude Code not available")
        print("Install from: https://www.anthropic.com/claude/code")
        exit(1)
    
    print("✓ Claude Code is installed")
    
    print("\nTesting LLM call...")
    try:
        response = call_claude(
            "Respond with exactly: 'Session Intelligence LLM test passed'",
            timeout=30
        )
        print(f"✓ Response received: {response[:100]}")
        
        if "test passed" in response.lower():
            print("✓ LLM integration working correctly")
        else:
            print("⚠ Unexpected response (but LLM is responding)")
            
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        exit(1)
