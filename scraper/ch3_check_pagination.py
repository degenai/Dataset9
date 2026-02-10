import requests
import re
import sys
import os

BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-9-files"

# Use Lynx User-Agent as it was successful with curl
HEADERS = {
    'User-Agent': 'Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/3.7.1'
}

def check_page(page_num):
    url = f"{BASE_URL}?page={page_num}"
    print(f"Checking page {page_num}...", end='', flush=True)

    try:
        resp = requests.get(url, headers=HEADERS)

        if resp.status_code != 200:
            print(f" Status {resp.status_code}")
            return None, resp.status_code

        files = re.findall(r'(EFTA\d{8}\.pdf)', resp.text)
        files = sorted(list(set(files)))

        print(f" Found {len(files)} files")
        return files, resp.status_code
    except Exception as e:
        print(f" Error: {e}")
        return None, 0

def main():
    # 1. Verify reported last page (9282)
    files_9282, status_9282 = check_page(9282)
    if files_9282:
        with open('chapter3_pagination_fix/manifests/page_9282.txt', 'w') as f:
            for file in files_9282:
                f.write(file + '\n')

    # 2. Check next page (9283)
    files_9283, status_9283 = check_page(9283)

    # 3. Check significantly higher page to confirm no wrapping
    files_10000, status_10000 = check_page(10000)

    # 4. Check negative page to confirm behavior
    files_neg, status_neg = check_page(-1)

    print("\nAnalysis:")
    if files_9282:
        print(f"Page 9282 (Last Reported): {len(files_9282)} files")
        print(f"  First file: {files_9282[0]}")
        print(f"  Last file:  {files_9282[-1]}")
    else:
        print("Page 9282 failed to load.")

    if not files_9283:
        print("Page 9283 (Next): Empty/Error (Expected behavior for fixed pagination)")
    else:
        # Check if page 9283 is same as 9282 or neg page (wrapped)
        if files_9282 and files_9283 == files_9282:
             print("  Page 9283 is identical to 9282 (Last page repeat).")
        elif files_neg and files_9283 == files_neg:
             print("  Page 9283 is identical to negative page default (Wrapped).")
        else:
             print(f"Page 9283 (Next): {len(files_9283)} files - UNIQUE CONTENT (Unexpected)")

    if not files_10000:
        print("Page 10000: Empty/Error (Confirmed limit)")
    else:
         # Check if page 10000 is same as 9282 or neg page (wrapped)
        if files_9282 and files_10000 == files_9282:
             print("  Page 10000 is identical to 9282 (Last page repeat).")
        elif files_neg and files_10000 == files_neg:
             print("  Page 10000 is identical to negative page default (Wrapped).")
        else:
             print(f"Page 10000: {len(files_10000)} files - UNIQUE CONTENT (Unexpected)")

if __name__ == "__main__":
    main()
