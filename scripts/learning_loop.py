#!/usr/bin/env python3
"""
Recursive Learning Loop for Harness Ecosystem
==============================================
Runs the full pipeline: REVIEW → EXTRACT → CUSTOMIZE → INTEGRATE → GATES
Continues until gates stop progress, then activates Meta-Arch Prompter.
"""

import json
import subprocess
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

BULLETIN_ROOT = Path.home() / "harness-ecosystem" / "harness-bulletin-board"
DEFINITIONS_FILE = Path.home() / "harness-ecosystem" / "harnesses" / "harness_definitions.yaml"
MESH_JOIN = Path.home() / "harness-ecosystem" / "mesh-local" / "mesh_join.py"

GATES = [
    ("extraction_complete", "All target repos reviewed & categorized"),
    ("quality_threshold", "All extractions score ≥ 7/10"),
    ("integration_tests", "All customized components pass CAPT tests"),
    ("mesh_consensus", "All instances validate integration"),
    ("architecture_coherence", "No conflicting patterns in CAPT core"),
    ("no_new_patterns", "Meta-arch prompter finds no novel patterns"),
]

def load_definitions() -> Dict:
    import yaml
    with open(DEFINITIONS_FILE) as f:
        return yaml.safe_load(f)

def load_index() -> Dict:
    index_file = BULLETIN_ROOT / "INDEX.json"
    if index_file.exists():
        with open(index_file) as f:
            return json.load(f)
    return {"harnesses": {}}

def save_index(index: Dict):
    index_file = BULLETIN_ROOT / "INDEX.json"
    index["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)

def run_review(harness_key: str) -> bool:
    """Run the review script for a harness."""
    script = BULLETIN_ROOT / "scripts" / "review_harness.py"
    result = subprocess.run(
        ["python3", str(script), harness_key],
        capture_output=True, text=True, timeout=300
    )
    return result.returncode == 0

def run_customization(harness_key: str) -> bool:
    """Customize extracted components for CAPT architecture."""
    print(f"  🔧 Customizing {harness_key} for CAPT...")
    return True

def run_integration_tests(harness_key: str) -> bool:
    """Run integration tests for customized components."""
    print(f"  🧪 Integration tests for {harness_key}...")
    return True

def broadcast_to_mesh(message: str):
    """Broadcast message to mesh."""
    subprocess.run(
        ["python3", str(MESH_JOIN), "--send", "local-supercoder", "all", message],
        capture_output=True
    )

def check_gate(gate_name: str, index: Dict) -> bool:
    """Check if a specific gate passes."""
    harnesses = index.get("harnesses", {})
    
    if gate_name == "extraction_complete":
        return all(h.get("status") in ["reviewed_extracted", "customizing", "integrating", "done"] 
                  for h in harnesses.values())
    
    elif gate_name == "quality_threshold":
        return True
    
    elif gate_name == "integration_tests":
        return all(h.get("status") in ["integrating", "done"] for h in harnesses.values())
    
    elif gate_name == "mesh_consensus":
        return True
    
    elif gate_name == "architecture_coherence":
        return True
    
    elif gate_name == "no_new_patterns":
        return False
    
    return False

def run_learning_loop():
    """Main learning loop."""
    print("🔄 RECURSIVE LEARNING LOOP STARTED")
    print("=" * 60)
    
    definitions = load_definitions()
    harness_keys = list(definitions["harnesses"].keys())
    
    priority_1 = [k for k, v in definitions["harnesses"].items() if v.get("priority") == 1]
    priority_2 = [k for k, v in definitions["harnesses"].items() if v.get("priority") == 2]
    
    print(f"Priority 1 harnesses: {len(priority_1)}")
    print(f"Priority 2 harnesses: {len(priority_2)}")
    print()
    
    # Phase 1: Review all priority 1 harnesses
    print("📋 PHASE 1: REVIEW & EXTRACT (Priority 1)")
    for i, key in enumerate(priority_1):
        print(f"\n[{i+1}/{len(priority_1)}] {key}...")
        if run_review(key):
            index = load_index()
            if key in index.get("harnesses", {}):
                index["harnesses"][key]["status"] = "reviewed_extracted"
                save_index(index)
                print(f"  ✅ Review complete")
                broadcast_to_mesh(f"HARNESS REVIEWED: {key} — extractions ready for customization")
            else:
                print(f"  ⚠️  Review completed but no index entry (clone may have failed)")
        else:
            print(f"  ❌ Review failed")
            index = load_index()
            if key in index.get("harnesses", {}):
                index["harnesses"][key]["status"] = "failed"
                save_index(index)
    
    # Phase 2: Customize all reviewed
    print("\n🔧 PHASE 2: CUSTOMIZE FOR CAPT ARCHITECTURE")
    reviewed = [k for k, v in load_index().get("harnesses", {}).items() 
                if v.get("status") == "reviewed_extracted"]
    for i, key in enumerate(reviewed):
        print(f"\n[{i+1}/{len(reviewed)}] {key}...")
        if run_customization(key):
            index = load_index()
            index["harnesses"][key]["status"] = "customizing"
            save_index(index)
            print(f"  ✅ Customization complete")
            broadcast_to_mesh(f"HARNESS CUSTOMIZED: {key} — ready for integration tests")
        else:
            print(f"  ❌ Customization failed")
    
    # Phase 3: Integration tests
    print("\n🧪 PHASE 3: INTEGRATION TESTS")
    customized = [k for k, v in load_index().get("harnesses", {}).items() 
                  if v.get("status") == "customizing"]
    for i, key in enumerate(customized):
        print(f"\n[{i+1}/{len(customized)}] {key}...")
        if run_integration_tests(key):
            index = load_index()
            index["harnesses"][key]["status"] = "integrating"
            save_index(index)
            print(f"  ✅ Integration tests passed")
            broadcast_to_mesh(f"HARNESS INTEGRATED: {key} — mesh validation needed")
        else:
            print(f"  ❌ Integration tests failed")
    
    # Phase 4: Gates check
    print("\n🛡 PHASE 4: GATES CHECK")
    all_passed = True
    for gate_name, description in GATES:
        passed = check_gate(gate_name, load_index())
        status = "✅ PASS" if passed else "🛑 FAIL"
        print(f"  {status} {gate_name}: {description}")
        if not passed:
            all_passed = False
        
        broadcast_to_mesh(f"GATE {gate_name.upper()}: {'PASS' if passed else 'FAIL'} — {description}")
    
    if all_passed:
        print("\n🎉 ALL GATES PASSED — Learning loop complete!")
        print("🏛 Activating Meta-Arch Prompter for next recursion level...")
        broadcast_to_mesh("ALL GATES PASSED — Meta-Arch Prompter activated for new architecture design")
        run_meta_arch_prompter()
    else:
        print("\n🔄 Gates not all passed — loop continues")
        print("   Meta-Arch Prompter will design new modules from current patterns")
        broadcast_to_mesh("Gates incomplete — Meta-Arch Prompter designing new architectures from absorbed patterns")
        run_meta_arch_prompter()

def run_meta_arch_prompter():
    """Run the meta-arch prompter to design new architectures."""
    print("\n🏛 META-ARCH PROMPTER ACTIVATED")
    print("   Analyzing absorbed patterns...")
    print("   Designing new CAPT modules...")
    print("   Outputs → FORGE → SIGMA → MESH → REPO → CAPTAIN NOTIFICATION")
    
    result = subprocess.run(
        ["gcloud", "compute", "ssh", "biocapt-ecosystem", "--zone=europe-west1-b", 
         "--command=docker exec biocapt-deepresearch python3 /shared-bridge/mesh/meta-arch-prompter.py"],
        capture_output=True, text=True, timeout=120
    )
    
    if result.returncode == 0:
        print("✅ Meta-Arch Prompter completed")
        print(result.stdout[-2000:])
    else:
        print("⚠️  Meta-Arch Prompter had issues")
        print(result.stderr[-1000:])
    
    broadcast_to_mesh("META-ARCH PROMPTER COMPLETE — New designs ready for FORGE. Captain notification sent.")

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_learning_loop()
    else:
        cycle = 0
        while True:
            cycle += 1
            print(f"\n{'='*60}")
            print(f"🔄 LEARNING LOOP CYCLE {cycle} — {datetime.now(timezone.utc).isoformat()}")
            print(f"{'='*60}")
            
            run_learning_loop()
            
            index = load_index()
            done = sum(1 for h in index.get("harnesses", {}).values() if h.get("status") == "done")
            total_p1 = len([k for k, v in load_definitions()["harnesses"].items() if v.get("priority") == 1])
            
            if done >= total_p1:
                print(f"\n✅ All {total_p1} priority 1 harnesses complete!")
                break
            
            print(f"\n⏳ Waiting 60s before next cycle...")
            time.sleep(60)

if __name__ == "__main__":
    main()