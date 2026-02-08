#!/usr/bin/env python3
"""
DOJ DataSet 9 - Ch2 Mitnick Pattern Probe
==========================================

Expanded hacker-brain exploration for Chapter 2.
~400+ probes targeting pages beyond the sequential scrape range.
Compares against Ch2 baseline (345K+ files).

  python ch2_mitnick_probe.py

Author: DataSet 9 Completion Project
Date: February 2026 - Chapter 2
"""

import hashlib
import json
import random
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
# Config
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
TIMEOUT = 15
DELAY = 0.8
SKIP_BELOW = 50_000  # Sequential scrape covers 0-50K

END = 184_467_440_737_095_516  # Known positive limit

PROJECT_ROOT = Path(__file__).parent.parent
CH2_CHECKPOINT = PROJECT_ROOT / "chapter2" / "manifests" / "ch2_checkpoint.json"
OUTPUT_DIR = PROJECT_ROOT / "chapter2" / "probe_results"
RESULTS_FILE = OUTPUT_DIR / "ch2_mitnick_results.json"

console = Console()

# ============================================================================
# Probe generators
# ============================================================================

def generate_probes():
    """~400+ probes across all categories. Returns [(page, category, reason), ...]"""
    pages = []

    # ── 1. Geometric fill: 50K to 10M in fine steps ──────────────────────
    for n in [50000, 60000, 70000, 75000, 80000, 90000, 100000,
              110000, 120000, 125000, 130000, 140000, 150000,
              175000, 200000, 225000, 250000, 275000, 300000,
              350000, 400000, 450000, 500000, 550000, 600000,
              650000, 700000, 750000, 800000, 850000, 900000, 950000,
              1000000, 1100000, 1200000, 1300000, 1400000, 1500000,
              1750000, 2000000, 2500000, 3000000, 3500000, 4000000,
              4500000, 5000000, 6000000, 7000000, 7500000, 8000000,
              9000000, 10000000]:
        pages.append((n, "geometric", f"{n:,}"))

    # ── 2. Powers of 2 ───────────────────────────────────────────────────
    for exp in range(16, 55):
        v = 2**exp
        if v > SKIP_BELOW:
            pages.append((v, "power2", f"2^{exp}"))
            pages.append((v - 1, "power2", f"2^{exp}-1"))
            pages.append((v + 1, "power2", f"2^{exp}+1"))

    # ── 3. Powers of 10 ──────────────────────────────────────────────────
    for exp in range(5, 18):
        v = 10**exp
        pages.append((v, "power10", f"10^{exp}"))
        pages.append((v + 1, "power10", f"10^{exp}+1"))
        pages.append((v - 1, "power10", f"10^{exp}-1"))

    # ── 4. Programmer magic numbers ──────────────────────────────────────
    magics = [
        (0xDEADBEEF, "DEADBEEF"), (0xCAFEBABE, "CAFEBABE"),
        (0xBAADF00D, "BAADFOOD"), (0xFEEDFACE, "FEEDFACE"),
        (0x8BADF00D, "8BADFOOD"), (0xDEADC0DE, "DEADCODE"),
        (0xBADCAB1E, "BADCABLE"), (0xDEFEC8ED, "DEFECATED"),
        (0xD15EA5E, "DISEASE"), (0xCAFED00D, "CAFEDOOD"),
        (0xFACEB00C, "FACEBOOK"), (0xB16B00B5, "BIGBOOBS"),
        (0xBEEFCAFE, "BEEFCAFE"), (0xFEE1DEAD, "FEELDEAD"),
        (0xABAD1DEA, "ABADIDEA"), (0xDEADFA11, "DEADFALL"),
        (80085, "BOOBS"), (8008135, "BOOBIES"),
        (1337, "LEET"), (31337, "ELEET"),
        (420, "420"), (69, "Nice"), (666, "Beast"),
        (9001, "Over 9000"), (42, "Meaning of life"),
    ]
    for v, reason in magics:
        if v > SKIP_BELOW:
            pages.append((v, "magic", reason))

    # ── 5. Fibonacci ─────────────────────────────────────────────────────
    a, b = 1, 1
    while b < 10_000_000_000:
        a, b = b, a + b
        if b > SKIP_BELOW:
            pages.append((b, "fibonacci", f"Fib"))

    # ── 6. Primes ────────────────────────────────────────────────────────
    primes = [
        50021, 50023, 50033, 75011, 75017, 100003, 100019, 100043,
        150001, 200003, 250007, 500009, 750019, 1000003, 1000033,
        2000003, 5000017, 10000019, 10000079, 50000017, 100000007,
        1000000007, 1000000009,
    ]
    for p in primes:
        pages.append((p, "prime", f"Prime {p:,}"))

    # ── 7. DOJ / Epstein specifics ───────────────────────────────────────
    # EFTA numbers of the 27 DOJ-only files as page numbers
    doj_only = [
        39025, 387143, 387145, 387291, 534391,
        537470, 547917, 548119, 548155, 770595,
        823190, 823191, 823192, 823221, 823319,
        877475, 901740, 919433, 919434, 932520,
        932521, 932522, 932523, 984666, 984668,
        1135215, 1135708,
    ]
    for e in doj_only:
        if e > SKIP_BELOW:
            pages.append((e, "doj_only", f"EFTA{e:08d} as page"))

    # Dataset cross-references
    for ds in range(1, 15):
        for mult in [10000, 100000, 1000000]:
            v = ds * mult
            if v > SKIP_BELOW:
                pages.append((v, "doj", f"DS{ds} x {mult:,}"))

    # Epstein dates
    dates = [
        (20190810, "Epstein death"), (20060630, "First arrest"),
        (20190706, "Second arrest"), (20200702, "Maxwell arrest"),
        (19530120, "Epstein birth"), (20160413, "Shuliak travel"),
        (20240101, "Dataset release era"),
    ]
    for v, reason in dates:
        pages.append((v, "date", reason))

    # ── 8. Integer boundaries ────────────────────────────────────────────
    boundaries = [
        (65535, "u16 max"), (65536, "u16+1"),
        (16777215, "24-bit max"), (16777216, "2^24"),
        (2147483647, "i32 max"), (2147483648, "i32+1"),
        (4294967295, "u32 max"), (4294967296, "u32+1"),
    ]
    for v, reason in boundaries:
        if v > SKIP_BELOW:
            pages.append((v, "boundary", reason))

    # ── 9. Near the abyss (positive limit) ───────────────────────────────
    offsets = [1, 2, 5, 10, 22, 50, 100, 500, 1000, 10000,
               100000, 1000000, 10000000, 100000000]
    for off in offsets:
        pages.append((END - off, "abyss", f"limit - {off:,}"))
    # Fractions of limit
    for div in [2, 3, 4, 5, 7, 10, 100, 1000, 10000]:
        pages.append((END // div, "abyss", f"limit / {div}"))
    # Mirror the page-22 clamp
    pages.append((END - 22, "abyss", "limit - 22 (mirror neg clamp)"))

    # ── 10. Dead zone boundary probes ────────────────────────────────────
    # Ch1 content died around 7500-8500, Ch2 around 8000+
    # Content came back in Ch1 at 8500, 9200, 9850, 10000
    # Probe just beyond sequential scrape boundary
    for base in [50001, 50010, 50050, 50100, 50500, 51000, 52000, 55000]:
        pages.append((base, "dead_zone", f"Just past 50K"))

    # ── 11. Extended random scatter ──────────────────────────────────────
    random.seed(2026)  # Reproducible

    # 100 random in 50K-1M
    for _ in range(100):
        pages.append((random.randint(50001, 1000000), "random", "50K-1M scatter"))

    # 50 random in 1M-100M
    for _ in range(50):
        pages.append((random.randint(1000001, 100000000), "random", "1M-100M scatter"))

    # 30 random in 100M-10B
    for _ in range(30):
        pages.append((random.randint(100000001, 10000000000), "random", "100M-10B scatter"))

    # 20 random in 10B-1T
    for _ in range(20):
        pages.append((random.randint(10000000001, 1000000000000), "random", "10B-1T scatter"))

    # ── Dedupe and sort ──────────────────────────────────────────────────
    seen = set()
    unique = []
    for p, cat, reason in pages:
        if p not in seen and p > SKIP_BELOW:
            seen.add(p)
            unique.append((p, cat, reason))

    return sorted(unique, key=lambda x: x[0])

# ============================================================================
# Core
# ============================================================================

def load_baseline():
    if not CH2_CHECKPOINT.exists():
        console.print("[yellow]No Ch2 checkpoint. Running against empty baseline.[/yellow]")
        return set()
    with open(CH2_CHECKPOINT) as f:
        data = json.load(f)
    files = set(data.get("seen", []))
    console.print(f"[green]Ch2 baseline: {len(files):,} files[/green]")
    return files


def fetch_page(page: int):
    """Returns (files: list | None, status: str)."""
    url = f"{BASE_URL}?page={page}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (DS9-Mitnick-Ch2)"}, timeout=TIMEOUT)
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
        return None, "timeout"
    except requests.RequestException:
        return None, "error"


def fmt(n):
    a = abs(n)
    if a >= 1e15: return f"{n:,} ({a/1e15:.1f}Q)"
    if a >= 1e12: return f"{n:,} ({a/1e12:.1f}T)"
    if a >= 1e9:  return f"{n:,} ({a/1e9:.1f}B)"
    if a >= 1e6:  return f"{n:,} ({a/1e6:.1f}M)"
    return f"{n:,}"

# ============================================================================
# Main
# ============================================================================

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    console.print(Panel.fit(
        "[bold cyan]Ch2 Mitnick Probe[/bold cyan]\n\n"
        "Expanded hacker-brain search: ~400+ probes\n"
        "Magic numbers, powers, primes, fibonacci, DOJ patterns,\n"
        "integer boundaries, random scatter, near-limit exploration\n\n"
        "[dim]Skipping pages 0-50K (covered by sequential scrape)[/dim]",
        title="The Art of Intrusion"
    ))

    baseline = load_baseline()
    probes = generate_probes()
    console.print(f"[cyan]Probes: {len(probes)}[/cyan]\n")

    results = []
    all_new = set()
    cat_stats = {}

    for i, (page, cat, reason) in enumerate(probes, 1):
        files, status = fetch_page(page)

        if cat not in cat_stats:
            cat_stats[cat] = {"probed": 0, "ok": 0, "new": 0}
        cat_stats[cat]["probed"] += 1

        if status == "ok" and files is not None:
            cat_stats[cat]["ok"] += 1
            new = [f for f in files if f not in baseline and f not in all_new]

            if new:
                all_new.update(new)
                cat_stats[cat]["new"] += len(new)
                console.print(f"  [{i:>4}/{len(probes)}]  {fmt(page):>35}  [green]OK[/green]  {len(files)} files  [bold green]+{len(new)} NEW[/bold green]  [{cat}] {reason}")
                for f in new[:3]:
                    console.print(f"           [green]{f}[/green]")
            else:
                console.print(f"  [{i:>4}/{len(probes)}]  {fmt(page):>35}  [dim]OK  {len(files)} files[/dim]  [{cat}] {reason}")

            results.append({"page": page, "cat": cat, "reason": reason,
                            "status": "ok", "files": len(files), "new": len(new)})
        else:
            console.print(f"  [{i:>4}/{len(probes)}]  {fmt(page):>35}  [red]{status}[/red]  [{cat}] {reason}")
            results.append({"page": page, "cat": cat, "reason": reason,
                            "status": status, "files": 0, "new": 0})

        time.sleep(DELAY)

    # ── Category summary ─────────────────────────────────────────────────
    console.print()
    table = Table(title="[bold]Category Summary[/bold]", box=box.ROUNDED)
    table.add_column("Category", style="cyan", width=15)
    table.add_column("Probed", justify="right", width=8)
    table.add_column("OK", justify="right", width=8)
    table.add_column("New Files", justify="right", width=10)

    total_probed = 0
    total_ok = 0
    total_new = 0
    for cat in sorted(cat_stats):
        s = cat_stats[cat]
        total_probed += s["probed"]
        total_ok += s["ok"]
        total_new += s["new"]
        nf = f"[green]{s['new']}[/green]" if s["new"] else "[dim]-[/dim]"
        table.add_row(cat, str(s["probed"]), str(s["ok"]), nf)

    table.add_row("[bold]TOTAL[/bold]", f"[bold]{total_probed}[/bold]",
                  f"[bold]{total_ok}[/bold]", f"[bold green]{total_new}[/bold green]")
    console.print(table)

    # ── Save ─────────────────────────────────────────────────────────────
    output = {
        "timestamp": datetime.now().isoformat(),
        "total_probes": len(probes),
        "baseline_files": len(baseline),
        "new_files_found": len(all_new),
        "new_files_list": sorted(all_new),
        "category_stats": cat_stats,
        "results": results,
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    # ── Verdict ──────────────────────────────────────────────────────────
    console.print()
    if all_new:
        console.print(Panel.fit(
            f"[bold green]FOUND {len(all_new)} NEW FILES[/bold green]\n"
            f"Files not in Ch2 baseline ({len(baseline):,} files).\n"
            f"Saved to {RESULTS_FILE}",
            title="Discovery"
        ))
    else:
        console.print(Panel.fit(
            "[bold yellow]No new files discovered.[/bold yellow]\n"
            "All probed pages return content already in the Ch2 baseline.\n\n"
            "[dim]\"Sometimes the only winning move is not to play.\" - WarGames[/dim]",
            title="Probe Complete"
        ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted![/yellow]")
        sys.exit(0)
