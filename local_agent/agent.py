"""
Local Agent Main Entry Point
- Loads config
- Sets up logging and version info
- Supports multiple scan flows (public, authenticated)
- For each flow: sets up Playwright, performs login if needed, crawls, tags results
- Handles PII detection and mapping
- Captures screenshots
- Reports progress/results
- Saves application map and logs
"""
import json
import logging
import sys
from pathlib import Path
import asyncio
from datetime import datetime
from playwright_utils import launch_browser, new_context, goto_page, close_browser, perform_login, crawl_application
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from typing import Tuple
from pii_utils import mask_pii_in_element, encrypt_mapping_file

# Version info
AGENT_VERSION = "0.1.0"

# Directories
LOG_DIR = Path("logs")
SCREENSHOT_DIR = Path("screenshots")
PII_MAP_DIR = Path("pii_maps")
APP_MAP_DIR = Path("application_maps")

# Ensure directories exist
for d in [LOG_DIR, SCREENSHOT_DIR, PII_MAP_DIR, APP_MAP_DIR]:
    d.mkdir(exist_ok=True)

def load_config(config_path):
    """Load and validate config from JSON file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def setup_logging():
    """Set up logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "agent.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

# Utility to mask PII in a single element
async def run_scan_flow(flow, base_url, scan_config, aut_id):
    """Run a single scan flow: login if needed, then crawl. Tag results with flow name and save map."""
    logging.info(f"Starting scan flow: {flow['name']}")
    playwright, browser = await launch_browser(headless=True)
    context = await new_context(browser)
    start_url = base_url
    if flow.get("login"):
        page = await goto_page(context, flow["login"]["login_url"])
        login_success = await perform_login(page, flow["login"])
        if not login_success:
            logging.error(f"Login failed for flow: {flow['name']}")
            await close_browser(playwright, browser)
            return
        # Optionally, set start_url to a post-login page
        start_url = flow["login"].get("post_login_url", base_url)
    # Crawl and get application map (to be implemented in crawl_application)
    app_map = await crawl_application(context, start_url, scan_config)
    # PII masking setup
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    fake = Faker()
    pii_mapping = {}
    # Mask PII in all elements of all pages
    for page in app_map:
        for i, el in enumerate(page["elements"]):
            masked_el, el_mapping = mask_pii_in_element(el, analyzer, anonymizer, fake)
            page["elements"][i] = masked_el
            pii_mapping.update(el_mapping)
    # Save mapping file (encrypted)
    mapping_file = PII_MAP_DIR / f"pii_mapping_{aut_id}_{flow['name']}.json"
    encrypt_mapping_file(pii_mapping, mapping_file)
    # Tag application map with flow name and metadata
    result = {
        "aut_id": aut_id,
        "scan_flow": flow["name"],
        "scanned_at": datetime.utcnow().isoformat() + "Z",
        "application_map": app_map,
        "agent_version": AGENT_VERSION
    }
    # Save application map to file
    out_file = APP_MAP_DIR / f"app_map_{aut_id}_{flow['name']}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logging.info(f"Saved application map for flow '{flow['name']}' to {out_file}")
    await close_browser(playwright, browser)
    logging.info(f"Completed scan flow: {flow['name']}")

def main():
    print(f"Local Agent v{AGENT_VERSION}")
    setup_logging()
    config = load_config("config.json")
    base_url = config["base_url"]
    scan_config = config["scan"]
    aut_id = config.get("aut_id", "app")
    # Support multiple scan flows (public, authenticated)
    scan_flows = config.get("scan_flows")
    if not scan_flows:
        # Fallback: single flow, use top-level login if present
        scan_flows = [{"name": "default", "login": config.get("login")}] 
    loop = asyncio.get_event_loop()
    for flow in scan_flows:
        loop.run_until_complete(run_scan_flow(flow, base_url, scan_config, aut_id))
    logging.info("Agent run complete.")

if __name__ == "__main__":
    main() 