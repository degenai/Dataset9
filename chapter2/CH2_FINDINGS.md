# Chapter 2: Re-Investigation Findings

**Started**: February 6, 2026  
**Ch2 scrape completed**: February 8, 2026  
**Status**: Complete. Chapter 3 planned.

This document continues from the [Chapter 1 README](../README.md) and [Adjacent File Analysis](../ADJACENT_FILE_ANALYSIS.md).

---

## Background

Chapter 1 (Feb 2-3, 2026) scraped 13,000 pages of DOJ Dataset 9 pagination and found:
- 77,766 unique files on DOJ website (vs 531,256 in the torrent -- only 15% coverage)
- 3 files listed on DOJ but absent from the torrent (EFTA00326497, EFTA00326501, EFTA00534391)
- Pagination limit at exactly 2^64 / 100 (page 184,467,440,737,095,516)
- Adjacent file analysis linking the 3 missing files to Karyna Shuliak's April 2016 St. Thomas travel

Community tips on Feb 6 prompted Chapter 2:
- u/EmergencyBox4977: negative page numbers return content
- u/betterl8thannvr: the 3 missing files are "No Images Produced" video placeholders
- Reports that the DOJ pagination had changed since Ch1

---

## Finding 1: Pagination Limits

### Positive Limit -- Unchanged

| Metric | Value |
|--------|-------|
| Last working page | +184,467,440,737,095,516 |
| First failing page | +184,467,440,737,095,517 (HTTP 503) |
| Changed since Ch1? | **No** |

The positive limit remains exactly 2^64 / 100.

### Negative Pages -- No Hidden Content

Tested negative page numbers from -1 down to -10^99 (a 100-digit number). Every single negative page returned the **exact same content** as positive page 22 (Ch1 baseline). The DOJ's Drupal backend clamps all negative page values to a default page. The boundary at ~10^99 is a URL length limit, not a content boundary.

**Conclusion**: No hidden content in negative page space.

### Page 0

Returns 50 unique files spanning EFTA00039025 through EFTA00039882 -- the lowest-numbered EFTA files in the entire dataset. These are the same 50 files in both Ch1 and Ch2 manifests.

Page 0 is **not** a duplicate of page 22 (different content hashes). However, page 0's exact content is duplicated across 142 other pages in Ch1's pagination (pages 660, 661, 673, 674, etc.), consistent with the chaotic Drupal pager behavior seen throughout.

All negative pages return the content of page 22, not page 0 -- confirming the server's negative-number fallback lands on a different default than the first page.

---

## Finding 2: The Pagination Has Changed -- Dramatically

### The Numbers

| Metric | Ch1 (Feb 2-3) | Ch2 (Feb 7-8) |
|--------|---------------|---------------|
| Pages scraped | 13,001 | 40,001 |
| Unique files found | 77,766 | 345,262 |
| DOJ coverage of torrent | ~15% | ~65% |
| Productive pages (with new files) | ~1,553 | 7,253 |
| All content exhausted by page | ~10,500 | ~9,500 |

### Diff: Ch1 vs Ch2

| Metric | Count |
|--------|-------|
| Ch1 total files | 77,766 |
| Ch2 total files | 345,262 |
| Files in both scrapes | 50,799 |
| New in Ch2 (not in Ch1) | 294,463 |
| Gone from Ch1 (not in Ch2) | 26,967 |

Only **50,799 files** (65% of Ch1) appear in both scrapes. The pagination reshuffled which documents are visible, but the extended 40K scan recovered more overlap than the initial 13K run.

### Diff: Ch2 vs Torrent

| Metric | Count |
|--------|-------|
| Ch2 DOJ files | 345,262 |
| Torrent files | 531,256 |
| In common | 345,223 |
| DOJ only (not in torrent) | **39** |
| Torrent only (not on DOJ) | 186,033 |

Ch1 had 3 DOJ-only files. Ch2 has **39**. See Finding 5 below.

---

## Finding 3: Page Range Distribution (Ch2 vs Ch1)

Directly comparable to the [Ch1 page-range table](../README.md#efta-distribution-by-page-range). Ch2's pagination is far more productive per page, with a much more even spread across the full EFTA range.

### Ch2: EFTA Distribution by Page Range (40K pages)

```
Page Range    Min EFTA       Max EFTA       New Files
---------------------------------------------------------
0-499         EFTA00039025   EFTA00270154   16,643
500-999       EFTA00039025   EFTA00338545   21,858
1000-1499     EFTA00039025   EFTA00384056    8,268
1500-1999     EFTA00039025   EFTA00421621   22,168
2000-2499     EFTA00039025   EFTA00462528   13,300
2500-2999     EFTA00039025   EFTA00526569   21,812
3000-3499     EFTA00039025   EFTA00570364   12,075
3500-3999     EFTA00039025   EFTA00642517    9,333
4000-4499     EFTA00039025   EFTA00683520   22,448
4500-4999     EFTA00039025   EFTA00730390    8,737
5000-5499     EFTA00039025   EFTA00769836   14,972
5500-5999     EFTA00039025   EFTA00839148   19,655
6000-6499     EFTA00039025   EFTA00879353   19,421
6500-6999     EFTA00039025   EFTA00912862   21,821
7000-7499     EFTA00039025   EFTA00949489   23,385
7500-7999     EFTA00949490   EFTA00987980   24,794
8000-8499     EFTA00987981   EFTA01032635   24,947
8500-8999     EFTA01032636   EFTA01137729   24,735
9000-9499     EFTA01137733   EFTA01262781   14,890
9500-40000    (no new files - all wraps/redundant)

TOTAL UNIQUE FILES ON DOJ WEBSITE: 345,262
TOTAL FILES IN TORRENT: 531,256
```

### Ch1: EFTA Distribution by Page Range (13K pages)

```
Page Range    Min EFTA       Max EFTA       New Files
---------------------------------------------------------
0-499         EFTA00039025   EFTA00267311   21,842
500-999       EFTA00267314   EFTA00337032   18,983
1000-1499     EFTA00067524   EFTA00380774   14,396
1500-1999     EFTA00092963   EFTA00413050    2,709
2000-2499     EFTA00083599   EFTA00426736    4,432
2500-2999     EFTA00218527   EFTA00423620    4,515
3000-3499     EFTA00203975   EFTA00539216    2,692
3500-3999     EFTA00137295   EFTA00313715      329
4000-4499     EFTA00078217   EFTA00338754      706
4500-4999     EFTA00338134   EFTA00384534    2,825
5000-5499     EFTA00377742   EFTA00415182    1,353
5500-5999     EFTA00416356   EFTA00432673    1,214
6000-6499     EFTA00213187   EFTA00270156      501
6500-6999     EFTA00068280   EFTA00281003      554
7000-7499     EFTA00154989   EFTA00425720      106
7500-8499     (no new files - all wraps/redundant)
8500-8999     EFTA00168409   EFTA00169291       10
9000-9499     EFTA00154873   EFTA00154974       35
9500-9999     EFTA00139661   EFTA00377759      324
10000-10499   EFTA00140897   EFTA01262781      240
10500-12999   (no new files - all wraps/redundant)

TOTAL UNIQUE FILES ON DOJ WEBSITE: 77,766
TOTAL FILES IN TORRENT: 531,256
```

### Key Differences

1. **Yield per page band**: Ch2 averages ~18,000 new files per 500-page band through page 9,500. Ch1 dropped below 1,000 after page 3,500.
2. **Max EFTA progression**: Ch2's max EFTA climbs steadily (270K at page 500, up to 1.26M at page 9,500). Ch1's max EFTA was stuck below 540K for the entire scrape.
3. **Content exhaustion**: Both scrapes run dry around pages 9,500-10,500. Pages beyond that are pure wraps/redundant in both cases.
4. **Min EFTA**: Ch2 shows EFTA00039025 as min on nearly every band (low-numbered files mixed into every page). Ch1 showed a more varied min EFTA per band.

---

## Finding 4: Status of the 3 Original Missing Files

From the [Adjacent File Analysis](../ADJACENT_FILE_ANALYSIS.md), Ch1 identified 3 inaccessible files clustering around the Shuliak travel chain:

| EFTA | Ch1 Status | Ch2 Status | In Torrent? |
|------|-----------|-----------|-------------|
| 00326497 | Listed on DOJ, inaccessible | **Still listed** (recovered in 40K scan) | No |
| 00326501 | Listed on DOJ, inaccessible | **Still listed** (recovered in 40K scan) | No |
| 00534391 | Listed on DOJ, inaccessible | **Still listed** (in 39 DOJ-only files) | No |

- All 3 original inaccessible files persist in the Ch2 40K scan. They had dropped from the first 13K pages but reappeared deeper in the pagination.
- All 3 remain absent from the torrent.
- All 3 are now confirmed as "No Images Produced" video placeholders.
- All 3 remain absent from the torrent.

Community identification of these as "No Images Produced" video placeholders (see [Adjacent File Analysis update](../ADJACENT_FILE_ANALYSIS.md#update-feb-6-2026-no-images-produced-files)) means the corresponding video content exists somewhere -- possibly in Dataset 10.

---

## Finding 5: 39 DOJ-Only Files

Ch2 (40K pages) found 39 files on the DOJ website that are **not present in the torrent** (up from 3 in Ch1, up from 27 at 13K pages):

```
EFTA00039025  EFTA00326497  EFTA00326501  EFTA00387143  EFTA00387145
EFTA00387291  EFTA00416849  EFTA00416850  EFTA00416851  EFTA00416852
EFTA00417088  EFTA00417089  EFTA00417090  EFTA00417091  EFTA00417095
EFTA00417096  EFTA00417097  EFTA00417098  EFTA00478790  EFTA00481186
EFTA00534391  EFTA00770595  EFTA00823190  EFTA00823191  EFTA00823192
EFTA00823221  EFTA00823319  EFTA00877475  EFTA00901740  EFTA00919433
EFTA00919434  EFTA00932520  EFTA00932521  EFTA00932522  EFTA00932523
EFTA00984666  EFTA00984668  EFTA01135215  EFTA01135708
```

Note: The original 3 inaccessible files (326497, 326501, 534391) are all present. The extended 40K scan recovered 326497 and 326501 which had dropped from the first 13K pages.

Notable clusters suggesting related documents:
- **416849-416852 / 417088-417098**: Two tight batches of 4 and 8 files in the 416K-417K range (12 files total)
- **823190-823192 / 823221 / 823319**: Five files in the 823K range
- **919433-919434, 932520-932523**: Pairs/groups in the 919K-932K range
- **984666 / 984668**: Adjacent pair with a gap (984667 is in the torrent)
- **1135215 / 1135708**: Two files ~500 apart in the 1.13M range

These clusters warrant adjacent-file analysis similar to the [original 3 files investigation](../ADJACENT_FILE_ANALYSIS.md).

---

## Finding 6: Pagination Shifts Mid-Scan

After the 40K scan completed (~16 hours runtime), we ran a pagination change check against 20 sample pages. **11 out of 20 pages returned different content than when originally scraped.**

### Pagination Change Check Results

| Page | Checkpoint Hash | Live Hash | Files | Verdict |
|------|----------------|-----------|-------|---------|
| 0 | 98328bdbb54a4528 | 98328bdbb54a4528 | 50 | MATCH |
| 10 | 98328bdbb54a4528 | c139cf8634de2cfc | 50 | **CHANGED** |
| 50 | 98328bdbb54a4528 | 98328bdbb54a4528 | 50 | MATCH |
| 100 | 98328bdbb54a4528 | 98328bdbb54a4528 | 50 | MATCH |
| 200 | 98328bdbb54a4528 | 985ec7d2c6f4de4c | 50 | **CHANGED** |
| 500 | 39f5ed908d36e035 | 39f5ed908d36e035 | 50 | MATCH |
| 750 | ea9f5a298556407b | ea9f5a298556407b | 50 | MATCH |
| 1,000 | 98328bdbb54a4528 | 3d9a12c3ea3d2f02 | 50 | **CHANGED** |
| 1,500 | 91311ebcb81d5e04 | 91311ebcb81d5e04 | 50 | MATCH |
| 2,000 | cd08038e76083cc3 | cd08038e76083cc3 | 50 | MATCH |
| 3,000 | 98328bdbb54a4528 | 98328bdbb54a4528 | 50 | MATCH |
| 5,000 | 98328bdbb54a4528 | 30923b527d9d1cca | 50 | **CHANGED** |
| 7,500 | 6b559bc41d908d5f | 6b559bc41d908d5f | 50 | MATCH |
| 10,000 | 42ec10a75caeaaca | 34b2782ddecb7fbb | 41 | **CHANGED** |
| 12,000 | 42ec10a75caeaaca | 34b2782ddecb7fbb | 41 | **CHANGED** |
| 15,000 | empty | 34b2782ddecb7fbb | 41 | **CHANGED** |
| 20,000 | 98328bdbb54a4528 | 34b2782ddecb7fbb | 41 | **CHANGED** |
| 25,000 | 3bf43aba6aec15e6 | 34b2782ddecb7fbb | 41 | **CHANGED** |
| 28,000 | empty | 34b2782ddecb7fbb | 41 | **CHANGED** |
| 30,000 | empty | 34b2782ddecb7fbb | 41 | **CHANGED** |

### Observations

1. **Low pages partially stable**: Pages 0, 50, 100, 500, 750, 1500, 2000, 3000, 7500 held steady (9 of 20).
2. **Scattered low-page changes**: Pages 10, 200, 1000, 5000 flipped despite being in the productive range.
3. **Everything above 10,000 changed**: All high pages now return 41 files with the same hash (`34b2782ddecb7fbb`). Previously empty pages (15K, 28K, 30K) now have content. Previously 50-file pages now serve 41.
4. **The new "default page"** for high pages is 41 files, not 50. The pagination structure itself has changed -- not just the content mapping.

### Implications

This is the most significant methodological finding of the project:

- **Long-running scrapes are not internally consistent.** Our 16-hour scan straddled a pagination reshuffle. The early pages (0-9,500, scraped in the first ~3 hours) are likely on one pagination instance, while later pages may reflect a mix.
- **The data is still valuable.** All 345,262 unique files are real DOJ-indexed documents regardless of which pagination instance served them. The file-level data is sound; it's the per-page structure that's unreliable.
- **Periodic change checks are mandatory.** Any future scrape must include pagination stability verification at intervals, not just at the end.
- **The Mitnick probe was foregone.** With the pagination shifted mid-scan, running pattern probes against the new instance would produce results incomparable to the scrape data. Deferred to Chapter 3.

---

## Next Steps: Chapter 3

The pagination instability is now a documented, reproducible phenomenon. Before any further scraping:

1. **Characterize the shift frequency** -- how often does the DOJ pagination reshuffle? Hourly? Daily? On a schedule?
2. **Build a pagination-aware scraper** -- periodic change checks during the scan, with the ability to detect and flag when the underlying pagination has shifted
3. **Faster scraping** -- parallel processes to complete a full scan within a single pagination window (estimated ~3 hours for the productive 0-9,500 range)
4. **Investigate the diff** -- what exactly changed in the 11 shifted pages? Do the new pages contain files not in our manifest? The pagination change check needs to report file-level diffs, not just hash mismatches
5. **Adjacent file analysis** on the 39 DOJ-only files, particularly the 416K-417K cluster

---

*Chapter 2 analysis conducted: February 6-8, 2026*  
*Last updated: February 8, 2026*  
*License: Unlicense (Public Domain)*
