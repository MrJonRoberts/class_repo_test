#!/usr/bin/env python3
import subprocess
import sys
import os
from datetime import datetime

# Inherit the normal environment but disable SSL verification for Git
GIT_ENV = os.environ.copy()
GIT_ENV["GIT_SSL_NO_VERIFY"] = "true"

def is_git_repo() -> bool:
    """Check if the current directory is inside a Git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return result.returncode == 0 and result.stdout.strip() == "true"

def get_branch_name_from_folder() -> str:
    """Derive the branch name from the current folder name."""
    return os.path.basename(os.getcwd())

def commit_and_push(message: str, branch: str):
    """Stage all changes, commit with the given message, and push to the specified branch."""
    # Stage all changes
    print("🔄 Staging changes...")
    subprocess.run(["git", "add", "."], check=True)

    # Commit
    print(f"✏️  Committing with message: '{message}'")
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        stderr = result.stderr.lower()
        if "nothing to commit" in stderr:
            print("ℹ️  Nothing to commit.")
            return
        else:
            print(f"❌ Commit failed:\n{result.stderr.strip()}")
            sys.exit(1)
    else:
        print(result.stdout.strip())

    # Push
    print(f"🚀 Pushing to remote branch '{branch}'...")
    subprocess.run(
        ["git", "push", "-u", "origin", branch],
        check=True,
        env=GIT_ENV
    )
    print("✅ Push complete.")

def main():
    if not is_git_repo():
        print("❌ Error: This directory is not a Git repository.")
        sys.exit(1)

    # Derive branch name
    branch = get_branch_name_from_folder()

    # Optional: verify that HEAD is on the same branch
    head = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE,
        text=True
    ).stdout.strip()
    if head != branch:
        print(f"⚠️  Warning: current Git branch is '{head}', but folder name is '{branch}'.")
        branch = head

    # Build commit message: use provided message or current date/time
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        commit_and_push(message, branch)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ An error occurred during Git operations:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

