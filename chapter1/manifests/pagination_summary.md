# DOJ Epstein DataSet 9 - Pagination Analysis Report

> **Purpose**: Document the chaotic pagination behavior of the DOJ's DataSet 9 file listing
> for journalists, researchers, and archivists.

## Executive Summary

The DOJ's pagination system for DataSet 9 exhibits **severely broken behavior** that makes
complete archival difficult. This report documents the specific failures observed.

## Key Statistics

| Metric | Value | Notes |
|--------|-------|-------|
| Scrape Date | 2026-02-02 | |
| Total Pages Scraped | 13,001 | |
| **Total Unique Files** | **77,766** | Deduplicated count |
| Total File References | 512,431 | Including duplicates |
| Duplication Rate | 84.8% | Files appearing on multiple pages |
| Pages with New Content | 1,756 | |
| True Pagination Wraps | 3126 | Exact duplicate pages |
| Redundant Pages | 8119 | No new files, not exact match |
| EFTA Range | EFTA00039025 - EFTA01262781 | |
| Scrape Errors | 0 | Pages that failed to load |

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
| 660 | Page 0 | EFTA00039025 | 50 |
| 661 | Page 0 | EFTA00039025 | 50 |
| 673 | Page 0 | EFTA00039025 | 50 |
| 674 | Page 0 | EFTA00039025 | 50 |
| 675 | Page 0 | EFTA00039025 | 50 |
| 691 | Page 0 | EFTA00039025 | 50 |
| 703 | Page 0 | EFTA00039025 | 50 |
| 720 | Page 0 | EFTA00039025 | 50 |
| 721 | Page 0 | EFTA00039025 | 50 |
| 730 | Page 0 | EFTA00039025 | 50 |
| 731 | Page 0 | EFTA00039025 | 50 |
| 732 | Page 1 | EFTA00039882 | 50 |
| 751 | Page 0 | EFTA00039025 | 50 |
| 752 | Page 0 | EFTA00039025 | 50 |
| 753 | Page 1 | EFTA00039882 | 50 |
| 766 | Page 0 | EFTA00039025 | 50 |
| 768 | Page 0 | EFTA00039025 | 50 |
| 772 | Page 0 | EFTA00039025 | 50 |
| 773 | Page 0 | EFTA00039025 | 50 |
| 787 | Page 0 | EFTA00039025 | 50 |
| 789 | Page 0 | EFTA00039025 | 50 |
| 790 | Page 0 | EFTA00039025 | 50 |
| 820 | Page 0 | EFTA00039025 | 50 |
| 828 | Page 0 | EFTA00039025 | 50 |
| 829 | Page 0 | EFTA00039025 | 50 |
| 836 | Page 0 | EFTA00039025 | 50 |
| 838 | Page 0 | EFTA00039025 | 50 |
| 863 | Page 0 | EFTA00039025 | 50 |
| 867 | Page 0 | EFTA00039025 | 50 |
| 873 | Page 0 | EFTA00039025 | 50 |

*...and 3096 more true wraps (see pagination_index.json)*

## Redundant Pages (Sample)

These pages had **no new files** but weren't exact duplicates of any single earlier page.
This suggests files are distributed chaotically across the pagination:

- Page 22: 50 files, all previously seen
- Page 23: 50 files, all previously seen
- Page 48: 50 files, all previously seen
- Page 54: 50 files, all previously seen
- Page 63: 50 files, all previously seen
- Page 98: 50 files, all previously seen
- Page 99: 50 files, all previously seen
- Page 100: 50 files, all previously seen
- Page 101: 50 files, all previously seen
- Page 102: 50 files, all previously seen
- Page 104: 50 files, all previously seen
- Page 115: 50 files, all previously seen
- Page 123: 50 files, all previously seen
- Page 145: 50 files, all previously seen
- Page 161: 50 files, all previously seen
- Page 175: 50 files, all previously seen
- Page 180: 50 files, all previously seen
- Page 181: 50 files, all previously seen
- Page 182: 50 files, all previously seen
- Page 185: 50 files, all previously seen

*...and 8099 more redundant pages*

## EFTA Number Distribution

Files are **NOT** distributed sequentially across pages. Different page ranges
contain different EFTA number ranges:

| Page Range | EFTA Min | EFTA Max | New Files |
|------------|----------|----------|----------|
| 0-499 | EFTA00039025 | EFTA00267311 | 21,842 |
| 500-999 | EFTA00267314 | EFTA00337032 | 18,983 |
| 1000-1499 | EFTA00067524 | EFTA00380774 | 14,396 |
| 1500-1999 | EFTA00092963 | EFTA00413050 | 2,709 |
| 2000-2499 | EFTA00083599 | EFTA00426736 | 4,432 |
| 2500-2999 | EFTA00218527 | EFTA00423620 | 4,515 |
| 3000-3499 | EFTA00203975 | EFTA00539216 | 2,692 |
| 3500-3999 | EFTA00137295 | EFTA00313715 | 329 |
| 4000-4499 | EFTA00078217 | EFTA00338754 | 706 |
| 4500-4999 | EFTA00338134 | EFTA00384534 | 2,825 |
| 5000-5499 | EFTA00377742 | EFTA00415182 | 1,353 |
| 5500-5999 | EFTA00416356 | EFTA00432673 | 1,214 |
| 6000-6499 | EFTA00213187 | EFTA00270156 | 501 |
| 6500-6999 | EFTA00068280 | EFTA00281003 | 554 |
| 7000-7499 | EFTA00154989 | EFTA00425720 | 106 |
| 8500-8999 | EFTA00168409 | EFTA00169291 | 10 |
| 9000-9499 | EFTA00154873 | EFTA00154974 | 35 |
| 9500-9999 | EFTA00139661 | EFTA00377759 | 324 |
| 10000-10499 | EFTA00140897 | EFTA01262781 | 240 |

## Implications

### For Archivists
1. **Simple pagination won't work**: Stopping at any arbitrary page will miss files.
2. **Deduplication is mandatory**: The same file appears on multiple pages.
3. **Full scrape required**: Must scrape all 13000+ pages to ensure completeness.

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

1. Scraping each page from 0 to 13000 with 1-second delays
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
*Scrape completed: February 02, 2026 at 21:19:39*  
*For questions: See project repository*
