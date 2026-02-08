#!/usr/bin/env python3
"""EFTA number distribution: Ch1 vs Ch2 vs Torrent."""

import re
from pathlib import Path
from collections import Counter
from rich.console import Console
from rich.table import Table
from rich import box

PROJECT = Path(__file__).parent.parent
console = Console()

def load_efta_numbers(path: Path) -> list:
    nums = []
    with open(path) as f:
        for line in f:
            m = re.search(r"EFTA(\d{8})", line.strip(), re.I)
            if m:
                nums.append(int(m.group(1)))
    return sorted(nums)

def bucket(nums, size=50_000):
    c = Counter()
    for n in nums:
        c[(n // size) * size] += 1
    return dict(sorted(c.items()))

def main():
    ch1_path = PROJECT / "chapter1" / "manifests" / "doj_dataset9_manifest.txt"
    ch2_path = PROJECT / "chapter2" / "manifests" / "doj_dataset9_manifest.txt"
    torrent_path = PROJECT / "manifests" / "torrent_manifest.txt"
    if not torrent_path.exists():
        torrent_path = PROJECT / "chapter1" / "manifests" / "torrent_manifest.txt"

    sources = {}
    for name, path in [("Ch1", ch1_path), ("Ch2", ch2_path), ("Torrent", torrent_path)]:
        if path.exists():
            nums = load_efta_numbers(path)
            sources[name] = nums
            console.print(f"[green]{name}[/green]: {len(nums):,} files, EFTA range {nums[0]:08d}–{nums[-1]:08d}")
        else:
            console.print(f"[red]{name}[/red]: not found")

    # Bucketed distribution
    all_buckets = set()
    bucketed = {}
    for name, nums in sources.items():
        b = bucket(nums)
        bucketed[name] = b
        all_buckets.update(b.keys())

    table = Table(title="[bold]EFTA Distribution (50K buckets)[/bold]", box=box.ROUNDED)
    table.add_column("EFTA Range", style="cyan", width=22)
    for name in sources:
        table.add_column(name, justify="right", width=10)
    table.add_column("Ch2 vs Ch1", justify="right", width=12)

    for b in sorted(all_buckets):
        row = [f"{b:08d}–{b+49999:08d}"]
        ch1_val = bucketed.get("Ch1", {}).get(b, 0)
        ch2_val = bucketed.get("Ch2", {}).get(b, 0)
        for name in sources:
            val = bucketed[name].get(b, 0)
            row.append(f"{val:,}" if val else "[dim]–[/dim]")
        diff = ch2_val - ch1_val
        if diff > 0:
            row.append(f"[green]+{diff:,}[/green]")
        elif diff < 0:
            row.append(f"[red]{diff:,}[/red]")
        else:
            row.append("[dim]=[/dim]")
        table.add_row(*row)

    console.print(table)

    # DOJ-only files (Ch2 not in torrent)
    doj_only = PROJECT / "chapter2" / "manifests" / "doj_not_in_torrent.txt"
    if doj_only.exists():
        nums = load_efta_numbers(doj_only)
        console.print(f"\n[bold]27 DOJ-only files (not in torrent):[/bold]")
        for n in nums:
            console.print(f"  EFTA{n:08d}")

    # Summary stats
    if "Ch1" in sources and "Ch2" in sources:
        ch1_set = set(sources["Ch1"])
        ch2_set = set(sources["Ch2"])
        console.print(f"\n[bold]Range comparison:[/bold]")
        console.print(f"  Ch1: {min(sources['Ch1']):08d} to {max(sources['Ch1']):08d}")
        console.print(f"  Ch2: {min(sources['Ch2']):08d} to {max(sources['Ch2']):08d}")
        only_ch2 = ch2_set - ch1_set
        if only_ch2:
            console.print(f"  New in Ch2: {min(only_ch2):08d} to {max(only_ch2):08d} ({len(only_ch2):,} files)")

if __name__ == "__main__":
    main()
