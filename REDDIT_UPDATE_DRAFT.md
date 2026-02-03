# Reddit Update Draft - DataSet 9 Indexing Progress

**Post this as a reply to your thread:**

---

**Update: DataSet 9 Pagination is SEVERELY broken - First indexing run complete, more coming**

Just finished an initial indexing run of the DOJ DataSet 9 pagination. The results are... concerning.

**What I found:**

| Metric | Value |
|--------|-------|
| Pages scraped | ~2,500+ |
| Unique files discovered | **62,000+** |
| True pagination wraps | 167 |
| Redundant pages | 900+ |

**The pagination is chaos:**

- Pages 0-1200: Normal behavior, ~50 new files per page
- Pages 1200-2400: Mostly wraps and redundant pages (content repeating)
- Page 2460: Suddenly, fresh content appears again after 100+ pages of nothing

The pagination doesn't just loop at page 905 like some people thought. It loops multiple times, at irregular intervals, with hidden batches of unique content appearing at unexpected page numbers.

**My script stopped at ~2500 pages** after 100 consecutive pages with no new files. But then I manually checked page 2460 and found fresh content. This means **there could be more hidden content at higher page numbers**.

**Next steps:**

1. Running another pass through page 10,000 with no early stopping
2. Brute force exploration of edge cases:
   - Multiples (1000, 2000, 5000, 10000...)
   - Powers of 2 (1024, 2048, 4096, 8192...)
   - Random sampling in 10k-100k range
   - Other mathematical patterns

**Why this matters:**

If you just scraped pages 0-905 and stopped at the first wrap, you'd have maybe 35-40k files. The actual dataset appears to be 60k+ and possibly more. The 86 GiB torrent may be significantly incomplete.

Will update with results from the extended run. Code is available if anyone wants to help verify.

**TL;DR:** DOJ pagination is broken/weird enough that content is hidden at unexpected page numbers. Simple scrapers miss most of the dataset. Doing thorough exploration to find everything.

---

*Edit this as needed for your posting style. Remove the table if Reddit formatting breaks it.*
