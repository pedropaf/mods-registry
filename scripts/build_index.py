#!/usr/bin/env python3
"""
Build index.json from all YAML manifests in the manifests/ directory.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --output dist/index.json
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


MANIFESTS_DIR = Path(__file__).parent.parent / "manifests"
DEFAULT_OUTPUT = Path(__file__).parent.parent / "index.json"

VALID_TYPES = {
    "checkpoint",
    "diffusion_model",
    "lora",
    "vae",
    "text_encoder",
    "controlnet",
    "upscaler",
    "embedding",
    "ipadapter",
    "segmentation",
    "recipe",
}

TYPE_DIR_MAP = {
    "checkpoints": "checkpoint",
    "diffusion_models": "diffusion_model",
    "loras": "lora",
    "vae": "vae",
    "text_encoders": "text_encoder",
    "controlnet": "controlnet",
    "upscalers": "upscaler",
    "embeddings": "embedding",
    "ipadapters": "ipadapter",
    "segmentation": "segmentation",
    "recipes": "recipe",
}

VALID_CATEGORIES = {
    "general",
    "style",
    "character",
    "concept",
    "product",
    "technique",
    "acceleration",
    "editing",
    "upscaling",
    "segmentation",
    "controlnet",
}


def validate_manifest(manifest: dict, filepath: Path) -> list[str]:
    """Validate a single manifest. Returns list of errors."""
    errors = []
    filename_id = filepath.stem

    # Required fields
    for field in ["id", "name", "type"]:
        if field not in manifest:
            errors.append(f"Missing required field: {field}")

    if not errors:
        # ID must match filename
        if manifest["id"] != filename_id:
            errors.append(
                f"ID '{manifest['id']}' does not match filename '{filename_id}'"
            )

        # Type must be valid
        if manifest["type"] not in VALID_TYPES:
            errors.append(
                f"Invalid type '{manifest['type']}'. Must be one of: {VALID_TYPES}"
            )

        # Validate category if present
        if "category" in manifest and manifest["category"] not in VALID_CATEGORIES:
            errors.append(
                f"Invalid category '{manifest['category']}'. Must be one of: {VALID_CATEGORIES}"
            )

        # Recipe type: must have recipe config, doesn't need file/variants
        is_recipe = manifest["type"] == "recipe"

        # Check for variants/file presence (used by non-recipe types and validation below)
        has_variants = "variants" in manifest and len(manifest.get("variants", [])) > 0
        has_file = "file" in manifest and manifest["file"] is not None

        if is_recipe:
            if "recipe" not in manifest:
                errors.append("Recipe type must have a 'recipe' config section")
            elif "base_model" not in manifest.get("recipe", {}):
                errors.append("Recipe 'recipe' section must have 'base_model'")
        else:
            if not has_variants and not has_file:
                errors.append("Must have either 'variants' (non-empty) or 'file'")

        # Validate variants
        if has_variants:
            for i, variant in enumerate(manifest["variants"]):
                for field in ["id", "file", "url", "sha256", "size"]:
                    if field not in variant:
                        errors.append(f"Variant {i} missing required field: {field}")
                if "size" in variant and not isinstance(variant["size"], int):
                    errors.append(f"Variant {i} 'size' must be an integer (bytes)")

        # Validate file
        if has_file:
            f = manifest["file"]
            for field in ["url", "sha256", "size"]:
                if field not in f:
                    errors.append(f"File missing required field: {field}")
            if "size" in f and not isinstance(f["size"], int):
                errors.append("File 'size' must be an integer (bytes)")

        # Warn if no preview images (needed for web UI)
        if not manifest.get("preview_images"):
            pass  # Optional for now — will become required for web UI

    return errors


def check_placeholder_hashes(manifest: dict) -> list[str]:
    """Check for placeholder hashes that haven't been verified."""
    warnings = []

    if "variants" in manifest:
        for v in manifest["variants"]:
            if v.get("sha256", "").startswith("VERIFY_"):
                warnings.append(
                    f"Variant '{v.get('id', '?')}' has placeholder hash: {v['sha256']}"
                )

    if "file" in manifest and manifest["file"]:
        if manifest["file"].get("sha256", "").startswith("VERIFY_"):
            warnings.append(
                f"File has placeholder hash: {manifest['file']['sha256']}"
            )

    return warnings


def _coerce_floats(obj):
    """Recursively walk a structure and convert string values that look like
    scientific-notation floats (e.g. '1e-4', '5e-5') into actual floats.
    YAML safe_load treats these as strings; JSON and serde need them as numbers."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                try:
                    if "e" in v.lower() and not v.startswith("0x"):
                        obj[k] = float(v)
                except (ValueError, TypeError):
                    pass
            else:
                _coerce_floats(v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                try:
                    if "e" in v.lower() and not v.startswith("0x"):
                        obj[i] = float(v)
                except (ValueError, TypeError):
                    pass
            else:
                _coerce_floats(v)


def build_index(output_path: Path = DEFAULT_OUTPUT) -> bool:
    """Build index.json from all manifests. Returns True if successful."""
    items = []
    errors_found = False
    warnings_found = False

    if not MANIFESTS_DIR.exists():
        print(f"ERROR: Manifests directory not found: {MANIFESTS_DIR}")
        return False

    # Walk all type directories
    for type_dir in sorted(MANIFESTS_DIR.iterdir()):
        if not type_dir.is_dir():
            continue

        dir_name = type_dir.name
        if dir_name not in TYPE_DIR_MAP:
            print(f"WARNING: Unknown directory: {dir_name}")
            continue

        expected_type = TYPE_DIR_MAP[dir_name]

        for manifest_file in sorted(type_dir.glob("*.yaml")):
            print(f"  Processing: {manifest_file.relative_to(MANIFESTS_DIR)}")

            try:
                with open(manifest_file) as f:
                    manifest = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"  ERROR: Failed to parse YAML: {e}")
                errors_found = True
                continue

            if manifest is None:
                print(f"  ERROR: Empty manifest file")
                errors_found = True
                continue

            # Validate
            validation_errors = validate_manifest(manifest, manifest_file)
            if validation_errors:
                for err in validation_errors:
                    print(f"  ERROR: {err}")
                errors_found = True
                continue

            # Check type matches directory
            if manifest["type"] != expected_type:
                print(
                    f"  ERROR: Type '{manifest['type']}' doesn't match directory "
                    f"'{dir_name}' (expected '{expected_type}')"
                )
                errors_found = True
                continue

            # Check for placeholder hashes
            hash_warnings = check_placeholder_hashes(manifest)
            for w in hash_warnings:
                print(f"  WARNING: {w}")
                warnings_found = True

            # In CI (strict mode), placeholder hashes are errors
            strict = os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS") or "--strict" in sys.argv
            if strict and hash_warnings:
                print(f"  ERROR: Placeholder hashes not allowed in CI. Run verify_hashes.py first.")
                errors_found = True
                continue

            items.append(manifest)

    if errors_found:
        print(f"\nERROR: Validation failed. Fix errors above before building index.")
        return False

    # Sort items by ID for deterministic output
    items.sort(key=lambda x: x["id"])

    # Fix scientific notation values that YAML parsed as strings (e.g. "1e-4")
    _coerce_floats(items)

    # Count by type
    type_counts = {}
    cloud_count = 0
    for item in items:
        t = item.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
        if item.get("cloud_available"):
            cloud_count += 1

    # Build index v2 with metadata
    index = {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_count": len(items),
        "type_counts": type_counts,
        "cloud_available_count": cloud_count,
        "schema_url": "https://registry.mods.sh/schemas/manifest.schema.json",
        "items": items,
    }

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    print(f"\nBuilt index with {len(items)} items → {output_path}")
    if warnings_found:
        print("WARNING: Some hashes are placeholders. Run verify_hashes.py to compute them.")

    return True


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] != "--output" else DEFAULT_OUTPUT
    if len(sys.argv) > 2 and sys.argv[1] == "--output":
        output = Path(sys.argv[2])

    print(f"Building index from {MANIFESTS_DIR}/")
    success = build_index(output)
    sys.exit(0 if success else 1)
