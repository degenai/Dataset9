#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Extended Page Exploration Probe
========================================================

Explores DOJ pagination beyond the sequential scrape using:
- Mathematical patterns (powers, primes, fibonacci)
- Random scattershot sampling across huge ranges

This script is ISOLATED from the main scraper data:
- Reads scraper_checkpoint.json as READ-ONLY baseline
- Writes to probe_*.json files only

Usage:
    python exploration_probe.py                    # Full run
    python exploration_probe.py --random-only      # Skip patterns
    python exploration_probe.py --samples 500      # More random samples
    python exploration_probe.py --resume           # Resume from checkpoint

Author: DataSet 9 Completion Project
Date: February 2026
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    MofNCompleteColumn,
)
from rich.table import Table
from rich import box
from rich.live import Live
from rich.layout import Layout

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
REQUEST_DELAY = 1.2  # Seconds between requests
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT = os.getenv("DATASET9_USER_AGENT", "Mozilla/5.0 (compatible; DataSet9-Bot/1.0; +https://github.com/DataSet9-Project)")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
SCRAPER_CHECKPOINT = MANIFESTS_DIR / "scraper_checkpoint.json"  # READ-ONLY
PROBE_CHECKPOINT = MANIFESTS_DIR / "probe_checkpoint.json"
PROBE_RESULTS = MANIFESTS_DIR / "probe_results.json"
PROBE_DISCOVERIES = MANIFESTS_DIR / "probe_discoveries.txt"

console = Console()

# ============================================================================
# Mathematical Pattern Generators
# ============================================================================

def generate_powers_of_2(min_val: int, max_val: int) -> List[int]:
    """Generate powers of 2 in range."""
    result = []
    power = 1
    while power <= max_val:
        if power >= min_val:
            result.append(power)
        power *= 2
    return result

def generate_powers_of_10(min_val: int, max_val: int) -> List[int]:
    """Generate powers of 10 in range."""
    result = []
    power = 1
    while power <= max_val:
        if power >= min_val:
            result.append(power)
        power *= 10
    return result

def generate_fibonacci(min_val: int, max_val: int) -> List[int]:
    """Generate fibonacci numbers in range."""
    result = []
    a, b = 1, 1
    while b <= max_val:
        if b >= min_val:
            result.append(b)
        a, b = b, a + b
    return result

def generate_primes_near(targets: List[int], count: int = 2) -> List[int]:
    """Generate primes near target numbers."""
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    result = []
    for target in targets:
        # Find primes near this target
        found = 0
        for offset in range(1000):
            if is_prime(target + offset):
                result.append(target + offset)
                found += 1
                if found >= count:
                    break
            if offset > 0 and is_prime(target - offset):
                result.append(target - offset)
                found += 1
                if found >= count:
                    break
    return sorted(set(result))

def generate_round_numbers(min_val: int, max_val: int) -> List[int]:
    """Generate round numbers (multiples of 10k, 100k, 1M, etc.)."""
    result = []
    for mult in [10_000, 25_000, 50_000, 100_000, 250_000, 500_000, 
                 1_000_000, 2_500_000, 5_000_000, 10_000_000, 25_000_000,
                 50_000_000, 100_000_000, 250_000_000, 500_000_000]:
        if min_val <= mult <= max_val:
            result.append(mult)
    return result

def generate_edge_numbers(min_val: int, max_val: int) -> List[int]:
    """Generate edge cases like 99999, 100001, 999999, etc."""
    edges = []
    for boundary in [100_000, 1_000_000, 10_000_000, 100_000_000, 1_000_000_000]:
        edges.extend([boundary - 1, boundary + 1])
    return [e for e in edges if min_val <= e <= max_val]

# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ProbeResult:
    """Result from probing a single page."""
    page_num: int
    category: str  # 'pattern' or 'random'
    pattern_type: str  # 'power_2', 'fibonacci', 'random_10k_100k', etc.
    files_found: int
    new_files: int
    is_empty: bool
    is_error: bool
    probe_time: str
    files: List[str] = field(default_factory=list)

@dataclass
class ProbeState:
    """Full state of the probe operation."""
    started_at: str
    last_updated: str
    baseline_files: int  # From sequential scrape
    total_probes: int
    completed_probes: int
    probed_pages: Set[int]
    new_files_found: Set[str]
    results: List[ProbeResult]
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['probed_pages'] = list(self.probed_pages)
        d['new_files_found'] = list(self.new_files_found)
        d['results'] = [asdict(r) for r in self.results]
        return d
    
    @classmethod
    def from_dict(cls, d: dict) -> 'ProbeState':
        d['probed_pages'] = set(d.get('probed_pages', []))
        d['new_files_found'] = set(d.get('new_files_found', []))
        d['results'] = [ProbeResult(**r) for r in d.get('results', [])]
        return cls(**d)

# ============================================================================
# Core Functions
# ============================================================================

def load_baseline_files() -> Set[str]:
    """Load seen files from sequential scrape (READ-ONLY)."""
    if not SCRAPER_CHECKPOINT.exists():
        console.print("[yellow]Warning: No scraper checkpoint found. Starting with empty baseline.[/yellow]")
        return set()
    
    try:
        with open(SCRAPER_CHECKPOINT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        seen = set(data.get('seen_files', []))
        console.print(f"[green]Loaded {len(seen):,} files from sequential scrape baseline[/green]")
        return seen
    except Exception as e:
        console.print(f"[red]Error loading baseline: {e}[/red]")
        return set()

def load_probe_state() -> Optional[ProbeState]:
    """Load probe checkpoint if exists."""
    if not PROBE_CHECKPOINT.exists():
        return None
    try:
        with open(PROBE_CHECKPOINT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ProbeState.from_dict(data)
    except Exception as e:
        console.print(f"[yellow]Could not load probe checkpoint: {e}[/yellow]")
        return None

def save_probe_state(state: ProbeState):
    """Save probe checkpoint."""
    state.last_updated = datetime.now().isoformat()
    with open(PROBE_CHECKPOINT, 'w', encoding='utf-8') as f:
        json.dump(state.to_dict(), f)

def fetch_page(page_num: int) -> Optional[List[str]]:
    """Fetch a single page and extract EFTA filenames."""
    url = f"{BASE_URL}?page={page_num}"
    
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                url,
                headers={'User-Agent': USER_AGENT},
                timeout=REQUEST_TIMEOUT
            )
            
            if resp.status_code == 404:
                return []
            
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.text, 'lxml')
            links = soup.find_all('a', href=re.compile(r'EFTA\d{8}\.pdf', re.IGNORECASE))
            
            files = []
            for link in links:
                match = re.search(r'(EFTA\d{8})', link['href'], re.IGNORECASE)
                if match:
                    files.append(match.group(1).upper())
            
            return files
            
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
            else:
                return None
    
    return None

def generate_probe_pages(config: argparse.Namespace) -> Dict[str, List[int]]:
    """Generate all page numbers to probe based on config."""
    min_page = config.min_page
    max_page = config.max_page
    
    probes = {}
    
    if not config.random_only:
        # Mathematical patterns
        probes['power_2'] = generate_powers_of_2(min_page, max_page)
        probes['power_10'] = generate_powers_of_10(min_page, max_page)
        probes['fibonacci'] = generate_fibonacci(min_page, max_page)
        probes['round'] = generate_round_numbers(min_page, max_page)
        probes['edge'] = generate_edge_numbers(min_page, max_page)
        
        # Primes near round numbers
        prime_targets = [100_000, 1_000_000, 10_000_000, 100_000_000]
        prime_targets = [t for t in prime_targets if min_page <= t <= max_page]
        probes['prime'] = generate_primes_near(prime_targets)
    
    # Random scattershot - configurable samples per range
    samples = config.samples
    ranges = [
        ('random_13k_100k', 13001, 100_000),
        ('random_100k_1M', 100_000, 1_000_000),
        ('random_1M_10M', 1_000_000, 10_000_000),
        ('random_10M_100M', 10_000_000, 100_000_000),
        ('random_100M_1B', 100_000_000, 1_000_000_000),
    ]
    
    for name, range_min, range_max in ranges:
        effective_min = max(range_min, min_page)
        effective_max = min(range_max, max_page)
        if effective_min < effective_max:
            available = effective_max - effective_min
            n_samples = min(samples, available)
            probes[name] = random.sample(range(effective_min, effective_max), n_samples)
    
    return probes

def run_probe(config: argparse.Namespace):
    """Main probe execution."""
    console.print(Panel.fit(
        "[bold cyan]DOJ DataSet 9 - Extended Exploration Probe[/bold cyan]\n"
        f"Mode: {'Random Only' if config.random_only else 'Patterns + Random'}\n"
        f"Range: {config.min_page:,} to {config.max_page:,}\n"
        f"Samples per range: {config.samples}",
        title="Probe Configuration"
    ))
    
    # Load baseline
    baseline_files = load_baseline_files()
    
    # Load or create state
    state = None
    if config.resume:
        state = load_probe_state()
        if state:
            console.print(f"[green]Resuming from checkpoint: {state.completed_probes}/{state.total_probes} probes[/green]")
    
    # Generate probe pages
    probe_sets = generate_probe_pages(config)
    
    # Count total probes
    all_pages = []
    page_categories = {}
    for category, pages in probe_sets.items():
        for p in pages:
            if p not in page_categories:
                page_categories[p] = category
                all_pages.append(p)
    
    all_pages = sorted(set(all_pages))
    
    if state is None:
        state = ProbeState(
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            baseline_files=len(baseline_files),
            total_probes=len(all_pages),
            completed_probes=0,
            probed_pages=set(),
            new_files_found=set(),
            results=[]
        )
    
    # Filter out already probed pages
    pages_to_probe = [p for p in all_pages if p not in state.probed_pages]
    
    console.print(f"\n[cyan]Total unique pages to probe: {len(pages_to_probe):,}[/cyan]")
    
    # Show category breakdown
    category_counts = {}
    for cat in probe_sets:
        category_counts[cat] = len(probe_sets[cat])
    
    table = Table(title="Probe Categories", box=box.ROUNDED)
    table.add_column("Category", style="cyan")
    table.add_column("Pages", justify="right")
    for cat, count in sorted(category_counts.items()):
        table.add_row(cat, f"{count:,}")
    table.add_row("[bold]Total[/bold]", f"[bold]{len(all_pages):,}[/bold]")
    console.print(table)
    
    if not pages_to_probe:
        console.print("[yellow]All pages already probed![/yellow]")
        return
    
    # Probe pages
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Probing pages...", total=len(pages_to_probe))
        
        discoveries_this_run = 0
        
        for page_num in pages_to_probe:
            category = page_categories.get(page_num, 'unknown')
            is_pattern = not category.startswith('random')
            
            progress.update(task, description=f"Page {page_num:,} ({category})")
            
            files = fetch_page(page_num)
            
            if files is None:
                # Error
                result = ProbeResult(
                    page_num=page_num,
                    category='pattern' if is_pattern else 'random',
                    pattern_type=category,
                    files_found=0,
                    new_files=0,
                    is_empty=True,
                    is_error=True,
                    probe_time=datetime.now().isoformat()
                )
            else:
                # Check for new files
                new_files = [f for f in files if f not in baseline_files and f not in state.new_files_found]
                
                result = ProbeResult(
                    page_num=page_num,
                    category='pattern' if is_pattern else 'random',
                    pattern_type=category,
                    files_found=len(files),
                    new_files=len(new_files),
                    is_empty=len(files) == 0,
                    is_error=False,
                    probe_time=datetime.now().isoformat(),
                    files=new_files if new_files else []
                )
                
                if new_files:
                    state.new_files_found.update(new_files)
                    discoveries_this_run += len(new_files)
                    console.print(f"\n[bold green]*** DISCOVERY at page {page_num:,}: {len(new_files)} NEW FILES! ***[/bold green]")
                    for f in new_files[:5]:
                        console.print(f"  [green]{f}[/green]")
                    if len(new_files) > 5:
                        console.print(f"  [green]... and {len(new_files) - 5} more[/green]")
            
            state.results.append(result)
            state.probed_pages.add(page_num)
            state.completed_probes += 1
            
            # Save checkpoint periodically
            if state.completed_probes % 50 == 0:
                save_probe_state(state)
            
            progress.advance(task)
            time.sleep(REQUEST_DELAY)
    
    # Final save
    save_probe_state(state)
    
    # Save discoveries to text file
    if state.new_files_found:
        with open(PROBE_DISCOVERIES, 'w', encoding='utf-8') as f:
            for fname in sorted(state.new_files_found):
                f.write(fname + '\n')
    
    # Save full results
    with open(PROBE_RESULTS, 'w', encoding='utf-8') as f:
        json.dump(state.to_dict(), f, indent=2)
    
    # Summary
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]Probe Complete![/bold green]\n\n"
        f"Pages probed: {state.completed_probes:,}\n"
        f"Baseline files: {state.baseline_files:,}\n"
        f"[bold]New files discovered: {len(state.new_files_found):,}[/bold]\n"
        f"Discoveries this run: {discoveries_this_run:,}\n\n"
        f"Results saved to:\n"
        f"  {PROBE_RESULTS}\n"
        f"  {PROBE_DISCOVERIES}",
        title="Summary"
    ))
    
    # Show discovery breakdown by category
    if state.results:
        cat_discoveries = {}
        for r in state.results:
            if r.new_files > 0:
                cat_discoveries[r.pattern_type] = cat_discoveries.get(r.pattern_type, 0) + r.new_files
        
        if cat_discoveries:
            table = Table(title="Discoveries by Category", box=box.ROUNDED)
            table.add_column("Category", style="cyan")
            table.add_column("New Files", justify="right", style="green")
            for cat, count in sorted(cat_discoveries.items(), key=lambda x: -x[1]):
                table.add_row(cat, f"{count:,}")
            console.print(table)

def main():
    parser = argparse.ArgumentParser(description="DOJ DataSet 9 Extended Exploration Probe")
    parser.add_argument('--random-only', action='store_true',
                        help='Skip mathematical pattern probes, only do random sampling')
    parser.add_argument('--samples', type=int, default=100,
                        help='Number of random samples per range (default: 100)')
    parser.add_argument('--min-page', type=int, default=13001,
                        help='Minimum page number to probe (default: 13001)')
    parser.add_argument('--max-page', type=int, default=1_000_000_000,
                        help='Maximum page number to probe (default: 1 billion)')
    parser.add_argument('--resume', action='store_true',
                        help='Resume from checkpoint')
    
    args = parser.parse_args()
    
    try:
        run_probe(args)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted! Progress saved to checkpoint.[/yellow]")
        sys.exit(0)

if __name__ == "__main__":
    main()
