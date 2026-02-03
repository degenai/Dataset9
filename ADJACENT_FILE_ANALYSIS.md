# Adjacent File Analysis: EFTA00326497, EFTA00326501, EFTA00534391

## Executive Summary

Three files listed in the DOJ's Dataset 9 pagination are inaccessible from both the DOJ website and the 86GB public torrent. Adjacent file analysis reveals these are not random corruptions—all three cluster around the same event: **Karyna Shuliak's April 2016 departure from St. Thomas, U.S. Virgin Islands** (the departure point for Epstein's Little St. James island).

More significantly, two of the missing files (326497 and 534391) appear to be **the same document processed in two separate batches**—one redacted, one unredacted—**approximately 208,000 files apart in the index**. This pattern is highly unlikely without coordinated action, suggesting deliberate removal rather than technical failure.

---

## Key Finding: Duplicate Processing Batches

The EFTA 326xxx and 534xxx ranges contain **the same underlying documents processed twice**:

| EFTA 326xxx (Redacted) | EFTA 534xxx (Unredacted) | Content |
|------------------------|--------------------------|---------|
| 326494-326496 | 534388-534390 | AmEx travel confirmation, Lesley Groff forward |
| **326497 - MISSING** | **534391 - MISSING** | Unknown |
| 326498-326500 | — | Forward continuation pages |
| **326501 - MISSING** | — | Unknown |
| 326502-326504 | — | Shuliak reply "Thanks so much" |
| 326505-326506 | — | AmEx Invoice #245413 |
| — | 534392 | Epstein personal email to Shuliak |

The 326xxx batch shows redacted email addresses (black boxes). The 534xxx batch shows unredacted addresses, revealing:
- **Lesley Groff** (lesley.jee@gmail.com) — Epstein's executive assistant
- **Ann Rodriquez** (annrodriquez@yahoo.com) — Epstein staff
- **Bella Klein** (bklein575@gmail.com) — Epstein staff
- **Karyna Shuliak** (karynashuliak@icloud.com) — Epstein's girlfriend

**The gaps appear in both processing batches, ~208,000 files apart.** Random file corruption affecting the same logical document across two separate processing runs—indexed hundreds of thousands of positions apart—is highly unlikely without coordinated action.

---

## Document Chain Reconstruction

### The Event: April 10-13, 2016

Karyna Shuliak, Epstein's girlfriend, was booked on Delta flight DL676 departing **Charlotte Amalie, Cyril E. King Airport (St. Thomas)** on April 13, 2016, arriving at JFK. Travel was booked via American Express Centurion (black card) service.

### Timeline from Documents

| Time | Document | EFTA # | Description |
|------|----------|--------|-------------|
| Apr 10, 11:31 AM | AmEx Confirmation | 326494-326496 | Sent to lesley.jee@gmail.com (Groff's JEE account) |
| Apr 10, 11:33 AM | Groff Forward | 326498-326500, 534388-534390 | Forwarded to Shuliak, CC'd staff |
| Apr 10, 11:35 AM | Shuliak Reply | 326502-326504 | "Thanks so much" |
| Apr 10, 3:52 PM | **Epstein Email** | **534392** | Personal message to Shuliak |
| Apr 11, 10:02 AM | AmEx Invoice | 326505-326506 | Invoice #245413 for booking |
| Apr 13, 1:35 PM | — | — | Scheduled departure from St. Thomas |

### The Gaps

- **EFTA00326497**: Falls between the original AmEx confirmation (326494-326496) and the Groff forward (326498). Likely the PDF ticket attachment referenced in the emails ("SHULIAK_KARYNA-QWURMO.pdf").

- **EFTA00326501**: Falls between the forward continuation (326498-326500) and Shuliak's reply (326502). Unknown content—possibly another attachment or a separate communication.

- **EFTA00534391**: Falls between the unredacted Groff forward (534388-534390) and Epstein's personal email (534392). This places the gap **immediately adjacent to direct Epstein correspondence**.

---

## The Epstein Email (EFTA00534392)

The document immediately following missing file 534391 is a personal email from Jeffrey Epstein to Karyna Shuliak:

```
From: "jeffrey E." <jeevacation@gmail.com>
To: Karyna Shuliak
Subject: [blank]
Date: Sun, 10 Apr 2016 19:52:13 +0000

order http://softskull.com/dd-product/undone/
```

The email includes Epstein's standard legal disclaimer identifying communications as "property of JEE" (Jeffrey E. Epstein).

### The Book

**"Undone"** by John Colapinto
- **Publisher**: Soft Skull Press
- **On-sale date**: April 12, 2016
- **Epstein's recommendation**: April 10, 2016 (**two days before public release**)
- **ISBN**: 978-1593766451

**Publisher's description**: "Dez is a former lawyer and teacher—an ephebophile with a proclivity for teenage girls, hiding out in a trailer park with his latest conquest, Chloe. Having been in and out of courtrooms (and therapists' offices) for a number of years, Dez is at odds with a society that persecutes him over his desires."

**About the author**: John Colapinto is a staff writer at The New Yorker, former contributor to Vanity Fair, Rolling Stone, and New York Times Magazine.

**Archive link**: https://web.archive.org/web/2016*/http://softskull.com/dd-product/undone/

### Relevance

Epstein recommended a novel with a sympathetic pedophile protagonist **before its public release**, to his girlfriend, on the same day travel was being coordinated for her departure from St. Thomas. The missing file 534391 sits immediately before this email in the document index.

---

## Open Questions

1. **What is EFTA00534391?** Its position between staff travel logistics and Epstein's personal correspondence makes it potentially significant. Was it another Epstein email? An attachment? A separate document?

2. **How did Epstein obtain "Undone" before release?** Options include: advance review copy, personal connection to the author, or publishing industry access. John Colapinto's media circles (New Yorker, Vanity Fair) overlap with Epstein's known social cultivation.

3. **Why do gaps appear in both processing batches?** If the same document is missing from both the redacted (326xxx) and unredacted (534xxx) versions, this suggests removal at a level that affected both processing runs—either at the source or during DOJ document production.

4. **Is this April 2016 trip unique?** Are there other Shuliak travel records in the corpus? Do they show similar gaps? A pattern across multiple trips would strengthen the case for targeted removal.

5. **What other communications exist from jeevacation@gmail.com?** Grepping the corpus for Epstein's personal email address may reveal additional context.

---

## How to Verify

This analysis can be independently reproduced:

1. **Obtain the torrent**: The 86GB Dataset 9 torrent is available via standard sources. Verify file count: 531,256 files.

2. **Check adjacent files**: Navigate to the EFTA numbers listed above. Confirm 326497, 326501, and 534391 are absent.

3. **Attempt DOJ direct access**:
   - https://www.justice.gov/epstein/files/DataSet%209/EFTA00326497.pdf
   - https://www.justice.gov/epstein/files/DataSet%209/EFTA00326501.pdf
   - https://www.justice.gov/epstein/files/DataSet%209/EFTA00534391.pdf
   
   All three return error pages.

4. **Compare redacted vs unredacted batches**: Pull files from both 326xxx and 534xxx ranges for the same email chain. Confirm the redaction patterns and the presence of gaps in both.

5. **Run your own grep**: Search the corpus for "QWURMO" (booking reference), "Shuliak", "jeevacation", "Colapinto", and the missing EFTA numbers to find any references.

**Torrent verification**: Compare your file listing against the manifest in this repository (`manifests/torrent_manifest.txt`).

---

## Methodology Notes

- Adjacent files pulled from local copy of 86GB torrent (531,256 files)
- DOJ website pagination scraped to 13,000 pages (77,766 unique file references)
- Missing files confirmed inaccessible via both DOJ direct URLs and torrent contents
- EFTA numbers are sequential processing identifiers assigned during document production, not chronological dates

---

## Files Referenced

| EFTA | Status | Content Summary |
|------|--------|-----------------|
| 326494 | ✓ Present | AmEx confirmation email (page 1) |
| 326495 | ✓ Present | AmEx confirmation (page 2) |
| 326496 | ✓ Present | AmEx confirmation (page 3) |
| **326497** | **✗ MISSING** | **Unknown - likely PDF attachment** |
| 326498 | ✓ Present | Groff forward to Shuliak (page 1) |
| 326499 | ✓ Present | Groff forward (page 2) |
| 326500 | ✓ Present | Groff forward (page 3) |
| **326501** | **✗ MISSING** | **Unknown** |
| 326502 | ✓ Present | Shuliak reply (page 1) |
| 326503 | ✓ Present | Shuliak reply (page 2) |
| 326504 | ✓ Present | Shuliak reply (page 3) |
| 326505 | ✓ Present | AmEx Invoice (page 1) |
| 326506 | ✓ Present | AmEx Invoice (page 2) |
| 534388 | ✓ Present | Groff forward - UNREDACTED (page 1) |
| 534389 | ✓ Present | Groff forward - UNREDACTED (page 2) |
| 534390 | ✓ Present | Groff forward - UNREDACTED (page 3) |
| **534391** | **✗ MISSING** | **Unknown - adjacent to Epstein email** |
| 534392 | ✓ Present | Epstein email re: "Undone" book |

---

## Conclusion

The three missing files are not random. They cluster around a single event (Shuliak's April 2016 St. Thomas departure), appear across two separate processing batches ~208,000 files apart, and include a gap immediately adjacent to Epstein's personal correspondence. The pattern is consistent with targeted removal rather than technical corruption.

---

*Analysis conducted: February 2026*  
*Repository: github.com/degenai/Dataset9*  
*License: Unlicense (Public Domain)*
