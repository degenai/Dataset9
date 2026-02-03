# DataSet 9 Pagination Analysis Notes

## Observations During Scrape (Feb 2, 2026)

### Pattern Discovery

| Page Range | New Files/Page | Observation |
|------------|----------------|-------------|
| 0-400 | +50 | Fresh content, no overlap |
| 500s | +25 | **Transition zone** - 50% duplicates per page |
| 600s | +50 | New band of fresh content |
| ~700+ | varies | **First TRUE WRAPS appear** - exact page duplicates |

### Key Finding: Sharded/Batched Upload Theory

The pagination appears to cycle through separate upload batches:
- Band A → Overlap zone → Band B → Overlap → etc.
- The 50→25→50 pattern suggests interleaved data shards
- True wraps at 700+ indicate pagination is now hitting exact duplicate pages

---

## TODO: Post-Scrape Data Science Analysis

### Statistical Analysis
- [ ] Plot new_files vs page_number (scatter + trendline)
- [ ] Identify all transition points (where +50 drops to +25 or less)
- [ ] Cluster analysis on EFTA number ranges by page band
- [ ] Calculate periodicity of wrap patterns (is there a consistent cycle?)

### Pattern Mining
- [ ] Identify distinct "upload batches" based on EFTA number clustering
- [ ] Map which EFTA ranges appear on which page bands
- [ ] Detect if there's a mathematical relationship (modulo, etc.) in the pagination

### Forensic Questions
- [ ] Do the batch boundaries correlate with known DOJ release dates?
- [ ] Are certain EFTA ranges more "scattered" than others? (potential priority docs?)
- [ ] Is there evidence of selective removal? (gaps in EFTA sequences)

### Visualization Deliverables
- [ ] Heatmap: Page number vs EFTA number (showing the chaos visually)
- [ ] Timeline: New files discovered over pagination (cumulative + per-page)
- [ ] Network graph: Which pages share content with which other pages

### Tools to Consider
- pandas for data manipulation
- matplotlib/seaborn for visualization  
- scipy for statistical analysis
- networkx for page relationship graphs

---

## Raw Observations Log

*Timestamped notes during scrape:*

- **Page ~500**: Transition from +50 to +25 new files per page
- **Page ~600**: Back to +50 new files per page  
- **Page ~700**: First true wraps (exact duplicate pages) detected
- **Page 765**: +50 new
- **Page 766**: TRUE WRAP (first confirmed wrap point)
- **Page 800s**: +50 new pattern, occasional +22 randomly, wraps growing faster than redundants
- **Page 900s**: +50 new pattern holds steady
- **Page 1000s**: Still +50 new - massive dump of unique content continues
- **Page 1100s**: +50 new holds, wraps gaining on redundant count
- **Page 1500**: 55,221 unique - growth rate slowing
- **Page 1800**: 56,875 unique - only +1,654 in 300 pages (was +50/page earlier)
- **Page 2000**: 57,930 unique - asymptote forming
- **Page 2400s**: Mostly redundant pages, plateau at ~61,400 unique
- **Page 2460**: NEW TRANCHE - +50 new files suddenly! Fresh content band discovered

### Key Insights

1. **Initial dump (pages 0-1200)**: ~50 new files/page, rapid growth to ~45,000 files
2. **Slowdown (pages 1200-2400)**: Growth rate drops dramatically, mostly wraps/redundant  
3. **Hidden bands**: Fresh content appears at unexpected intervals (e.g., page 2460)
4. **Asymptote breaking**: Just when it looked like 61,400 was the ceiling, new content emerged

### Growth Rate Analysis (from checkpoint data)
| Page Range | Files Gained | Rate |
|------------|--------------|------|
| 0-1000 | ~40,875 | ~41/page |
| 1000-1500 | ~14,346 | ~29/page |
| 1500-2000 | ~2,709 | ~5/page |
| 2000-2450 | ~3,470 | ~8/page |
| 2450-2481 | +750 | **~24/page - ACCELERATION** |

---

## TODO: Brute Force High Page Exploration

After main scrape completes, run exploration script to check:
- [ ] Sequential pages up to 10,000
- [ ] Multiples: 1000, 2000, 3000... 10000, 20000, 50000, 100000
- [ ] Squares: 100, 400, 900, 1600, 2500, 10000, 40000
- [ ] Primes: 997, 1009, 2003, 3001, 5003, 7001, 10007
- [ ] Powers of 2: 1024, 2048, 4096, 8192, 16384, 32768
- [ ] Random samples in ranges: 10k-50k, 50k-100k, 100k-500k
- [ ] Edge cases: MAX_INT-adjacent, negative (if accepted)

Purpose: Catch any hidden content at unexpected page numbers

---

*This file will be expanded after scrape completes with full analysis.*
