#!/usr/bin/env python3
"""
Harness Ecosystem Orchestrator — Master Control
================================================
Single entry point for the entire harness ecosystem pipeline.
"""

import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path.home() / "harness-ecosystem" / "harness-bulletin-board" / "scripts"
MESH_JOIN = Path.home() / "harness-ecosystem" / "mesh-local" / "mesh_join.py"

def run_script(script_name: str, args: list = None):
    """Run a script from the scripts directory."""
    script_path = SCRIPTS_DIR / script_name
    cmd = ["python3", str(script_path)] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr and result.returncode != 0:
        print(result.stderr, file=sys.stderr)
    return result.returncode == 0

def broadcast_mesh(message: str):
    """Broadcast to mesh."""
    subprocess.run(
        ["python3", str(MESH_JOIN), "--send", "local-supercoder", "all", message],
        capture_output=True
    )

def main():
    if len(sys.argv) < 2:
        print("""
🏛 HARNESS ECOSYSTEM ORCHESTRATOR
==================================

Usage:
  python3 orchestrator.py review <harness_key>     # Review a single harness
  python3 orchestrator.py review-all               # Review all priority 1 harnesses
  python3 orchestrator.py loop                     # Run full learning loop
  python3 orchestrator.py loop-once                # Run one learning loop cycle
  python3 orchestrator.py picks [show|pick]        # Captain's 5 picks
  python3 orchestrator.py slack [full|harness|gate|meta]  # Slack broadcast
  python3 orchestrator.py github                   # Setup GitHub repo
  python3 orchestrator.py mesh [poll|status]       # Mesh operations
  python3 orchestrator.py status                   # Full status report
  python3 orchestrator.py meta-arch                # Run meta-arch prompter
        """)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "review" and len(sys.argv) >= 3:
        harness_key = sys.argv[2]
        print(f"🔍 Reviewing {harness_key}...")
        if run_script("review_harness.py", [harness_key]):
            broadcast_mesh(f"HARNESS REVIEWED: {harness_key} — extractions ready for customization")
            print("✅ Review complete")
        else:
            print("❌ Review failed")
    
    elif cmd == "review-all":
        print("🔍 Reviewing ALL priority 1 harnesses...")
        # Load definitions to get priority 1
        import yaml
        with open(Path.home() / "harness-ecosystem" / "harnesses" / "harness_definitions.yaml") as f:
            defs = yaml.safe_load(f)
        
        p1 = [k for k, v in defs["harnesses"].items() if v.get("priority") == 1]
        for i, key in enumerate(p1, 1):
            print(f"\n[{i}/{len(p1)}] {key}...")
            if run_script("review_harness.py", [key]):
                broadcast_mesh(f"HARNESS REVIEWED: {key}")
                print(f"  ✅ {key} complete")
            else:
                print(f"  ❌ {key} failed")
    
    elif cmd == "loop":
        print("🔄 Starting continuous learning loop...")
        run_script("learning_loop.py")
    
    elif cmd == "loop-once":
        print("🔄 Running single learning loop cycle...")
        run_script("learning_loop.py", ["--once"])
    
    elif cmd == "picks":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else "show"
        run_script("captain_picks.py", [subcmd])
    
    elif cmd == "slack":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else "full"
        if subcmd == "full":
            run_script("slack_broadcast.py", ["full"])
        elif subcmd == "harness" and len(sys.argv) > 3:
            run_script("slack_broadcast.py", ["harness", sys.argv[3]])
        elif subcmd == "gate" and len(sys.argv) > 4:
            run_script("slack_broadcast.py", ["gate", sys.argv[3], sys.argv[4]] + sys.argv[5:])
        elif subcmd == "meta" and len(sys.argv) > 3:
            run_script("slack_broadcast.py", ["meta", sys.argv[3], " ".join(sys.argv[4:])])
    
    elif cmd == "github":
        print("🚀 Setting up GitHub repository...")
        run_script("setup_github_repo.py")
    
    elif cmd == "mesh":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else "poll"
        if subcmd == "poll":
            subprocess.run(["python3", str(MESH_JOIN), "--poll"])
        elif subcmd == "status":
            subprocess.run(["python3", str(MESH_JOIN), "--poll"])
            # Also check GCP mesh
            subprocess.run([
                "gcloud", "compute", "ssh", "biocapt-ecosystem", "--zone=europe-west1-b",
                "--command=docker exec biocapt-deepresearch python3 /shared-bridge/mesh/mesh_join.py --poll"
            ])
    
    elif cmd == "status":
        # Full status report
        print("📊 HARNESS ECOSYSTEM STATUS")
        print("=" * 60)
        
        # Mesh status
        print("\n🌐 MESH STATUS:")
        subprocess.run(["python3", str(MESH_JOIN), "--poll"])
        
        # Bulletin index
        import json
        index_file = Path.home() / "harness-ecosystem" / "harness-bulletin-board" / "INDEX.json"
        if index_file.exists():
            with open(index_file) as f:
                index = json.load(f)
            print(f"\n📋 BULLETIN BOARD:")
            print(f"   Last updated: {index.get('last_updated', 'never')}")
            for key, data in sorted(index.get("harnesses", {}).items()):
                status = data.get("status", "unknown")
                extractions = data.get("extractions", 0)
                print(f"   {key}: {status} ({extractions} extractions)")
        else:
            print("\n📋 BULLETIN BOARD: Not initialized")
        
        # Captain's picks
        picks_file = Path.home() / "harness-ecosystem" / "harness-bulletin-board" / "captain_picks.json"
        if picks_file.exists():
            with open(picks_file) as f:
                picks = json.load(f)
            print(f"\n🎯 CAPTAIN'S 5 PICKS: {', '.join(picks['picks'])}")
        else:
            print("\n🎯 CAPTAIN'S 5 PICKS: Not selected yet")
    
    elif cmd == "meta-arch":
        print("🏛 Running Meta-Arch Prompter on GCP...")
        result = subprocess.run([
            "gcloud", "compute", "ssh", "biocapt-ecosystem", "--zone=europe-west1-b",
            "--command=docker exec biocapt-deepresearch python3 /shared-bridge/mesh/meta-arch-prompter.py"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Meta-Arch Prompter completed")
            print(result.stdout)
        else:
            print("❌ Meta-Arch Prompter failed")
            print(result.stderr)
        
        broadcast_mesh("META-ARCH PROMPTER COMPLETE — New designs ready for FORGE")
    
    else:
        print(f"Unknown command: {cmd}")

if __name__ == "__main__":
    main()
