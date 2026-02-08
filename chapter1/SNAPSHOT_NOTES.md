# Chapter 1: Initial Pagination Index & Analysis

**Date**: February 2-3, 2026  
**Snapshot preserved**: February 6, 2026

## What Was Done

1. Sequential scrape of DOJ Dataset 9 pages 0 through 13,000
2. Torrent inventory of the 86GB torrent (531,256 files)
3. Diff: DOJ scrape vs torrent
4. Extended probes: random pages up to 1 billion, mathematical patterns, Mitnick-style hacker patterns
5. Binary search for pagination limit (found: page 184,467,440,737,095,516 = 2^64/100)
6. Backward scrape from pagination limit
7. Adjacent file analysis of 3 inaccessible files

## Key Numbers

| Metric | Value |
|--------|-------|
| DOJ pages scraped | 13,001 (pages 0-13000) |
| Unique files on DOJ | 77,766 |
| Files in torrent | 531,256 |
| Files on DOJ but not in torrent | 3 (inaccessible) |
| Positive pagination limit | 184,467,440,737,095,516 |
| Negative pages tested | None (discovered later) |

## The 3 Inaccessible Files

- EFTA00326497
- EFTA00326501
- EFTA00534391

All return error pages on DOJ website. Not present in torrent.  
Later identified as "No Images Produced" placeholder PDFs for video content.

## Files in This Snapshot

- `manifests/` - Core scrape outputs (manifest, checkpoint, pagination index)
- `probe_results/` - Extended exploration results (random probe, Mitnick probe, pagination end search)
