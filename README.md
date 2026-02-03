# Epstein DOJ DataSet 9 - Pagination Analysis & Archive Tools

Mission: Exhaustive analysis of DOJ Epstein Files DataSet 9 pagination to identify gaps, document anomalies, and preserve evidence.

## Key Findings (Feb 2-3, 2026)

### 3 Files Appear to be Scrubbed

These files are listed in DOJ pagination but cannot be downloaded:

- EFTA00326497 - Returns error page
- EFTA00326501 - Returns error page  
- EFTA00534391 - Returns error page

These files are NOT in any public torrent. This is potential evidence of document removal.

### The Torrent (87 GB) is More Complete Than DOJ Website

- DOJ Website (13,000 pages scraped): 77,766 files
- 86GB Torrent: 531,256 files
- DOJ-only files (not in torrent): 3 (all inaccessible)

The DOJ website only exposes ~15% of Dataset 9's actual contents.

### Pagination Limit Discovered

The DOJ pagination has an exact limit: page 184,467,440,737,095,516

This is exactly 2^64 / 100 (max unsigned 64-bit integer divided by 100).

The pagination is an infinite loop - the same ~77k files cycle forever across 184 quadrillion pages. No hidden content exists at extreme page numbers.

## EFTA Ranges by Page Band

```
Page Range    Min EFTA       Max EFTA       New Files
---------------------------------------------------------
0-499         EFTA00039025   EFTA00267311   21,842
500-999       EFTA00039025   EFTA00337032   18,983
1000-1499     EFTA00039025   EFTA00380774   14,396
1500-1999     EFTA00039025   EFTA00413050   2,709
2000-2499     EFTA00039025   EFTA00426736   4,432
2500-2999     EFTA00039025   EFTA00423620   4,515
3000-3499     EFTA00039025   EFTA00539216   2,692
3500-3999     EFTA00039025   EFTA00314873   329
4000-4499     EFTA00039025   EFTA00339594   706
4500-4999     EFTA00039025   EFTA00385086   2,825
5000-5499     EFTA00039025   EFTA00415182   1,353
5500-5999     EFTA00039025   EFTA00432673   1,214
6000-6499     EFTA00039025   EFTA00270156   501
6500-6999     EFTA00039025   EFTA00283711   554
7000-7499     EFTA00039025   EFTA00425720   106
8500-8999     EFTA00039025   EFTA00238253   10
9000-9499     EFTA00039025   EFTA00156979   35
9500-9999     EFTA00039025   EFTA00377759   324

TOTAL UNIQUE FILES: 77,766
```

## Quick Start

```bash
cd scraper
pip install -r requirements.txt

# Run the sequential scraper
python scrape_doj_manifest.py

# Random exploration probe
python exploration_probe.py --random-only --samples 100

# Find the exact pagination limit
python find_exact_end.py

# Scrape backwards from the end
python scrape_from_end.py

# Mitnick-style pattern probe
python mitnick_probe.py
```

## Project Structure

```
.
├── scraper/
│   ├── scrape_doj_manifest.py    # Main sequential pagination scraper
│   ├── exploration_probe.py      # Random page exploration
│   ├── find_exact_end.py         # Binary search for pagination limit
│   ├── find_pagination_end.py    # Initial exponential probe
│   ├── scrape_from_end.py        # Backwards scraper from limit
│   ├── mitnick_probe.py          # Hacker-pattern exploration
│   ├── visualize_pagination.py   # Data visualization
│   ├── inventory_torrent.py      # Torrent file lister
│   ├── download_gaps.py          # Gap downloader
│   └── requirements.txt
├── manifests/
│   ├── doj_dataset9_manifest.txt    # 77,766 unique files from DOJ
│   ├── torrent_manifest.txt         # 531,256 files in torrent
│   ├── doj_not_in_torrent.txt       # 3 inaccessible files
│   ├── scraper_checkpoint.json      # Scraper state/resume data
│   ├── pagination_index.json        # Full pagination structure
│   ├── probe_results.json           # Random probe results
│   ├── pagination_exact_end.json    # Limit search results
│   └── mitnick_probe_results.json   # Pattern probe results
├── Dataset Diff Plan/
│   ├── FINDINGS_SUMMARY.md          # Comprehensive analysis
│   └── INACCESSIBLE_FILES.txt       # The 3 scrubbed files
├── FINAL_REDDIT_POST.txt            # Ready-to-post findings
└── README.md
```

## Scripts

### scrape_doj_manifest.py

Main sequential scraper - handles chaotic pagination with deduplication.

```bash
python scrape_doj_manifest.py              # Fresh start
python scrape_doj_manifest.py --resume     # Resume from checkpoint
python scrape_doj_manifest.py --fresh      # Force fresh start
```

### exploration_probe.py

Random sampling across huge page ranges.

```bash
python exploration_probe.py --random-only --samples 100
python exploration_probe.py --resume
```

### find_exact_end.py

Binary search to find exact pagination boundary.

```bash
python find_exact_end.py
```

### mitnick_probe.py

Hacker-brain pattern exploration - magic numbers, primes, fibonacci, edge cases.

```bash
python mitnick_probe.py
```

## Verification Results

- Sequential (0-13k): 13,000 pages tested, 77,766 files found
- Random (to 1B): 500 pages tested, 0 new files
- End zone (184Q backwards): 100 pages tested, 0 new files
- Mitnick patterns: 150 pages tested, 0 new files

Conclusion: All unique content is in pages 0-13,000. Higher pages are loops.

## The 3 Inaccessible Files

```
https://www.justice.gov/epstein/files/DataSet%209/EFTA00326497.pdf
https://www.justice.gov/epstein/files/DataSet%209/EFTA00326501.pdf
https://www.justice.gov/epstein/files/DataSet%209/EFTA00534391.pdf
```

All return "An error was encountered while processing the file" when accessed.

## Recommendations

1. Use the torrent as primary source - DOJ website hides 85% of content
2. Investigate the 3 inaccessible files - Evidence of potential removal
3. Cross-reference with other datasets - Similar patterns may exist

## License

Public domain for accountability research. All source documents are from DOJ public releases.

---

Analysis conducted: February 2-3, 2026
Sequential pages scraped: 13,000
Total DOJ requests: ~15,000+
Pagination limit discovered: 184,467,440,737,095,516
