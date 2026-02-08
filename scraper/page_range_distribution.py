#!/usr/bin/env python3
"""
Page Range Distribution - Ch1 style table
==========================================

Reads pagination_index.json and produces the page-range EFTA table
matching the format in the Ch1 README.

  python page_range_distribution.py

Author: DataSet 9 Completion Project
Date: February 2026 - Chapter 2
"""

import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import box

PROJECT_ROOT = Path(__file__).parent.parent
console = Console()

BAND_SIZE = 500


def load_index(path):
    with open(path) as f:
        return json.load(f)


def build_table(index_data, title):
    pages = index_data.get("pages", {})

    bands = {}
    for page_str, info in pages.items():
        page = int(page_str)
        band = (page // BAND_SIZE) * BAND_SIZE
        band_key = f"{band}-{band + BAND_SIZE - 1}"

        if band_key not in bands:
            bands[band_key] = {"min_efta": None, "max_efta": None, "new": 0, "sort": band}

        new_count = info.get("new", 0)
        bands[band_key]["new"] += new_count

        min_e = info.get("min_efta")
        max_e = info.get("max_efta")
        if min_e:
            if bands[band_key]["min_efta"] is None or min_e < bands[band_key]["min_efta"]:
                bands[band_key]["min_efta"] = min_e
        if max_e:
            if bands[band_key]["max_efta"] is None or max_e > bands[band_key]["max_efta"]:
                bands[band_key]["max_efta"] = max_e

    table = Table(title=f"[bold]{title}[/bold]", box=box.ROUNDED, show_lines=False)
    table.add_column("Page Range", style="cyan", width=14)
    table.add_column("Min EFTA", width=16)
    table.add_column("Max EFTA", width=16)
    table.add_column("New Files", justify="right", width=10)

    sorted_bands = sorted(bands.items(), key=lambda x: x[1]["sort"])

    # Collapse runs of zero-new bands (whether empty or all-seen dupes)
    i = 0
    while i < len(sorted_bands):
        key, data = sorted_bands[i]

        if data["new"] == 0:
            # Start of dead run
            start_sort = data["sort"]
            end_sort = data["sort"]
            while i < len(sorted_bands) and sorted_bands[i][1]["new"] == 0:
                end_sort = sorted_bands[i][1]["sort"]
                i += 1
            start_label = str(start_sort)
            end_label = str(end_sort + BAND_SIZE - 1)
            table.add_row(
                f"{start_label}-{end_label}",
                "[dim](no new files - all wraps/redundant)[/dim]", "", "[dim]0[/dim]"
            )
        else:
            min_e = data["min_efta"] or "—"
            max_e = data["max_efta"] or "—"
            new_str = f"[green]{data['new']:,}[/green]" if data["new"] > 0 else "[dim]0[/dim]"
            table.add_row(key, min_e, max_e, new_str)
            i += 1

    console.print(table)

    # Summary
    total_new = sum(d["new"] for d in bands.values())
    total_files = index_data.get("total_files", total_new)
    console.print(f"\n  [bold]TOTAL UNIQUE FILES: {total_files:,}[/bold]")
    console.print(f"  Pages scraped: {len(pages):,}")
    console.print()


def main():
    ch2_index = PROJECT_ROOT / "chapter2" / "manifests" / "pagination_index.json"

    if ch2_index.exists():
        data = load_index(ch2_index)
        build_table(data, "Ch2 EFTA Distribution by Page Range (40K pages)")
    else:
        console.print("[red]No Ch2 pagination_index.json found.[/red]")

    # Also show Ch1
    ch1_index = PROJECT_ROOT / "chapter1" / "manifests" / "pagination_index.json"
    if ch1_index.exists():
        data = load_index(ch1_index)
        build_table(data, "Ch1 EFTA Distribution by Page Range (13K pages)")


if __name__ == "__main__":
    main()
