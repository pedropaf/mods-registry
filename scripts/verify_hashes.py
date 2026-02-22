#!/usr/bin/env python3
"""
Download files from a manifest and compute/verify their SHA256 hashes.

Usage:
    python scripts/verify_hashes.py manifests/vae/flux-vae.yaml
    python scripts/verify_hashes.py manifests/checkpoints/flux-dev.yaml --variant fp8
"""

import hashlib
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)


def compute_sha256(url: str, filename: str) -> str:
    """Download a file and compute its SHA256 hash."""
    print(f"  Downloading: {filename}")
    print(f"  URL: {url}")

    req = Request(url, headers={"User-Agent": "mods-registry/1.0"})

    hasher = hashlib.sha256()
    downloaded = 0

    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        with urlopen(req, timeout=120) as response:
            content_length = response.headers.get("Content-Length")
            total = int(content_length) if content_length else None

            while True:
                chunk = response.read(8192 * 1024)  # 8MB chunks
                if not chunk:
                    break
                hasher.update(chunk)
                downloaded += len(chunk)

                if total:
                    pct = (downloaded / total) * 100
                    mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    print(
                        f"\r  Progress: {mb:.0f}/{total_mb:.0f} MB ({pct:.1f}%)",
                        end="",
                        flush=True,
                    )
                else:
                    mb = downloaded / (1024 * 1024)
                    print(f"\r  Downloaded: {mb:.0f} MB", end="", flush=True)

    print()  # newline after progress
    return hasher.hexdigest()


def verify_manifest(filepath: Path, variant_filter: str | None = None):
    """Verify hashes for a manifest."""
    with open(filepath) as f:
        manifest = yaml.safe_load(f)

    print(f"\nVerifying: {manifest['name']} ({manifest['id']})")
    print(f"Type: {manifest['type']}")

    files_to_check = []

    if "variants" in manifest and manifest["variants"]:
        for v in manifest["variants"]:
            if variant_filter and v["id"] != variant_filter:
                continue
            files_to_check.append(
                {
                    "label": f"Variant: {v['id']}",
                    "url": v["url"],
                    "filename": v["file"],
                    "expected": v["sha256"],
                    "size": v["size"],
                }
            )
    elif "file" in manifest and manifest["file"]:
        f = manifest["file"]
        files_to_check.append(
            {
                "label": "File",
                "url": f["url"],
                "filename": f.get("file", filepath.stem),
                "expected": f["sha256"],
                "size": f["size"],
            }
        )

    if not files_to_check:
        print("  No files to verify.")
        return

    for entry in files_to_check:
        print(f"\n  [{entry['label']}]")
        size_gb = entry["size"] / (1024**3)
        print(f"  Size: {size_gb:.2f} GB")

        is_placeholder = entry["expected"].startswith("VERIFY_")
        if is_placeholder:
            print(f"  Expected hash: PLACEHOLDER ({entry['expected']})")
        else:
            print(f"  Expected hash: {entry['expected']}")

        try:
            actual = compute_sha256(entry["url"], entry["filename"])
        except Exception as e:
            print(f"  ERROR: Download failed: {e}")
            continue

        print(f"  Computed hash: {actual}")

        if is_placeholder:
            print(f"  → Replace placeholder with: {actual}")
        elif actual == entry["expected"]:
            print(f"  ✓ Hash matches!")
        else:
            print(f"  ✗ HASH MISMATCH!")
            print(f"    Expected: {entry['expected']}")
            print(f"    Got:      {actual}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_hashes.py <manifest.yaml> [--variant <id>]")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    variant = None
    if "--variant" in sys.argv:
        idx = sys.argv.index("--variant")
        if idx + 1 < len(sys.argv):
            variant = sys.argv[idx + 1]

    if not filepath.exists():
        print(f"ERROR: File not found: {filepath}")
        sys.exit(1)

    verify_manifest(filepath, variant)
