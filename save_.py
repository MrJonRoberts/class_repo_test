#!/usr/bin/env python3
import subprocess
import sys
import os
import hashlib
from datetime import datetime

# File to store baseline checksum after first run
SCRIPT_PATH = os.path.abspath(__file__)
HASH_STORE = os.path.join(os.path.dirname(SCRIPT_PATH), ".expected_hash")

# Environment for Git: disable SSL verification
GIT_ENV = os.environ.copy()
GIT_ENV["GIT_SSL_NO_VERIFY"] = "true"

def compute_hash(path: str) -> str:
    """Compute SHA-256 of the given file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_integrity():
    """On first run, store the script's checksum. Then verify thereafter."""
    actual = compute_hash(SCRIPT_PATH)
    if not os.path.exists(HASH_STORE):
        with open(HASH_STORE, "w") as fh:
            fh.write(actual)
        print(f"🔖 Initial checksum stored: {actual}")
    else:
        expected = open(HASH_STORE).read().strip()
        if actual != expected:
            sys.stderr.write(
                "🛑 Integrity check failed!\n"
                f" Expected: {expected}\n"
                f"   Actual: {actual}\n"
                " Exiting.\n"
            )
            sys.exit(1)

def is_git_repo() -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    return result.returncode == 0 and result.stdout.strip() == "true"

def get_branch_name_from_folder() -> str:
    return os.path.basename(os.getcwd())

def commit_and_push(message: str, branch: str):
    print("🔄 Staging changes...")
    subprocess.run(["git", "add", "."], check=True)
    print(f"✏️  Committing with message: '{message}'")
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True
    )
    if result.returncode != 0:

        if "nothing to commit" in result.stderr.lower():
            print("ℹ️  Nothing to commit.")
            return
        else:
            sys.stderr.write(f"ℹ️  Nothing to commit.\n")
            sys.exit(1)
    else:
        print(result.stdout.strip())
    print(f"🚀 Pushing to remote branch '{branch}'...")
    subprocess.run(
        ["git", "push", "-u", "origin", branch],
        check=True, env=GIT_ENV
    )
    print("✅ Push complete.")

def main():
    verify_integrity()
    if not is_git_repo():
        sys.stderr.write("❌ Error: This directory is not a Git repository.\n")
        sys.exit(1)
    branch = get_branch_name_from_folder()
    head = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE, text=True
    ).stdout.strip()
    if head != branch:
        print(f"⚠️  Warning: HEAD is '{head}', using '{head}' instead.")
        branch = head
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_and_push(message, branch)

if __name__ == "__main__":
    main()
