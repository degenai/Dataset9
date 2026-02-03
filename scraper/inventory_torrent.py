#!/usr/bin/env python3
"""
DOJ Epstein DataSet 9 - Torrent Inventory Tool
==============================================

Lists all EFTA files contained in the downloaded torrent archive.
Handles .tar.xz, .tar, .zip, and extracted directories.

Run with: python inventory_torrent.py <path_to_archive_or_directory>

Author: DataSet 9 Completion Project
Date: February 2026
"""

import argparse
import os
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MANIFESTS_DIR = PROJECT_ROOT / "manifests"
OUTPUT_FILE = MANIFESTS_DIR / "torrent_manifest.txt"

EFTA_PATTERN = re.compile(r'EFTA\d{8}')

console = Console()

# ============================================================================
# Inventory Functions
# ============================================================================

def inventory_tar_xz(archive_path: Path) -> set:
    """List EFTA files in a .tar.xz archive without extracting."""
    console.print(f"[cyan]Reading tar.xz archive (this may take a while)...[/]")
    
    files = set()
    
    # Use tar command for better performance with xz
    try:
        # Try using system tar (faster for large archives)
        result = subprocess.run(
            ['tar', '-tf', str(archive_path)],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                match = EFTA_PATTERN.search(line)
                if match:
                    files.add(match.group(0))
            return files
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    # Fall back to Python tarfile (slower but more portable)
    console.print("[yellow]Falling back to Python tarfile (slower)...[/]")
    
    with tarfile.open(archive_path, 'r:xz') as tar:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("[cyan]Reading archive...", total=None)
            
            for member in tar:
                match = EFTA_PATTERN.search(member.name)
                if match:
                    files.add(match.group(0))
                    progress.update(task, description=f"[cyan]Found {len(files):,} files...")
    
    return files

def inventory_tar(archive_path: Path) -> set:
    """List EFTA files in a .tar archive."""
    files = set()
    
    with tarfile.open(archive_path, 'r') as tar:
        for member in tar:
            match = EFTA_PATTERN.search(member.name)
            if match:
                files.add(match.group(0))
    
    return files

def inventory_zip(archive_path: Path) -> set:
    """List EFTA files in a .zip archive."""
    files = set()
    
    with zipfile.ZipFile(archive_path, 'r') as zf:
        for name in zf.namelist():
            match = EFTA_PATTERN.search(name)
            if match:
                files.add(match.group(0))
    
    return files

def inventory_directory(dir_path: Path) -> set:
    """List EFTA files in an extracted directory."""
    files = set()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning directory...", total=None)
        
        for root, dirs, filenames in os.walk(dir_path):
            for filename in filenames:
                match = EFTA_PATTERN.search(filename)
                if match:
                    files.add(match.group(0))
            progress.update(task, description=f"[cyan]Found {len(files):,} files...")
    
    return files

def inventory(path: Path) -> set:
    """Auto-detect format and inventory the archive/directory."""
    if path.is_dir():
        console.print(f"[cyan]Inventorying directory: {path}[/]")
        return inventory_directory(path)
    
    suffix = ''.join(path.suffixes).lower()
    
    if suffix in ['.tar.xz', '.txz']:
        return inventory_tar_xz(path)
    elif suffix == '.tar':
        return inventory_tar(path)
    elif suffix == '.zip':
        return inventory_zip(path)
    else:
        console.print(f"[yellow]Unknown format {suffix}, trying as tar.xz...[/]")
        return inventory_tar_xz(path)

# ============================================================================
# Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Inventory EFTA files in torrent archive or directory"
    )
    parser.add_argument(
        "path",
        type=Path,
        nargs='?',
        default=PROJECT_ROOT / "rDataHoarderMagnet" / "DataSet_9.tar.xz",
        help="Path to archive file or extracted directory"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_FILE,
        help=f"Output manifest file (default: {OUTPUT_FILE})"
    )
    args = parser.parse_args()
    
    if not args.path.exists():
        console.print(f"[red]Error: Path not found: {args.path}[/]")
        sys.exit(1)
    
    console.print(Panel.fit(
        f"[bold cyan]Torrent Inventory Tool[/]\n"
        f"Source: [dim]{args.path}[/]\n"
        f"Output: [dim]{args.output}[/]",
        border_style="cyan"
    ))
    
    # Inventory
    files = inventory(args.path)
    
    if not files:
        console.print("[red]No EFTA files found![/]")
        sys.exit(1)
    
    # Sort and save
    files = sorted(files)
    
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        f.write(f"# Torrent inventory - {len(files)} files\n")
        f.write(f"# Source: {args.path}\n")
        f.write(f"# Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")
        for efta in files:
            f.write(f"{efta}.pdf\n")
    
    console.print(Panel.fit(
        f"[bold green]Inventory Complete![/]\n\n"
        f"Total EFTA files: [bold]{len(files):,}[/]\n"
        f"EFTA range: [bold]{files[0]} - {files[-1]}[/]\n"
        f"Saved to: [cyan]{args.output}[/]",
        border_style="green"
    ))

if __name__ == "__main__":
    main()
