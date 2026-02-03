#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Find Exact Pagination End
==================================================

Uses binary search to find the EXACT page number where DOJ pagination breaks.

Phase 1: Exponential probe to find upper bound (first failure)
Phase 2: Binary search between last success and first failure
Phase 3: Confirm exact transition point

Author: DataSet 9 Completion Project
Date: February 2026
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
REQUEST_TIMEOUT = 30
KNOWN_WORKING = 13000  # We know this works from sequential scrape

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
EXACT_END_LOG = MANIFESTS_DIR / "pagination_exact_end.json"

console = Console()

# ============================================================================
# Visual Components
# ============================================================================

def create_status_display(
    phase: str,
    current_test: int,
    lower_bound: int,
    upper_bound: int,
    last_result: str,
    history: list,
    search_range: Optional[int] = None
) -> Panel:
    """Create a rich panel showing current search state."""
    
    # Main status
    status_text = Text()
    status_text.append(f"Phase: ", style="dim")
    status_text.append(f"{phase}\n\n", style="bold cyan")
    
    status_text.append(f"Testing Page: ", style="dim")
    status_text.append(f"{current_test:,}\n", style="bold yellow")
    
    status_text.append(f"Lower Bound:  ", style="dim")
    status_text.append(f"{lower_bound:,} ", style="green")
    status_text.append("(works)\n", style="dim green")
    
    status_text.append(f"Upper Bound:  ", style="dim")
    if upper_bound == float('inf'):
        status_text.append("∞ (unknown)\n", style="dim")
    else:
        status_text.append(f"{upper_bound:,} ", style="red")
        status_text.append("(fails)\n", style="dim red")
    
    if search_range and search_range > 0:
        status_text.append(f"\nSearch Range: ", style="dim")
        status_text.append(f"{search_range:,} pages\n", style="cyan")
    
    status_text.append(f"\nLast Result:  ", style="dim")
    if "OK" in last_result or "works" in last_result.lower():
        status_text.append(last_result, style="green")
    elif "FAIL" in last_result or "404" in last_result:
        status_text.append(last_result, style="red")
    else:
        status_text.append(last_result, style="yellow")
    
    # Recent history
    if history:
        status_text.append("\n\n─── Recent Tests ───\n", style="dim")
        for h in history[-8:]:
            page, result = h
            if result == 'OK':
                status_text.append(f"  {page:>20,}  ", style="dim")
                status_text.append("✓ OK\n", style="green")
            else:
                status_text.append(f"  {page:>20,}  ", style="dim")
                status_text.append(f"✗ {result}\n", style="red")
    
    return Panel(status_text, title="[bold]Pagination End Search[/bold]", box=box.ROUNDED)

def create_progress_bar(lower: int, upper: int, current: int) -> Panel:
    """Create a visual representation of the search space."""
    if upper == float('inf') or upper <= lower:
        return Panel("[dim]Searching for upper bound...[/dim]", title="Search Space")
    
    width = 50
    range_size = upper - lower
    if range_size <= 0:
        return Panel("[green]Found exact boundary![/green]", title="Search Space")
    
    pos = int((current - lower) / range_size * width)
    pos = max(0, min(width - 1, pos))
    
    bar = ""
    bar += "[green]" + "█" * pos + "[/green]"
    bar += "[yellow]▓[/yellow]"
    bar += "[red]" + "░" * (width - pos - 1) + "[/red]"
    
    return Panel(
        f"[green]{lower:,}[/green] {bar} [red]{upper:,}[/red]\n"
        f"[dim]← works                                    fails →[/dim]",
        title="Search Space"
    )

# ============================================================================
# Core Functions
# ============================================================================

def test_page(page_num: int) -> Tuple[bool, str, int]:
    """
    Test if a page works.
    Returns: (works: bool, status: str, file_count: int)
    """
    url = f"{BASE_URL}?page={page_num}"
    
    try:
        resp = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (DataSet9 Research Project)'},
            timeout=REQUEST_TIMEOUT
        )
        
        if resp.status_code == 404:
            return False, '404', 0
        
        if resp.status_code != 200:
            return False, f'HTTP {resp.status_code}', 0
        
        # Check for error page content
        if 'error' in resp.text.lower()[:500] and 'EFTA' not in resp.text:
            return False, 'ERROR_PAGE', 0
        
        soup = BeautifulSoup(resp.text, 'lxml')
        links = soup.find_all('a', href=re.compile(r'EFTA\d{8}\.pdf', re.IGNORECASE))
        
        file_count = len(links)
        
        # Page works if we got a valid response (even with 0 files - that's still "working")
        return True, 'OK', file_count
        
    except requests.Timeout:
        return False, 'TIMEOUT', 0
    except requests.RequestException as e:
        return False, f'ERROR', 0

def find_upper_bound(start: int = KNOWN_WORKING) -> Tuple[int, int, list]:
    """
    Phase 1: Exponential search to find first failing page.
    Returns: (last_working, first_failing, history)
    """
    console.print("\n[bold cyan]Phase 1: Finding Upper Bound[/bold cyan]")
    console.print("[dim]Exponentially increasing page numbers until failure...[/dim]\n")
    
    last_working = start
    test_page_num = start * 2  # Start doubling
    history = []
    
    # Test known working first
    works, status, files = test_page(start)
    history.append((start, 'OK' if works else status))
    
    if not works:
        console.print(f"[red]Warning: Start page {start} doesn't work![/red]")
        return 0, start, history
    
    with Live(console=console, refresh_per_second=4) as live:
        while True:
            display = create_status_display(
                phase="1 - Exponential Search",
                current_test=test_page_num,
                lower_bound=last_working,
                upper_bound=float('inf'),
                last_result="Testing...",
                history=history
            )
            live.update(display)
            
            works, status, files = test_page(test_page_num)
            history.append((test_page_num, 'OK' if works else status))
            
            result_str = f"{status} ({files} files)" if works else status
            display = create_status_display(
                phase="1 - Exponential Search",
                current_test=test_page_num,
                lower_bound=last_working if works else last_working,
                upper_bound=float('inf') if works else test_page_num,
                last_result=result_str,
                history=history
            )
            live.update(display)
            
            if works:
                last_working = test_page_num
                # Double the test page, but cap at reasonable max
                if test_page_num > 10**18:
                    console.print(f"\n[bold green]Reached 10^18 and still working! DOJ has no practical limit.[/bold green]")
                    return last_working, float('inf'), history
                test_page_num = test_page_num * 2
            else:
                # Found upper bound!
                console.print(f"\n[bold yellow]Found upper bound: {test_page_num:,} fails![/bold yellow]")
                return last_working, test_page_num, history
            
            time.sleep(0.8)

def binary_search_exact(lower: int, upper: int, history: list) -> Tuple[int, list]:
    """
    Phase 2: Binary search to find exact transition point.
    Returns: (exact_boundary, history)
    """
    console.print("\n[bold cyan]Phase 2: Binary Search[/bold cyan]")
    console.print(f"[dim]Searching between {lower:,} and {upper:,}...[/dim]\n")
    
    with Live(console=console, refresh_per_second=4) as live:
        while upper - lower > 1:
            mid = (lower + upper) // 2
            search_range = upper - lower
            
            display = create_status_display(
                phase="2 - Binary Search",
                current_test=mid,
                lower_bound=lower,
                upper_bound=upper,
                last_result="Testing...",
                history=history,
                search_range=search_range
            )
            live.update(display)
            
            works, status, files = test_page(mid)
            history.append((mid, 'OK' if works else status))
            
            if works:
                lower = mid
                result_str = f"OK ({files} files) - moving up"
            else:
                upper = mid
                result_str = f"{status} - moving down"
            
            display = create_status_display(
                phase="2 - Binary Search",
                current_test=mid,
                lower_bound=lower,
                upper_bound=upper,
                last_result=result_str,
                history=history,
                search_range=upper - lower
            )
            live.update(display)
            
            time.sleep(0.8)
    
    return lower, history

def confirm_boundary(boundary: int, history: list) -> Tuple[int, int, list]:
    """
    Phase 3: Confirm the exact boundary by testing boundary and boundary+1.
    Returns: (last_working, first_failing, history)
    """
    console.print("\n[bold cyan]Phase 3: Confirming Boundary[/bold cyan]")
    
    # Test the boundary
    works_at_boundary, status1, files1 = test_page(boundary)
    history.append((boundary, 'OK' if works_at_boundary else status1))
    
    # Test boundary + 1
    works_after, status2, files2 = test_page(boundary + 1)
    history.append((boundary + 1, 'OK' if works_after else status2))
    
    if works_at_boundary and not works_after:
        return boundary, boundary + 1, history
    elif not works_at_boundary:
        # Need to search lower
        return boundary - 1, boundary, history
    else:
        # Both work, search higher
        return boundary + 1, boundary + 2, history

def run_search():
    """Main search execution."""
    console.print(Panel.fit(
        "[bold cyan]DOJ DataSet 9 - Exact Pagination End Finder[/bold cyan]\n\n"
        "Phase 1: Exponential probe to find upper bound\n"
        "Phase 2: Binary search to find exact transition\n"
        "Phase 3: Confirm exact boundary",
        title="Mission"
    ))
    
    all_history = []
    
    # Phase 1: Find upper bound
    last_working, first_failing, history = find_upper_bound(KNOWN_WORKING)
    all_history.extend(history)
    
    if first_failing == float('inf'):
        # No end found
        result = {
            'search_time': datetime.now().isoformat(),
            'result': 'NO_END_FOUND',
            'highest_tested': last_working,
            'history': [(p, s) for p, s in all_history]
        }
        with open(EXACT_END_LOG, 'w') as f:
            json.dump(result, f, indent=2)
        
        console.print(Panel.fit(
            f"[bold green]NO PAGINATION END FOUND![/bold green]\n\n"
            f"DOJ pagination works up to at least:\n"
            f"[bold]{last_working:,}[/bold]\n\n"
            f"The pagination appears to have no practical upper limit.",
            title="Result"
        ))
        return
    
    # Phase 2: Binary search
    exact_boundary, history = binary_search_exact(last_working, first_failing, all_history)
    all_history = history
    
    # Phase 3: Confirm
    confirmed_last, confirmed_first_fail, history = confirm_boundary(exact_boundary, all_history)
    all_history = history
    
    # Save results
    result = {
        'search_time': datetime.now().isoformat(),
        'result': 'BOUNDARY_FOUND',
        'last_working_page': confirmed_last,
        'first_failing_page': confirmed_first_fail,
        'history': [(p, s) for p, s in all_history]
    }
    with open(EXACT_END_LOG, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Final display
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]EXACT BOUNDARY FOUND![/bold green]\n\n"
        f"Last working page:  [green]{confirmed_last:,}[/green]\n"
        f"First failing page: [red]{confirmed_first_fail:,}[/red]\n\n"
        f"Total tests: {len(all_history)}\n"
        f"Saved to: {EXACT_END_LOG}",
        title="[bold]Result[/bold]",
        box=box.DOUBLE
    ))
    
    # Show history table
    table = Table(title="Test History", box=box.ROUNDED)
    table.add_column("Page", justify="right", style="cyan")
    table.add_column("Result", width=15)
    
    for page, status in all_history:
        if status == 'OK':
            table.add_row(f"{page:,}", "[green]✓ OK[/green]")
        else:
            table.add_row(f"{page:,}", f"[red]✗ {status}[/red]")
    
    console.print(table)

if __name__ == "__main__":
    try:
        run_search()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
