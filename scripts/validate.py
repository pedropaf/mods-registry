#!/usr/bin/env python3
"""
Validate manifest YAML files against the expected schema.

Usage:
    python scripts/validate.py                              # Validate all
    python scripts/validate.py manifests/checkpoints/flux-dev.yaml  # Validate specific
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

# Reuse validation from build_index
sys.path.insert(0, str(Path(__file__).parent))
from build_index import validate_manifest, check_placeholder_hashes, MANIFESTS_DIR, TYPE_DIR_MAP


def validate_files(files: list[Path]) -> bool:
    """Validate a list of manifest files. Returns True if all valid."""
    all_valid = True

    for filepath in files:
        print(f"Validating: {filepath}")

        try:
            with open(filepath) as f:
                manifest = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"  ERROR: Failed to parse YAML: {e}")
            all_valid = False
            continue

        if manifest is None:
            print(f"  ERROR: Empty manifest file")
            all_valid = False
            continue

        errors = validate_manifest(manifest, filepath)
        warnings = check_placeholder_hashes(manifest)

        if errors:
            for err in errors:
                print(f"  ERROR: {err}")
            all_valid = False
        elif warnings:
            for w in warnings:
                print(f"  WARNING: {w}")
            print(f"  OK (with warnings)")
        else:
            print(f"  OK")

    return all_valid


def find_all_manifests() -> list[Path]:
    """Find all YAML files in manifests/."""
    files = []
    for type_dir in sorted(MANIFESTS_DIR.iterdir()):
        if type_dir.is_dir() and type_dir.name in TYPE_DIR_MAP:
            files.extend(sorted(type_dir.glob("*.yaml")))
    return files


if __name__ == "__main__":
    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:]]
    else:
        files = find_all_manifests()

    if not files:
        print("No manifest files found.")
        sys.exit(1)

    print(f"Validating {len(files)} manifest(s)...\n")
    valid = validate_files(files)

    print(f"\n{'All manifests valid!' if valid else 'Some manifests have errors.'}")
    sys.exit(0 if valid else 1)
