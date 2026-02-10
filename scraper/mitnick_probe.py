#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Mitnick Pattern Probe
==============================================

"The art of intrusion" - Kevin Mitnick

Final hacker-brain exploration looking for hidden content using:
- Mathematical patterns (primes, fibonacci, powers)
- Programmer magic numbers (0xDEADBEEF, 0xCAFEBABE, etc.)
- Integer boundary edge cases
- DOJ-specific patterns (dataset numbers, EFTA ranges)
- Random chaos theory probes
- Suspicious round numbers

Author: DataSet 9 Completion Project  
Date: February 2026
"""

import hashlib
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
REQUEST_TIMEOUT = 30
REQUEST_DELAY = 0.8
USER_AGENT = os.getenv("DATASET9_USER_AGENT", "Mozilla/5.0 (compatible; DataSet9-Bot/1.0; +https://github.com/DataSet9-Project)")

PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
SCRAPER_CHECKPOINT = MANIFESTS_DIR / "scraper_checkpoint.json"
MITNICK_RESULTS = MANIFESTS_DIR / "mitnick_probe_results.json"

console = Console()

# ============================================================================
# Mitnick Pattern Generators - Think Like a Hacker
# ============================================================================

def generate_mitnick_pages() -> List[Tuple[int, str, str]]:
    """
    Generate page numbers a hacker would check.
    Returns: List of (page_num, category, reason)
    """
    pages = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY 1: Programmer Magic Numbers
    # ═══════════════════════════════════════════════════════════════════════
    magic_numbers = [
        (0xDEADBEEF, "magic", "DEADBEEF - classic debug marker"),
        (0xCAFEBABE, "magic", "CAFEBABE - Java class file magic"),
        (0xBAADF00D, "magic", "BAADFOOD - Windows heap debug"),
        (0xFEEDFACE, "magic", "FEEDFACE - Mach-O magic"),
        (0x8BADF00D, "magic", "8BADFOOD - iOS watchdog kill"),
        (0xDEADC0DE, "magic", "DEADCODE - dead code marker"),
        (0xC0FFEE, "magic", "COFFEE - programmer fuel"),
        (0xBADCAB1E, "magic", "BADCABLE - network debug"),
        (1337, "magic", "LEET - hacker culture"),
        (31337, "magic", "ELEET - elite hacker"),
        (42, "magic", "Answer to everything"),
        (420, "magic", "420 blaze it"),
        (69, "magic", "Nice"),
        (666, "magic", "Number of the beast"),
        (1984, "magic", "Orwell"),
        (2001, "magic", "Space Odyssey"),
        (9001, "magic", "Over 9000!"),
        (80085, "magic", "BOOBS - juvenile but checked"),
        (8008135, "magic", "BOOBIES - ditto"),
        (5318008, "magic", "BOOBIES upside down"),
    ]
    pages.extend(magic_numbers)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY 2: Powers and Mathematical Patterns
    # ═══════════════════════════════════════════════════════════════════════
    
    # Powers of 2 we haven't checked in detail
    for exp in [15, 16, 17, 18, 19, 20, 21, 22, 23, 24]:
        pages.append((2**exp, "power2", f"2^{exp}"))
        pages.append((2**exp - 1, "power2", f"2^{exp} - 1 (Mersenne)"))
        pages.append((2**exp + 1, "power2", f"2^{exp} + 1"))
    
    # Fibonacci sequence - nature's pattern
    fib = [1, 1]
    while fib[-1] < 10_000_000:
        fib.append(fib[-1] + fib[-2])
    for f in fib:
        if f > 10000:
            pages.append((f, "fibonacci", f"Fib({fib.index(f)})"))
    
    # First 20 primes over 10000
    primes = [10007, 10009, 10037, 10039, 10061, 10067, 10069, 10079, 10091, 10093,
              10099, 10103, 10111, 10133, 10139, 10141, 10151, 10159, 10163, 10169,
              100003, 100019, 100043, 100049, 100057,  # Primes near 100k
              1000003, 1000033, 1000037,  # Primes near 1M
              10000019, 10000079]  # Primes near 10M
    for p in primes:
        pages.append((p, "prime", f"Prime {p}"))
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY 3: DOJ/Epstein Specific Patterns
    # ═══════════════════════════════════════════════════════════════════════
    
    # Dataset numbers as page numbers
    for ds in range(1, 15):
        pages.append((ds * 10000, "doj", f"DataSet {ds} × 10000"))
        pages.append((ds * 100000, "doj", f"DataSet {ds} × 100000"))
    
    # EFTA number ranges as page numbers
    efta_ranges = [
        39025,   # Min EFTA we found
        267311,  # Early max
        337032,  # Mid max  
        539216,  # Late max
        326497,  # One of the MISSING files!
        326501,  # Another MISSING file!
        534391,  # Third MISSING file!
    ]
    for e in efta_ranges:
        pages.append((e, "efta", f"EFTA number as page"))
    
    # Epstein significant dates (as numbers)
    dates = [
        (20190810, "date", "Epstein death date 2019-08-10"),
        (20060630, "date", "First arrest 2006-06-30"),
        (20190706, "date", "Second arrest 2019-07-06"),
        (20200702, "date", "Maxwell arrest 2020-07-02"),
        (19530120, "date", "Epstein birth 1953-01-20"),
    ]
    pages.extend(dates)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY 4: Integer Boundaries
    # ═══════════════════════════════════════════════════════════════════════
    
    boundaries = [
        (32767, "boundary", "Max signed 16-bit"),
        (32768, "boundary", "Max signed 16-bit + 1"),
        (65535, "boundary", "Max unsigned 16-bit"),
        (65536, "boundary", "Max unsigned 16-bit + 1"),
        (16777215, "boundary", "Max 24-bit (16M colors)"),
        (16777216, "boundary", "2^24"),
        (2147483647, "boundary", "Max signed 32-bit"),
        (2147483648, "boundary", "Max signed 32-bit + 1"),
    ]
    pages.extend(boundaries)
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY 5: Suspicious Patterns from Our Data
    # ═══════════════════════════════════════════════════════════════════════
    
    # Pages where we found content tranches in sequential scrape
    content_tranches = [
        (766, "tranche", "First true wrap detected"),
        (2460, "tranche", "Tranche discovered"),
        (3450, "tranche", "New files found"),
        (3750, "tranche", "+195 new files"),
        (4100, "tranche", "+38 new files"),
        (8900, "tranche", "Late content"),
        (9200, "tranche", "Late content"),
        (9850, "tranche", "Late content"),
        (9997, "tranche", "+36 files near 10k"),
    ]
    # Check multiples of these
    for base, cat, reason in content_tranches:
        for mult in [10, 100, 1000]:
            pages.append((base * mult, "tranche_mult", f"{reason} × {mult}"))
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY 6: Chaos Theory / Random Hacker Intuition
    # ═══════════════════════════════════════════════════════════════════════
    
    random.seed(1337)  # Reproducible chaos
    
    # Random numbers that "feel" significant
    chaos = [
        (12345, "chaos", "Sequential digits"),
        (54321, "chaos", "Reverse sequential"),
        (11111, "chaos", "All ones"),
        (22222, "chaos", "All twos"),
        (99999, "chaos", "All nines"),
        (100000, "chaos", "Round 100k"),
        (123456, "chaos", "Sequential 6"),
        (654321, "chaos", "Reverse 6"),
        (111111, "chaos", "Six ones"),
        (999999, "chaos", "Six nines"),
        (1000000, "chaos", "Round 1M"),
        (1234567, "chaos", "Sequential 7"),
        (7654321, "chaos", "Reverse 7"),
        (1111111, "chaos", "Seven ones"),
        (9999999, "chaos", "Seven nines"),
        (10000000, "chaos", "Round 10M"),
    ]
    pages.extend(chaos)
    
    # Random samples in unexplored ranges
    for _ in range(20):
        r = random.randint(13001, 1000000)
        pages.append((r, "random", "Random probe"))
    
    # ═══════════════════════════════════════════════════════════════════════
    # CATEGORY 7: Near the End - Edge of the Abyss
    # ═══════════════════════════════════════════════════════════════════════
    
    # We found the end at 184,467,440,737,095,516
    END = 184_467_440_737_095_516
    
    abyss = [
        (END - 1000, "abyss", "1000 before end"),
        (END - 10000, "abyss", "10k before end"),
        (END - 100000, "abyss", "100k before end"),
        (END - 1000000, "abyss", "1M before end"),
        (END // 2, "abyss", "Halfway to end"),
        (END // 3, "abyss", "Third to end"),
        (END // 10, "abyss", "Tenth to end"),
        (END // 100, "abyss", "Hundredth to end"),
    ]
    pages.extend(abyss)
    
    # Sort by page number and dedupe
    # IMPORTANT: Skip pages 0-13000 - we already scraped those sequentially!
    ALREADY_SCRAPED = 13000
    
    seen = set()
    unique = []
    for p, cat, reason in pages:
        if p not in seen and p > ALREADY_SCRAPED:
            seen.add(p)
            unique.append((p, cat, reason))
    
    return sorted(unique, key=lambda x: x[0])

# ============================================================================
# Core Functions
# ============================================================================

def load_baseline() -> Set[str]:
    """Load baseline files from sequential scrape."""
    if not SCRAPER_CHECKPOINT.exists():
        return set()
    try:
        with open(SCRAPER_CHECKPOINT, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return set(data.get('seen_files', []))
    except:
        return set()

def fetch_page(page_num: int) -> Tuple[Optional[List[str]], str]:
    """Fetch a page and extract files."""
    url = f"{BASE_URL}?page={page_num}"
    
    try:
        resp = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
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
    except:
        return None, 'ERROR'

def format_num(n: int) -> str:
    """Format number with magnitude."""
    if n >= 1e15:
        return f"{n:,} ({n/1e15:.1f}Q)"
    elif n >= 1e12:
        return f"{n:,} ({n/1e12:.1f}T)"
    elif n >= 1e9:
        return f"{n:,} ({n/1e9:.1f}B)"
    elif n >= 1e6:
        return f"{n:,} ({n/1e6:.1f}M)"
    elif n >= 1e3:
        return f"{n:,}"
    else:
        return str(n)

def run_mitnick_probe():
    """Execute the Mitnick-style probe."""
    
    console.print(Panel.fit(
        "[bold red]╔═══════════════════════════════════════════════════════════╗[/bold red]\n"
        "[bold red]║[/bold red] [bold cyan]MITNICK MODE: The Art of Intrusion[/bold cyan]                      [bold red]║[/bold red]\n"
        "[bold red]╠═══════════════════════════════════════════════════════════╣[/bold red]\n"
        "[bold red]║[/bold red] [dim]\"Social engineering the DOJ pagination...\"[/dim]               [bold red]║[/bold red]\n"
        "[bold red]║[/bold red]                                                             [bold red]║[/bold red]\n"
        "[bold red]║[/bold red] Probing with:                                               [bold red]║[/bold red]\n"
        "[bold red]║[/bold red]   • Programmer magic numbers (0xDEADBEEF, 1337, etc.)       [bold red]║[/bold red]\n"
        "[bold red]║[/bold red]   • Mathematical patterns (primes, fibonacci, powers)       [bold red]║[/bold red]\n"
        "[bold red]║[/bold red]   • DOJ-specific patterns (EFTA ranges, dataset numbers)    [bold red]║[/bold red]\n"
        "[bold red]║[/bold red]   • Integer boundaries (32-bit limits, etc.)                [bold red]║[/bold red]\n"
        "[bold red]║[/bold red]   • Chaos theory random probes                              [bold red]║[/bold red]\n"
        "[bold red]║[/bold red]   • Edge of the abyss (near page limit)                     [bold red]║[/bold red]\n"
        "[bold red]╚═══════════════════════════════════════════════════════════╝[/bold red]",
        title="[bold]🔓 HACKING THE GIBSON[/bold]"
    ))
    
    # Load baseline
    baseline = load_baseline()
    console.print(f"\n[green]Baseline loaded: {len(baseline):,} known files[/green]")
    
    # Generate probe pages
    probes = generate_mitnick_pages()
    console.print(f"[cyan]Probes to execute: {len(probes)}[/cyan]\n")
    
    # Results tracking
    results = []
    discoveries = []
    seen_hashes = {}
    all_new_files: Set[str] = set()
    
    # Category stats
    cat_stats = {}
    
    # Create table
    table = Table(title="[bold red]MITNICK PROBE RESULTS[/bold red]", box=box.HEAVY, expand=True)
    table.add_column("#", justify="right", width=4)
    table.add_column("Page", style="cyan", width=22)
    table.add_column("Category", width=12)
    table.add_column("Reason", width=28)
    table.add_column("Status", width=8)
    table.add_column("Files", justify="right", width=6)
    table.add_column("New!", justify="right", width=5)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Probing...", total=len(probes))
        
        for i, (page_num, category, reason) in enumerate(probes):
            progress.update(task, description=f"[{category}] {reason}")
            
            files, status = fetch_page(page_num)
            
            # Track category
            if category not in cat_stats:
                cat_stats[category] = {'probed': 0, 'ok': 0, 'new_files': 0}
            cat_stats[category]['probed'] += 1
            
            if status == 'OK' and files is not None:
                cat_stats[category]['ok'] += 1
                
                # Check for new files
                new_files = [f for f in files if f not in baseline and f not in all_new_files]
                
                if new_files:
                    all_new_files.update(new_files)
                    cat_stats[category]['new_files'] += len(new_files)
                    discoveries.append({
                        'page': page_num,
                        'category': category,
                        'reason': reason,
                        'new_files': new_files
                    })
                    
                    # Highlight discovery!
                    table.add_row(
                        str(i + 1),
                        format_num(page_num),
                        f"[bold]{category}[/bold]",
                        reason,
                        "[green]OK[/green]",
                        str(len(files)),
                        f"[bold green]{len(new_files)}![/bold green]"
                    )
                    console.print(f"\n[bold green]*** DISCOVERY! Page {page_num:,} has {len(new_files)} NEW FILES! ***[/bold green]")
                    for f in new_files[:5]:
                        console.print(f"    [green]{f}[/green]")
                else:
                    table.add_row(
                        str(i + 1),
                        format_num(page_num),
                        f"[dim]{category}[/dim]",
                        reason,
                        "[green]OK[/green]",
                        str(len(files)),
                        "-"
                    )
                
                results.append({
                    'page': page_num,
                    'category': category,
                    'reason': reason,
                    'status': 'OK',
                    'files': len(files),
                    'new_files': len(new_files)
                })
            else:
                table.add_row(
                    str(i + 1),
                    format_num(page_num),
                    f"[dim]{category}[/dim]",
                    reason,
                    f"[red]{status}[/red]",
                    "-",
                    "-"
                )
                results.append({
                    'page': page_num,
                    'category': category,
                    'reason': reason,
                    'status': status,
                    'files': 0,
                    'new_files': 0
                })
            
            progress.advance(task)
            time.sleep(REQUEST_DELAY)
    
    # Show results table
    console.print(table)
    
    # Category summary
    console.print("\n")
    cat_table = Table(title="[bold]Category Summary[/bold]", box=box.ROUNDED)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Probed", justify="right")
    cat_table.add_column("OK", justify="right")
    cat_table.add_column("New Files", justify="right", style="green")
    
    for cat in sorted(cat_stats.keys()):
        stats = cat_stats[cat]
        cat_table.add_row(
            cat,
            str(stats['probed']),
            str(stats['ok']),
            str(stats['new_files']) if stats['new_files'] > 0 else "-"
        )
    
    console.print(cat_table)
    
    # Save results
    output = {
        'probe_time': datetime.now().isoformat(),
        'total_probes': len(probes),
        'baseline_files': len(baseline),
        'new_files_found': len(all_new_files),
        'new_files_list': list(all_new_files),
        'discoveries': discoveries,
        'category_stats': cat_stats,
        'results': results
    }
    
    with open(MITNICK_RESULTS, 'w') as f:
        json.dump(output, f, indent=2)
    
    # Final summary
    console.print("\n")
    if all_new_files:
        console.print(Panel.fit(
            f"[bold green]*** MITNICK PROBE FOUND {len(all_new_files)} NEW FILES! ***[/bold green]\n\n"
            f"Check {MITNICK_RESULTS} for details.",
            title="[bold]SUCCESS[/bold]"
        ))
    else:
        console.print(Panel.fit(
            "[bold yellow]No new files discovered.[/bold yellow]\n\n"
            "The DOJ pagination contains no hidden treasures.\n"
            "All paths lead to the same 77,766 files.\n\n"
            "[dim]\"Sometimes the only winning move is not to play.\" - WarGames[/dim]",
            title="[bold]PROBE COMPLETE[/bold]"
        ))
    
    console.print(f"\n[dim]Results saved to {MITNICK_RESULTS}[/dim]")

if __name__ == "__main__":
    try:
        run_mitnick_probe()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
