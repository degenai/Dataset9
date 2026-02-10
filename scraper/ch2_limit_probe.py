#!/usr/bin/env python3
"""
DOJ DataSet 9 - Chapter 2 Pagination Limit Probe
=================================================

Lightweight script to find pagination boundaries in both directions.
Modeled on the Chapter 1 find_exact_end.py that successfully found
the positive limit at 184,467,440,737,095,516.

Three checks:
  1. Page 0 sanity check (does it still work? what's on it?)
  2. Positive limit re-verify (has it changed since Ch1?)
  3. Negative limit search (exponential + binary, no artificial cap)

Author: DataSet 9 Completion Project
Date: February 2026 - Chapter 2
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
REQUEST_TIMEOUT = 15
DELAY = 0.8
USER_AGENT = os.getenv("DATASET9_USER_AGENT", "Mozilla/5.0 (compatible; DataSet9-Bot/1.0; +https://github.com/DataSet9-Project)")

# Chapter 1 findings
CH1_POSITIVE_LIMIT = 184_467_440_737_095_516  # 2^64 / 100

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "chapter2" / "negative_pages"
RESULTS_FILE = OUTPUT_DIR / "ch2_limit_probe.json"

console = Console()

# ============================================================================
# Core: test a single page
# ============================================================================

def test_page(page_num: int) -> tuple:
    """
    Test if a page works. Single attempt, no retries.
    Returns: (works: bool, status: str, file_count: int)
    """
    url = f"{BASE_URL}?page={page_num}"
    try:
        resp = requests.get(
            url,
            headers={'User-Agent': USER_AGENT},
            timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 404:
            return False, '404', 0
        if resp.status_code != 200:
            return False, f'HTTP_{resp.status_code}', 0
        if 'error' in resp.text.lower()[:500] and 'EFTA' not in resp.text:
            return False, 'ERROR_PAGE', 0

        soup = BeautifulSoup(resp.text, 'lxml')
        links = soup.find_all('a', href=re.compile(r'EFTA\d{8}\.pdf', re.IGNORECASE))
        return True, 'OK', len(links)

    except requests.Timeout:
        return False, 'TIMEOUT', 0
    except requests.RequestException:
        return False, 'ERROR', 0


def fmt(n: int) -> str:
    """Format a page number with magnitude label."""
    a = abs(n)
    sign = "-" if n < 0 else "+"
    if a >= 1e18:
        return f"{n:,} ({sign}{a/1e18:.1f} quintillion)"
    if a >= 1e15:
        return f"{n:,} ({sign}{a/1e15:.1f} quadrillion)"
    if a >= 1e12:
        return f"{n:,} ({sign}{a/1e12:.1f} trillion)"
    if a >= 1e9:
        return f"{n:,} ({sign}{a/1e9:.1f}B)"
    if a >= 1e6:
        return f"{n:,} ({sign}{a/1e6:.1f}M)"
    return f"{n:,}"

# ============================================================================
# Check 1: Page 0
# ============================================================================

def check_page_zero() -> dict:
    console.print("\n[bold cyan]Check 1: Page 0[/bold cyan]")
    works, status, files = test_page(0)
    if works:
        console.print(f"  [green]OK[/green] - {files} files")
    else:
        console.print(f"  [red]{status}[/red]")
    return {'page': 0, 'works': works, 'status': status, 'files': files}

# ============================================================================
# Check 2: Positive limit re-verify
# ============================================================================

def check_positive_limit() -> dict:
    console.print("\n[bold cyan]Check 2: Positive Limit (re-verify Ch1)[/bold cyan]")
    console.print(f"  [dim]Ch1 found: +{CH1_POSITIVE_LIMIT:,}[/dim]")

    history = []

    # Test the known limit
    console.print(f"  Testing +{CH1_POSITIVE_LIMIT:,} ...", end=" ")
    w1, s1, f1 = test_page(CH1_POSITIVE_LIMIT)
    history.append((CH1_POSITIVE_LIMIT, s1))
    console.print(f"[green]OK ({f1} files)[/green]" if w1 else f"[red]{s1}[/red]")

    # Test limit + 1
    console.print(f"  Testing +{CH1_POSITIVE_LIMIT + 1:,} ...", end=" ")
    w2, s2, f2 = test_page(CH1_POSITIVE_LIMIT + 1)
    history.append((CH1_POSITIVE_LIMIT + 1, s2))
    console.print(f"[green]OK ({f2} files)[/green]" if w2 else f"[red]{s2}[/red]")

    if w1 and not w2:
        console.print(f"  [green]Positive limit UNCHANGED at +{CH1_POSITIVE_LIMIT:,}[/green]")
        return {'last_working': CH1_POSITIVE_LIMIT, 'first_failing': CH1_POSITIVE_LIMIT + 1,
                'changed': False, 'history': history}

    if w1 and w2:
        console.print(f"  [yellow]Limit moved UP! Searching...[/yellow]")
        lw, ff, h = _exponential_then_binary(CH1_POSITIVE_LIMIT + 1, direction=1)
        history.extend(h)
        return {'last_working': lw, 'first_failing': ff, 'changed': True, 'history': history}

    if not w1:
        console.print(f"  [yellow]Ch1 limit no longer works! Searching lower...[/yellow]")
        # Quick check page 0
        w0, _, _ = test_page(0)
        if not w0:
            console.print(f"  [bold red]Page 0 broken too. Site may be down.[/bold red]")
            return {'last_working': None, 'first_failing': 0, 'changed': True, 'history': history}
        lw, ff, h = _exponential_then_binary(13000, direction=1)
        history.extend(h)
        return {'last_working': lw, 'first_failing': ff, 'changed': True, 'history': history}

    return {'last_working': None, 'first_failing': None, 'changed': True, 'history': history}

# ============================================================================
# Check 3: Negative limit
# ============================================================================

def check_negative_limit() -> dict:
    console.print("\n[bold cyan]Check 3: Negative Limit[/bold cyan]")

    # Quick sanity: does -1 work?
    console.print(f"  Testing page -1 ...", end=" ")
    w, s, f = test_page(-1)
    console.print(f"[green]OK ({f} files)[/green]" if w else f"[red]{s}[/red]")

    if not w:
        console.print(f"  [red]Negative pages not supported.[/red]")
        return {'supported': False, 'last_working': 0, 'first_failing': -1, 'history': [(-1, s)]}

    lw, ff, history = _exponential_then_binary(-1, direction=-1)
    return {'supported': True, 'last_working': lw, 'first_failing': ff, 'history': history}

# ============================================================================
# Shared: Exponential probe + Binary search
# ============================================================================

def _exponential_then_binary(start: int, direction: int) -> tuple:
    """
    direction=1 : search positive (doubling upward)
    direction=-1: search negative (doubling downward)

    Returns: (last_working, first_failing_or_None, history)
    """
    label = "POSITIVE" if direction == 1 else "NEGATIVE"
    history = []

    last_working = start
    probe = start * 2 if start != 0 else direction  # avoid 0*2=0

    console.print(f"\n  [bold]{label} exponential search[/bold]")

    # Phase 1: Exponential
    while True:
        console.print(f"    {fmt(probe):>45} ...", end=" ")
        works, status, files = test_page(probe)
        history.append((probe, status))

        if works:
            console.print(f"[green]OK ({files} files)[/green]")
            last_working = probe
            probe = probe * 2
        else:
            console.print(f"[red]{status}[/red]")
            first_failing = probe
            console.print(f"  [yellow]Bound found! Fails at {fmt(first_failing)}[/yellow]")
            break

        time.sleep(DELAY)

    # Phase 2: Binary search
    low = min(last_working, first_failing)
    high = max(last_working, first_failing)

    console.print(f"\n  [bold]{label} binary search[/bold]  ({fmt(low)} to {fmt(high)})")

    while high - low > 1:
        mid = (low + high) // 2
        works, status, files = test_page(mid)
        history.append((mid, status))

        tag = f"[green]OK[/green]" if works else f"[red]{status}[/red]"
        console.print(f"    {fmt(mid):>45} {tag}  range: {high - low:,}")

        if direction == 1:
            # Positive: works -> go higher, fails -> go lower
            if works:
                low = mid
            else:
                high = mid
        else:
            # Negative: works (more negative works) -> go lower, fails -> go higher
            if works:
                high = mid  # mid works, try more negative (lower)
            else:
                low = mid   # mid fails, boundary is above (higher)

        time.sleep(DELAY)

    # Confirm
    if direction == 1:
        last_w, first_f = low, high
    else:
        last_w, first_f = high, low  # high is less negative (works), low is more negative (fails)

    console.print(f"\n  [bold]Confirming...[/bold]")
    cw, cs, _ = test_page(last_w)
    history.append((last_w, cs))
    console.print(f"    {fmt(last_w):>45}  [green]{'OK' if cw else cs}[/green]")

    cf, cfs, _ = test_page(first_f)
    history.append((first_f, cfs))
    console.print(f"    {fmt(first_f):>45}  [red]{'OK' if cf else cfs}[/red]")

    return last_w, first_f, history

# ============================================================================
# Main
# ============================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]DOJ DataSet 9 - Ch2 Pagination Limit Probe[/bold cyan]\n\n"
        "1. Page 0 sanity check\n"
        "2. Positive limit re-verify\n"
        "3. Negative limit search\n\n"
        "[dim]Modeled on Ch1 find_exact_end.py (the one that worked)[/dim]",
        title="Mission"
    ))

    results = {'timestamp': datetime.now().isoformat()}

    # Check 1
    results['page_zero'] = check_page_zero()
    time.sleep(DELAY)

    # Check 2
    results['positive'] = check_positive_limit()
    time.sleep(DELAY)

    # Check 3
    results['negative'] = check_negative_limit()

    # ── Summary ──────────────────────────────────────────────────────────
    console.print("\n")
    table = Table(title="[bold]Pagination Limits[/bold]", box=box.DOUBLE, show_lines=True)
    table.add_column("Check", width=12, style="bold")
    table.add_column("Last Working", width=40, style="green")
    table.add_column("First Failing", width=40, style="red")
    table.add_column("Notes", width=20)

    # Page 0
    pz = results['page_zero']
    table.add_row("Page 0",
                  f"{'OK' if pz['works'] else 'FAIL'} ({pz['files']} files)",
                  "-", "")

    # Positive
    pos = results['positive']
    pos_note = "[bold red]CHANGED[/bold red]" if pos.get('changed') else "Same as Ch1"
    table.add_row("Positive",
                  f"+{pos['last_working']:,}" if pos.get('last_working') else "N/A",
                  f"+{pos['first_failing']:,}" if pos.get('first_failing') else "None",
                  pos_note)

    # Negative
    neg = results['negative']
    if not neg.get('supported'):
        neg_note = "Not supported"
    elif neg.get('first_failing') is None:
        neg_note = "No limit found"
    else:
        neg_note = ""
    table.add_row("Negative",
                  f"{neg['last_working']:,}" if neg.get('last_working') else "N/A",
                  f"{neg['first_failing']:,}" if neg.get('first_failing') else "None found",
                  neg_note)

    console.print(table)

    # Save
    # Convert history tuples for JSON
    for key in ('positive', 'negative'):
        if 'history' in results[key]:
            results[key]['history'] = [(p, s) for p, s in results[key]['history']]

    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)

    console.print(f"\n[dim]Saved to {RESULTS_FILE}[/dim]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
