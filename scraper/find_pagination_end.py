#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Find Pagination End
============================================

Probes increasingly absurd page numbers to find where DOJ pagination breaks.
Tests powers of 10 up to quintillions to find the actual ceiling.

Tracks for each page:
- LOOP: Exact duplicate content of a previously seen page (via content hash)
- REDUNDANT: All files seen before, but different arrangement
- NEW: Contains files not seen in baseline
- EMPTY: No files returned
- ERROR: Server error or 404

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
from rich.live import Live
from rich import box

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
REQUEST_TIMEOUT = 30

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
SCRAPER_CHECKPOINT = MANIFESTS_DIR / "scraper_checkpoint.json"
END_SEARCH_LOG = MANIFESTS_DIR / "pagination_end_search.json"

console = Console()

# ============================================================================
# Test Page Numbers - Increasingly Absurd
# ============================================================================

def generate_test_pages() -> List[int]:
    """Generate increasingly absurd page numbers to test."""
    pages = []
    
    # Powers of 10: 10^4 through 10^18 (quadrillions)
    for exp in range(4, 19):
        pages.append(10 ** exp)
    
    # Also test some edge cases
    edges = [
        # Billions
        1_000_000_000,
        2_147_483_647,      # Max signed 32-bit int
        2_147_483_648,      # Max signed 32-bit + 1
        4_294_967_295,      # Max unsigned 32-bit
        4_294_967_296,      # Max unsigned 32-bit + 1
        
        # Trillions
        1_000_000_000_000,
        
        # Quadrillions  
        1_000_000_000_000_000,
        
        # Quintillions
        1_000_000_000_000_000_000,
        
        # Max signed 64-bit
        9_223_372_036_854_775_807,
    ]
    
    pages.extend(edges)
    
    # Sort and dedupe
    return sorted(set(pages))

# ============================================================================
# Core Functions
# ============================================================================

def load_baseline() -> tuple[Set[str], Dict[str, int]]:
    """Load baseline files and page hashes from sequential scrape."""
    if not SCRAPER_CHECKPOINT.exists():
        console.print("[yellow]Warning: No scraper checkpoint found.[/yellow]")
        return set(), {}
    
    try:
        with open(SCRAPER_CHECKPOINT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        seen_files = set(data.get('seen_files', []))
        
        # Build page hashes from existing pages
        page_hashes = {}
        pages_data = data.get('pages', {})
        for page_num, page_info in pages_data.items():
            if 'content_hash' in page_info:
                h = page_info['content_hash']
                if h not in page_hashes:
                    page_hashes[h] = int(page_num)
        
        console.print(f"[green]Loaded {len(seen_files):,} baseline files, {len(page_hashes):,} content hashes[/green]")
        return seen_files, page_hashes
        
    except Exception as e:
        console.print(f"[red]Error loading baseline: {e}[/red]")
        return set(), {}

def compute_content_hash(files: List[str]) -> str:
    """Compute hash of sorted file list for loop detection."""
    if not files:
        return "empty"
    content = "|".join(sorted(files))
    return hashlib.md5(content.encode()).hexdigest()[:16]

def fetch_page(page_num: int) -> tuple[Optional[List[str]], str]:
    """
    Fetch a page and return (files, status).
    Status: 'ok', 'empty', 'error', 'timeout', '404'
    """
    url = f"{BASE_URL}?page={page_num}"
    
    try:
        resp = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (DataSet9 Research Project)'},
            timeout=REQUEST_TIMEOUT
        )
        
        if resp.status_code == 404:
            return None, '404'
        
        if resp.status_code != 200:
            return None, f'http_{resp.status_code}'
        
        soup = BeautifulSoup(resp.text, 'lxml')
        links = soup.find_all('a', href=re.compile(r'EFTA\d{8}\.pdf', re.IGNORECASE))
        
        files = []
        for link in links:
            match = re.search(r'(EFTA\d{8})', link['href'], re.IGNORECASE)
            if match:
                files.append(match.group(1).upper())
        
        if not files:
            return [], 'empty'
        
        return files, 'ok'
        
    except requests.Timeout:
        return None, 'timeout'
    except requests.RequestException as e:
        return None, f'error: {str(e)[:50]}'

def classify_page(
    files: List[str],
    baseline_files: Set[str],
    page_hashes: Dict[str, int],
    seen_this_run: Set[str]
) -> tuple[str, Optional[int]]:
    """
    Classify a page result.
    Returns (classification, loops_to_page)
    
    Classifications:
    - LOOP: Exact content match to earlier page
    - REDUNDANT: All files seen before, different arrangement
    - NEW: Has files not in baseline
    - EMPTY: No files
    """
    if not files:
        return 'EMPTY', None
    
    content_hash = compute_content_hash(files)
    
    # Check if exact loop
    if content_hash in page_hashes:
        return 'LOOP', page_hashes[content_hash]
    
    # Check for new files
    new_files = [f for f in files if f not in baseline_files and f not in seen_this_run]
    if new_files:
        return 'NEW', None
    
    # All files seen, but different arrangement
    return 'REDUNDANT', None

def format_page_num(n: int) -> str:
    """Format large numbers with names."""
    if n >= 1_000_000_000_000_000_000:
        return f"{n:,} (quintillion range)"
    elif n >= 1_000_000_000_000_000:
        return f"{n:,} (quadrillion range)"
    elif n >= 1_000_000_000_000:
        return f"{n:,} (trillion range)"
    elif n >= 1_000_000_000:
        return f"{n:,} (billion range)"
    elif n >= 1_000_000:
        return f"{n:,} (million range)"
    else:
        return f"{n:,}"

def run_end_search():
    """Main search for pagination end."""
    console.print(Panel.fit(
        "[bold cyan]DOJ DataSet 9 - Pagination End Search[/bold cyan]\n\n"
        "Testing increasingly absurd page numbers to find where DOJ breaks.\n"
        "Testing from 10,000 up to 9 quintillion (max 64-bit int).",
        title="Mission"
    ))
    
    # Load baseline
    baseline_files, page_hashes = load_baseline()
    seen_this_run: Set[str] = set()
    
    # Generate test pages
    test_pages = generate_test_pages()
    console.print(f"\n[cyan]Testing {len(test_pages)} page numbers[/cyan]\n")
    
    # Results table
    results = []
    
    # Create live display
    table = Table(title="Pagination End Search", box=box.ROUNDED, expand=True)
    table.add_column("Page Number", style="cyan", width=35)
    table.add_column("Status", width=12)
    table.add_column("Files", justify="right", width=8)
    table.add_column("Classification", width=15)
    table.add_column("Notes", width=30)
    
    with Live(table, console=console, refresh_per_second=4) as live:
        for page_num in test_pages:
            # Fetch page
            files, status = fetch_page(page_num)
            
            if status == 'ok' and files is not None:
                classification, loops_to = classify_page(
                    files, baseline_files, page_hashes, seen_this_run
                )
                
                # Update seen files
                if classification == 'NEW':
                    new_files = [f for f in files if f not in baseline_files and f not in seen_this_run]
                    seen_this_run.update(new_files)
                
                # Track content hash
                content_hash = compute_content_hash(files)
                if content_hash not in page_hashes:
                    page_hashes[content_hash] = page_num
                
                # Format result
                file_count = len(files)
                notes = ""
                if classification == 'LOOP':
                    notes = f"Same as page {loops_to:,}"
                elif classification == 'NEW':
                    notes = f"{len([f for f in files if f not in baseline_files]):,} new files!"
                
                # Style based on classification
                if classification == 'LOOP':
                    class_style = "[yellow]LOOP[/yellow]"
                elif classification == 'REDUNDANT':
                    class_style = "[dim]REDUNDANT[/dim]"
                elif classification == 'NEW':
                    class_style = "[bold green]NEW!!![/bold green]"
                else:
                    class_style = classification
                
                status_style = "[green]OK[/green]"
                
            elif status == 'empty':
                file_count = 0
                class_style = "[dim]EMPTY[/dim]"
                status_style = "[yellow]EMPTY[/yellow]"
                notes = "Page exists but no files"
                classification = 'EMPTY'
                
            elif status == '404':
                file_count = 0
                class_style = "[red]404[/red]"
                status_style = "[red]404[/red]"
                notes = "PAGE NOT FOUND - END?"
                classification = '404'
                
            else:
                file_count = 0
                class_style = f"[red]{status}[/red]"
                status_style = f"[red]ERROR[/red]"
                notes = status
                classification = 'ERROR'
            
            # Add row
            table.add_row(
                format_page_num(page_num),
                status_style,
                str(file_count) if file_count else "-",
                class_style,
                notes
            )
            
            # Store result
            results.append({
                'page_num': page_num,
                'status': status,
                'files': file_count,
                'classification': classification,
                'notes': notes,
                'timestamp': datetime.now().isoformat()
            })
            
            # Small delay
            time.sleep(1.0)
    
    # Save results
    with open(END_SEARCH_LOG, 'w', encoding='utf-8') as f:
        json.dump({
            'search_time': datetime.now().isoformat(),
            'pages_tested': len(test_pages),
            'results': results
        }, f, indent=2)
    
    # Summary
    console.print("\n")
    
    # Find where it breaks
    first_404 = None
    first_error = None
    for r in results:
        if r['classification'] == '404' and first_404 is None:
            first_404 = r['page_num']
        if r['classification'] == 'ERROR' and first_error is None:
            first_error = r['page_num']
    
    # Count by classification
    class_counts = {}
    for r in results:
        c = r['classification']
        class_counts[c] = class_counts.get(c, 0) + 1
    
    summary_table = Table(title="Summary", box=box.ROUNDED)
    summary_table.add_column("Classification", style="cyan")
    summary_table.add_column("Count", justify="right")
    for c, count in sorted(class_counts.items()):
        summary_table.add_row(c, str(count))
    console.print(summary_table)
    
    if first_404:
        console.print(f"\n[bold red]PAGINATION ENDS AT: {format_page_num(first_404)}[/bold red]")
    elif first_error:
        console.print(f"\n[bold yellow]FIRST ERROR AT: {format_page_num(first_error)}[/bold yellow]")
    else:
        console.print(f"\n[bold green]No end found! DOJ pagination works up to {format_page_num(test_pages[-1])}[/bold green]")
    
    console.print(f"\n[dim]Results saved to {END_SEARCH_LOG}[/dim]")

if __name__ == "__main__":
    try:
        run_end_search()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
