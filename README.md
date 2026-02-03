# Epstein DOJ DataSet 9 Completion Project

**Mission:** Assemble the first complete public mirror of DOJ Epstein Files DataSet 9.

## Background

The DOJ removed ZIP downloads but individual PDFs remain accessible. Existing torrents are incomplete (~86 GiB of estimated 150-250+ GiB). This project identifies gaps, scrapes missing files, and packages for redistribution.

## Critical Discovery (Feb 2, 2026)

The DOJ pagination is **severely broken**:

- **~8,000+ unique pages** (not ~905 as initially thought)
- **~350,000-450,000 files** (not 45,000-50,000)
- **Chaotic wrap behavior**: Pages don't follow sequential order
- **Multiple wrap points**: Content loops back at pages 905, 1810, 2716, 4526, and more

This means the 86 GiB torrent may contain only **35-50%** of the complete dataset.

## Quick Start

```bash
# 1. Install dependencies
cd scraper
pip install -r requirements.txt

# 2. Run the manifest scraper (takes 2-4 hours)
python scrape_doj_manifest.py

# 3. Once torrent is downloaded, inventory it
python inventory_torrent.py ../rDataHoarderMagnet/DataSet_9.tar.xz

# 4. Download the gaps
python download_gaps.py
```

## Project Structure

```
.
├── scraper/
│   ├── scrape_doj_manifest.py   # Main pagination scraper
│   ├── download_gaps.py         # Gap downloader
│   ├── inventory_torrent.py     # Torrent file lister
│   └── requirements.txt
├── manifests/
│   ├── doj_dataset9_manifest.txt    # All unique files on DOJ
│   ├── pagination_index.json        # Full pagination structure
│   ├── pagination_summary.md        # Human-readable analysis
│   ├── wrap_points.txt              # Where pagination wraps
│   ├── torrent_manifest.txt         # Files in torrent
│   └── missing_files.txt            # Gap list (DOJ - torrent)
├── downloads/
│   └── dataset9_gaps/               # Downloaded PDFs
├── rDataHoarderMagnet/
│   └── DataSet_9.tar.xz             # Torrent download (in progress)
└── README.md
```

## Scripts

### scrape_doj_manifest.py

Scrapes all ~8,100 pages of the DOJ file listing, handling the chaotic pagination.

```bash
# Full scrape (2-4 hours)
python scrape_doj_manifest.py

# Resume from checkpoint
python scrape_doj_manifest.py --resume

# Scrape to specific page
python scrape_doj_manifest.py --max-page 1000
```

**Features:**
- Rich terminal UI with progress bars
- Automatic checkpoint every 50 pages
- Resume capability
- Pagination index for journalism research

### inventory_torrent.py

Lists all EFTA files in the torrent archive.

```bash
# Auto-detect format
python inventory_torrent.py ../rDataHoarderMagnet/DataSet_9.tar.xz

# For extracted directory
python inventory_torrent.py /path/to/extracted/folder
```

### download_gaps.py

Downloads files present in DOJ manifest but missing from torrent.

```bash
# Download all gaps
python download_gaps.py

# Adjust concurrency
python download_gaps.py --concurrency 5

# Test with limited files
python download_gaps.py --limit 100
```

**Features:**
- Async downloads for speed
- Automatic rate limiting on 429 errors
- PDF validation (magic bytes check)
- Resume capability (skips existing valid files)

## Pagination Findings

The DOJ website uses extremely buggy pagination:

| Page | EFTA Range | Notes |
|------|------------|-------|
| 0 | 00039025 | Start of dataset |
| 905 | 00039025 | WRAPS to page 0 |
| 910 | 00329xxx | Unique content again |
| 1810 | 00039025 | WRAPS again |
| 1811 | 00406xxx | New unique range |
| 2716 | 00039025 | WRAPS again |
| 3620 | 00577xxx | More unique content |
| 8000 | 00419xxx | Last confirmed unique |
| 8050+ | 00039025 | All wrap to beginning |

**Implications:**
1. Simple scrapers that stop at page 905 miss ~90% of the data
2. EFTA numbers don't follow page order
3. Deduplication is essential
4. The chaos may indicate intentional obfuscation or incompetence

## Outputs

After running the scripts, you'll have:

1. **`doj_dataset9_manifest.txt`** - Every unique EFTA filename from DOJ
2. **`pagination_index.json`** - Full pagination structure for researchers
3. **`pagination_summary.md`** - Human-readable analysis documenting the chaos
4. **`missing_files.txt`** - Files to download (DOJ - torrent)
5. **`downloads/dataset9_gaps/`** - The actual PDFs

## Distribution

Once complete:

1. Create final archive:
   ```bash
   # Merge torrent + gaps
   tar -xf rDataHoarderMagnet/DataSet_9.tar.xz -C output/
   cp downloads/dataset9_gaps/*.pdf output/
   
   # Compress
   tar -cf - output/ | xz -9 -T0 > DataSet_9_COMPLETE.tar.xz
   sha256sum DataSet_9_COMPLETE.tar.xz > DataSet_9_COMPLETE.tar.xz.sha256
   ```

2. Upload to:
   - Internet Archive (archive.org)
   - Create torrent and post to r/DataHoarder
   - Share with journalists/researchers

## License

This project is for public accountability research. All documents are from DOJ public releases.

---

*Project initiated: February 2026*
*For transparency and accountability*
