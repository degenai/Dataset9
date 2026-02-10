# Visual Scraper Guide: Bypassing DOJ Protection

This guide details how to set up and run the `scraper/visual_scrape_prototype.py` script to bypass the Akamai WAF protection on `justice.gov`.

## Prerequisites

1.  **Python 3.8+**: Ensure you have Python installed.
2.  **Selenium WebDriver**: Install the Selenium library.
    ```bash
    pip install selenium
    ```
3.  **Browser Driver**: Download the appropriate driver for your browser (e.g., ChromeDriver for Google Chrome). Ensure it's in your system PATH.
    *   Chrome: https://chromedriver.chromium.org/downloads
    *   Firefox: https://github.com/mozilla/geckodriver/releases
4.  **OCR Engine (Tesseract)**: Install Tesseract OCR.
    *   **Windows**: Download the installer from https://github.com/UB-Mannheim/tesseract/wiki
    *   **macOS**: `brew install tesseract`
    *   **Linux**: `sudo apt-get install tesseract-ocr`
5.  **Python OCR Wrapper**: Install `pytesseract` and `Pillow`.
    ```bash
    pip install pytesseract Pillow
    ```

## Configuration

Edit `scraper/visual_scrape_prototype.py`:

1.  **Uncomment the Imports**: Remove the `#` at the beginning of the `import` lines for Selenium and Pytesseract.
2.  **Initialize Driver**: Uncomment the code inside `init_driver()` to create a real browser instance.
    *   *Tip*: Using a standard browser window (not headless) is often less detectable. You can minimize it, but keep it open.
3.  **Tesseract Path (Windows Only)**: If you installed Tesseract on Windows, you might need to specify the path to the executable:
    ```python
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```

## Usage

Run the script from the command line:

```bash
python scraper/visual_scrape_prototype.py --start 0 --end 9283
```

*   `--start`: The page number to start scraping from (default: 0).
*   `--end`: The page number to stop at (exclusive). To scrape up to page 9282, use 9283.

## How it Works

1.  **Browser Automation**: Selenium launches a real browser instance, making the request look like a human user.
2.  **Visual Capture**: It navigates to each page of the dataset and takes a screenshot.
3.  **OCR Processing**: The screenshot is passed to Tesseract OCR, which extracts text from the image.
4.  **Pattern Matching**: The script searches the extracted text for the "EFTA" file pattern (e.g., `EFTA12345678`).
5.  **Manifest Generation**: It saves the found file numbers to a text file for each page.

## Troubleshooting

*   **Access Denied**: If you still get 403 errors, try adding `time.sleep(5)` between requests to slow down. You can also try using `undetected-chromedriver`:
    ```bash
    pip install undetected-chromedriver
    ```
    Then update the script to use `import undetected_chromedriver as uc` and `driver = uc.Chrome()`.
*   **Empty OCR Results**: If the OCR isn't picking up the text, check the screenshots in the `screenshots/` directory. Ensure the text is clear and readable. You may need to adjust the image preprocessing (e.g., convert to grayscale, increase contrast) before passing it to Tesseract.
