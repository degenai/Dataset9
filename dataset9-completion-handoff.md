# Agent Handoff: Epstein DataSet 9 Completion Project

## Mission
Assemble the first complete public mirror of DOJ Epstein Files DataSet 9. The DOJ removed ZIP downloads but individual PDFs remain accessible. Existing torrents are incomplete (~86 GiB of estimated 100+ GiB). Your job: identify gaps, scrape missing files, package for redistribution.

## Why This Matters
- DataSet 9 contains ~1.5M pages of FBI 302s, victim statements, seized device contents
- No complete public archive exists as of Feb 2, 2026
- Journalists and researchers are working with incomplete data
- You're building infrastructure for accountability

---

## Current State

### What Exists
| Source | Size | Status |
|--------|------|--------|
| Torrent (larger) | 86.74 GiB | Incomplete, hash: `acb9cb1741502c7dc09460e4fb7b44eac8022906` |
| Torrent (smaller) | 45.6 GiB | Incomplete, hash: `0a3d4b84a77bd982c9c2761f40944402b94f9c64` |
| Archive.org URL list | Unknown | Possibly incomplete, at `archive.org/details/dataset9_url_list` |
| DOJ individual PDFs | Full set | Still accessible at `justice.gov/epstein/files/DataSet%209/` |

### DOJ URL Patterns
```
# File listing (paginated)
https://www.justice.gov/epstein/doj-disclosures/data-set-9-files?page={0,1,2...}

# Individual PDFs
https://www.justice.gov/epstein/files/DataSet%209/EFTA{8-digits}.pdf

# Example
https://www.justice.gov/epstein/files/DataSet%209/EFTA00010001.pdf
```

### File Naming Convention
- All files: `EFTA` + 8 digits + `.pdf`
- DataSet 9 range: Estimated EFTA00008529 through EFTA0015XXXX (unconfirmed upper bound)
- Sequential but may have gaps from redactions/withholdings

---

## Phase 1: Scrape DOJ Master File List

### Objective
Get the authoritative list of every file DOJ claims is in DataSet 9.

### Approach
```python
import requests
from bs4 import BeautifulSoup
import time
import re

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"
OUTPUT_FILE = "doj_dataset9_manifest.txt"

def scrape_doj_listing():
    all_files = []
    page = 0
    
    while True:
        url = f"{BASE_URL}?page={page}"
        print(f"Scraping page {page}...")
        
        resp = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (research archival project)'
        })
        
        if resp.status_code != 200:
            print(f"Got {resp.status_code}, stopping")
            break
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Find all EFTA links - adjust selector based on actual page structure
        links = soup.find_all('a', href=re.compile(r'EFTA\d{8}\.pdf'))
        
        if not links:
            print(f"No files found on page {page}, stopping")
            break
            
        for link in links:
            filename = re.search(r'(EFTA\d{8}\.pdf)', link['href'])
            if filename:
                all_files.append(filename.group(1))
        
        print(f"  Found {len(links)} files")
        page += 1
        time.sleep(1)  # Be polite
    
    # Dedupe and sort
    all_files = sorted(set(all_files))
    
    with open(OUTPUT_FILE, 'w') as f:
        for filename in all_files:
            f.write(filename + '\n')
    
    print(f"Total unique files: {len(all_files)}")
    return all_files

if __name__ == "__main__":
    scrape_doj_listing()
```

### Expected Output
- `doj_dataset9_manifest.txt` - one filename per line
- Estimated 50,000-150,000 files based on page count estimates

### Fallback
If DOJ listing is rate-limited or broken, use Archive.org URL list:
```bash
wget https://archive.org/download/dataset9_url_list/dataset9_url_list.txt
grep -oP 'EFTA\d{8}' dataset9_url_list.txt | sort -u > doj_dataset9_manifest.txt
```

---

## Phase 2: Inventory Torrent Contents

### Objective
List every file in the 86 GiB torrent to compare against DOJ manifest.

### Prerequisites
User must download torrent first:
```
magnet:?xt=urn:btih:acb9cb1741502c7dc09460e4fb7b44eac8022906&dn=DataSet_9.tar.xz
```

### Approach
```bash
# Option A: List without extracting (if tar.xz)
tar -tf DataSet_9.tar.xz | grep -oP 'EFTA\d{8}' | sort -u > torrent_dataset9_manifest.txt

# Option B: If already extracted to directory
find ./DataSet9/ -name "EFTA*.pdf" -printf "%f\n" | sort -u > torrent_dataset9_manifest.txt

# Option C: If it's a ZIP
unzip -l DataSet9-incomplete.zip | grep -oP 'EFTA\d{8}' | sort -u > torrent_dataset9_manifest.txt
```

### Expected Output
- `torrent_dataset9_manifest.txt` - one filename per line
- Should contain 40,000-80,000 files based on torrent size

---

## Phase 3: Identify Missing Files

### Objective
Diff the two manifests to find gaps.

### Approach
```bash
# Files in DOJ listing but NOT in torrent
comm -23 <(sort doj_dataset9_manifest.txt) <(sort torrent_dataset9_manifest.txt) > missing_from_torrent.txt

# Count
echo "Missing files: $(wc -l < missing_from_torrent.txt)"

# Generate download URLs
sed 's|^|https://www.justice.gov/epstein/files/DataSet%209/|' missing_from_torrent.txt > missing_urls.txt
```

### Expected Output
- `missing_from_torrent.txt` - EFTA filenames missing from torrent
- `missing_urls.txt` - full URLs ready for wget/aria2c
- Estimated 10,000-50,000 missing files (10-40 GiB)

---

## Phase 4: Download Missing Files

### Objective
Scrape all missing PDFs from DOJ.

### Approach (aria2c - fastest)
```bash
# Install if needed
# apt install aria2

# Download with 3 parallel connections, 1 retry, organized output
aria2c \
  --input-file=missing_urls.txt \
  --dir=./dataset9_gaps \
  --max-concurrent-downloads=3 \
  --max-connection-per-server=1 \
  --min-split-size=1M \
  --retry-wait=5 \
  --max-tries=3 \
  --continue=true \
  --log=download.log \
  --log-level=notice
```

### Approach (wget - simpler)
```bash
wget \
  --input-file=missing_urls.txt \
  --directory-prefix=./dataset9_gaps \
  --wait=0.5 \
  --random-wait \
  --continue \
  --no-clobber \
  2>&1 | tee download.log
```

### Approach (Python - most control)
```python
import requests
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_DIR = "./dataset9_gaps"
WORKERS = 3
DELAY = 0.5

os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_file(url):
    filename = url.split('/')[-1]
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return f"SKIP {filename}"
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200 and len(resp.content) > 1000:
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            return f"OK {filename}"
        else:
            return f"FAIL {filename} - {resp.status_code}"
    except Exception as e:
        return f"ERROR {filename} - {e}"

def main():
    with open('missing_urls.txt') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Downloading {len(urls)} files...")
    
    failed = []
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(download_file, url): url for url in urls}
        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            print(f"[{i+1}/{len(urls)}] {result}")
            if result.startswith("FAIL") or result.startswith("ERROR"):
                failed.append(futures[future])
            time.sleep(DELAY)
    
    with open('failed_downloads.txt', 'w') as f:
        for url in failed:
            f.write(url + '\n')
    
    print(f"\nComplete. {len(failed)} failures logged to failed_downloads.txt")

if __name__ == "__main__":
    main()
```

### Rate Limiting Notes
- DOJ appears to allow moderate scraping
- 3 concurrent connections with 0.5s delay is conservative
- If you get 429s, back off to 1 connection with 2s delay
- Estimated time: 10-30 hours depending on gap size

---

## Phase 5: Validate & Package

### Objective
Verify downloads and create distributable archive.

### Validation
```bash
# Check for truncated/error files (< 1KB usually means error page)
find ./dataset9_gaps -name "*.pdf" -size -1k > corrupt_files.txt

# Verify PDF magic bytes
for f in ./dataset9_gaps/*.pdf; do
    if ! head -c 4 "$f" | grep -q '%PDF'; then
        echo "$f" >> not_valid_pdf.txt
    fi
done

# Count what we got
echo "Downloaded: $(ls ./dataset9_gaps/*.pdf 2>/dev/null | wc -l)"
echo "Corrupt: $(wc -l < corrupt_files.txt)"
```

### Merge with Torrent Contents
```bash
# Extract torrent if needed
tar -xf DataSet_9.tar.xz -C ./dataset9_complete/

# Copy gap files in
cp ./dataset9_gaps/*.pdf ./dataset9_complete/

# Verify total count
ls ./dataset9_complete/*.pdf | wc -l
```

### Create Distributable Archive
```bash
# Create compressed archive
tar -cf - ./dataset9_complete | xz -9 -T0 > DataSet_9_COMPLETE.tar.xz

# Generate checksums
sha256sum DataSet_9_COMPLETE.tar.xz > DataSet_9_COMPLETE.tar.xz.sha256
md5sum DataSet_9_COMPLETE.tar.xz > DataSet_9_COMPLETE.tar.xz.md5

# Create file manifest
ls ./dataset9_complete/*.pdf | sort > DataSet_9_COMPLETE_manifest.txt
```

### Create Torrent for Distribution
```bash
# Install if needed: apt install mktorrent

mktorrent \
  -a udp://tracker.opentrackr.org:1337/announce \
  -a udp://open.demonii.com:1337/announce \
  -a udp://tracker.torrent.eu.org:451/announce \
  -a udp://exodus.desync.com:6969/announce \
  -c "Epstein DOJ Files DataSet 9 - COMPLETE - Feb 2026" \
  -n "DataSet_9_COMPLETE" \
  -o DataSet_9_COMPLETE.torrent \
  DataSet_9_COMPLETE.tar.xz
```

---

## Phase 6: Distribution

### Upload Targets
1. **Internet Archive** (preferred)
   - Create account at archive.org
   - Upload via web or `ia` CLI tool
   - Tag: `epstein`, `doj`, `foia`, `dataset9`

2. **Torrent** 
   - Seed the .torrent file
   - Post magnet link to r/DataHoarder

3. **Academic Mirror**
   - Contact journalists/researchers who might host

### Documentation to Include
```markdown
# DataSet 9 - COMPLETE

## Contents
- XX,XXX PDF files from DOJ Epstein Files DataSet 9
- EFTA range: EFTA00008529 - EFTA000XXXXX
- Total size: ~XXX GB uncompressed

## Sources
- Primary: justice.gov/epstein (scraped Feb 2026)
- Base: r/DataHoarder torrent (86.74 GiB incomplete)
- Gaps: Direct DOJ scrape (XX GiB)

## Checksums
- SHA256: [hash]
- MD5: [hash]

## Known Issues
- XX files returned 404 (listed in missing_404.txt)
- XX files heavily redacted
- Some files may be duplicates across datasets

## Verification
Compare against DOJ listing at:
https://www.justice.gov/epstein/doj-disclosures/data-set-9-files
```

---

## Project Structure
```
dataset9-completion/
├── scraper/
│   └── scrape_doj_listing.py
├── manifests/
│   ├── doj_dataset9_manifest.txt      # What DOJ says exists
│   ├── torrent_dataset9_manifest.txt  # What torrent has
│   ├── missing_from_torrent.txt       # Gap list
│   └── missing_urls.txt               # URLs to download
├── downloads/
│   ├── dataset9_gaps/                 # Downloaded gap files
│   └── download.log
├── validation/
│   ├── corrupt_files.txt
│   ├── not_valid_pdf.txt
│   └── failed_downloads.txt
├── output/
│   ├── DataSet_9_COMPLETE.tar.xz
│   ├── DataSet_9_COMPLETE.tar.xz.sha256
│   ├── DataSet_9_COMPLETE.torrent
│   └── DataSet_9_COMPLETE_manifest.txt
└── README.md
```

---

## Success Criteria
- [ ] DOJ manifest scraped (know total file count)
- [ ] Torrent inventoried 
- [ ] Gap identified and quantified
- [ ] All available gaps downloaded
- [ ] 404s documented separately
- [ ] Archive created and checksummed
- [ ] Torrent created and seeding
- [ ] Uploaded to Archive.org
- [ ] Magnet link posted to r/DataHoarder

---

## Contact / Credit
Project initiated by: [your handle]
For: Public accountability research
Date: February 2026

When complete, post to:
- r/DataHoarder
- r/Epstein  
- Archive.org
