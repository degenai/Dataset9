#!/usr/bin/env python3
"""Page 0 check. That's it."""

import os, re, sys, requests
from bs4 import BeautifulSoup

URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files?page=0"
USER_AGENT = os.getenv("DATASET9_USER_AGENT", "Mozilla/5.0 (compatible; DataSet9-Bot/1.0; +https://github.com/DataSet9-Project)")

try:
    r = requests.get(URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        sys.exit(1)
    files = [
        re.search(r"(EFTA\d{8})", a["href"]).group(1).upper()
        for a in BeautifulSoup(r.text, "lxml").find_all("a", href=re.compile(r"EFTA\d{8}\.pdf", re.I))
        if re.search(r"(EFTA\d{8})", a["href"])
    ]
    print(f"Files:  {len(files)}")
    for f in files:
        print(f"  {f}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
