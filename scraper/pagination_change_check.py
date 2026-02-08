#!/usr/bin/env python3
"""
Pagination Change Check
========================

Quick check: has the DOJ pagination shifted since our scrape started?
Fetches ~20 known pages, compares content hashes against the checkpoint.

  python pagination_change_check.py

Author: DataSet 9 Completion Project
Date: February 2026 - Chapter 2
"""

import hashlib
import json
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich import box

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
TIMEOUT = 15
DELAY = 0.8

PROJECT_ROOT = Path(__file__).parent.parent
CHECKPOINT = PROJECT_ROOT / "chapter2" / "manifests" / "ch2_checkpoint.json"

SAMPLE_PAGES = [0, 10, 50, 100, 200, 500, 750, 1000, 1500, 2000,
                3000, 5000, 7500, 10000, 12000, 15000, 20000, 25000, 28000, 30000]

console = Console()


def fetch_hash(page: int) -> tuple:
    """Fetch a page, return (content_hash, file_count, status)."""
    url = f"{BASE_URL}?page={page}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (DS9-PagCheck)"}, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, 0, f"HTTP_{r.status_code}"
        soup = BeautifulSoup(r.text, "lxml")
        links = soup.find_all("a", href=re.compile(r"EFTA\d{8}\.pdf", re.I))
        files = []
        for a in links:
            m = re.search(r"(EFTA\d{8})", a["href"], re.I)
            if m:
                files.append(m.group(1).upper())
        h = hashlib.md5("|".join(sorted(files)).encode()).hexdigest()[:16] if files else "empty"
        return h, len(files), "ok"
    except requests.Timeout:
        return None, 0, "timeout"
    except requests.RequestException:
        return None, 0, "error"


def main():
    if not CHECKPOINT.exists():
        console.print("[red]No checkpoint found. Run ch2_scrape.py first.[/red]")
        sys.exit(1)

    with open(CHECKPOINT) as f:
        cp = json.load(f)

    pages_data = cp.get("pages", {})
    saved_at = cp.get("saved_at", "?")
    console.print(f"[dim]Checkpoint from: {saved_at}[/dim]")
    console.print(f"[dim]Testing {len(SAMPLE_PAGES)} pages...[/dim]\n")

    table = Table(title="[bold]Pagination Change Check[/bold]", box=box.ROUNDED, show_lines=True)
    table.add_column("Page", justify="right", width=8, style="cyan")
    table.add_column("Checkpoint Hash", width=18)
    table.add_column("Live Hash", width=18)
    table.add_column("Files", justify="right", width=6)
    table.add_column("Verdict", width=12)

    matches = 0
    mismatches = 0
    skipped = 0

    for page in SAMPLE_PAGES:
        cp_entry = pages_data.get(str(page))
        if not cp_entry or cp_entry.get("hash") in (None, "error"):
            table.add_row(f"{page:,}", "[dim]no data[/dim]", "[dim]--[/dim]", "--", "[dim]skip[/dim]")
            skipped += 1
            time.sleep(DELAY)
            continue

        cp_hash = cp_entry["hash"]
        live_hash, file_count, status = fetch_hash(page)

        if status != "ok":
            table.add_row(f"{page:,}", cp_hash, f"[red]{status}[/red]", "--", "[yellow]error[/yellow]")
            skipped += 1
        elif live_hash == cp_hash:
            table.add_row(f"{page:,}", cp_hash, live_hash, str(file_count), "[green]MATCH[/green]")
            matches += 1
        else:
            table.add_row(f"{page:,}", cp_hash, f"[red]{live_hash}[/red]", str(file_count), "[bold red]CHANGED[/bold red]")
            mismatches += 1

        time.sleep(DELAY)

    console.print(table)

    # Verdict
    console.print()
    if mismatches == 0:
        console.print(f"[bold green]PAGINATION STABLE[/bold green]  ({matches}/{matches+skipped} matched, {skipped} skipped)")
    else:
        console.print(f"[bold red]PAGINATION CHANGED[/bold red]  ({mismatches} pages differ!)")
        console.print(f"[red]The DOJ reshuffled pagination during our scan. Data may be mixed.[/red]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
