#!/usr/bin/env python3
"""
Captain's 5 Picks — The Hills to Die On
========================================
Interactive selection for Captain to choose the 5 core harnesses
that truly resonate with their workflow and become the foundation fleet.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

BULLETIN_ROOT = Path.home() / "harness-ecosystem" / "harness-bulletin-board"
DEFINITIONS_FILE = Path.home() / "harness-ecosystem" / "harnesses" / "harness_definitions.yaml"

def load_definitions():
    import yaml
    with open(DEFINITIONS_FILE) as f:
        return yaml.safe_load(f)

def load_index():
    index_file = BULLETIN_ROOT / "INDEX.json"
    if index_file.exists():
        with open(index_file) as f:
            return json.load(f)
    return {"harnesses": {}}

def save_picks(picks: list):
    """Save Captain's 5 picks."""
    picks_file = BULLETIN_ROOT / "captain_picks.json"
    data = {
        "captain": "KnowUrKnot",
        "selected_at": datetime.now(timezone.utc).isoformat(),
        "picks": picks,
        "reasoning": "These 5 harnesses resonate most with Captain's workflow and will form the core fleet."
    }
    with open(picks_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Captain's picks saved to {picks_file}")

def show_candidates():
    """Show all candidate harnesses with their status."""
    definitions = load_definitions()
    index = load_index()
    
    print("\n" + "="*80)
    print("🎯 CAPTAIN'S 5 PICKS — SELECT THE CORE FLEET")
    print("="*80)
    print("\nThese will be the harnesses we build everything around.")
    print("Choose the 5 that *truly resonate* with your workflow.\n")
    
    all_harnesses = definitions["harnesses"]
    
    # Group by priority
    p1 = [(k, v) for k, v in all_harnesses.items() if v.get("priority") == 1]
    p2 = [(k, v) for k, v in all_harnesses.items() if v.get("priority") == 2]
    
    for group_name, group in [("PRIMARY (Priority 1)", p1), ("CANDIDATES (Priority 2)", p2)]:
        print(f"\n{'─'*80}")
        print(f"  {group_name}")
        print(f"{'─'*80}")
        
        for key, defn in group:
            status = index.get("harnesses", {}).get(key, {}).get("status", "pending")
            extractions = index.get("harnesses", {}).get(key, {}).get("extractions", 0)
            status_icon = {"done": "✅", "reviewed_extracted": "📦", "customizing": "🔧", 
                          "integrating": "🔗", "pending": "⏳", "failed": "❌"}.get(status, "❓")
            
            print(f"\n  {status_icon} [{key}] {defn['name']}")
            print(f"       Repo: {defn['repo']} | Type: {defn['type']} | Category: {defn['category']}")
            print(f"       Status: {status.replace('_', ' ').title()} | Extractions: {extractions}")
            print(f"       {defn['description']}")

def interactive_select():
    """Interactive selection for Captain."""
    definitions = load_definitions()
    all_keys = list(definitions["harnesses"].keys())
    
    print("\n" + "="*80)
    print("Enter the keys of your 5 picks (comma-separated), or 'auto' for suggested:")
    print("Example: hermes,soulforge,openclaw,teleclaw,nanoclaw")
    print("="*80)
    
    # Show suggested based on Captain's known preferences
    suggested = ["hermes", "soulforge", "openclaw", "teleclaw", "nanoclaw"]
    print(f"\nSuggested (based on your ecosystem): {', '.join(suggested)}")
    
    choice = input("\nYour 5 picks: ").strip()
    
    if choice.lower() == "auto":
        picks = suggested
    else:
        picks = [p.strip() for p in choice.split(",")]
    
    # Validate
    valid_picks = []
    for p in picks:
        if p in all_keys:
            valid_picks.append(p)
        else:
            print(f"⚠️  Unknown harness: {p}")
    
    if len(valid_picks) != 5:
        print(f"\n❌ Need exactly 5 valid picks. Got {len(valid_picks)}: {valid_picks}")
        return False
    
    # Confirm
    print(f"\n🎯 YOUR 5 PICKS:")
    for i, p in enumerate(valid_picks, 1):
        defn = definitions["harnesses"][p]
        print(f"  {i}. {defn['name']} ({p}) — {defn['description']}")
    
    confirm = input("\nConfirm? (y/n): ").strip().lower()
    if confirm in ["y", "yes"]:
        save_picks(valid_picks)
        print("\n✅ Captain's 5 picks confirmed! These are the hills you die on.")
        print("The meta-arch prompter will learn from these 5 to design future architectures.")
        return True
    else:
        print("Cancelled.")
        return False

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show_candidates()
    elif len(sys.argv) > 1 and sys.argv[1] == "pick":
        interactive_select()
    else:
        show_candidates()
        print("\nRun with 'pick' to make your selection:")
        print("  python3 captain_picks.py pick")

if __name__ == "__main__":
    main()
