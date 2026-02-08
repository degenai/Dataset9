#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Chapter Diff Tool
==========================================

Compares data across Chapter 1 (Feb 2-3) and Chapter 2 (Feb 6+):

1. Chapter 1 DOJ scrape vs Chapter 2 DOJ scrape
   - Files added/removed from DOJ pagination
   - Pagination structure changes
   
2. Chapter 2 DOJ scrape vs torrent
   - Same comparison as Chapter 1 but with fresh data
   
3. Negative pages vs everything
   - Any unique files only on negative pages?

4. Combined: what does Chapter 2 tell us that Chapter 1 didn't?

Author: DataSet 9 Completion Project
Date: February 2026 - Chapter 2
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Set

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
CH1_DIR = PROJECT_ROOT / "chapter1" / "manifests"
CH2_DIR = PROJECT_ROOT / "chapter2" / "manifests"
CH2_NEG = PROJECT_ROOT / "chapter2" / "negative_pages"
DIFF_DIR = PROJECT_ROOT / "chapter2" / "diffs"
TORRENT_MANIFEST = PROJECT_ROOT / "manifests" / "torrent_manifest.txt"

console = Console()

# ============================================================================
# Helpers
# ============================================================================

def load_manifest(path: Path) -> Set[str]:
    """Load a manifest file (one filename per line) into a set."""
    if not path.exists():
        console.print(f"[yellow]Not found: {path}[/yellow]")
        return set()
    
    files = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                # Normalize: remove .pdf extension if present for consistent comparison
                name = line.replace('.pdf', '').upper()
                if not name.startswith('EFTA'):
                    name = line.replace('.pdf', '')
                files.add(name)
    
    return files


def load_checkpoint_files(path: Path) -> Set[str]:
    """Load seen_files from a checkpoint JSON."""
    if not path.exists():
        console.print(f"[yellow]Not found: {path}[/yellow]")
        return set()
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return set(data.get('seen_files', []))
    except Exception as e:
        console.print(f"[red]Error loading {path}: {e}[/red]")
        return set()


def load_negative_discoveries(path: Path) -> Set[str]:
    """Load negative page discoveries."""
    if not path.exists():
        return set()
    files = set()
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                files.add(line.replace('.pdf', '').upper())
    return files


def save_file_list(files: Set[str], path: Path, header: str = ""):
    """Save a set of files to a text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        if header:
            f.write(f"# {header}\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Count: {len(files)}\n\n")
        for fname in sorted(files):
            f.write(fname + '\n')

# ============================================================================
# Diff Operations
# ============================================================================

def diff_chapter1_vs_chapter2():
    """Compare Chapter 1 and Chapter 2 DOJ scrapes."""
    console.print(Panel.fit(
        "[bold cyan]Diff 1: Chapter 1 vs Chapter 2 DOJ Scrapes[/bold cyan]",
        title="Comparison"
    ))
    
    # Load both
    ch1_files = load_manifest(CH1_DIR / "doj_dataset9_manifest.txt")
    if not ch1_files:
        ch1_files = load_checkpoint_files(CH1_DIR / "scraper_checkpoint.json")
    
    ch2_files = load_manifest(CH2_DIR / "doj_dataset9_manifest.txt")
    if not ch2_files:
        ch2_files = load_checkpoint_files(CH2_DIR / "scraper_checkpoint.json")
    
    if not ch1_files:
        console.print("[red]No Chapter 1 data found![/red]")
        return
    if not ch2_files:
        console.print("[red]No Chapter 2 data found! Run the scraper first.[/red]")
        return
    
    # Compute diffs
    added = ch2_files - ch1_files       # New in Chapter 2
    removed = ch1_files - ch2_files     # Gone from Chapter 2
    common = ch1_files & ch2_files      # In both
    
    # Display
    table = Table(title="Chapter 1 vs Chapter 2", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", width=35)
    table.add_column("Count", justify="right", style="bold")
    
    table.add_row("Chapter 1 unique files", f"{len(ch1_files):,}")
    table.add_row("Chapter 2 unique files", f"{len(ch2_files):,}")
    table.add_row("Files in common", f"{len(common):,}")
    table.add_row("[green]Added in Chapter 2[/green]", f"[green]{len(added):,}[/green]")
    table.add_row("[red]Removed since Chapter 1[/red]", f"[red]{len(removed):,}[/red]")
    table.add_row("Net change", f"{len(ch2_files) - len(ch1_files):+,}")
    
    console.print(table)
    
    # Save diffs
    if added:
        save_file_list(added, DIFF_DIR / "added_since_ch1.txt",
                       "Files found in Chapter 2 DOJ scrape but NOT in Chapter 1")
        console.print(f"  [green]Saved {len(added):,} added files to diffs/added_since_ch1.txt[/green]")
    
    if removed:
        save_file_list(removed, DIFF_DIR / "removed_since_ch1.txt",
                       "Files found in Chapter 1 DOJ scrape but NOT in Chapter 2")
        console.print(f"  [red]Saved {len(removed):,} removed files to diffs/removed_since_ch1.txt[/red]")
    
    # Show samples
    if added:
        console.print(f"\n[green]Sample of NEW files (first 10):[/green]")
        for f in sorted(added)[:10]:
            console.print(f"  [green]{f}[/green]")
        if len(added) > 10:
            console.print(f"  [dim]...and {len(added) - 10} more[/dim]")
    
    if removed:
        console.print(f"\n[red]Sample of REMOVED files (first 10):[/red]")
        for f in sorted(removed)[:10]:
            console.print(f"  [red]{f}[/red]")
        if len(removed) > 10:
            console.print(f"  [dim]...and {len(removed) - 10} more[/dim]")
    
    return ch1_files, ch2_files, added, removed


def diff_ch2_vs_torrent():
    """Compare Chapter 2 DOJ scrape against the torrent."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Diff 2: Chapter 2 DOJ Scrape vs Torrent[/bold cyan]",
        title="Comparison"
    ))
    
    ch2_files = load_manifest(CH2_DIR / "doj_dataset9_manifest.txt")
    if not ch2_files:
        ch2_files = load_checkpoint_files(CH2_DIR / "scraper_checkpoint.json")
    
    torrent_files = load_manifest(TORRENT_MANIFEST)
    
    if not ch2_files:
        console.print("[red]No Chapter 2 data found![/red]")
        return
    if not torrent_files:
        console.print("[red]No torrent manifest found![/red]")
        return
    
    # Diffs
    doj_only = ch2_files - torrent_files    # On DOJ but not in torrent
    torrent_only = torrent_files - ch2_files  # In torrent but not on DOJ
    common = ch2_files & torrent_files
    
    table = Table(title="Chapter 2 DOJ vs Torrent", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", width=35)
    table.add_column("Count", justify="right", style="bold")
    
    table.add_row("Chapter 2 DOJ files", f"{len(ch2_files):,}")
    table.add_row("Torrent files", f"{len(torrent_files):,}")
    table.add_row("In common", f"{len(common):,}")
    table.add_row("[yellow]On DOJ only (not in torrent)[/yellow]", f"[yellow]{len(doj_only):,}[/yellow]")
    table.add_row("[dim]In torrent only (not on DOJ)[/dim]", f"[dim]{len(torrent_only):,}[/dim]")
    
    console.print(table)
    
    if doj_only:
        save_file_list(doj_only, DIFF_DIR / "ch2_doj_not_in_torrent.txt",
                       "Files on DOJ (Chapter 2 scrape) but NOT in torrent")
        console.print(f"\n[yellow]Files on DOJ but not in torrent:[/yellow]")
        for f in sorted(doj_only):
            console.print(f"  [yellow]{f}[/yellow]")
    else:
        console.print("\n[green]All Chapter 2 DOJ files are in the torrent![/green]")
    
    return doj_only, torrent_only


def diff_negative_pages():
    """Check negative page discoveries against everything."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Diff 3: Negative Page Discoveries[/bold cyan]",
        title="Comparison"
    ))
    
    neg_files = load_negative_discoveries(CH2_NEG / "negative_discoveries.txt")
    
    if not neg_files:
        # Try loading from checkpoint
        neg_checkpoint = CH2_NEG / "negative_scrape_checkpoint.json"
        if neg_checkpoint.exists():
            try:
                with open(neg_checkpoint, 'r') as f:
                    data = json.load(f)
                neg_files = set(data.get('new_files', []))
            except:
                pass
    
    if not neg_files:
        console.print("[dim]No negative page discoveries to compare (or no new files found)[/dim]")
        return
    
    # Load everything else
    ch1_files = load_manifest(CH1_DIR / "doj_dataset9_manifest.txt")
    ch2_files = load_manifest(CH2_DIR / "doj_dataset9_manifest.txt")
    torrent_files = load_manifest(TORRENT_MANIFEST)
    
    all_positive = ch1_files | ch2_files
    all_known = all_positive | torrent_files
    
    unique_to_negative = neg_files - all_known
    
    table = Table(title="Negative Page Analysis", box=box.ROUNDED)
    table.add_column("Metric", style="cyan", width=40)
    table.add_column("Count", justify="right", style="bold")
    
    table.add_row("Files from negative pages", f"{len(neg_files):,}")
    table.add_row("Also in positive DOJ scrapes", f"{len(neg_files & all_positive):,}")
    table.add_row("Also in torrent", f"{len(neg_files & torrent_files):,}")
    table.add_row("[bold green]UNIQUE to negative pages[/bold green]", 
                  f"[bold green]{len(unique_to_negative):,}[/bold green]")
    
    console.print(table)
    
    if unique_to_negative:
        save_file_list(unique_to_negative, DIFF_DIR / "unique_to_negative_pages.txt",
                       "Files found ONLY via negative page numbers")
        console.print(f"\n[bold green]Files unique to negative pages:[/bold green]")
        for f in sorted(unique_to_negative)[:20]:
            console.print(f"  [green]{f}[/green]")
        if len(unique_to_negative) > 20:
            console.print(f"  [green]...and {len(unique_to_negative) - 20} more[/green]")


def generate_summary():
    """Generate a summary markdown of all diffs."""
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Generating Diff Summary[/bold cyan]",
        title="Summary"
    ))
    
    # Load all datasets
    ch1 = load_manifest(CH1_DIR / "doj_dataset9_manifest.txt")
    ch2 = load_manifest(CH2_DIR / "doj_dataset9_manifest.txt")
    torrent = load_manifest(TORRENT_MANIFEST)
    neg = load_negative_discoveries(CH2_NEG / "negative_discoveries.txt")
    
    # Build summary
    summary = f"""# Chapter 2 Diff Summary

Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}

## Dataset Sizes

| Source | Files |
|--------|-------|
| Chapter 1 DOJ Scrape (Feb 2-3) | {len(ch1):,} |
| Chapter 2 DOJ Scrape (Feb 6+) | {len(ch2):,} |
| Torrent (86GB) | {len(torrent):,} |
| Negative Page Discoveries | {len(neg):,} |

## Chapter 1 vs Chapter 2 Changes

| Metric | Count |
|--------|-------|
| Files added since Ch1 | {len(ch2 - ch1):,} |
| Files removed since Ch1 | {len(ch1 - ch2):,} |
| Net change | {len(ch2) - len(ch1):+,} |

## Chapter 2 vs Torrent

| Metric | Count |
|--------|-------|
| On DOJ but not in torrent | {len(ch2 - torrent):,} |
| In torrent but not on DOJ | {len(torrent - ch2):,} |

## All Sources Combined

| Metric | Count |
|--------|-------|
| Total unique files (all sources) | {len(ch1 | ch2 | torrent | neg):,} |
| Files only on DOJ (any chapter) | {len((ch1 | ch2) - torrent):,} |
| Files only in torrent | {len(torrent - (ch1 | ch2)):,} |
| Files only on negative pages | {len(neg - (ch1 | ch2 | torrent)):,} |
"""
    
    summary_path = DIFF_DIR / "DIFF_SUMMARY.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    console.print(f"[green]Summary saved to {summary_path}[/green]")

# ============================================================================
# Main
# ============================================================================

def main():
    console.print(Panel.fit(
        "[bold cyan]DOJ DataSet 9 - Chapter Diff Tool[/bold cyan]\n\n"
        "Comparing Chapter 1 (Feb 2-3) vs Chapter 2 (Feb 6+)\n"
        "Including negative page discoveries and torrent comparison",
        title="Diff Analysis"
    ))
    
    # Run all diffs
    diff_chapter1_vs_chapter2()
    diff_ch2_vs_torrent()
    diff_negative_pages()
    generate_summary()
    
    console.print("\n[bold green]All diffs complete![/bold green]")
    console.print(f"[dim]Results in: {DIFF_DIR}[/dim]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
