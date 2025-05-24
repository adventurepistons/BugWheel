import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
from pii_detection import detect_pii
from pii_detection.utils import mask_and_map

# Path to the test HTML file
HTML_PATH = str(Path(__file__).parent.parent / "test_pii.html")
HTML_URL = f"file:///{HTML_PATH.replace(os.sep, '/')}"

async def extract_text_and_inputs(page):
    # Get all visible text
    body_text = await page.inner_text('body')
    # Get all input values
    input_values = await page.eval_on_selector_all('input', 'els => els.map(e => e.value)')
    # Get all password input values and their indices
    password_inputs = await page.eval_on_selector_all('input[type="password"]', 'els => els.map(e => e.value)')
    return body_text + "\n" + "\n".join(input_values), input_values, password_inputs

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print(f"Opening {HTML_URL}")
        await page.goto(HTML_URL)
        text, input_values, password_inputs = await extract_text_and_inputs(page)
        print("\nExtracted text and input values:")
        print(text)
        # Mask password input values before PII detection
        for pw in password_inputs:
            if pw:
                fake_pw = f"<PII:PASSWORD>"
                text = text.replace(pw, fake_pw)
        # TODO: Integrate new placeholder-based masking logic here
        await browser.close()

    # Example input
    text = "Contact Nikhil at nikhil@example.com or call +1-555-123-4567. His SSN is 123-45-6789."

    # Step 1: Detect PII
    pii_entities = detect_pii(text)

    # Step 2: Mask and map
    masked_text, mapping = mask_and_map(text, pii_entities)

    print("Original text:", text)
    print("Masked text:", masked_text)
    print("Mapping:", mapping)

if __name__ == "__main__":
    asyncio.run(main()) 