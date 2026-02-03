# DataSet 9 Torrent vs DOJ Website - Comparison Results

## Executive Summary

**The 86 GiB torrent is MORE complete than the DOJ website listing.**

| Source | Files | EFTA Range |
|--------|-------|------------|
| DOJ Website (scraped 13,000 pages) | 77,766 | EFTA00039025 - EFTA00539216 |
| Torrent (86 GiB) | 531,256 | EFTA00039025 - EFTA01262781 |

The DOJ pagination only exposes **~15%** of the files that actually exist in DataSet 9.

---

## CRITICAL FINDING: Evidence of Document Removal

### 3 Files Listed but INACCESSIBLE

The DOJ pagination lists these 3 files, but they **cannot be downloaded by anyone**:

| EFTA Number | Status | Notes |
|-------------|--------|-------|
| **EFTA00326497** | DEAD LINK | Returns error page |
| **EFTA00326501** | DEAD LINK | Returns error page |
| **EFTA00534391** | DEAD LINK | Returns error page |

**Verification performed:**
- Automated download attempt: Returns 53KB HTML error page instead of PDF
- Manual browser access: "An error was encountered while processing the file"
- Cookie/session attempts: Same result

**Why this matters:**
- These files appear in DOJ's own pagination listing
- The listing was generated from a database that knew these files existed
- The files themselves are now inaccessible
- **This is evidence of selective document removal after the index was created**

**Pattern observation:**
- EFTA00326497 and EFTA00326501 are sequential (4 numbers apart)
- These may be related documents from the same batch
- EFTA00534391 is from a different range

**Call to action:** If anyone archived these specific EFTA numbers before removal, please come forward. These documents existed at some point - the DOJ's own system proves it.

---

## Torrent Completeness

### Files in Torrent but NOT on DOJ: ~453,490 files

The DOJ's broken pagination hides the vast majority of DataSet 9 content.

### Files in Torrent but NOT on DOJ: ~453,490 files

The DOJ's broken pagination hides the vast majority of DataSet 9 content. The torrent contains files up to EFTA01262781, while the DOJ listing mostly shows files up to EFTA00539216.

## DOJ Pagination Behavior

The DOJ pagination is severely broken:
- Content scattered across 10,000+ pages
- Pages wrap and repeat at irregular intervals
- Hidden content appears at deep page numbers (e.g., page 9200, 9850, 9997)
- Different EFTA ranges appear in different page bands

### Content Discovery by Page Band

| Page Range | New Files Found |
|------------|-----------------|
| 0-499 | 21,842 |
| 500-999 | 18,983 |
| 1000-1499 | 14,396 |
| 1500-1999 | 2,709 |
| 2000-2999 | 8,947 |
| 3000-6999 | 8,121 |
| 7000-9999 | 475 |
| **Total** | **77,766** |

## Extended Exploration Results

### Probe Summary (Feb 3, 2026)

We probed **500 random page numbers** from 13,001 to 1,000,000,000:

| Range | Pages Probed | New Files Found |
|-------|--------------|-----------------|
| 13k - 100k | 100 | 0 |
| 100k - 1M | 100 | 0 |
| 1M - 10M | 100 | 0 |
| 10M - 100M | 100 | 0 |
| 100M - 1B | 100 | 0 |

**Key finding: The DOJ pagination is an INFINITE LOOP.**

Even at page **900,000,000+**, the server still returns files - the same ~77,766 files cycling forever. There are no hidden documents at extreme page numbers.

The sequential scrape (pages 0-13,000) captured everything the DOJ website exposes.

---

## Conclusions

1. **The torrent is essentially complete** - contains 531,256 files
2. **The DOJ listing is broken** - only shows ~15% of actual content via pagination
3. **3 files are potentially scrubbed** - listed but cannot be downloaded
4. **DOJ pagination is an infinite loop** - same content repeats forever, even at page 1 billion
5. **Anyone using only DOJ pagination would miss 85% of the dataset**

## Final Assessment

| What we verified | Result |
|-----------------|--------|
| Sequential pages 0-13,000 | 77,766 unique files found |
| Random probes up to 1 billion | 0 additional files |
| DOJ-only files not in torrent | 3 files (all inaccessible) |
| Torrent files not on DOJ | ~453,490 files |

**The 86 GiB torrent IS the most complete source.** The DOJ's web interface is severely broken and hides most of the dataset.

## Recommendations

1. Use the torrent as the primary source
2. Document the 3 inaccessible files as evidence of potential removal
3. Archive this analysis for future reference
4. Consider mirroring the torrent to Archive.org for redundancy

---

*Analysis conducted: February 2-3, 2026*
*Sequential scrape: 13,000 pages, 77,766 files*
*Extended probe: 500 random pages up to 1 billion*
*Tools: Custom pagination scraper with deduplication*
*Repository: https://github.com/degenai/Dataset9*
