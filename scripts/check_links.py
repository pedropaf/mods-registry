#!/usr/bin/env python3
"""
Check all download URLs in manifests for link rot.
Sends a HEAD request to each URL and reports any that return non-200 status.

Usage:
    python scripts/check_links.py [--output report.json]

Exit code:
    0 — all URLs reachable
    1 — one or more broken URLs found
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
import yaml

MANIFESTS_DIR = Path(__file__).parent.parent / "manifests"
TIMEOUT = 30  # seconds per request


def collect_urls(manifest_path: Path) -> list[dict]:
    """Extract all download URLs and homepage URLs from a manifest file."""
    with open(manifest_path) as f:
        data = yaml.safe_load(f)

    urls = []
    manifest_id = data.get("id", manifest_path.stem)

    # Homepage URL
    homepage = data.get("homepage")
    if homepage:
        urls.append({"manifest": manifest_id, "url": homepage, "kind": "homepage"})

    # Single file
    if "file" in data and isinstance(data["file"], dict):
        url = data["file"].get("url")
        if url:
            urls.append({"manifest": manifest_id, "url": url, "kind": "download"})

    # Variants
    for variant in data.get("variants", []):
        if isinstance(variant, dict):
            url = variant.get("url")
            if not url and "file" in variant:
                url = variant["file"].get("url") if isinstance(variant["file"], dict) else None
            if url:
                vid = variant.get("id", "?")
                urls.append({"manifest": f"{manifest_id}:{vid}", "url": url, "kind": "download"})

    return urls


def check_url(url: str) -> tuple[int, str]:
    """HEAD request a URL. Returns (status_code, reason)."""
    try:
        # Some servers don't support HEAD, fall back to GET with stream
        resp = requests.head(url, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 405:
            # Method not allowed — try GET with no body
            resp = requests.get(url, timeout=TIMEOUT, stream=True, allow_redirects=True)
            resp.close()
        return resp.status_code, resp.reason
    except requests.exceptions.Timeout:
        return 0, "timeout"
    except requests.exceptions.ConnectionError as e:
        return 0, f"connection error: {e}"
    except Exception as e:
        return 0, str(e)


def main():
    parser = argparse.ArgumentParser(description="Check manifest download URLs")
    parser.add_argument("--output", help="Write JSON report to this path")
    args = parser.parse_args()

    # Collect all URLs
    all_urls = []
    for yaml_file in sorted(MANIFESTS_DIR.rglob("*.yaml")):
        all_urls.extend(collect_urls(yaml_file))

    print(f"Checking {len(all_urls)} URLs...")

    broken = []
    ok_count = 0

    for entry in all_urls:
        status, reason = check_url(entry["url"])
        kind = entry.get("kind", "download")
        label = f"[{kind}] {entry['manifest']}"
        if 200 <= status < 400:
            ok_count += 1
            print(f"  ✓ {label}")
        else:
            broken.append({**entry, "status": status, "reason": reason})
            print(f"  ✗ {label} → {status} {reason}")

    print()
    print(f"Results: {ok_count} OK, {len(broken)} broken")

    report = {"total": len(all_urls), "ok": ok_count, "broken": broken}

    if args.output:
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report written to {args.output}")

    if broken:
        sys.exit(1)


if __name__ == "__main__":
    main()
