#!/usr/bin/env python3
"""
Extract signals from session-intel DB using four different strategies.
Each strategy produces a focused dataset for LLM analysis.
"""

import json
import sqlite3
import sys
import os

DB_PATH = os.path.expanduser("~/.session-intel/sessions.db")


def get_db():
    return sqlite3.connect(DB_PATH)


def strategy_a_retry_chains(project: str, min_chain: int = 3) -> str:
    """Strategy A: Find consecutive retry messages and cluster them."""
    db = get_db()
    
    # Get high-struggle sessions for this project
    sessions = db.execute("""
        SELECT id, session_id, struggle_score, intent, domain
        FROM sessions
        WHERE project = ? AND struggle_score > 5
          AND intent IN ('execution', 'continuation', 'debug')
        ORDER BY struggle_score DESC
        LIMIT 10
    """, (project,)).fetchall()
    
    output = []
    for sess_id, orig_id, score, intent, domain in sessions:
        # Get retry messages
        retries = db.execute("""
            SELECT seq, content_preview
            FROM messages
            WHERE session_id = ? AND is_retry = 1 AND role = 'assistant'
            ORDER BY seq
        """, (sess_id,)).fetchall()
        
        if len(retries) < min_chain:
            continue
        
        # Find chains (retries within 5 messages of each other)
        chains = []
        current_chain = [retries[0]]
        for i in range(1, len(retries)):
            if retries[i][0] - retries[i-1][0] <= 5:
                current_chain.append(retries[i])
            else:
                if len(current_chain) >= min_chain:
                    chains.append(current_chain)
                current_chain = [retries[i]]
        if len(current_chain) >= min_chain:
            chains.append(current_chain)
        
        for chain in chains:
            chain_text = "\n".join([f"  [msg {seq}] {preview}" for seq, preview in chain])
            output.append(f"SESSION {orig_id[:12]} (score={score}, intent={intent}, domain={domain})\n"
                         f"Retry chain ({len(chain)} messages):\n{chain_text}\n")
    
    db.close()
    return "\n".join(output) if output else "(no retry chains found)"


def strategy_b_error_resolution(project: str) -> str:
    """Strategy B: Find error→discovery pairs."""
    db = get_db()
    
    sessions = db.execute("""
        SELECT id, session_id, struggle_score, intent, domain
        FROM sessions
        WHERE project = ? AND struggle_score > 5
          AND intent IN ('execution', 'continuation', 'debug')
        ORDER BY struggle_score DESC
        LIMIT 10
    """, (project,)).fetchall()
    
    output = []
    for sess_id, orig_id, score, intent, domain in sessions:
        # Get all flagged messages
        messages = db.execute("""
            SELECT seq, role, content_preview, has_error, is_discovery
            FROM messages
            WHERE session_id = ? AND (has_error = 1 OR is_discovery = 1)
            ORDER BY seq
        """, (sess_id,)).fetchall()
        
        # Find error→discovery pairs (discovery within 10 messages of error)
        pairs = []
        errors = [(seq, preview) for seq, role, preview, err, disc in messages if err]
        discoveries = [(seq, preview) for seq, role, preview, err, disc in messages if disc]
        
        for err_seq, err_text in errors:
            for disc_seq, disc_text in discoveries:
                if 0 < disc_seq - err_seq <= 10:
                    pairs.append((err_seq, err_text, disc_seq, disc_text))
                    break
        
        if pairs:
            pair_text = "\n".join([
                f"  ERROR [msg {es}]: {et[:150]}\n  RESOLUTION [msg {ds}]: {dt[:150]}"
                for es, et, ds, dt in pairs
            ])
            output.append(f"SESSION {orig_id[:12]} (score={score}, intent={intent}, domain={domain})\n{pair_text}\n")
    
    db.close()
    return "\n".join(output) if output else "(no error→resolution pairs found)"


def strategy_c_corrections(project: str) -> str:
    """Strategy C: Find user corrections with context."""
    db = get_db()
    
    sessions = db.execute("""
        SELECT id, session_id, struggle_score, intent, domain
        FROM sessions
        WHERE project = ? AND correction_count > 0
        ORDER BY correction_count DESC
        LIMIT 10
    """, (project,)).fetchall()
    
    output = []
    for sess_id, orig_id, score, intent, domain in sessions:
        corrections = db.execute("""
            SELECT m.seq, m.content_preview,
                   prev.content_preview as prev_msg,
                   next_msg.content_preview as next_msg
            FROM messages m
            LEFT JOIN messages prev ON prev.session_id = m.session_id AND prev.seq = m.seq - 1
            LEFT JOIN messages next_msg ON next_msg.session_id = m.session_id AND next_msg.seq = m.seq + 1
            WHERE m.session_id = ? AND m.is_correction = 1
            ORDER BY m.seq
        """, (sess_id,)).fetchall()
        
        if corrections:
            corr_text = "\n".join([
                f"  CLAUDE SAID [msg {seq-1}]: {(prev or '(none)')[:150]}\n"
                f"  USER CORRECTED [msg {seq}]: {preview[:150]}\n"
                f"  CLAUDE RESPONDED [msg {seq+1}]: {(next_m or '(none)')[:150]}"
                for seq, preview, prev, next_m in corrections
            ])
            output.append(f"SESSION {orig_id[:12]} (score={score}, intent={intent}, domain={domain})\n{corr_text}\n")
    
    db.close()
    return "\n".join(output) if output else "(no corrections found)"


def strategy_d_tool_repetition(project: str, min_repeats: int = 3) -> str:
    """Strategy D: Find repeated tool calls (same tool 3+ times in sequence)."""
    db = get_db()
    
    sessions = db.execute("""
        SELECT id, session_id, struggle_score, intent, domain
        FROM sessions
        WHERE project = ? AND struggle_score > 5
          AND intent IN ('execution', 'continuation', 'debug')
        ORDER BY struggle_score DESC
        LIMIT 10
    """, (project,)).fetchall()
    
    output = []
    for sess_id, orig_id, score, intent, domain in sessions:
        messages = db.execute("""
            SELECT seq, tool_names, content_preview
            FROM messages
            WHERE session_id = ? AND tool_call_count > 0
            ORDER BY seq
        """, (sess_id,)).fetchall()
        
        # Find tool repetition sequences
        repetitions = []
        i = 0
        while i < len(messages):
            seq, tools_json, preview = messages[i]
            if not tools_json:
                i += 1
                continue
            tools = json.loads(tools_json)
            if not tools:
                i += 1
                continue
            
            primary_tool = tools[0]
            chain = [(seq, preview)]
            j = i + 1
            while j < len(messages):
                next_tools = json.loads(messages[j][1]) if messages[j][1] else []
                if next_tools and next_tools[0] == primary_tool:
                    chain.append((messages[j][0], messages[j][2]))
                    j += 1
                elif not next_tools:
                    j += 1
                else:
                    break
            
            if len(chain) >= min_repeats:
                chain_text = "\n".join([f"  [msg {s}] {p[:120]}" for s, p in chain])
                repetitions.append(f"  Tool '{primary_tool}' repeated {len(chain)} times:\n{chain_text}")
            
            i = max(j, i + 1)
        
        if repetitions:
            output.append(f"SESSION {orig_id[:12]} (score={score}, intent={intent}, domain={domain})\n" +
                         "\n".join(repetitions) + "\n")
    
    db.close()
    return "\n".join(output) if output else "(no tool repetitions found)"


if __name__ == "__main__":
    project = sys.argv[1] if len(sys.argv) > 1 else "my-project"
    strategy = sys.argv[2] if len(sys.argv) > 2 else "all"
    
    strategies = {
        "a": ("Strategy A: Retry Chains", strategy_a_retry_chains),
        "b": ("Strategy B: Error→Resolution Pairs", strategy_b_error_resolution),
        "c": ("Strategy C: User Corrections", strategy_c_corrections),
        "d": ("Strategy D: Tool Repetition", strategy_d_tool_repetition),
    }
    
    if strategy == "all":
        for key, (name, func) in strategies.items():
            print(f"\n{'='*80}")
            print(f"  {name}")
            print(f"{'='*80}\n")
            print(func(project))
    else:
        name, func = strategies[strategy]
        print(func(project))
