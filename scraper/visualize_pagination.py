#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Pagination Visualizer
=============================================

Generates graphs and analysis showing document distribution across pages.
Run anytime during or after scraping to visualize the pagination patterns.

TERMINOLOGY:
- True Wrap: Page with IDENTICAL content to an earlier page
- Redundant Page: Page with no new files but different from any single earlier page
- New Files: Files appearing for the first time on this page

Run with: python visualize_pagination.py

Author: DataSet 9 Completion Project
Date: February 2026
"""

import json
import sys
from pathlib import Path
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
CHECKPOINT_FILE = MANIFESTS_DIR / "scraper_checkpoint.json"
INDEX_FILE = MANIFESTS_DIR / "pagination_index.json"

console = Console()

# ============================================================================
# ASCII Graph Functions
# ============================================================================

def create_sparkline(values: list, width: int = 60) -> str:
    """Create a compact sparkline visualization."""
    if not values:
        return "No data"
    
    max_val = max(values) if values else 1
    
    # Aggregate into buckets
    bucket_size = max(1, len(values) // width)
    buckets = []
    for i in range(0, len(values), bucket_size):
        chunk = values[i:i + bucket_size]
        buckets.append(max(chunk) if chunk else 0)
    
    # Sparkline characters (8 levels)
    spark_chars = " ▁▂▃▄▅▆▇█"
    
    sparkline = ""
    for val in buckets[:width]:
        level = int(val / max_val * 8) if max_val > 0 else 0
        level = min(8, max(0, level))
        sparkline += spark_chars[level]
    
    return sparkline

def create_ascii_histogram(data: dict, width: int = 70, height: int = 12) -> str:
    """
    Create an ASCII histogram of new files per page.
    """
    if not data:
        return "No data to graph"
    
    pages = sorted(data.keys())
    values = [data[p] for p in pages]
    
    if not values:
        return "No data"
    
    max_val = max(values)
    min_page = min(pages)
    max_page = max(pages)
    
    # Aggregate into columns
    num_cols = width - 8  # Leave room for Y axis
    pages_per_col = max(1, len(pages) // num_cols)
    
    cols = []
    for i in range(0, len(pages), pages_per_col):
        chunk = values[i:i + pages_per_col]
        cols.append(max(chunk) if chunk else 0)
    
    cols = cols[:num_cols]
    
    # Build graph
    lines = []
    lines.append(f"New Documents Per Page (pages {min_page}-{max_page})")
    lines.append("─" * width)
    
    for row in range(height):
        threshold = max_val * (height - row) / height
        
        # Y axis label
        if row == 0:
            label = f"{max_val:>5} │"
        elif row == height - 1:
            label = f"{'0':>5} │"
        elif row == height // 2:
            label = f"{max_val // 2:>5} │"
        else:
            label = "      │"
        
        # Draw bars
        bar_chars = []
        for col_val in cols:
            if col_val >= threshold and col_val > 0:
                bar_chars.append("█")
            else:
                bar_chars.append(" ")
        
        lines.append(label + "".join(bar_chars))
    
    # X axis
    lines.append("      └" + "─" * len(cols))
    x_label = f"       {min_page}"
    x_label += " " * (len(cols) - len(str(max_page)) - len(str(min_page)))
    x_label += f"{max_page}"
    lines.append(x_label)
    
    return "\n".join(lines)

# ============================================================================
# Analysis Functions
# ============================================================================

def analyze_content_bands(pages_data: dict) -> list:
    """
    Find contiguous page ranges with new content.
    
    Returns list of {start, end, total_new, efta_min, efta_max}
    """
    pages = sorted(pages_data.keys())
    bands = []
    
    band_start = None
    band_new = 0
    band_efta_min = None
    band_efta_max = None
    
    for page in pages:
        info = pages_data[page]
        new_files = info.get("new_files", 0)
        
        if new_files > 0:
            if band_start is None:
                band_start = page
                band_new = new_files
                band_efta_min = info.get("min_efta")
                band_efta_max = info.get("max_efta")
            else:
                band_new += new_files
                if info.get("min_efta") and (band_efta_min is None or info["min_efta"] < band_efta_min):
                    band_efta_min = info["min_efta"]
                if info.get("max_efta") and (band_efta_max is None or info["max_efta"] > band_efta_max):
                    band_efta_max = info["max_efta"]
        else:
            if band_start is not None:
                bands.append({
                    "start": band_start,
                    "end": page - 1,
                    "total_new": band_new,
                    "efta_min": band_efta_min,
                    "efta_max": band_efta_max,
                })
                band_start = None
                band_new = 0
                band_efta_min = None
                band_efta_max = None
    
    # Close final band
    if band_start is not None:
        bands.append({
            "start": band_start,
            "end": pages[-1],
            "total_new": band_new,
            "efta_min": band_efta_min,
            "efta_max": band_efta_max,
        })
    
    return bands

def compute_statistics(pages_data: dict) -> dict:
    """Compute detailed statistics from page data."""
    pages = sorted(pages_data.keys())
    
    new_files_list = [pages_data[p].get("new_files", 0) for p in pages]
    file_counts = [pages_data[p].get("file_count", 0) for p in pages]
    
    total_unique = sum(new_files_list)
    total_refs = sum(file_counts)
    
    true_wraps = [p for p in pages if pages_data[p].get("is_true_wrap", False)]
    redundant = [p for p in pages if pages_data[p].get("is_redundant", False)]
    pages_with_new = [p for p in pages if pages_data[p].get("new_files", 0) > 0]
    
    return {
        "total_pages": len(pages),
        "min_page": min(pages) if pages else 0,
        "max_page": max(pages) if pages else 0,
        "total_unique_files": total_unique,
        "total_file_references": total_refs,
        "duplication_rate": ((total_refs - total_unique) / total_refs * 100) if total_refs > 0 else 0,
        "pages_with_new_content": len(pages_with_new),
        "true_wraps": true_wraps,
        "true_wraps_count": len(true_wraps),
        "redundant_pages": redundant,
        "redundant_count": len(redundant),
        "max_new_per_page": max(new_files_list) if new_files_list else 0,
        "avg_new_per_page": sum(new_files_list) / len(new_files_list) if new_files_list else 0,
        "new_files_by_page": {p: pages_data[p].get("new_files", 0) for p in pages},
    }

# ============================================================================
# Main
# ============================================================================

def load_data() -> tuple:
    """Load page data from checkpoint or index file."""
    
    # Try checkpoint first (has latest data during scraping)
    if CHECKPOINT_FILE.exists():
        console.print(f"[cyan]Loading from checkpoint...[/]")
        with open(CHECKPOINT_FILE) as f:
            data = json.load(f)
        
        pages_data = data.get("pages", {})
        # Convert string keys to int
        pages_data = {int(k): v for k, v in pages_data.items()}
        return pages_data, data
    
    # Try completed index
    if INDEX_FILE.exists():
        console.print(f"[cyan]Loading from completed index...[/]")
        with open(INDEX_FILE) as f:
            data = json.load(f)
        
        pages_data = data.get("pages", {})
        pages_data = {int(k): v for k, v in pages_data.items()}
        return pages_data, data
    
    return None, None

def main():
    console.print(Panel.fit(
        "[bold cyan]DOJ DataSet 9 - Pagination Visualizer[/]\n"
        "[dim]Analyzing scraper data for patterns...[/]",
        border_style="cyan"
    ))
    
    pages_data, full_data = load_data()
    
    if not pages_data:
        console.print("[red]No data found![/]")
        console.print("[yellow]Run scrape_doj_manifest.py first to generate data.[/]")
        sys.exit(1)
    
    # Compute statistics
    stats = compute_statistics(pages_data)
    
    # Stats table
    stats_table = Table(title="[bold]Scrape Statistics[/]", box=box.ROUNDED)
    stats_table.add_column("Metric", style="cyan", width=30)
    stats_table.add_column("Value", style="green", width=20)
    
    stats_table.add_row("Pages Scraped", f"{stats['total_pages']:,}")
    stats_table.add_row("Page Range", f"{stats['min_page']} → {stats['max_page']}")
    stats_table.add_row("─" * 25, "─" * 15)
    stats_table.add_row("[bold]Unique Files Found[/]", f"[bold green]{stats['total_unique_files']:,}[/]")
    stats_table.add_row("Total File References", f"{stats['total_file_references']:,}")
    stats_table.add_row("Duplication Rate", f"{stats['duplication_rate']:.1f}%")
    stats_table.add_row("─" * 25, "─" * 15)
    stats_table.add_row("Pages with New Content", f"{stats['pages_with_new_content']:,}")
    stats_table.add_row("[yellow]True Wraps[/]", f"[yellow]{stats['true_wraps_count']}[/]")
    stats_table.add_row("[dim]Redundant Pages[/]", f"[dim]{stats['redundant_count']}[/]")
    stats_table.add_row("─" * 25, "─" * 15)
    stats_table.add_row("Max New Files/Page", f"{stats['max_new_per_page']}")
    stats_table.add_row("Avg New Files/Page", f"{stats['avg_new_per_page']:.1f}")
    
    console.print(stats_table)
    console.print()
    
    # Sparkline
    new_by_page = stats["new_files_by_page"]
    pages_sorted = sorted(new_by_page.keys())
    values = [new_by_page[p] for p in pages_sorted]
    
    console.print("[bold]New Files Per Page (sparkline):[/]")
    sparkline = create_sparkline(values, width=65)
    console.print(f"  {sparkline}")
    if pages_sorted:
        console.print(f"  [dim]Page {pages_sorted[0]}{' ' * 50}Page {pages_sorted[-1]}[/]")
    console.print()
    
    # ASCII histogram
    console.print("[bold]Distribution Graph:[/]")
    histogram = create_ascii_histogram(new_by_page, width=70, height=10)
    console.print(histogram)
    console.print()
    
    # True wraps analysis
    if stats["true_wraps"]:
        wraps_table = Table(title="[bold yellow]True Pagination Wraps[/]", box=box.SIMPLE)
        wraps_table.add_column("Page", style="yellow")
        wraps_table.add_column("Wraps To", style="cyan")
        wraps_table.add_column("First File", style="dim")
        
        for wp in stats["true_wraps"][:15]:
            page_info = pages_data.get(wp, {})
            wraps_to = page_info.get("wraps_to_page", "?")
            files = page_info.get("files", [])
            first_file = files[0] if files else "?"
            wraps_table.add_row(str(wp), str(wraps_to), first_file)
        
        if len(stats["true_wraps"]) > 15:
            wraps_table.add_row("...", f"({len(stats['true_wraps']) - 15} more)", "")
        
        console.print(wraps_table)
        console.print()
    
    # Content bands
    bands = analyze_content_bands(pages_data)
    if bands:
        bands_table = Table(title="[bold green]Content Bands (pages with new files)[/]", box=box.SIMPLE)
        bands_table.add_column("Pages", style="cyan")
        bands_table.add_column("New Files", style="green")
        bands_table.add_column("EFTA Range", style="yellow")
        
        # Show top bands by new files
        top_bands = sorted(bands, key=lambda x: x["total_new"], reverse=True)[:10]
        for band in sorted(top_bands, key=lambda x: x["start"]):
            pages_str = f"{band['start']}-{band['end']}"
            efta_range = f"{band['efta_min'] or '?'} → {band['efta_max'] or '?'}"
            bands_table.add_row(pages_str, f"{band['total_new']:,}", efta_range)
        
        console.print(bands_table)
        console.print()
    
    # Legend
    console.print(Panel(
        "[bold]Terminology:[/]\n"
        "• [yellow]True Wrap[/]: Page with IDENTICAL content to an earlier page\n"
        "• [dim]Redundant[/]: Page with no new files, but not identical to any single earlier page\n"
        "• [green]New Files[/]: Files appearing for the first time",
        title="[dim]Legend[/]",
        border_style="dim"
    ))
    
    console.print("\n[dim]Run this anytime to see updated analysis. Data from checkpoint file.[/]")

if __name__ == "__main__":
    main()
