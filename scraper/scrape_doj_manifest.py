#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Full Pagination Scraper & Index Builder
================================================================

Scrapes all pages of the DOJ DataSet 9 file listing, handling the
chaotic pagination behavior discovered on Feb 2, 2026.

METHODOLOGY:
- Scrapes each page sequentially with rate limiting
- Tracks EVERY file seen using a set for deduplication
- Distinguishes between:
  * TRUE WRAPS: Pages with identical content to an earlier page
  * REDUNDANT PAGES: Pages where all files were seen before (but not identical)
- Stores full page fingerprints (sorted file lists) for accurate wrap detection

Outputs:
- doj_dataset9_manifest.txt: Unique EFTA filenames (one per line)
- pagination_index.json: Full pagination structure for research
- pagination_summary.md: Human-readable analysis for journalists

Run with: python scrape_doj_manifest.py
Resume from checkpoint: python scrape_doj_manifest.py --resume

Author: DataSet 9 Completion Project
Date: February 2026
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict

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
    TimeRemainingColumn,
    MofNCompleteColumn,
)
from rich.table import Table
from rich import box

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
MAX_PAGE = 10000  # Scrape through this page number (extended for thorough coverage)
CHECKPOINT_INTERVAL = 50  # Save checkpoint every N pages
REQUEST_DELAY = 1.0  # Seconds between requests (be polite to DOJ)
REQUEST_TIMEOUT = 30  # Seconds
MAX_RETRIES = 3
CONSECUTIVE_EMPTY_THRESHOLD = None  # Disabled - run all pages regardless

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
CHECKPOINT_FILE = MANIFESTS_DIR / "scraper_checkpoint.json"

# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PageData:
    """Data collected from a single page."""
    page_num: int
    files: List[str]           # All files on this page
    file_count: int
    min_efta: Optional[str]
    max_efta: Optional[str]
    new_files: int             # Files not seen on earlier pages
    duplicate_files: int       # Files already seen
    scrape_time: str
    content_hash: str          # Hash of sorted file list for exact matching
    is_true_wrap: bool = False        # Exact duplicate of earlier page
    wraps_to_page: Optional[int] = None  # Which page it duplicates
    is_redundant: bool = False        # All files seen but not exact match

@dataclass  
class ScrapeState:
    """Full state of the scraping operation."""
    started_at: str
    last_updated: str
    current_page: int
    total_unique_files: int
    seen_files: Set[str]
    pages: Dict[int, PageData]
    page_hashes: Dict[str, int]  # content_hash -> first page with that content
    true_wraps: List[int]        # Pages that are exact duplicates
    redundant_pages: List[int]   # Pages with no new files but different order
    consecutive_empty: int = 0
    total_requests: int = 0
    total_errors: int = 0
    
    def to_checkpoint(self) -> dict:
        """Convert to JSON-serializable checkpoint."""
        return {
            "started_at": self.started_at,
            "last_updated": datetime.now().isoformat(),
            "current_page": self.current_page,
            "total_unique_files": self.total_unique_files,
            "seen_files": list(self.seen_files),
            "pages": {str(k): asdict(v) for k, v in self.pages.items()},
            "page_hashes": self.page_hashes,
            "true_wraps": self.true_wraps,
            "redundant_pages": self.redundant_pages,
            "consecutive_empty": self.consecutive_empty,
            "total_requests": self.total_requests,
            "total_errors": self.total_errors,
        }
    
    @classmethod
    def from_checkpoint(cls, data: dict) -> "ScrapeState":
        """Load from checkpoint file."""
        pages = {}
        for k, v in data.get("pages", {}).items():
            pages[int(k)] = PageData(**v)
        
        return cls(
            started_at=data["started_at"],
            last_updated=data["last_updated"],
            current_page=data["current_page"],
            total_unique_files=data["total_unique_files"],
            seen_files=set(data["seen_files"]),
            pages=pages,
            page_hashes=data.get("page_hashes", {}),
            true_wraps=data.get("true_wraps", data.get("wrap_points", [])),
            redundant_pages=data.get("redundant_pages", []),
            consecutive_empty=data.get("consecutive_empty", 0),
            total_requests=data.get("total_requests", 0),
            total_errors=data.get("total_errors", 0),
        )

# ============================================================================
# Console UI
# ============================================================================

console = Console()

def create_efta_range_table(state: ScrapeState) -> Table:
    """Create a table showing EFTA ranges discovered."""
    table = Table(title="[bold yellow]EFTA Ranges by Page Band[/]", box=box.SIMPLE)
    
    table.add_column("Page Range", style="cyan")
    table.add_column("Min EFTA", style="green")
    table.add_column("Max EFTA", style="green")
    table.add_column("New Files", style="yellow")
    
    # Group pages into bands of 500
    bands = {}
    for page_num, page_data in state.pages.items():
        band = (page_num // 500) * 500
        band_key = f"{band}-{band+499}"
        if band_key not in bands:
            bands[band_key] = {"min": None, "max": None, "count": 0}
        
        if page_data.min_efta:
            if bands[band_key]["min"] is None or page_data.min_efta < bands[band_key]["min"]:
                bands[band_key]["min"] = page_data.min_efta
            if bands[band_key]["max"] is None or page_data.max_efta > bands[band_key]["max"]:
                bands[band_key]["max"] = page_data.max_efta
        bands[band_key]["count"] += page_data.new_files
    
    for band_key in sorted(bands.keys(), key=lambda x: int(x.split("-")[0])):
        band = bands[band_key]
        if band["count"] > 0:
            table.add_row(
                band_key,
                band["min"] or "-",
                band["max"] or "-",
                f"{band['count']:,}"
            )
    
    return table

# ============================================================================
# Scraping Functions
# ============================================================================

def compute_content_hash(files: List[str]) -> str:
    """
    Compute a hash of the page content for exact duplicate detection.
    
    Uses sorted file list to ensure consistent hashing regardless of order.
    """
    if not files:
        return "empty"
    content = "|".join(sorted(files))
    return hashlib.md5(content.encode()).hexdigest()[:16]

def extract_efta_files(html: str) -> List[str]:
    """Extract EFTA filenames from page HTML."""
    soup = BeautifulSoup(html, 'lxml')
    files = []
    
    # Find all links containing EFTA numbers
    pattern = re.compile(r'EFTA\d{8}\.pdf')
    for link in soup.find_all('a', href=pattern):
        match = pattern.search(link.get('href', ''))
        if match:
            # Store without .pdf extension for cleaner data
            files.append(match.group(0).replace('.pdf', ''))
    
    return files

def scrape_page(page_num: int, session: requests.Session) -> Tuple[List[str], bool]:
    """
    Scrape a single page from DOJ.
    
    Returns:
        Tuple of (list of EFTA files, success boolean)
    """
    url = f"{BASE_URL}?page={page_num}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            files = extract_efta_files(response.text)
            return files, True
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                console.print(f"[red]Failed to scrape page {page_num}: {e}[/]")
                return [], False
    
    return [], False

# ============================================================================
# Checkpoint Functions
# ============================================================================

def save_checkpoint(state: ScrapeState):
    """Save current state to checkpoint file."""
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_data = state.to_checkpoint()
    
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint_data, f)
    
    # Also save current manifest
    manifest_path = MANIFESTS_DIR / "doj_dataset9_manifest.txt"
    with open(manifest_path, 'w') as f:
        for efta in sorted(state.seen_files):
            f.write(f"{efta}.pdf\n")

def load_checkpoint() -> Optional[ScrapeState]:
    """Load state from checkpoint file."""
    if not CHECKPOINT_FILE.exists():
        return None
    
    try:
        with open(CHECKPOINT_FILE, 'r') as f:
            data = json.load(f)
        return ScrapeState.from_checkpoint(data)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load checkpoint: {e}[/]")
        return None

# ============================================================================
# Output Generation
# ============================================================================

def generate_outputs(state: ScrapeState):
    """Generate all output files."""
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    
    console.print("\n[bold cyan]Generating output files...[/]")
    
    # 1. Manifest file (unique EFTA filenames)
    manifest_path = MANIFESTS_DIR / "doj_dataset9_manifest.txt"
    with open(manifest_path, 'w') as f:
        for efta in sorted(state.seen_files):
            f.write(f"{efta}.pdf\n")
    console.print(f"  [green]✓[/] {manifest_path.name}: {len(state.seen_files):,} unique files")
    
    # 2. Pagination index JSON
    index_path = MANIFESTS_DIR / "pagination_index.json"
    index_data = {
        "metadata": {
            "project": "Epstein DOJ DataSet 9 Completion Project",
            "purpose": "Document chaotic pagination behavior for journalism/research",
            "scraped_at": state.started_at,
            "completed_at": datetime.now().isoformat(),
            "total_pages_scraped": len(state.pages),
            "total_unique_files": state.total_unique_files,
            "total_requests": state.total_requests,
            "total_errors": state.total_errors,
        },
        "definitions": {
            "true_wrap": "Page with IDENTICAL content (same files) as an earlier page",
            "redundant_page": "Page where all files were seen before, but not identical to any single earlier page",
            "new_files": "Count of files on this page not seen on any earlier page",
            "content_hash": "MD5 hash of sorted file list for exact duplicate detection",
        },
        "summary": {
            "true_wraps_count": len(state.true_wraps),
            "true_wraps": state.true_wraps,
            "redundant_pages_count": len(state.redundant_pages),
            "redundant_pages": state.redundant_pages[:100],  # First 100 only
        },
        "pages": {str(k): asdict(v) for k, v in sorted(state.pages.items())},
    }
    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=2)
    console.print(f"  [green]✓[/] {index_path.name}: Full pagination structure")
    
    # 3. Summary markdown
    summary_path = MANIFESTS_DIR / "pagination_summary.md"
    generate_summary_markdown(state, summary_path)
    console.print(f"  [green]✓[/] {summary_path.name}: Human-readable analysis")

def generate_summary_markdown(state: ScrapeState, path: Path):
    """Generate human-readable summary for journalists."""
    
    # Calculate statistics
    pages_with_new = sum(1 for p in state.pages.values() if p.new_files > 0)
    total_files_seen = sum(p.file_count for p in state.pages.values())
    
    # Find EFTA range
    all_efta = sorted(state.seen_files)
    min_efta = all_efta[0] if all_efta else "N/A"
    max_efta = all_efta[-1] if all_efta else "N/A"
    
    # Calculate duplication rate
    if total_files_seen > 0:
        dup_rate = ((total_files_seen - state.total_unique_files) / total_files_seen) * 100
    else:
        dup_rate = 0
    
    content = f"""# DOJ Epstein DataSet 9 - Pagination Analysis Report

> **Purpose**: Document the chaotic pagination behavior of the DOJ's DataSet 9 file listing
> for journalists, researchers, and archivists.

## Executive Summary

The DOJ's pagination system for DataSet 9 exhibits **severely broken behavior** that makes
complete archival difficult. This report documents the specific failures observed.

## Key Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| Scrape Date | {state.started_at[:10]} | |
| Total Pages Scraped | {len(state.pages):,} | |
| **Total Unique Files** | **{state.total_unique_files:,}** | Deduplicated count |
| Total File References | {total_files_seen:,} | Including duplicates |
| Duplication Rate | {dup_rate:.1f}% | Files appearing on multiple pages |
| Pages with New Content | {pages_with_new:,} | |
| True Pagination Wraps | {len(state.true_wraps)} | Exact duplicate pages |
| Redundant Pages | {len(state.redundant_pages)} | No new files, not exact match |
| EFTA Range | {min_efta} - {max_efta} | |
| Scrape Errors | {state.total_errors} | Pages that failed to load |

## Definitions

For clarity in this analysis:

- **True Wrap**: A page that contains the **exact same files** as an earlier page.
  This indicates the pagination has literally looped back.
  
- **Redundant Page**: A page where **all files were already seen** on earlier pages,
  but the specific combination doesn't match any single earlier page. This indicates
  chaotic file distribution across pages.
  
- **New Files**: Files appearing on a page that were **never seen** on any earlier page.

## True Pagination Wraps

These pages contain **identical content** to earlier pages, indicating the pagination
system has looped back:

| Page | Identical To | First File | File Count |
|------|--------------|------------|------------|
"""
    
    # Add true wraps
    for wp in state.true_wraps[:30]:
        page_data = state.pages.get(wp)
        if page_data:
            content += f"| {wp} | Page {page_data.wraps_to_page} | {page_data.files[0] if page_data.files else 'N/A'} | {page_data.file_count} |\n"
    
    if len(state.true_wraps) > 30:
        content += f"\n*...and {len(state.true_wraps) - 30} more true wraps (see pagination_index.json)*\n"
    
    if not state.true_wraps:
        content += "| (none detected yet) | | | |\n"
    
    content += f"""
## Redundant Pages (Sample)

These pages had **no new files** but weren't exact duplicates of any single earlier page.
This suggests files are distributed chaotically across the pagination:

"""
    
    for rp in state.redundant_pages[:20]:
        page_data = state.pages.get(rp)
        if page_data:
            content += f"- Page {rp}: {page_data.file_count} files, all previously seen\n"
    
    if len(state.redundant_pages) > 20:
        content += f"\n*...and {len(state.redundant_pages) - 20} more redundant pages*\n"
    
    content += f"""
## EFTA Number Distribution

Files are **NOT** distributed sequentially across pages. Different page ranges
contain different EFTA number ranges:

"""
    
    # Add EFTA ranges by page band
    bands = {}
    for page_num, page_data in state.pages.items():
        band = (page_num // 500) * 500
        band_key = f"{band}-{band+499}"
        if band_key not in bands:
            bands[band_key] = {"min": None, "max": None, "new": 0}
        
        if page_data.min_efta and page_data.new_files > 0:
            if bands[band_key]["min"] is None or page_data.min_efta < bands[band_key]["min"]:
                bands[band_key]["min"] = page_data.min_efta
            if bands[band_key]["max"] is None or page_data.max_efta > bands[band_key]["max"]:
                bands[band_key]["max"] = page_data.max_efta
        bands[band_key]["new"] += page_data.new_files
    
    content += "| Page Range | EFTA Min | EFTA Max | New Files |\n"
    content += "|------------|----------|----------|----------|\n"
    
    for band_key in sorted(bands.keys(), key=lambda x: int(x.split("-")[0])):
        band = bands[band_key]
        if band["new"] > 0:
            content += f"| {band_key} | {band['min'] or '-'} | {band['max'] or '-'} | {band['new']:,} |\n"
    
    content += f"""
## Implications

### For Archivists
1. **Simple pagination won't work**: Stopping at any arbitrary page will miss files.
2. **Deduplication is mandatory**: The same file appears on multiple pages.
3. **Full scrape required**: Must scrape all {MAX_PAGE}+ pages to ensure completeness.

### For Journalists
1. **The chaos may be intentional or incompetent**: The pagination behavior is unusual.
2. **Files were likely uploaded in batches**: Different EFTA ranges on different page bands
   suggests multiple upload sessions.
3. **Verification is difficult**: Without a master list from DOJ, completeness cannot
   be independently verified.

### For Researchers
1. **Use the manifest file**: `doj_dataset9_manifest.txt` contains all unique files found.
2. **Raw data available**: `pagination_index.json` contains per-page data for analysis.
3. **Pattern analysis possible**: The wrap points and EFTA distribution may reveal
   upload timing and methodology.

## Methodology

This analysis was conducted by:

1. Scraping each page from 0 to {state.current_page} with 1-second delays
2. Extracting all EFTA file links from each page's HTML
3. Computing a content hash (MD5 of sorted file list) for each page
4. Comparing each page's hash against all previous pages to detect true wraps
5. Tracking all unique files across all pages using a set data structure
6. Recording detailed statistics for each page

The scraper source code is available for audit in `scraper/scrape_doj_manifest.py`.

## Data Files

| File | Description |
|------|-------------|
| `doj_dataset9_manifest.txt` | One filename per line, all unique files |
| `pagination_index.json` | Complete per-page data in JSON format |
| `pagination_summary.md` | This report |

---

*Generated by DataSet 9 Completion Project*  
*Scrape completed: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}*  
*For questions: See project repository*
"""
    
    with open(path, 'w') as f:
        f.write(content)

# ============================================================================
# Main Scraper
# ============================================================================

def run_scraper(resume: bool = False):
    """Main scraping loop with rich UI."""
    global MAX_PAGE
    
    # Initialize or resume state
    if resume:
        state = load_checkpoint()
        if state:
            console.print(f"[green]Resuming from checkpoint at page {state.current_page}[/]")
            console.print(f"[dim]  Unique files so far: {state.total_unique_files:,}[/]")
            console.print(f"[dim]  True wraps: {len(state.true_wraps)}, Redundant pages: {len(state.redundant_pages)}[/]")
            start_page = state.current_page + 1
        else:
            console.print("[yellow]No checkpoint found, starting fresh[/]")
            resume = False
    
    if not resume:
        state = ScrapeState(
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            current_page=0,
            total_unique_files=0,
            seen_files=set(),
            pages={},
            page_hashes={},
            true_wraps=[],
            redundant_pages=[],
        )
        start_page = 0
    
    # Print header
    console.print(Panel.fit(
        "[bold cyan]DOJ Epstein DataSet 9 - Full Pagination Scraper[/]\n\n"
        f"Pages: {start_page} → {MAX_PAGE}\n"
        f"Checkpoint: every {CHECKPOINT_INTERVAL} pages\n"
        f"Rate limit: {REQUEST_DELAY}s between requests\n\n"
        "[dim]Press Ctrl+C to stop (progress saved)[/]",
        title="[bold white]Starting Scrape[/]",
        border_style="cyan"
    ))
    
    # Create session with headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) DataSet9-Archival-Project/1.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        
        task = progress.add_task(
            "[cyan]Scraping pages...",
            total=MAX_PAGE - start_page + 1
        )
        
        for page_num in range(start_page, MAX_PAGE + 1):
            page_start = time.time()
            
            # Scrape page
            files, success = scrape_page(page_num, session)
            state.total_requests += 1
            
            if not success:
                state.total_errors += 1
                progress.update(task, advance=1, description=f"[red]Page {page_num} ERROR[/]")
                time.sleep(REQUEST_DELAY)
                continue
            
            # Process results
            new_files = [f for f in files if f not in state.seen_files]
            dup_files = [f for f in files if f in state.seen_files]
            content_hash = compute_content_hash(files)
            
            # Detect wrap type
            is_true_wrap = False
            wraps_to_page = None
            is_redundant = False
            
            if files:
                if content_hash in state.page_hashes:
                    # EXACT duplicate of an earlier page = true wrap
                    is_true_wrap = True
                    wraps_to_page = state.page_hashes[content_hash]
                    state.true_wraps.append(page_num)
                elif len(new_files) == 0:
                    # No new files but not an exact match = redundant
                    is_redundant = True
                    state.redundant_pages.append(page_num)
                else:
                    # Has new content - register this hash
                    state.page_hashes[content_hash] = page_num
            
            # Create page data
            page_data = PageData(
                page_num=page_num,
                files=files,  # Store all files for accurate analysis
                file_count=len(files),
                min_efta=min(files) if files else None,
                max_efta=max(files) if files else None,
                new_files=len(new_files),
                duplicate_files=len(dup_files),
                scrape_time=datetime.now().isoformat(),
                content_hash=content_hash,
                is_true_wrap=is_true_wrap,
                wraps_to_page=wraps_to_page,
                is_redundant=is_redundant,
            )
            
            # Update state
            state.seen_files.update(new_files)
            state.total_unique_files = len(state.seen_files)
            state.pages[page_num] = page_data
            state.current_page = page_num
            
            # Track consecutive empty pages
            if len(new_files) == 0:
                state.consecutive_empty += 1
            else:
                state.consecutive_empty = 0
            
            # Update progress description
            if is_true_wrap:
                desc = f"[cyan]Page {page_num}[/] | [bold yellow]TRUE WRAP → {wraps_to_page}[/]"
            elif is_redundant:
                desc = f"[cyan]Page {page_num}[/] | [yellow]redundant[/] | {state.total_unique_files:,} total"
            else:
                desc = f"[cyan]Page {page_num}[/] | [green]+{len(new_files)} new[/] | {state.total_unique_files:,} total"
            
            progress.update(task, advance=1, description=desc)
            
            # Checkpoint
            if page_num % CHECKPOINT_INTERVAL == 0 and page_num > 0:
                save_checkpoint(state)
                progress.console.print(
                    f"  [dim]💾 Checkpoint @ page {page_num}: "
                    f"{state.total_unique_files:,} unique files, "
                    f"{len(state.true_wraps)} wraps, "
                    f"{len(state.redundant_pages)} redundant[/]"
                )
            
            # Check stop condition (only if threshold is set)
            if CONSECUTIVE_EMPTY_THRESHOLD and state.consecutive_empty >= CONSECUTIVE_EMPTY_THRESHOLD:
                progress.console.print(
                    f"\n[yellow]⏹ Stopping: {CONSECUTIVE_EMPTY_THRESHOLD} consecutive pages with no new files[/]"
                )
                break
            
            # Rate limiting
            elapsed = time.time() - page_start
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)
    
    # Final checkpoint
    save_checkpoint(state)
    
    # Generate outputs
    generate_outputs(state)
    
    # Print final summary
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]✓ Scraping Complete![/]\n\n"
        f"[bold]Unique files:[/] {state.total_unique_files:,}\n"
        f"[bold]Pages scraped:[/] {len(state.pages):,}\n"
        f"[bold]True wraps:[/] {len(state.true_wraps)}\n"
        f"[bold]Redundant pages:[/] {len(state.redundant_pages)}\n"
        f"[bold]Errors:[/] {state.total_errors}\n\n"
        f"Output: [cyan]{MANIFESTS_DIR}[/]",
        title="[bold white]Summary[/]",
        border_style="green"
    ))
    
    # Show EFTA range table
    console.print("\n")
    console.print(create_efta_range_table(state))

# ============================================================================
# Entry Point
# ============================================================================

def main():
    global MAX_PAGE
    
    parser = argparse.ArgumentParser(
        description="Scrape DOJ Epstein DataSet 9 file listings"
    )
    parser.add_argument(
        "--resume", "-r",
        action="store_true",
        help="Resume from last checkpoint"
    )
    parser.add_argument(
        "--max-page",
        type=int,
        default=MAX_PAGE,
        help=f"Maximum page number to scrape (default: {MAX_PAGE})"
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start fresh, ignoring any existing checkpoint"
    )
    parser.add_argument(
        "--no-stop",
        action="store_true",
        help="Don't stop early - scrape all pages regardless of consecutive empty pages"
    )
    parser.add_argument(
        "--stop-after",
        type=int,
        default=None,
        help="Stop after N consecutive pages with no new files (default: disabled)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for manifests (default: manifests/)"
    )
    args = parser.parse_args()
    
    global CONSECUTIVE_EMPTY_THRESHOLD, MANIFESTS_DIR, CHECKPOINT_FILE
    MAX_PAGE = args.max_page
    
    # Handle custom output directory
    if args.output_dir:
        MANIFESTS_DIR = Path(args.output_dir)
        CHECKPOINT_FILE = MANIFESTS_DIR / "scraper_checkpoint.json"
        MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
        console.print(f"[cyan]Output directory: {MANIFESTS_DIR}[/cyan]")
    
    # Handle stop condition
    if args.no_stop:
        CONSECUTIVE_EMPTY_THRESHOLD = None
    elif args.stop_after:
        CONSECUTIVE_EMPTY_THRESHOLD = args.stop_after
    # else: keep default (None = don't stop)
    
    if args.fresh and CHECKPOINT_FILE.exists():
        console.print("[yellow]Removing existing checkpoint for fresh start...[/]")
        CHECKPOINT_FILE.unlink()
    
    try:
        run_scraper(resume=args.resume)
    except KeyboardInterrupt:
        console.print("\n[yellow]⏸ Interrupted! Progress saved to checkpoint.[/]")
        console.print("[dim]Resume with: python scrape_doj_manifest.py --resume[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
