# Epstein DOJ Dataset 9 - Evidence of Targeted Document Removal

## Key Finding: Three Files Removed from Two Processing Batches

Three files are listed in DOJ's Dataset 9 pagination but cannot be accessed from either the DOJ website or the 86GB public torrent. Adjacent file analysis reveals:

**All three files cluster around the same event**: Karyna Shuliak's April 2016 departure from St. Thomas, U.S. Virgin Islands—the departure point for Epstein's Little St. James island.

**Two of the missing files appear in separate processing batches ~208,000 files apart**:

| Redacted Batch | Unredacted Batch | Status |
|----------------|------------------|--------|
| EFTA00326497 | EFTA00534391 | Both MISSING |

The same logical document is missing from both a redacted version (326xxx range) and an unredacted version (534xxx range), processed in completely separate batches. Random file corruption does not affect the same document across two processing runs indexed hundreds of thousands of positions apart.

**The missing file 534391 sits immediately before a personal Epstein email** recommending a novel with a sympathetic pedophile protagonist—two days before the book's public release.

See [ADJACENT_FILE_ANALYSIS.md](ADJACENT_FILE_ANALYSIS.md) for full investigation.

---

## The Missing Files

| EFTA | DOJ Website | Torrent | Adjacent Content |
|------|-------------|---------|------------------|
| 00326497 | Error page | Missing | Between AmEx confirmation and Groff forward |
| 00326501 | Error page | Missing | Between forward and Shuliak reply |
| 00534391 | Error page | Missing | Immediately before Epstein personal email |

Try them yourself:
- https://www.justice.gov/epstein/files/DataSet%209/EFTA00326497.pdf
- https://www.justice.gov/epstein/files/DataSet%209/EFTA00326501.pdf
- https://www.justice.gov/epstein/files/DataSet%209/EFTA00534391.pdf

---

## Secondary Finding: DOJ Website Hides 85% of Dataset

| Source | Files | Coverage |
|--------|-------|----------|
| DOJ Website (13,000 pages scraped) | 77,766 | ~15% |
| 86GB Torrent | 531,256 | ~100% |

The DOJ's pagination system is broken—an infinite loop cycling the same files. We found the exact limit: **page 184,467,440,737,095,516** (2^64 / 100). Even at page 900 quadrillion, it returns the same content as page 0.

Anyone relying solely on the DOJ website is missing 85% of Dataset 9.

---

## EFTA Distribution by Page Range

```
Page Range    Min EFTA       Max EFTA       New Files
---------------------------------------------------------
0-499         EFTA00039025   EFTA00267311   21,842
500-999       EFTA00267314   EFTA00337032   18,983
1000-1499     EFTA00067524   EFTA00380774   14,396
1500-1999     EFTA00092963   EFTA00413050   2,709
2000-2499     EFTA00083599   EFTA00426736   4,432
2500-2999     EFTA00218527   EFTA00423620   4,515
3000-3499     EFTA00203975   EFTA00539216   2,692
3500-3999     EFTA00137295   EFTA00313715   329
4000-4499     EFTA00078217   EFTA00338754   706
4500-4999     EFTA00338134   EFTA00384534   2,825
5000-5499     EFTA00377742   EFTA00415182   1,353
5500-5999     EFTA00416356   EFTA00432673   1,214
6000-6499     EFTA00213187   EFTA00270156   501
6500-6999     EFTA00068280   EFTA00281003   554
7000-7499     EFTA00154989   EFTA00425720   106
7500-8499     (no new files - all wraps/redundant)
8500-8999     EFTA00168409   EFTA00169291   10
9000-9499     EFTA00154873   EFTA00154974   35
9500-9999     EFTA00139661   EFTA00377759   324
10000-10499   EFTA00140897   EFTA01262781   240
10500-12999   (no new files - all wraps/redundant)

TOTAL UNIQUE FILES ON DOJ WEBSITE: 77,766
TOTAL FILES IN TORRENT: 531,256
```

---

## Repository Contents

### Analysis
- [ADJACENT_FILE_ANALYSIS.md](ADJACENT_FILE_ANALYSIS.md) - Full investigation of the 3 missing files
- [FINAL_REDDIT_POST.txt](FINAL_REDDIT_POST.txt) - Summary for distribution

### Manifests
- `manifests/doj_dataset9_manifest.txt` - 77,766 files from DOJ website
- `manifests/torrent_manifest.txt` - 531,256 files from torrent
- `manifests/doj_not_in_torrent.txt` - The 3 missing files
- `manifests/pagination_index.json` - Full pagination structure

### Scripts
- `scraper/scrape_doj_manifest.py` - Sequential pagination scraper
- `scraper/exploration_probe.py` - Random page exploration
- `scraper/find_exact_end.py` - Binary search for pagination limit
- `scraper/mitnick_probe.py` - Pattern-based exploration

---

## How to Verify

1. **Check the missing files yourself** - Click the DOJ links above

2. **Get the torrent** and confirm 326497, 326501, 534391 are absent

3. **Read adjacent files** - Pull the EFTA numbers around the gaps to see the Shuliak travel chain

4. **Run the scraper** - Reproduce our 77,766 file count from DOJ pagination:
   ```bash
   cd scraper
   pip install -r requirements.txt
   python scrape_doj_manifest.py
   ```

5. **Compare manifests** - Diff `doj_dataset9_manifest.txt` against `torrent_manifest.txt`

---

## Conclusion

The three missing files are not random technical failures. They cluster around a single event, appear across two separate processing batches ~208,000 files apart, and include a gap immediately adjacent to Epstein's personal correspondence. The pattern is consistent with targeted removal.

---

*Analysis conducted: February 2-3, 2026*  
*License: Unlicense (Public Domain)*
