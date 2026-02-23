#!/usr/bin/env python3
"""
Fetch SHA256 hashes from HuggingFace via HEAD requests (no file download needed).

Uses the x-linked-etag header which contains the SHA256 hash for LFS files.

Usage:
    python scripts/fetch_hashes_from_hf.py                    # Fix all VERIFY_ placeholders
    python scripts/fetch_hashes_from_hf.py --dry-run           # Show what would change
    python scripts/fetch_hashes_from_hf.py manifests/checkpoints/flux-dev.yaml  # Fix one file
"""

import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

MANIFESTS_DIR = Path(__file__).parent.parent / "manifests"


def get_sha256_from_hf(url: str) -> str | None:
    """Get SHA256 hash from HuggingFace via HEAD request (x-linked-etag header)."""
    if "huggingface.co" not in url:
        print(f"    SKIP: Not a HuggingFace URL")
        return None

    req = Request(url, method="HEAD", headers={"User-Agent": "mods-registry/1.0"})
    try:
        resp = urlopen(req, timeout=30)
        etag = resp.headers.get("x-linked-etag") or resp.headers.get("etag")
        if etag:
            # Strip quotes
            return etag.strip('"')
        # Follow redirect and check there
        return None
    except HTTPError as e:
        if e.code == 302 or e.code == 301:
            # HF redirects — check the redirect response headers
            etag = e.headers.get("x-linked-etag") or e.headers.get("etag")
            if etag:
                return etag.strip('"')
        if e.code == 401 or e.code == 403:
            print(f"    GATED: Requires authentication (HTTP {e.code})")
            return None
        print(f"    ERROR: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"    ERROR: {e}")
        return None


def process_manifest(filepath: Path, dry_run: bool = False) -> tuple[int, int]:
    """Process a single manifest file. Returns (found, updated) counts."""
    with open(filepath) as f:
        content = f.read()

    if "VERIFY_" not in content:
        return 0, 0

    data = yaml.safe_load(content)
    found = 0
    updated = 0

    entries = []  # (placeholder, url, yaml_path_desc)

    if "variants" in data and data["variants"]:
        for v in data["variants"]:
            if isinstance(v.get("sha256"), str) and v["sha256"].startswith("VERIFY_"):
                entries.append((v["sha256"], v["url"], f"variant {v['id']}"))
    elif "file" in data and data["file"]:
        f = data["file"]
        if isinstance(f.get("sha256"), str) and f["sha256"].startswith("VERIFY_"):
            entries.append((f["sha256"], f["url"], "file"))

    found = len(entries)
    if not entries:
        return 0, 0

    print(f"\n  {data['name']} ({filepath.name}) — {found} placeholder(s)")

    for placeholder, url, desc in entries:
        print(f"    [{desc}] Fetching hash...")
        sha256 = get_sha256_from_hf(url)
        if sha256 and len(sha256) == 64:
            if not dry_run:
                content = content.replace(f'"{placeholder}"', f'"{sha256}"')
                content = content.replace(f"'{placeholder}'", f'"{sha256}"')
                # Handle unquoted
                content = content.replace(f"sha256: {placeholder}", f'sha256: "{sha256}"')
            print(f"    OK: {sha256}")
            updated += 1
        elif sha256:
            print(f"    WARN: Got non-SHA256 value: {sha256[:40]}...")
        else:
            print(f"    FAILED: Could not get hash")

        time.sleep(0.2)  # Rate limit

    if not dry_run and updated > 0:
        with open(filepath, "w") as f:
            f.write(content)
        print(f"    WROTE: {filepath}")

    return found, updated


def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        files = [Path(a) for a in args]
    else:
        files = sorted(MANIFESTS_DIR.rglob("*.yaml"))

    total_found = 0
    total_updated = 0

    mode = "DRY RUN" if dry_run else "UPDATING"
    print(f"=== Fetching SHA256 hashes from HuggingFace ({mode}) ===")

    for filepath in files:
        found, updated = process_manifest(filepath, dry_run)
        total_found += found
        total_updated += updated

    print(f"\n=== Done: {total_updated}/{total_found} hashes resolved ===")
    if dry_run and total_found > 0:
        print("Run without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
