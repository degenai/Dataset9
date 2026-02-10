#!/usr/bin/env python3
"""
DOJ DataSet 9 - Chapter 2 Re-Scrape
=====================================

Clean re-index of the DOJ DataSet 9 pagination.
Walks pages 0..MAX_PAGE, collects EFTA files, saves manifest.
Auto-diffs against Chapter 1 when done.

  python ch2_scrape.py              # fresh run
  python ch2_scrape.py --resume     # resume from checkpoint

Author: DataSet 9 Completion Project
Date: February 2026 - Chapter 2
"""

import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# ============================================================================
# Config
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
MAX_PAGE = 40_000
DELAY = 1.0
TIMEOUT = 15
RETRIES = 3
CHECKPOINT_EVERY = 50
USER_AGENT = os.getenv("DATASET9_USER_AGENT", "Mozilla/5.0 (compatible; DataSet9-Bot/1.0; +https://github.com/DataSet9-Project)")

PROJECT_ROOT = Path(__file__).parent.parent
OUT = PROJECT_ROOT / "chapter2" / "manifests"
CH1 = PROJECT_ROOT / "chapter1" / "manifests"
CHECKPOINT = OUT / "ch2_checkpoint.json"

console = Console()

# ============================================================================
# Fetch
# ============================================================================

def fetch_page(page: int) -> tuple:
    """Returns (files: list[str] | None, status: str)."""
    url = f"{BASE_URL}?page={page}"
    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            if r.status_code == 404:
                return None, "404"
            if r.status_code != 200:
                return None, f"HTTP_{r.status_code}"
            soup = BeautifulSoup(r.text, "lxml")
            links = soup.find_all("a", href=re.compile(r"EFTA\d{8}\.pdf", re.I))
            files = []
            for a in links:
                m = re.search(r"(EFTA\d{8})", a["href"], re.I)
                if m:
                    files.append(m.group(1).upper())
            return files, "ok"
        except requests.Timeout:
            if attempt < RETRIES:
                console.print(f"    [dim]timeout, retry {attempt+1}/{RETRIES}[/dim]")
                time.sleep(attempt * 2)
            else:
                return None, "timeout"
        except requests.RequestException:
            if attempt < RETRIES:
                time.sleep(attempt * 2)
            else:
                return None, "error"
    return None, "error"

# ============================================================================
# Checkpoint
# ============================================================================

def save_checkpoint(page, seen, pages_data):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT, "w") as f:
        json.dump({
            "page": page,
            "seen": sorted(seen),
            "pages": pages_data,
            "saved_at": datetime.now().isoformat(),
        }, f)

def load_checkpoint():
    if not CHECKPOINT.exists():
        return None
    with open(CHECKPOINT) as f:
        data = json.load(f)
    return {
        "page": data["page"],
        "seen": set(data["seen"]),
        "pages": data["pages"],
    }

# ============================================================================
# EFTA Distribution
# ============================================================================

def show_efta_distribution(files: set, title: str, bucket_size: int = 50_000):
    nums = []
    for f in files:
        m = re.search(r"EFTA(\d{8})", f, re.I)
        if m:
            nums.append(int(m.group(1)))
        elif f.isdigit():
            nums.append(int(f))
    if not nums:
        return
    nums.sort()
    buckets = Counter((n // bucket_size) * bucket_size for n in nums)

    table = Table(title=f"[bold]{title}[/bold]", box=box.ROUNDED)
    table.add_column("EFTA Range", style="cyan", width=22)
    table.add_column("Files", justify="right", width=10)
    table.add_column("Bar", width=30)

    max_count = max(buckets.values())
    for b in sorted(buckets):
        count = buckets[b]
        bar_len = int(count / max_count * 25)
        bar = "[green]" + "#" * bar_len + "[/green]"
        table.add_row(f"{b:08d}–{b+bucket_size-1:08d}", f"{count:,}", bar)

    console.print(table)
    console.print(f"  [dim]{len(nums):,} files, range {nums[0]:08d}–{nums[-1]:08d}[/dim]\n")

# ============================================================================
# Main scrape
# ============================================================================

def scrape(resume=False):
    OUT.mkdir(parents=True, exist_ok=True)

    # Init or resume
    start_page = 0
    seen = set()
    pages_data = {}

    if resume:
        cp = load_checkpoint()
        if cp:
            start_page = cp["page"] + 1
            seen = cp["seen"]
            pages_data = cp["pages"]
            console.print(f"[green]Resumed from page {start_page} ({len(seen):,} files)[/green]")
        else:
            console.print("[yellow]No checkpoint found, starting fresh[/yellow]")

    console.print(Panel.fit(
        f"[bold cyan]Ch2 Re-Scrape[/bold cyan]\n"
        f"Pages {start_page}..{MAX_PAGE}  |  {len(seen):,} files known",
        title="DataSet 9"
    ))

    # Load Ch1 baseline for comparison
    ch1_files = set()
    ch1_manifest = CH1 / "doj_dataset9_manifest.txt"
    if ch1_manifest.exists():
        with open(ch1_manifest) as f:
            for line in f:
                name = line.strip().replace(".pdf", "")
                if name:
                    ch1_files.add(name)
        console.print(f"[dim]Ch1 baseline: {len(ch1_files):,} files[/dim]")

    # Show Ch1 EFTA distribution before we start
    if ch1_files:
        show_efta_distribution(ch1_files, "Ch1 Baseline EFTA Distribution")

    consecutive_empty = 0
    errors = 0
    pages_with_new = 0
    pages_all_seen = 0
    t0 = time.time()

    for page in range(start_page, MAX_PAGE + 1):
        files, status = fetch_page(page)

        if status != "ok" or files is None:
            errors += 1
            consecutive_empty += 1
            pages_data[str(page)] = {"files": 0, "new": 0, "hash": "error", "error": status}
            console.print(f"  {page:>6}  [red]{status}[/red]")
            time.sleep(DELAY)
            continue

        # Classify
        new = [f for f in files if f not in seen]
        content_hash = hashlib.md5("|".join(sorted(files)).encode()).hexdigest()[:16] if files else "empty"

        seen.update(new)

        efta_nums = []
        for f in files:
            m = re.search(r"EFTA(\d{8})", f, re.I)
            if m:
                efta_nums.append(int(m.group(1)))

        pages_data[str(page)] = {
            "files": len(files),
            "new": len(new),
            "hash": content_hash,
            "min_efta": f"EFTA{min(efta_nums):08d}" if efta_nums else None,
            "max_efta": f"EFTA{max(efta_nums):08d}" if efta_nums else None,
        }

        # Display
        if len(new) > 0:
            console.print(f"  {page:>6}  [green]OK[/green]  {len(files):>3} files  [bold green]+{len(new)} new[/bold green]  total: {len(seen):,}")
            consecutive_empty = 0
            pages_with_new += 1
        elif files:
            console.print(f"  {page:>6}  [dim]OK  {len(files):>3} files  (all seen)[/dim]")
            consecutive_empty = 0
            pages_all_seen += 1
        else:
            console.print(f"  {page:>6}  [dim]empty[/dim]")
            consecutive_empty += 1

        # Checkpoint + summary
        if page % CHECKPOINT_EVERY == 0 and page > 0:
            save_checkpoint(page, seen, pages_data)
            new_vs_ch1 = len(seen - ch1_files) if ch1_files else 0
            missing_vs_ch1 = len(ch1_files - seen) if ch1_files else 0
            elapsed_m = (time.time() - t0) / 60
            console.print(
                f"  [bold cyan]── pg {page:,} ──[/bold cyan]"
                f"  [green]{len(seen):,} unique[/green]"
                f"  |  {pages_with_new} pages w/ new, {pages_all_seen} dupes, {errors} errors"
                f"  |  vs Ch1: [green]+{new_vs_ch1}[/green] new, [red]-{missing_vs_ch1:,}[/red] not yet seen"
                f"  |  {elapsed_m:.1f}m"
            )

        time.sleep(DELAY)

    # ── Retry failed pages ────────────────────────────────────────────
    failed_pages = [int(p) for p, d in pages_data.items() if isinstance(d, dict) and d.get("error")]
    if failed_pages:
        console.print(f"\n[bold yellow]Retrying {len(failed_pages)} failed pages (up to 100 rounds)...[/bold yellow]")
        for attempt in range(1, 101):
            still_failed = []
            for page in failed_pages:
                files, status = fetch_page(page)
                if status == "ok" and files is not None:
                    new = [f for f in files if f not in seen]
                    content_hash = hashlib.md5("|".join(sorted(files)).encode()).hexdigest()[:16] if files else "empty"
                    seen.update(new)
                    pages_data[str(page)] = {"files": len(files), "new": len(new), "hash": content_hash}
                    tag = f"[bold green]+{len(new)} new[/bold green]" if new else "(all seen)"
                    console.print(f"  [green]✓[/green] pg {page:>6}  {len(files)} files  {tag}  (round {attempt})")
                else:
                    still_failed.append(page)
                time.sleep(DELAY)
            failed_pages = still_failed
            if not failed_pages:
                console.print(f"  [green]All failed pages recovered![/green]")
                break
            if attempt % 10 == 0:
                console.print(f"  [dim]Round {attempt}: {len(failed_pages)} still failing[/dim]")
        if failed_pages:
            console.print(f"  [red]{len(failed_pages)} pages still failed after 100 rounds: {failed_pages}[/red]")

    elapsed = time.time() - t0

    # Save final outputs
    save_checkpoint(MAX_PAGE, seen, pages_data)

    manifest_file = OUT / "doj_dataset9_manifest.txt"
    with open(manifest_file, "w") as f:
        for name in sorted(seen):
            f.write(f"{name}.pdf\n")

    index_file = OUT / "pagination_index.json"
    with open(index_file, "w") as f:
        json.dump({
            "scraped_at": datetime.now().isoformat(),
            "total_files": len(seen),
            "pages_scraped": len(pages_data),
            "errors": errors,
            "elapsed_seconds": round(elapsed),
            "pages": pages_data,
        }, f, indent=2)

    # ── Summary ──────────────────────────────────────────────────────
    console.print(f"\n[bold green]Done.[/bold green]  {len(seen):,} unique files from {len(pages_data)} pages in {elapsed/60:.1f} min")
    console.print(f"  Manifest: {manifest_file}")
    console.print(f"  Index:    {index_file}")

    # ── Auto-diffs ─────────────────────────────────────────────────────
    ch1_manifest = CH1 / "doj_dataset9_manifest.txt"
    if ch1_manifest.exists():
        diff_against_ch1(seen, ch1_manifest)

    torrent_manifest = PROJECT_ROOT / "manifests" / "torrent_manifest.txt"
    if not torrent_manifest.exists():
        torrent_manifest = CH1 / "torrent_manifest.txt"
    if torrent_manifest.exists():
        diff_against_torrent(seen, torrent_manifest)

    # Final EFTA distribution
    show_efta_distribution(seen, "Ch2 Final EFTA Distribution")

def diff_against_ch1(ch2_files: set, ch1_path: Path):
    console.print("\n[bold cyan]Diff vs Chapter 1[/bold cyan]")
    ch1 = set()
    with open(ch1_path) as f:
        for line in f:
            name = line.strip().replace(".pdf", "")
            if name:
                ch1.add(name)

    only_ch2 = ch2_files - ch1
    only_ch1 = ch1 - ch2_files
    common = ch1 & ch2_files

    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Metric", style="bold", width=25)
    table.add_column("Count", justify="right", width=12)

    table.add_row("Ch1 total files", f"{len(ch1):,}")
    table.add_row("Ch2 total files", f"{len(ch2_files):,}")
    table.add_row("In common", f"{len(common):,}")
    table.add_row("[green]New in Ch2[/green]", f"[green]{len(only_ch2):,}[/green]")
    table.add_row("[red]Removed since Ch1[/red]", f"[red]{len(only_ch1):,}[/red]")
    console.print(table)

    # Save diff files
    if only_ch2:
        with open(OUT / "new_in_ch2.txt", "w") as f:
            for name in sorted(only_ch2):
                f.write(f"{name}.pdf\n")
        console.print(f"  [green]New files saved to new_in_ch2.txt[/green]")

    if only_ch1:
        with open(OUT / "removed_since_ch1.txt", "w") as f:
            for name in sorted(only_ch1):
                f.write(f"{name}.pdf\n")
        console.print(f"  [red]Removed files saved to removed_since_ch1.txt[/red]")

    if not only_ch2 and not only_ch1:
        console.print("  [green]Manifests are identical.[/green]")

def diff_against_torrent(ch2_files: set, torrent_path: Path):
    console.print("\n[bold cyan]Diff vs Torrent[/bold cyan]")
    torrent = set()
    with open(torrent_path) as f:
        for line in f:
            name = line.strip().replace(".pdf", "")
            if name:
                torrent.add(name)

    only_doj = ch2_files - torrent
    only_torrent = torrent - ch2_files
    common = ch2_files & torrent

    table = Table(box=box.ROUNDED, show_lines=True)
    table.add_column("Metric", style="bold", width=25)
    table.add_column("Count", justify="right", width=12)

    table.add_row("Ch2 DOJ files", f"{len(ch2_files):,}")
    table.add_row("Torrent files", f"{len(torrent):,}")
    table.add_row("In common", f"{len(common):,}")
    table.add_row("[green]DOJ only (not in torrent)[/green]", f"[green]{len(only_doj):,}[/green]")
    table.add_row("[yellow]Torrent only (not on DOJ)[/yellow]", f"[yellow]{len(only_torrent):,}[/yellow]")
    console.print(table)

    if only_doj:
        with open(OUT / "doj_not_in_torrent.txt", "w") as f:
            for name in sorted(only_doj):
                f.write(f"{name}.pdf\n")
        console.print(f"  [green]DOJ-only files saved to doj_not_in_torrent.txt[/green]")
        console.print(f"  [dim]  (Ch1 had 3 files the torrent didn't have)[/dim]")

    if only_torrent:
        with open(OUT / "torrent_not_on_doj.txt", "w") as f:
            for name in sorted(only_torrent):
                f.write(f"{name}.pdf\n")
        console.print(f"  [yellow]Torrent-only files saved to torrent_not_on_doj.txt[/yellow]")

# ============================================================================

if __name__ == "__main__":
    try:
        if "--distro" in sys.argv:
            # Just show distributions from existing data, no scraping
            ch1_path = CH1 / "doj_dataset9_manifest.txt"
            ch2_path = OUT / "doj_dataset9_manifest.txt"
            torrent_path = PROJECT_ROOT / "manifests" / "torrent_manifest.txt"
            if not torrent_path.exists():
                torrent_path = CH1 / "torrent_manifest.txt"
            for label, path in [("Ch1", ch1_path), ("Ch2", ch2_path), ("Torrent", torrent_path)]:
                if path.exists():
                    files = set()
                    with open(path) as f:
                        for line in f:
                            name = line.strip().replace(".pdf", "")
                            if name:
                                files.add(name)
                    show_efta_distribution(files, f"{label} EFTA Distribution ({len(files):,} files)")
                else:
                    console.print(f"[dim]{label}: not found[/dim]")
        else:
            scrape(resume="--resume" in sys.argv)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Use --resume to continue.[/yellow]")
        sys.exit(0)
