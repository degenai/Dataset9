#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Scrape From Pagination End
===================================================

Scrapes pages working BACKWARDS from the discovered pagination end.
Found end: ~184,467,440,737,095,516 (184 quadrillion!)

Tracks new files discovered and compares against baseline.

Author: DataSet 9 Completion Project
Date: February 2026
"""

import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
from rich.live import Live
from rich import box

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.0

# The discovered end point
PAGINATION_END = 184_467_440_737_095_516

# How many pages to scrape working backwards
PAGES_TO_SCRAPE = 100

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
SCRAPER_CHECKPOINT = MANIFESTS_DIR / "scraper_checkpoint.json"
END_SCRAPE_LOG = MANIFESTS_DIR / "end_scrape_results.json"
END_DISCOVERIES = MANIFESTS_DIR / "end_scrape_discoveries.txt"

console = Console()

# ============================================================================
# Core Functions
# ============================================================================

def load_baseline() -> Set[str]:
    """Load baseline files from sequential scrape."""
    if not SCRAPER_CHECKPOINT.exists():
        console.print("[yellow]Warning: No scraper checkpoint found.[/yellow]")
        return set()
    
    try:
        with open(SCRAPER_CHECKPOINT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        seen = set(data.get('seen_files', []))
        return seen
    except Exception as e:
        console.print(f"[red]Error loading baseline: {e}[/red]")
        return set()

def compute_content_hash(files: List[str]) -> str:
    """Compute hash of sorted file list."""
    if not files:
        return "empty"
    content = "|".join(sorted(files))
    return hashlib.md5(content.encode()).hexdigest()[:16]

def fetch_page(page_num: int) -> tuple[Optional[List[str]], str]:
    """Fetch a page and extract files."""
    url = f"{BASE_URL}?page={page_num}"
    
    try:
        resp = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (DataSet9 Research Project)'},
            timeout=REQUEST_TIMEOUT
        )
        
        if resp.status_code == 404:
            return None, '404'
        if resp.status_code == 503:
            return None, '503'
        if resp.status_code != 200:
            return None, f'HTTP_{resp.status_code}'
        
        soup = BeautifulSoup(resp.text, 'lxml')
        links = soup.find_all('a', href=re.compile(r'EFTA\d{8}\.pdf', re.IGNORECASE))
        
        files = []
        for link in links:
            match = re.search(r'(EFTA\d{8})', link['href'], re.IGNORECASE)
            if match:
                files.append(match.group(1).upper())
        
        return files, 'OK'
        
    except requests.Timeout:
        return None, 'TIMEOUT'
    except requests.RequestException:
        return None, 'ERROR'

def format_big_num(n: int) -> str:
    """Format huge numbers readably."""
    if n >= 1_000_000_000_000_000:
        return f"{n:,} ({n/1e15:.1f}Q)"
    elif n >= 1_000_000_000_000:
        return f"{n:,} ({n/1e12:.1f}T)"
    elif n >= 1_000_000_000:
        return f"{n:,} ({n/1e9:.1f}B)"
    else:
        return f"{n:,}"

def run_backwards_scrape():
    """Scrape pages working backwards from the end."""
    
    console.print(Panel.fit(
        "[bold cyan]DOJ DataSet 9 - Scrape From End[/bold cyan]\n\n"
        f"Starting page: [yellow]{format_big_num(PAGINATION_END)}[/yellow]\n"
        f"Direction: [cyan]← BACKWARDS[/cyan]\n"
        f"Pages to scrape: [green]{PAGES_TO_SCRAPE}[/green]",
        title="Configuration"
    ))
    
    # Load baseline
    baseline_files = load_baseline()
    console.print(f"[green]Loaded {len(baseline_files):,} baseline files[/green]\n")
    
    # Track state
    results = []
    all_new_files: Set[str] = set()
    content_hashes: Dict[str, int] = {}
    
    # Stats
    total_ok = 0
    total_error = 0
    total_files_seen = 0
    total_new = 0
    total_loops = 0
    total_redundant = 0
    
    # Create results table
    table = Table(title="Backwards Scrape Progress", box=box.ROUNDED, expand=True)
    table.add_column("#", justify="right", width=4)
    table.add_column("Page Number", style="cyan", width=30)
    table.add_column("Status", width=8)
    table.add_column("Files", justify="right", width=6)
    table.add_column("New", justify="right", width=5)
    table.add_column("Type", width=12)
    table.add_column("Notes", width=25)
    
    with Live(table, console=console, refresh_per_second=4) as live:
        for i in range(PAGES_TO_SCRAPE):
            page_num = PAGINATION_END - i
            
            # Fetch with retry for 503s
            files = None
            status = None
            for attempt in range(3):
                files, status = fetch_page(page_num)
                if status != '503':
                    break
                time.sleep(2)  # Wait longer for 503
            
            if status == 'OK' and files is not None:
                total_ok += 1
                total_files_seen += len(files)
                
                # Check for new files
                new_files = [f for f in files if f not in baseline_files and f not in all_new_files]
                
                # Classify page
                content_hash = compute_content_hash(files)
                
                if content_hash in content_hashes:
                    page_type = "LOOP"
                    total_loops += 1
                    notes = f"Same as #{PAGINATION_END - content_hashes[content_hash]}"
                    type_style = "[yellow]LOOP[/yellow]"
                elif new_files:
                    page_type = "NEW"
                    total_new += len(new_files)
                    all_new_files.update(new_files)
                    notes = f"+{len(new_files)} new!"
                    type_style = "[bold green]NEW!!![/bold green]"
                elif len(files) > 0:
                    page_type = "REDUNDANT"
                    total_redundant += 1
                    notes = "All seen before"
                    type_style = "[dim]REDUNDANT[/dim]"
                else:
                    page_type = "EMPTY"
                    notes = ""
                    type_style = "[dim]EMPTY[/dim]"
                
                # Track hash
                if content_hash not in content_hashes:
                    content_hashes[content_hash] = i
                
                # Add to table
                table.add_row(
                    str(i + 1),
                    format_big_num(page_num),
                    "[green]OK[/green]",
                    str(len(files)),
                    str(len(new_files)) if new_files else "-",
                    type_style,
                    notes
                )
                
                # Store result
                results.append({
                    'index': i,
                    'page_num': page_num,
                    'status': 'OK',
                    'files': len(files),
                    'new_files': len(new_files),
                    'type': page_type,
                    'content_hash': content_hash,
                    'file_list': new_files if new_files else []
                })
                
            else:
                total_error += 1
                table.add_row(
                    str(i + 1),
                    format_big_num(page_num),
                    f"[red]{status}[/red]",
                    "-",
                    "-",
                    f"[red]ERROR[/red]",
                    ""
                )
                
                results.append({
                    'index': i,
                    'page_num': page_num,
                    'status': status,
                    'files': 0,
                    'new_files': 0,
                    'type': 'ERROR'
                })
            
            time.sleep(REQUEST_DELAY)
    
    # Save results
    output = {
        'scrape_time': datetime.now().isoformat(),
        'start_page': PAGINATION_END,
        'pages_scraped': PAGES_TO_SCRAPE,
        'direction': 'backwards',
        'stats': {
            'total_ok': total_ok,
            'total_error': total_error,
            'total_files_seen': total_files_seen,
            'total_new_files': len(all_new_files),
            'total_loops': total_loops,
            'total_redundant': total_redundant
        },
        'results': results
    }
    
    with open(END_SCRAPE_LOG, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Save discoveries
    if all_new_files:
        with open(END_DISCOVERIES, 'w') as f:
            for fname in sorted(all_new_files):
                f.write(fname + '\n')
    
    # Summary
    console.print("\n")
    
    summary_table = Table(title="Summary", box=box.DOUBLE)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", justify="right")
    
    summary_table.add_row("Pages scraped", f"{PAGES_TO_SCRAPE}")
    summary_table.add_row("Successful", f"[green]{total_ok}[/green]")
    summary_table.add_row("Errors", f"[red]{total_error}[/red]")
    summary_table.add_row("Total files seen", f"{total_files_seen:,}")
    summary_table.add_row("Loops detected", f"[yellow]{total_loops}[/yellow]")
    summary_table.add_row("Redundant pages", f"{total_redundant}")
    summary_table.add_row("[bold]NEW FILES FOUND[/bold]", f"[bold green]{len(all_new_files)}[/bold green]")
    
    console.print(summary_table)
    
    if all_new_files:
        console.print(f"\n[bold green]*** {len(all_new_files)} NEW FILES DISCOVERED! ***[/bold green]")
        console.print(f"[dim]Saved to {END_DISCOVERIES}[/dim]")
        console.print("\nNew files:")
        for f in sorted(all_new_files)[:20]:
            console.print(f"  [green]{f}[/green]")
        if len(all_new_files) > 20:
            console.print(f"  ... and {len(all_new_files) - 20} more")
    else:
        console.print("\n[yellow]No new files found - all content same as baseline.[/yellow]")
    
    console.print(f"\n[dim]Full results saved to {END_SCRAPE_LOG}[/dim]")

if __name__ == "__main__":
    try:
        run_backwards_scrape()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
