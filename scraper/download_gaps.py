#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Gap Downloader
======================================

Downloads missing PDF files identified by comparing the DOJ manifest
against the torrent contents.

Features:
- Async downloads for speed
- Automatic rate limiting with backoff on 429 errors
- Resume capability (skips already downloaded files)
- PDF validation (checks magic bytes)
- Rich terminal UI with progress bars

Run with: python download_gaps.py
Resume: python download_gaps.py --resume

Author: DataSet 9 Completion Project
Date: February 2026
"""

import argparse
import asyncio
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set
import random

import aiohttp
import aiofiles
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    MofNCompleteColumn,
    DownloadColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich import box

# ============================================================================
# Configuration
# ============================================================================

BASE_PDF_URL = "https://www.justice.gov/epstein/files/DataSet%209/"
DEFAULT_CONCURRENCY = 3  # Parallel downloads
MIN_CONCURRENCY = 1
REQUEST_DELAY = 1.0  # Base delay between requests (per worker)
JITTER_MAX = 0.5  # Random jitter added to delay
REQUEST_TIMEOUT = 60  # Seconds
MAX_RETRIES = 3
BACKOFF_MULTIPLIER = 2
MIN_PDF_SIZE = 1024  # Minimum valid PDF size (1KB)
PDF_MAGIC = b'%PDF'

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
DOWNLOADS_DIR = PROJECT_ROOT / "downloads" / "dataset9_gaps"
LOG_FILE = PROJECT_ROOT / "downloads" / "download.log"
FAILED_FILE = PROJECT_ROOT / "downloads" / "failed_downloads.txt"
PROGRESS_FILE = PROJECT_ROOT / "downloads" / "download_progress.json"

# ============================================================================
# Console UI
# ============================================================================

console = Console()

class DownloadStats:
    """Track download statistics."""
    def __init__(self):
        self.started_at = datetime.now()
        self.total_files = 0
        self.completed = 0
        self.skipped = 0
        self.failed = 0
        self.total_bytes = 0
        self.rate_limited = 0
        self.current_concurrency = DEFAULT_CONCURRENCY
        
    def success_rate(self) -> float:
        total = self.completed + self.failed
        return (self.completed / total * 100) if total > 0 else 100.0

# ============================================================================
# Download Functions
# ============================================================================

async def download_file(
    session: aiohttp.ClientSession,
    efta_name: str,
    stats: DownloadStats,
    semaphore: asyncio.Semaphore,
) -> bool:
    """
    Download a single PDF file.
    
    Returns True if successful, False if failed.
    """
    url = f"{BASE_PDF_URL}{efta_name}.pdf"
    output_path = DOWNLOADS_DIR / f"{efta_name}.pdf"
    
    # Skip if already exists and valid
    if output_path.exists():
        if output_path.stat().st_size >= MIN_PDF_SIZE:
            # Quick validation - check PDF magic bytes
            with open(output_path, 'rb') as f:
                if f.read(4) == PDF_MAGIC:
                    stats.skipped += 1
                    return True
        # File exists but invalid - delete and redownload
        output_path.unlink()
    
    async with semaphore:
        for attempt in range(MAX_RETRIES):
            try:
                # Add jitter to avoid thundering herd
                await asyncio.sleep(REQUEST_DELAY + random.uniform(0, JITTER_MAX))
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                    if response.status == 429:
                        # Rate limited - back off
                        stats.rate_limited += 1
                        backoff = BACKOFF_MULTIPLIER ** (attempt + 1)
                        await asyncio.sleep(backoff)
                        continue
                    
                    if response.status == 404:
                        # File doesn't exist on server
                        log_failure(efta_name, "404 Not Found")
                        stats.failed += 1
                        return False
                    
                    response.raise_for_status()
                    
                    content = await response.read()
                    
                    # Validate PDF
                    if len(content) < MIN_PDF_SIZE:
                        log_failure(efta_name, f"Too small: {len(content)} bytes")
                        stats.failed += 1
                        return False
                    
                    if not content.startswith(PDF_MAGIC):
                        log_failure(efta_name, "Invalid PDF magic bytes")
                        stats.failed += 1
                        return False
                    
                    # Write file
                    async with aiofiles.open(output_path, 'wb') as f:
                        await f.write(content)
                    
                    stats.completed += 1
                    stats.total_bytes += len(content)
                    return True
                    
            except asyncio.TimeoutError:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(BACKOFF_MULTIPLIER ** attempt)
                else:
                    log_failure(efta_name, "Timeout")
                    stats.failed += 1
                    return False
                    
            except aiohttp.ClientError as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(BACKOFF_MULTIPLIER ** attempt)
                else:
                    log_failure(efta_name, str(e))
                    stats.failed += 1
                    return False
        
        return False

def log_failure(efta_name: str, reason: str):
    """Log a failed download."""
    with open(FAILED_FILE, 'a') as f:
        f.write(f"{efta_name}\t{reason}\t{datetime.now().isoformat()}\n")

async def run_downloads(files_to_download: List[str], concurrency: int = DEFAULT_CONCURRENCY):
    """Run the download process with progress UI."""
    
    stats = DownloadStats()
    stats.total_files = len(files_to_download)
    
    # Create output directory
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize failed log
    if FAILED_FILE.exists():
        # Keep existing failures, just append
        pass
    else:
        FAILED_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FAILED_FILE, 'w') as f:
            f.write("# Failed downloads log\n")
            f.write("# Format: EFTA_NAME\\tREASON\\tTIMESTAMP\n\n")
    
    # Print header
    console.print(Panel.fit(
        f"[bold cyan]DOJ Epstein DataSet 9 - Gap Downloader[/]\n"
        f"Files to download: [bold]{len(files_to_download):,}[/]\n"
        f"Concurrency: [bold]{concurrency}[/]\n"
        f"Output: [dim]{DOWNLOADS_DIR}[/]",
        title="[bold white]Starting Downloads[/]",
        border_style="cyan"
    ))
    
    # Create semaphore for concurrency control
    semaphore = asyncio.Semaphore(concurrency)
    
    # Create HTTP session
    connector = aiohttp.TCPConnector(limit=concurrency * 2, limit_per_host=concurrency)
    async with aiohttp.ClientSession(
        connector=connector,
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) DataSet9-Archival-Project/1.0',
            'Accept': 'application/pdf,*/*',
        }
    ) as session:
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            
            task = progress.add_task(
                "[cyan]Downloading...",
                total=len(files_to_download)
            )
            
            # Process in batches
            batch_size = concurrency * 10
            for i in range(0, len(files_to_download), batch_size):
                batch = files_to_download[i:i + batch_size]
                
                tasks = [
                    download_file(session, efta, stats, semaphore)
                    for efta in batch
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Update progress
                completed_in_batch = sum(1 for r in results if r is True)
                progress.update(
                    task,
                    advance=len(batch),
                    description=f"[cyan]Downloading[/] | [green]{stats.completed:,} OK[/] | [yellow]{stats.skipped:,} skip[/] | [red]{stats.failed} fail[/]"
                )
                
                # Adaptive rate limiting
                if stats.rate_limited > 10:
                    console.print("[yellow]Many 429s detected - reducing concurrency[/]")
                    concurrency = max(MIN_CONCURRENCY, concurrency - 1)
                    stats.rate_limited = 0
    
    # Print summary
    elapsed = datetime.now() - stats.started_at
    
    console.print("\n")
    console.print(Panel.fit(
        f"[bold green]Downloads Complete![/]\n\n"
        f"Successful: [bold green]{stats.completed:,}[/]\n"
        f"Skipped (already had): [bold yellow]{stats.skipped:,}[/]\n"
        f"Failed: [bold red]{stats.failed:,}[/]\n"
        f"Total bytes: [bold]{stats.total_bytes / (1024**3):.2f} GB[/]\n"
        f"Duration: [bold]{elapsed}[/]\n"
        f"Success rate: [bold]{stats.success_rate():.1f}%[/]\n\n"
        f"Failed downloads logged to: [dim]{FAILED_FILE}[/]",
        title="[bold white]Summary[/]",
        border_style="green" if stats.failed == 0 else "yellow"
    ))

# ============================================================================
# Gap Analysis
# ============================================================================

def load_manifest(path: Path) -> Set[str]:
    """Load a manifest file into a set of EFTA names (without .pdf)."""
    if not path.exists():
        console.print(f"[red]Error: Manifest not found: {path}[/]")
        sys.exit(1)
    
    files = set()
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove .pdf extension if present
                if line.endswith('.pdf'):
                    line = line[:-4]
                files.add(line)
    return files

def compute_gap(doj_manifest: Path, torrent_manifest: Optional[Path]) -> List[str]:
    """
    Compute the gap between DOJ manifest and torrent contents.
    
    If torrent_manifest is None, returns all DOJ files.
    """
    doj_files = load_manifest(doj_manifest)
    console.print(f"[cyan]DOJ manifest:[/] {len(doj_files):,} files")
    
    if torrent_manifest and torrent_manifest.exists():
        torrent_files = load_manifest(torrent_manifest)
        console.print(f"[cyan]Torrent manifest:[/] {len(torrent_files):,} files")
        
        gap = doj_files - torrent_files
        console.print(f"[bold green]Gap (files to download):[/] {len(gap):,} files")
    else:
        console.print("[yellow]No torrent manifest - will download all DOJ files[/]")
        gap = doj_files
    
    return sorted(gap)

# ============================================================================
# Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Download missing DOJ Epstein DataSet 9 PDFs"
    )
    parser.add_argument(
        "--doj-manifest",
        type=Path,
        default=MANIFESTS_DIR / "doj_dataset9_manifest.txt",
        help="Path to DOJ manifest file"
    )
    parser.add_argument(
        "--torrent-manifest",
        type=Path,
        default=MANIFESTS_DIR / "torrent_manifest.txt",
        help="Path to torrent manifest file (optional)"
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"Number of parallel downloads (default: {DEFAULT_CONCURRENCY})"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry previously failed downloads"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files to download (for testing)"
    )
    args = parser.parse_args()
    
    # Check DOJ manifest exists
    if not args.doj_manifest.exists():
        console.print(f"[red]Error: DOJ manifest not found: {args.doj_manifest}[/]")
        console.print("[yellow]Run scrape_doj_manifest.py first to generate the manifest[/]")
        sys.exit(1)
    
    # Compute files to download
    torrent_manifest = args.torrent_manifest if args.torrent_manifest.exists() else None
    files_to_download = compute_gap(args.doj_manifest, torrent_manifest)
    
    if args.limit:
        files_to_download = files_to_download[:args.limit]
        console.print(f"[yellow]Limited to {args.limit} files for testing[/]")
    
    if not files_to_download:
        console.print("[green]No files to download - you're up to date![/]")
        return
    
    # Save gap list
    gap_file = MANIFESTS_DIR / "missing_files.txt"
    with open(gap_file, 'w') as f:
        for efta in files_to_download:
            f.write(f"{efta}.pdf\n")
    console.print(f"[dim]Gap list saved to {gap_file}[/]\n")
    
    # Run downloads
    try:
        asyncio.run(run_downloads(files_to_download, args.concurrency))
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted! Progress saved - run again to resume.[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
