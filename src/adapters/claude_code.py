#!/usr/bin/env python3
"""
Claude Code session adapter for session-intel.
Reads ~/.claude/projects/*/*.jsonl and ingests into sessions.db
"""

import json
import os
import glob
import re
import sqlite3
import sys
from datetime import datetime

DB_PATH = os.path.expanduser("~/.session-intel/sessions.db")
PROJECTS_PATH = os.path.expanduser("~/.claude/projects")

# Signals that Claude is struggling
ERROR_PATTERNS = [
    r'error[:\s]',
    r'failed',
    r'failure',
    r'not found',
    r'doesn\'t exist',
    r'invalid',
    r'cannot\b',
    r'unable to',
]

RETRY_PATTERNS = [
    r'let me try',
    r'let me check',
    r'let me fix',
    r'let me look',
    r'that didn\'t work',
    r'try a different',
    r'try another',
    r'instead,?\s+(let|I\'ll)',
    r'actually,?\s+(the|let|I)',
    r'the issue is',
    r'the problem is',
    r'I see the issue',
]

CORRECTION_PATTERNS = [
    r'^no[,.\s]',
    r'^wrong',
    r'^that\'s wrong',
    r'^actually[,\s]',
    r'you can\'t',
    r'that\'s not',
    r'that won\'t work',
    r'that doesn\'t',
    r'not what I',
    r'I said\b',
    r'I meant\b',
]

DISCOVERY_PATTERNS = [
    r'I see[\s!]',
    r'I found',
    r'the (issue|problem|root cause|reason) (is|was)',
    r'now I understand',
    r'that\'s because',
    r'the fix is',
    r'resolved',
    r'working now',
    r'successfully',
]

# Intent detection from first message + command patterns
INTENT_PATTERNS = {
    "execution": [
        r'implement',
        r'\bbuild\b',
        r'\bdeploy\b',
        r'\bfix\b',
        r'\bcreate\b',
        r'\bupdate\b',
        r'\badd\b',
        r'\bmodify\b',
        r'\brefactor\b',
        r'\bmigrate\b',
        r'resume work',
        r'continue.*work',
        r'executing.?plan',
        r'execute.?plan',
        r'subagent.driven',
        r'<command-message>fix</command-message>',
    ],
    "planning": [
        r'\bplan\b',
        r'brainstorm',
        r'discuss',
        r'what if',
        r'how should',
        r'let\'s think',
        r'strategy',
        r'approach',
        r'writing.?plan',
        r'<command-message>superpowers:brainstorm',
        r'<command-message>superpowers:writing',
    ],
    "debug": [
        r'not working',
        r'broken',
        r'failing',
        r'\berror\b',
        r'bug',
        r'crash',
        r'stuck',
        r'still failing',
        r'why (is|does|isn)',
        r'<command-message>fix',
    ],
    "config": [
        r'\bconnect\b',
        r'\binstall\b',
        r'\bconfigure\b',
        r'set.?up',
        r'api.?key',
        r'auth',
        r'credential',
        r'mcp',
        r'\.env\b',
        r'salesforce-connect',
    ],
    "research": [
        r'research',
        r'figure out',
        r'how does',
        r'what is',
        r'investigate',
        r'explore',
        r'look into',
        r'can we use',
        r'understand',
    ],
    "review": [
        r'\breview\b',
        r'look at',
        r'check.*status',
        r'what.*(state|progress)',
        r'where.*left off',
        r'audit',
        r'CLAUDE\.MD',
        r'CLAUDE\.md',
    ],
}


def detect_intent(first_message: str) -> str:
    """Detect session intent from first user message."""
    if not first_message:
        return "unknown"

    text = first_message.lower().strip()

    # Auto-startup / warmup sessions
    if text in ("warmup", "say hello", "tui", "think high"):
        return "startup"
    if text.startswith("# soul"):
        return "startup"
    if text.startswith("<command-name>/clear"):
        return "continuation"
    if text.startswith("<command-message>resume"):
        return "execution"
    if text.startswith("<command-message>tickets"):
        return "review"
    if text.startswith("<command-message>plugin"):
        return "config"
    if "read the latest session" in text or "read the latest_session" in text:
        return "startup"

    # Score each intent
    scores = {}
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                score += 1
        if score > 0:
            scores[intent] = score

    if not scores:
        return "unknown"

    # Return highest scoring intent
    return max(scores, key=scores.get)


def compute_struggle_score(session: dict) -> float:
    """Compute intent-adjusted struggle score."""
    intent = session.get("intent", "unknown")
    errors = session.get("error_count", 0)
    retries = session.get("retry_count", 0)
    corrections = session.get("correction_count", 0)

    if intent == "execution":
        return errors * 2 + retries * 2 + corrections * 3
    elif intent == "planning":
        return corrections * 3 + retries * 0.25
    elif intent == "debug":
        return retries * 1 + corrections * 3
    elif intent == "config":
        return retries * 2 + errors * 1
    elif intent == "research":
        return corrections * 3  # mostly noise otherwise
    elif intent == "review":
        return corrections * 2 + retries * 0.5
    elif intent == "startup":
        return 0  # warmup sessions aren't meaningful
    elif intent == "continuation":
        # treat like execution — they cleared and kept going
        return errors * 2 + retries * 2 + corrections * 3
    else:
        # unknown — use a balanced formula
        return errors + retries + corrections * 2


DOMAIN_PATTERNS = {
    "ui/design": [
        r'\bcomponent\b', r'\bpage\b', r'\bcss\b', r'\blayout\b', r'\bflexipage\b',
        r'\blwc\b', r'\breact\b', r'\bhtml\b', r'\bmodal\b', r'\bbutton\b',
        r'\bstyle\b', r'\btheme\b', r'\brender\b', r'\bfrontend\b', r'\bui\b',
        r'\btailwind\b', r'\bdesign\b', r'\bresponsive\b', r'\bnavigation\b',
        r'\bsidebar\b', r'\bheader\b', r'\btab\b', r'\bcard\b', r'\bicon\b',
        r'\bcolor\b', r'\bfont\b', r'\bgrid\b', r'\bflex\b', r'\bpadding\b',
        r'\bmargin\b', r'\bwidth\b', r'\bheight\b', r'\btsx\b', r'\bjsx\b',
        r'\bvite\b', r'\bhmr\b', r'\bscreenshot\b', r'\bvisual\b',
    ],
    "data": [
        r'\bsoql\b', r'\bsql\b', r'\bdatabase\b', r'\bmigrat\w*\b', r'\bschema\b',
        r'\brecord\b', r'\bquery\b', r'\.db\b', r'\bdml\b', r'\btable\b',
        r'\bcolumn\b', r'\bfield\b', r'\bsqlite\b', r'\binsert\b', r'\bselect\b',
        r'\bjoin\b', r'\bindex\b', r'\bcrud\b', r'\bdata\s?source\b',
        r'\bsync\b', r'\bingest\b', r'\betl\b', r'\bjson\b', r'\bcsv\b',
        r'\bparse\b', r'\bscrape\b', r'\bfetch\b',
    ],
    "workflow/automation": [
        r'\bflow\b', r'\btrigger\b', r'\bprocess\b', r'\bautomati\w*\b',
        r'\bcron\b', r'\bschedul\w*\b', r'\bemail\s?trigger\b', r'\bworkflow\b',
        r'\brule\b', r'\baction\b', r'\bprompt\b', r'\bscreen\s?flow\b',
        r'\brecord.?trigger\b', r'\bvalidation\b', r'\bapproval\b',
        r'\bnotif\w*\b', r'\balert\b', r'\bhook\b', r'\bwebhook\b',
    ],
    "architecture": [
        r'\brefactor\b', r'\bmodule\b', r'\bpattern\b', r'\bstructure\b',
        r'\bdirectory\b', r'\bextract\b', r'\babstract\w*\b', r'\borganiz\w*\b',
        r'\barchitect\w*\b', r'\bseparati\w*\b', r'\bdecouple\b', r'\blayer\b',
        r'\bplugin\b', r'\bsystem\b', r'\bframework\b', r'\bpattern\b',
    ],
    "api": [
        r'\bendpoint\b', r'\bapi\b', r'\brest\b', r'\broute\b', r'\brequest\b',
        r'\bresponse\b', r'\bintegration\b', r'\bhttp\b', r'\bfetch\b',
        r'\bpost\b', r'\bget\b', r'\bput\b', r'\bwebsocket\b', r'\boauth\b',
        r'\btoken\b', r'\bauth\w*\b',
    ],
    "infra/deploy": [
        r'\bdeploy\b', r'\bci\b', r'\bbuild\b', r'\bpackage\b', r'\bmanifest\b',
        r'\bsandbox\b', r'\bproduction\b', r'\bgit\b', r'\bbranch\b',
        r'\bmerge\b', r'\bcommit\b', r'\brelease\b', r'\bpipeline\b',
        r'\bdocker\b', r'\bserver\b', r'\bhost\b', r'\binstall\b',
    ],
    "config/auth": [
        r'\boauth\b', r'\btoken\b', r'\bapi.?key\b', r'\bcredential\b',
        r'\bmcp\b', r'\benv\b', r'\bsettings\b', r'\bconfig\w*\b',
        r'\bonboard\b', r'\bsetup\b', r'\bpermission\b', r'\baccess\b',
    ],
    "metadata": [
        r'\bdescri\w+\b', r'\blabel\b', r'\bhelp.?text\b', r'\benrich\b',
        r'\bdocument\b', r'\bannotat\w*\b', r'\bobject.?manager\b',
    ],
    "test/qa": [
        r'\btest\b', r'\bcoverage\b', r'\bassert\b', r'\bvalidat\w*\b',
        r'\bverif\w*\b', r'\bqa\b', r'\bregression\b', r'\bsanity\b',
        r'\bapex\s?test\b', r'\bedge\s?case\b',
    ],
}


def detect_domain(messages: list) -> str:
    """Detect session domain from message content across the session.
    Scans all messages, counts keyword hits per domain, returns top domain."""
    domain_scores = {d: 0 for d in DOMAIN_PATTERNS}

    for msg in messages:
        text = msg.get("content_preview", "").lower()
        if not text:
            continue
        for domain, patterns in DOMAIN_PATTERNS.items():
            for p in patterns:
                domain_scores[domain] += len(re.findall(p, text))

    if not any(domain_scores.values()):
        return "general"

    return max(domain_scores, key=domain_scores.get)


def decode_project_name(dirname: str) -> str:
    """Extract project name from Claude Code directory name.
    
    Claude Code sometimes creates dirs like: uuid-username-projectname
    This tries to extract the project name part.
    """
    parts = dirname.split("-")
    
    # If directory has many parts, assume last 1-2 are project name
    if len(parts) > 3:
        # Return last 2 parts (e.g., "my-app" from "abc-def-my-app")
        return "-".join(parts[-2:])
    
    # Otherwise just return as-is
    return dirname


def check_patterns(text: str, patterns: list) -> bool:
    text_lower = text.lower()
    for p in patterns:
        if re.search(p, text_lower):
            return True
    return False


def extract_tool_names(content) -> list:
    """Extract tool names from assistant message content blocks."""
    tools = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "toolCall":
                    tools.append(block.get("name", "unknown"))
                elif block.get("type") == "tool_use":
                    tools.append(block.get("name", "unknown"))
    return tools


def get_text_content(msg: dict) -> str:
    """Extract text from message content (handles string and list formats)."""
    content = msg.get("message", {}).get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return " ".join(parts)
    return str(content)


def process_session(filepath: str, project: str, session_id: str) -> dict:
    """Process a single session JSONL file into structured data."""
    stat = os.stat(filepath)
    created = datetime.fromtimestamp(stat.st_birthtime)
    modified = datetime.fromtimestamp(stat.st_mtime)

    session = {
        "id": f"claude-code:{session_id}",
        "source": "claude-code",
        "project": project,
        "session_id": session_id,
        "first_message": None,
        "message_count": 0,
        "user_message_count": 0,
        "assistant_message_count": 0,
        "tool_call_count": 0,
        "error_count": 0,
        "retry_count": 0,
        "correction_count": 0,
        "unique_tools": set(),
        "size_bytes": stat.st_size,
        "created_at": created.isoformat(),
        "modified_at": modified.isoformat(),
        "duration_minutes": round((modified - created).total_seconds() / 60, 1),
        "raw_path": filepath,
    }

    messages = []
    seq = 0

    try:
        with open(filepath, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = obj.get("type")
                if msg_type not in ("user", "assistant"):
                    continue

                text = get_text_content(obj)
                tool_names = []

                if msg_type == "assistant":
                    raw_content = obj.get("message", {}).get("content", "")
                    tool_names = extract_tool_names(raw_content)

                # Classify message
                has_error = False
                is_retry = False
                is_correction = False
                is_discovery = False

                if msg_type == "assistant":
                    has_error = check_patterns(text, ERROR_PATTERNS)
                    is_retry = check_patterns(text, RETRY_PATTERNS)
                    is_discovery = check_patterns(text, DISCOVERY_PATTERNS)
                elif msg_type == "user":
                    is_correction = check_patterns(text, CORRECTION_PATTERNS)

                # First user message
                if msg_type == "user" and session["first_message"] is None:
                    # Skip command caveats
                    if not text.startswith("<local-command-caveat>"):
                        session["first_message"] = text[:300]

                # Update session aggregates
                session["message_count"] += 1
                if msg_type == "user":
                    session["user_message_count"] += 1
                else:
                    session["assistant_message_count"] += 1
                session["tool_call_count"] += len(tool_names)
                if has_error:
                    session["error_count"] += 1
                if is_retry:
                    session["retry_count"] += 1
                if is_correction:
                    session["correction_count"] += 1
                session["unique_tools"].update(tool_names)

                messages.append({
                    "seq": seq,
                    "role": msg_type,
                    "timestamp": obj.get("timestamp", ""),
                    "content_preview": text[:300],
                    "tool_names": json.dumps(tool_names) if tool_names else None,
                    "tool_call_count": len(tool_names),
                    "has_error": int(has_error),
                    "is_retry": int(is_retry),
                    "is_correction": int(is_correction),
                    "is_discovery": int(is_discovery),
                })
                seq += 1

    except Exception as e:
        print(f"  Error processing {filepath}: {e}", file=sys.stderr)

    session["unique_tools"] = json.dumps(sorted(session["unique_tools"]))
    session["intent"] = detect_intent(session["first_message"] or "")
    session["domain"] = detect_domain(messages)
    session["struggle_score"] = compute_struggle_score(session)
    return session, messages


def ingest(hours: int = None, project_filter: str = None, force: bool = False):
    """Ingest Claude Code sessions into the database."""
    # Init DB
    schema_path = os.path.expanduser("~/.session-intel/schema.sql")
    db = sqlite3.connect(DB_PATH)
    with open(schema_path) as f:
        db.executescript(f.read())

    # Get already-ingested sessions (by raw_path + modified_at)
    existing = {}
    if not force:
        for row in db.execute("SELECT raw_path, modified_at FROM sessions WHERE source = 'claude-code'"):
            existing[row[0]] = row[1]

    cutoff = None
    if hours:
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=hours)

    ingested = 0
    skipped = 0
    updated = 0

    for projdir in glob.glob(f"{PROJECTS_PATH}/*"):
        project = decode_project_name(os.path.basename(projdir))

        if project_filter and project_filter.lower() not in project.lower():
            continue

        for fpath in glob.glob(f"{projdir}/*.jsonl"):
            fname = os.path.basename(fpath)
            if fname.startswith("CLAUDE") or not fname.endswith(".jsonl"):
                continue

            sid = fname.replace(".jsonl", "")
            stat = os.stat(fpath)
            modified = datetime.fromtimestamp(stat.st_mtime)

            if cutoff and modified < cutoff:
                continue

            # Check if already ingested and unchanged
            mod_iso = modified.isoformat()
            if fpath in existing and existing[fpath] == mod_iso:
                skipped += 1
                continue

            # Process
            session, messages = process_session(fpath, project, sid)

            # Upsert session
            is_update = fpath in existing
            db.execute("""
                INSERT OR REPLACE INTO sessions 
                (id, source, project, session_id, first_message, message_count,
                 user_message_count, assistant_message_count, tool_call_count,
                 error_count, retry_count, correction_count, unique_tools,
                 size_bytes, created_at, modified_at, duration_minutes, raw_path,
                 intent, domain, struggle_score, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                session["id"], session["source"], session["project"],
                session["session_id"], session["first_message"],
                session["message_count"], session["user_message_count"],
                session["assistant_message_count"], session["tool_call_count"],
                session["error_count"], session["retry_count"],
                session["correction_count"], session["unique_tools"],
                session["size_bytes"], session["created_at"],
                session["modified_at"], session["duration_minutes"],
                session["raw_path"], session["intent"],
                session["domain"], session["struggle_score"],
            ))

            # Replace messages
            db.execute("DELETE FROM messages WHERE session_id = ?", (session["id"],))
            for msg in messages:
                db.execute("""
                    INSERT INTO messages
                    (session_id, seq, role, timestamp, content_preview, tool_names,
                     tool_call_count, has_error, is_retry, is_correction, is_discovery)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session["id"], msg["seq"], msg["role"], msg["timestamp"],
                    msg["content_preview"], msg["tool_names"], msg["tool_call_count"],
                    msg["has_error"], msg["is_retry"], msg["is_correction"],
                    msg["is_discovery"],
                ))

            if is_update:
                updated += 1
            else:
                ingested += 1

    db.commit()

    # Summary
    total = db.execute("SELECT COUNT(*) FROM sessions WHERE source = 'claude-code'").fetchone()[0]
    total_msgs = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    print(f"Ingested: {ingested} new, {updated} updated, {skipped} unchanged")
    print(f"Total: {total} sessions, {total_msgs} messages")

    db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest Claude Code sessions")
    parser.add_argument("--hours", type=int, help="Only sessions modified in last N hours")
    parser.add_argument("--project", type=str, help="Filter by project name")
    parser.add_argument("--force", action="store_true", help="Re-ingest everything")
    args = parser.parse_args()

    ingest(hours=args.hours, project_filter=args.project, force=args.force)
