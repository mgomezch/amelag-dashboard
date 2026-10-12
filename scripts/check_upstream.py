#!/usr/bin/env python3
"""
check_upstream.py
Monitors and synchronizes data from the upstream AMELAG wastewater repository:
https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG

Commands:
  --check : Check if new commits exist upstream (exit code 2 if new commit, 0 if up to date).
  --sync  : Download new data, run static build, and record new commit hash.
  --force : Force sync even if commit hash matches.
"""

import argparse
import os
import subprocess
import sys
import urllib.request

UPSTREAM_REPO = "https://github.com/robert-koch-institut/Abwassersurveillance_AMELAG.git"
UPSTREAM_BRANCH = "refs/heads/main"
RAW_BASE_URL = "https://raw.githubusercontent.com/robert-koch-institut/Abwassersurveillance_AMELAG/main"

def get_remote_head():
    cmd = ["git", "ls-remote", UPSTREAM_REPO, UPSTREAM_BRANCH]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.PIPE, text=True, timeout=30)
        parts = out.strip().split()
        if parts:
            return parts[0].strip()
    except Exception as e:
        print(f"Error querying remote head: {e}", file=sys.stderr)
    return None

def get_recorded_head(commit_file):
    if os.path.exists(commit_file):
        try:
            with open(commit_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: could not read {commit_file}: {e}", file=sys.stderr)
    return None

def sync_data(root_dir, remote_sha, commit_file):
    agg_file = os.path.join(root_dir, "amelag_aggregierte_kurve.tsv")
    sites_file = os.path.join(root_dir, "amelag_einzelstandorte.tsv")

    print(f"Fetching latest dataset from RKI AMELAG (upstream commit {remote_sha[:7]})...")
    
    url_agg = f"{RAW_BASE_URL}/amelag_aggregierte_kurve.tsv"
    print(f"  Downloading {url_agg}...")
    urllib.request.urlretrieve(url_agg, agg_file)

    url_sites = f"{RAW_BASE_URL}/amelag_einzelstandorte.tsv"
    print(f"  Downloading {url_sites}...")
    urllib.request.urlretrieve(url_sites, sites_file)

    print("Rebuilding dashboard static pages and data structures...")
    import build
    build.build_data(root_dir)

    print(f"Recording upstream commit {remote_sha} into {commit_file}...")
    os.makedirs(os.path.dirname(commit_file), exist_ok=True)
    with open(commit_file, "w", encoding="utf-8") as f:
        f.write(f"{remote_sha}\n")

    print("Data synchronization complete!")

def main():
    parser = argparse.ArgumentParser(description="Check and sync AMELAG data from RKI repository")
    parser.add_argument("--check", action="store_true", help="Check if upstream has new commits")
    parser.add_argument("--sync", action="store_true", help="Sync data if new upstream commits are detected")
    parser.add_argument("--force", action="store_true", help="Force sync even if up to date")
    parser.add_argument("--dir", default=".", help="Root directory of amelag-dashboard project")

    args = parser.parse_args()
    root_dir = os.path.abspath(args.dir)
    sys.path.insert(0, os.path.join(root_dir, "scripts"))
    commit_file = os.path.join(root_dir, "data", "upstream_commit.txt")

    remote_sha = get_remote_head()
    if not remote_sha:
        print("Failed to resolve upstream repository HEAD.", file=sys.stderr)
        sys.exit(1)

    recorded_sha = get_recorded_head(commit_file)
    print(f"Upstream HEAD SHA : {remote_sha}")
    print(f"Recorded local SHA: {recorded_sha or '(none)'}")

    has_new_commit = (remote_sha != recorded_sha)

    if args.check:
        if has_new_commit:
            print("STATUS: New upstream commits available.")
            sys.exit(2)
        else:
            print("STATUS: Up to date.")
            sys.exit(0)

    if args.sync:
        if has_new_commit or args.force:
            sync_data(root_dir, remote_sha, commit_file)
            sys.exit(0)
        else:
            print("No updates needed. Upstream is identical to recorded SHA.")
            sys.exit(0)

    # Default action if neither --check nor --sync is specified
    if has_new_commit:
        print("New commits detected. Run with --sync to fetch and rebuild.")
        sys.exit(2)
    else:
        print("Up to date.")
        sys.exit(0)

if __name__ == "__main__":
    main()
