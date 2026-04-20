"""
refresh_hub.py — Orbit Client Hub daily refresh
================================================
Reads the latest CSV export and embeds it directly into orbit_hub.html so the
dashboard loads with fresh data without any user interaction.

Usage:
    python scripts/refresh_hub.py

    # With a specific CSV file:
    python scripts/refresh_hub.py --csv "C:/Users/Stephanie.Klahre/Downloads/combined_20260414.csv"

    # Dry run (shows what it would do, doesn't write):
    python scripts/refresh_hub.py --dry-run

Schedule via Windows Task Scheduler to run daily at 8:00 AM.
See README.md → "Automating the Hub" for setup steps.
"""

import os
import re
import sys
import glob
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

# Folder where your combined CSV exports land (adjust if needed)
CSV_SEARCH_PATHS = [
    Path.home() / "Downloads",
    Path.home() / "OneDrive" / "Downloads",
    Path.home() / "OneDrive - NetDocuments" / "Downloads",
    Path.home() / "OneDrive - NetDocuments" / "Documents",
]

# CSV filename pattern (change if yours is named differently)
CSV_PATTERN = "combined_*.csv"

# The HTML file to update
SCRIPT_DIR  = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
HUB_HTML    = PROJECT_DIR / "orbit_hub.html"

# Backup directory (keeps last 7 days of HTML backups)
BACKUP_DIR  = PROJECT_DIR / ".hub-backups"
KEEP_BACKUPS = 7

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_latest_csv(explicit_path=None):
    """Find the most recently modified CSV matching the pattern."""
    if explicit_path:
        p = Path(explicit_path)
        if not p.exists():
            raise FileNotFoundError(f"CSV not found: {explicit_path}")
        return p

    candidates = []
    for folder in CSV_SEARCH_PATHS:
        if folder.exists():
            candidates.extend(folder.glob(CSV_PATTERN))

    if not candidates:
        raise FileNotFoundError(
            f"No CSV matching '{CSV_PATTERN}' found in:\n" +
            "\n".join(f"  {p}" for p in CSV_SEARCH_PATHS) +
            "\n\nEither export a new CSV to one of these locations, or pass --csv <path>."
        )

    # Most recently modified
    return max(candidates, key=lambda p: p.stat().st_mtime)


def escape_for_js_template_literal(text):
    """Escape CSV text so it can be embedded safely in a JS template literal."""
    # Escape backticks and template literal syntax
    text = text.replace("\\", "\\\\")
    text = text.replace("`", "\\`")
    text = text.replace("${", "\\${")
    return text


def inject_csv_into_html(html_path, csv_text, csv_filename, timestamp):
    """
    Inject the CSV content into the HTML file as JS constants.
    Replaces any previously injected block, or inserts before </script>.
    """
    html = html_path.read_text(encoding="utf-8")

    escaped = escape_for_js_template_literal(csv_text)

    injection = (
        f"// ── AUTO-INJECTED by refresh_hub.py ──\n"
        f"// Source: {csv_filename}\n"
        f"// Refreshed: {timestamp}\n"
        f"const EMBEDDED_CSV  = `{escaped}`;\n"
        f"const EMBEDDED_DATE = '{timestamp}';\n"
        f"// ── END AUTO-INJECTED ──"
    )

    # Replace existing injection block if present
    pattern = re.compile(
        r"// ── AUTO-INJECTED by refresh_hub\.py ──.*?// ── END AUTO-INJECTED ──",
        re.DOTALL
    )
    if pattern.search(html):
        html = pattern.sub(injection, html)
    else:
        # Insert right before init() call at the bottom of the script
        html = html.replace("init();", injection + "\n\ninit();", 1)

    html_path.write_text(html, encoding="utf-8")


def backup_html(html_path, backup_dir):
    """Keep a dated backup and prune old ones."""
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest  = backup_dir / f"orbit_hub_{stamp}.html"
    shutil.copy2(html_path, dest)

    # Prune oldest backups beyond KEEP_BACKUPS
    all_backups = sorted(backup_dir.glob("orbit_hub_*.html"), key=lambda p: p.stat().st_mtime)
    for old in all_backups[:-KEEP_BACKUPS]:
        old.unlink()

    return dest


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Refresh Orbit Client Hub with latest CSV data.")
    parser.add_argument("--csv",      help="Path to CSV file (default: auto-detect latest)")
    parser.add_argument("--dry-run",  action="store_true", help="Show what would happen, don't write")
    args = parser.parse_args()

    print("=" * 56)
    print("  ndMAX Orbit — Hub Refresh")
    print("=" * 56)

    # 1. Find CSV
    try:
        csv_path = find_latest_csv(args.csv)
    except FileNotFoundError as e:
        print(f"\n❌  {e}")
        sys.exit(1)

    csv_size  = csv_path.stat().st_size / 1024
    csv_mtime = datetime.fromtimestamp(csv_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    print(f"\n  CSV  :  {csv_path.name}")
    print(f"  Size :  {csv_size:.1f} KB")
    print(f"  Date :  {csv_mtime}")

    # 2. Check HTML exists
    if not HUB_HTML.exists():
        print(f"\n❌  orbit_hub.html not found at {HUB_HTML}")
        sys.exit(1)

    print(f"\n  HTML :  {HUB_HTML.name}")

    if args.dry_run:
        print("\n  [DRY RUN] — no files written.")
        print("\n  Would inject CSV into HTML as EMBEDDED_CSV constant.")
        print("  Would keep last 7 backups in .hub-backups/")
        print("\n✅  Dry run complete.")
        return

    # 3. Read CSV
    csv_text = csv_path.read_text(encoding="utf-8-sig")  # utf-8-sig strips BOM if present
    row_count = csv_text.count("\n")
    print(f"  Rows :  ~{row_count}")

    # 4. Backup existing HTML
    backup_path = backup_html(HUB_HTML, BACKUP_DIR)
    print(f"\n  Backup  →  .hub-backups/{backup_path.name}")

    # 5. Inject
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    inject_csv_into_html(HUB_HTML, csv_text, csv_path.name, timestamp)

    print(f"\n✅  orbit_hub.html updated with {csv_path.name}")
    print(f"   Timestamp embedded: {timestamp}")
    print(f"\n   Open orbit_hub.html in Chrome or Edge — data loads automatically.\n")


if __name__ == "__main__":
    main()
