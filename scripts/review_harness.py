#!/usr/bin/env python3
"""
Harness Review & Extraction Pipeline
=====================================
Reviews a harness repo, extracts components, categorizes them,
and updates the bulletin board.
"""

import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

BULLETIN_ROOT = Path.home() / "harness-ecosystem" / "harness-bulletin-board"
HARNESSES_DIR = BULLETIN_ROOT / "harnesses"
EXTRACTIONS_DIR = BULLETIN_ROOT / "extractions"
DEFINITIONS_FILE = Path.home() / "harness-ecosystem" / "harnesses" / "harness_definitions.yaml"

CATEGORIES = [
    "memory_upgrades",
    "vision_upgrades",
    "research_upgrades",
    "codegen_upgrades",
    "infra_upgrades",
    "cognitive_upgrades",
    "platform_upgrades",
]

CATEGORY_KEYWORDS = {
    "memory_upgrades": ["memory", "vector", "embedding", "knowledge", "graph", "rag", "store", "retrieve", "index"],
    "vision_upgrades": ["vision", "image", "video", "multimodal", "visual", "vlm", "clip", "blip"],
    "research_upgrades": ["research", "search", "crawl", "scrape", "fact", "cite", "bibliography", "academic"],
    "codegen_upgrades": ["codegen", "generate", "template", "refactor", "scaffold", "boilerplate", "ast"],
    "infra_upgrades": ["deploy", "kubernetes", "docker", "orchestrat", "scale", "monitor", "infra", "ci/cd"],
    "cognitive_upgrades": ["reason", "plan", "think", "reflect", "meta", "learn", "improve", "autonomous", "agent"],
    "platform_upgrades": ["telegram", "discord", "slack", "web", "mobile", "api", "bot", "integration"],
}

def load_definitions() -> Dict:
    import yaml
    with open(DEFINITIONS_FILE) as f:
        return yaml.safe_load(f)

def clone_repo(repo_url: str, target_dir: Path) -> bool:
    """Clone a repository."""
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", f"https://github.com/{repo_url}.git", str(target_dir)],
            capture_output=True, text=True, timeout=120
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Clone failed: {e}")
        return False

def analyze_repo(repo_path: Path, extraction_targets: List[str]) -> Dict[str, Any]:
    """Analyze repository structure and extract relevant components."""
    findings = {
        "files_analyzed": 0,
        "categories_found": {cat: [] for cat in CATEGORIES},
        "key_files": [],
        "architecture_notes": [],
        "extraction_candidates": [],
    }
    
    # Walk the repo
    for file_path in repo_path.rglob("*"):
        if file_path.is_file() and not any(part.startswith(".") for part in file_path.parts):
            findings["files_analyzed"] += 1
            
            # Check if matches extraction targets
            rel_path = file_path.relative_to(repo_path)
            matches_target = any(target.replace("*", "") in str(rel_path) for target in extraction_targets)
            
            # Categorize by content
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                content_lower = content.lower()
                
                # Score each category
                for cat, keywords in CATEGORY_KEYWORDS.items():
                    score = sum(1 for kw in keywords if kw in content_lower)
                    if score > 0:
                        findings["categories_found"][cat].append({
                            "file": str(rel_path),
                            "score": score,
                            "matches_target": matches_target,
                            "size": len(content),
                        })
                
                # Key files (large, matches targets, or config)
                if matches_target or len(content) > 5000 or file_path.suffix in [".json", ".yaml", ".yml", ".toml"]:
                    findings["key_files"].append({
                        "path": str(rel_path),
                        "size": len(content),
                        "matches_target": matches_target,
                        "extension": file_path.suffix,
                    })
                    
            except Exception:
                pass
    
    # Sort categories by relevance
    for cat in findings["categories_found"]:
        findings["categories_found"][cat].sort(key=lambda x: x["score"], reverse=True)
        findings["categories_found"][cat] = findings["categories_found"][cat][:20]  # Top 20
    
    # Key files sorted by relevance
    findings["key_files"].sort(key=lambda x: (not x["matches_target"], -x["size"]))
    findings["key_files"] = findings["key_files"][:50]
    
    return findings

def extract_components(repo_path: Path, harness_name: str, findings: Dict) -> Dict[str, List[Dict]]:
    """Extract and categorize components for the bulletin board."""
    extractions = {cat: [] for cat in CATEGORIES}
    
    for cat, files in findings["categories_found"].items():
        for f in files[:10]:  # Top 10 per category
            try:
                full_path = repo_path / f["file"]
                content = full_path.read_text(encoding="utf-8", errors="ignore")
                
                # Create extraction entry
                extraction = {
                    "harness": harness_name,
                    "source_file": f["file"],
                    "category": cat,
                    "relevance_score": f["score"],
                    "content_preview": content[:2000],
                    "extracted_at": datetime.now(timezone.utc).isoformat(),
                    "size": len(content),
                }
                extractions[cat].append(extraction)
            except Exception as e:
                print(f"Failed to extract {f['file']}: {e}")
    
    return extractions

def save_extraction(harness_name: str, extractions: Dict):
    """Save extractions to category folders."""
    for cat, items in extractions.items():
        if not items:
            continue
        cat_dir = EXTRACTIONS_DIR / cat
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        for item in items:
            safe_name = item["source_file"].replace("/", "_").replace(".", "_")
            out_file = cat_dir / f"{harness_name}_{safe_name}.json"
            with open(out_file, "w") as f:
                json.dump(item, f, indent=2)

def generate_report(harness_name: str, definition: Dict, findings: Dict, extractions: Dict) -> str:
    """Generate markdown report for harness."""
    total_extractions = sum(len(v) for v in extractions.values())
    
    report = f"""# Harness Review: {definition['name']}
**Repo:** {definition['repo']} | **Type:** {definition['type']} | **Category:** {definition['category']}
**Priority:** {definition['priority']} | **Reviewed:** {datetime.now(timezone.utc).isoformat()}

## Status
- [x] Review Complete
- [x] Extraction Complete
- [ ] Customization
- [ ] Integration
- [ ] Mesh Broadcast

## Repository Analysis
- **Files Analyzed:** {findings['files_analyzed']}
- **Key Files Identified:** {len(findings['key_files'])}
- **Total Extractions:** {total_extractions}

## Category Breakdown
"""
    for cat in CATEGORIES:
        count = len(extractions.get(cat, []))
        if count > 0:
            top_scores = [e["relevance_score"] for e in extractions[cat][:5]]
            report += f"- **{cat.replace('_', ' ').title()}:** {count} extractions (top scores: {top_scores})\n"
        else:
            report += f"- **{cat.replace('_', ' ').title()}:** 0 extractions\n"
    
    report += "\n## Key Files\n"
    for kf in findings["key_files"][:15]:
        target_marker = " 🎯" if kf["matches_target"] else ""
        report += f"- `{kf['path']}` ({kf['size']} chars){target_marker}\n"
    
    report += f"""
## Extraction Targets (from definition)
{chr(10).join(f'- {t}' for t in definition.get('extraction_targets', []))}

## Architecture Notes
{chr(10).join(f'- {note}' for note in findings.get('architecture_notes', ['None recorded']))}

## Next Steps
1. Customize extracted components for CAPT architecture
2. Run integration tests
3. Broadcast to mesh
4. Update bulletin board
"""
    return report

def update_bulletin_index(harness_name: str, status: str, extractions: Dict):
    """Update the main bulletin board index."""
    index_file = BULLETIN_ROOT / "INDEX.json"
    
    if index_file.exists():
        with open(index_file) as f:
            index = json.load(f)
    else:
        index = {"harnesses": {}, "last_updated": ""}
    
    total = sum(len(v) for v in extractions.values())
    index["harnesses"][harness_name] = {
        "status": status,
        "extractions": total,
        "categories": {cat: len(v) for cat, v in extractions.items()},
        "updated": datetime.now(timezone.utc).isoformat(),
    }
    index["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    with open(index_file, "w") as f:
        json.dump(index, f, indent=2)

def main(harness_key: str):
    definitions = load_definitions()
    
    if harness_key not in definitions["harnesses"]:
        print(f"Unknown harness: {harness_key}")
        return
    
    definition = definitions["harnesses"][harness_key]
    print(f"\n🔍 Reviewing {definition['name']} ({definition['repo']})...")
    
    # Clone to temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / harness_key
        
        if not clone_repo(definition["repo"], repo_path):
            print(f"❌ Failed to clone {definition['repo']}")
            return
        
        print(f"✅ Cloned. Analyzing...")
        findings = analyze_repo(repo_path, definition.get("extraction_targets", []))
        
        print(f"✅ Analyzed {findings['files_analyzed']} files. Extracting...")
        extractions = extract_components(repo_path, harness_key, findings)
        
        print(f"✅ Extracted {sum(len(v) for v in extractions.values())} components. Saving...")
        save_extraction(harness_key, extractions)
        
        # Generate report
        report = generate_report(harness_key, definition, findings, extractions)
        report_path = HARNESSES_DIR / f"{harness_key}.md"
        HARNESSES_DIR.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report)
        
        # Update index
        update_bulletin_index(harness_key, "reviewed_extracted", extractions)
        
        print(f"✅ {definition['name']} review complete!")
        print(f"   Report: {report_path}")
        print(f"   Extractions: {sum(len(v) for v in extractions.values())} total")
        for cat, items in extractions.items():
            if items:
                print(f"     {cat}: {len(items)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 review_harness.py <harness_key>")
        sys.exit(1)
    main(sys.argv[1])
