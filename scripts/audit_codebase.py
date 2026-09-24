import os
import re
from pathlib import Path

ROOT = Path(r"C:\Users\Morice RUGEMARILA\.gemini\antigravity\scratch\my-afrianalyze")

EXCLUDE_DIRS = {".git", ".next", "node_modules", "__pycache__", ".venv", ".pytest_cache", "dist", "build"}

SUSPICIOUS_PATTERNS = [
    r"\bmock\b", r"\bmocks\b", r"\bmocked\b", r"\bfixture\b", r"\bfake\b",
    r"\bsynthetic\b", r"\bsample\b", r"\bdemo\b", r"\bdummy\b", r"\bplaceholder\b",
    r"\bhardcoded\b", r"\bTODO\b", r"\bFIXME\b", r"\bNotImplemented\b",
    r"return\s+\[\s*\]", r"return\s+\{\s*\}", r"return\s+None",
    r"localhost", r"127\.0\.0\.1", r"example\.com"
]

compiled_patterns = {p: re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS}

findings = []

for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        if not (f.endswith(".py") or f.endswith(".ts") or f.endswith(".tsx") or f.endswith(".yaml") or f.endswith(".yml") or f.endswith(".ini")):
            continue
        filepath = Path(root) / f
        rel_path = filepath.relative_to(ROOT)
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
            for idx, line in enumerate(lines, 1):
                for p_str, pat in compiled_patterns.items():
                    if pat.search(line):
                        findings.append({
                            "file": str(rel_path),
                            "line": idx,
                            "pattern": p_str,
                            "snippet": line.strip()[:100]
                        })
        except Exception as e:
            pass

print(f"Total suspicious pattern matches: {len(findings)}")

by_file = {}
for item in findings:
    f = item["file"]
    if f not in by_file:
        by_file[f] = []
    by_file[f].append(item)

sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)
print("\nTop 30 files with suspicious patterns:")
for f, items in sorted_files[:30]:
    print(f"  {f}: {len(items)} matches (e.g. {items[0]['pattern']} on L{items[0]['line']}: {items[0]['snippet']})")

import_regex = re.compile(r"^(?:from\s+([a-zA-Z0-9_\.]+)\s+import|import\s+([a-zA-Z0-9_\.]+))")
all_imports = set()

for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
    for f in files:
        if f.endswith(".py"):
            with open(Path(root) / f, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    m = import_regex.match(line.strip())
                    if m:
                        pkg = (m.group(1) or m.group(2)).split(".")[0]
                        all_imports.add(pkg)

stdlib = {
    "sys", "os", "re", "json", "time", "datetime", "math", "logging", "typing", "collections",
    "dataclasses", "abc", "uuid", "hashlib", "enum", "pathlib", "copy", "itertools", "functools",
    "traceback", "unittest", "shutil", "tempfile", "urllib", "asyncio", "threading", "contextlib", "decimal"
}
local_pkgs = {"packages", "agents", "apps", "connectors", "models", "tests", "scripts", "alembic"}

third_party = all_imports - stdlib - local_pkgs
print(f"\nDiscovered Third-Party Python Imports ({len(third_party)}):")
print(sorted(list(third_party)))
