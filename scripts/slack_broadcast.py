#!/usr/bin/env python3
"""
Slack Broadcast for Harness Bulletin Board
===========================================
Sends updates to #biocapt-mesh channel in Inversion Labs workspace.
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime, timezone

# Slack webhook URL - should be set in environment or config
SLACK_WEBHOOK_URL = os.environ.get("SLACK_BIOCAPT_WEBHOOK", "")

BULLETIN_ROOT = Path.home() / "harness-ecosystem" / "harness-bulletin-board"

def load_index() -> dict:
    index_file = BULLETIN_ROOT / "INDEX.json"
    if index_file.exists():
        with open(index_file) as f:
            return json.load(f)
    return {"harnesses": {}}

def format_harness_update(harness_key: str, data: dict) -> dict:
    """Format a harness update for Slack."""
    status_emoji = {
        "pending": "⏳",
        "reviewed_extracted": "📦",
        "customizing": "🔧",
        "integrating": "🔗",
        "done": "✅",
        "failed": "❌",
    }
    
    emoji = status_emoji.get(data.get("status", "pending"), "❓")
    extractions = data.get("extractions", 0)
    categories = data.get("categories", {})
    
    # Top categories
    top_cats = sorted(
        [(k, v) for k, v in categories.items() if v > 0],
        key=lambda x: x[1],
        reverse=True
    )[:3]
    
    cat_text = ", ".join(f"{k.replace('_', ' ')} ({v})" for k, v in top_cats) if top_cats else "none"
    
    return {
        "text": f"{emoji} *HARNESS BULLETIN — {harness_key.upper()}*",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🏛 HARNESS BULLETIN — {harness_key.upper()}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:* {data.get('status', 'unknown').replace('_', ' ').title()}"},
                    {"type": "mrkdwn", "text": f"*Extractions:* {extractions}"},
                    {"type": "mrkdwn", "text": f"*Top Categories:* {cat_text}"},
                    {"type": "mrkdwn", "text": f"*Updated:* {data.get('updated', '')[:19].replace('T', ' ')}"},
                ]
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f"Mesh: Connected • Repo: theinversionlabs/harness-bulletin-board • Captain: KnowUrKnot"}
                ]
            }
        ]
    }

def broadcast_to_slack(message: dict) -> bool:
    """Send message to Slack via webhook."""
    if not SLACK_WEBHOOK_URL:
        print("⚠️  SLACK_BIOCAPT_WEBHOOK not set. Skipping Slack broadcast.")
        return False
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=message, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Slack broadcast failed: {e}")
        return False

def broadcast_harness_update(harness_key: str):
    """Broadcast a single harness update."""
    index = load_index()
    if harness_key not in index.get("harnesses", {}):
        print(f"Harness {harness_key} not found in index")
        return
    
    message = format_harness_update(harness_key, index["harnesses"][harness_key])
    success = broadcast_to_slack(message)
    if success:
        print(f"✅ Slack broadcast sent for {harness_key}")
    else:
        print(f"❌ Slack broadcast failed for {harness_key}")

def broadcast_full_status():
    """Broadcast full bulletin board status."""
    index = load_index()
    harnesses = index.get("harnesses", {})
    
    if not harnesses:
        print("No harnesses to report")
        return
    
    # Summary
    total = len(harnesses)
    done = sum(1 for h in harnesses.values() if h.get("status") == "done")
    in_progress = sum(1 for h in harnesses.values() if h.get("status") in ["reviewed_extracted", "customizing", "integrating"])
    pending = sum(1 for h in harnesses.values() if h.get("status") == "pending")
    
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🏛 HARNESS BULLETIN — FULL STATUS", "emoji": True}
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Total Harnesses:* {total}"},
                {"type": "mrkdwn", "text": f"*Complete:* {done}"},
                {"type": "mrkdwn", "text": f"*In Progress:* {in_progress}"},
                {"type": "mrkdwn", "text": f"*Pending:* {pending}"},
            ]
        },
        {"type": "divider"},
    ]
    
    for key, data in sorted(harnesses.items()):
        status = data.get("status", "unknown")
        extractions = data.get("extractions", 0)
        emoji = {"done": "✅", "reviewed_extracted": "📦", "customizing": "🔧", "integrating": "🔗", "pending": "⏳", "failed": "❌"}.get(status, "❓")
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"{emoji} *{key}* — {status.replace('_', ' ').title()} ({extractions} extractions)"}
        })
    
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Mesh: Connected • {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"}]
    })
    
    message = {"blocks": blocks}
    success = broadcast_to_slack(message)
    if success:
        print("✅ Full status broadcast sent")
    else:
        print("❌ Full status broadcast failed")

def broadcast_learning_gate(gate_name: str, passed: bool, details: str = ""):
    """Broadcast a learning loop gate result."""
    emoji = "✅" if passed else "🛑"
    message = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} LEARNING GATE: {gate_name}", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Result:* {'PASSED' if passed else 'FAILED — LOOP CONTINUES'}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": details}} if details else {"type": "section", "text": {"type": "mrkdwn", "text": "No details provided"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Mesh: Connected • Pipeline: REVIEW→EXTRACT→CUSTOMIZE→INTEGRATE→GATES"}]}]
    }
    success = broadcast_to_slack(message)
    if success:
        print(f"✅ Gate broadcast sent: {gate_name} = {'PASS' if passed else 'FAIL'}")
    else:
        print(f"❌ Gate broadcast failed")

def broadcast_meta_arch_design(design_name: str, description: str):
    """Broadcast a new meta-arch design."""
    message = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "🏛 META-ARCH PROMPTER — NEW DESIGN", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Design:* {design_name}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Description:* {description}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "*Next:* FORGE → SIGMA → MESH → REPO → CAPTAIN NOTIFICATION"}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "Recursive architecture design from absorbed patterns"}]}]
    }
    success = broadcast_to_slack(message)
    if success:
        print(f"✅ Meta-arch design broadcast: {design_name}")
    else:
        print(f"❌ Meta-arch broadcast failed")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 slack_broadcast.py full              # Full status")
        print("  python3 slack_broadcast.py harness <key>     # Single harness")
        print("  python3 slack_broadcast.py gate <name> <pass|fail> [details]")
        print("  python3 slack_broadcast.py meta <design_name> <description>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "full":
        broadcast_full_status()
    elif cmd == "harness" and len(sys.argv) >= 3:
        broadcast_harness_update(sys.argv[2])
    elif cmd == "gate" and len(sys.argv) >= 4:
        gate_name = sys.argv[2]
        passed = sys.argv[3].lower() in ["pass", "true", "1", "yes"]
        details = " ".join(sys.argv[4:]) if len(sys.argv) > 4 else ""
        broadcast_learning_gate(gate_name, passed, details)
    elif cmd == "meta" and len(sys.argv) >= 4:
        broadcast_meta_arch_design(sys.argv[2], " ".join(sys.argv[3:]))
    else:
        print("Invalid command")

if __name__ == "__main__":
    main()
