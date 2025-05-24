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
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import json
import logging
import sys as _sys
import asyncio
from datetime import datetime
from playwright_utils import launch_browser, new_context, goto_page, close_browser, perform_login, crawl_application
import pytz
# --- PII detection/masking imports ---
from shared.pii_detection.pii_detection.ensemble import detect_pii

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
            logging.StreamHandler(_sys.stdout)
        ]
    )

# Utility to mask PII in all string fields of the application map
PII_RELEVANT_KEYS = {"text", "innerText", "label", "value", "input_value", "placeholder", "content"}

DEFAULT_CONFIDENCE_THRESHOLD = 0.7

def presidio_detect_and_mask(text, confidence_threshold=DEFAULT_CONFIDENCE_THRESHOLD):
    results = detect_pii(text)
    # Only keep entities above the confidence threshold
    filtered = [e for e in results if e.confidence is None or e.confidence >= confidence_threshold]
    # Sort by start index descending to avoid messing up indices
    filtered = sorted(filtered, key=lambda e: e.start, reverse=True)
    masked = text
    mapping = {}
    for i, entity in enumerate(filtered):
        val = entity.value
        placeholder = f"<PII_{entity.type}_{i}>"
        masked = masked[:entity.start] + placeholder + masked[entity.end:]
        mapping[placeholder] = val
    return masked, mapping

def mask_app_map(app_map):
    mapping = {}
    def mask_value(val):
        masked_val, map_ = presidio_detect_and_mask(val)
        mapping.update(map_)
        return masked_val
    def recurse(obj, parent_key=None):
        if isinstance(obj, dict):
            return {k: recurse(v, k) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [recurse(i, parent_key) for i in obj]
        elif isinstance(obj, str):
            if parent_key in PII_RELEVANT_KEYS:
                return mask_value(obj)
            else:
                return obj
        else:
            return obj
    masked_map = recurse(app_map)
    return masked_map, mapping

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
    # --- Mask PII in the application map ---
    masked_app_map, pii_mapping = mask_app_map(app_map)
    # Tag application map with flow name and metadata
    india_tz = pytz.timezone('Asia/Kolkata')
    result = {
        "aut_id": aut_id,
        "scan_flow": flow["name"],
        "scanned_at": datetime.now(india_tz).isoformat(),
        "application_map": masked_app_map,
        "pii_mapping": pii_mapping,
        "agent_version": AGENT_VERSION
    }
    # Save application map to file
    out_file = APP_MAP_DIR / f"app_map_{aut_id}_{flow['name']}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    # Save PII mapping separately for audit/de-mapping
    pii_map_file = PII_MAP_DIR / f"pii_map_{aut_id}_{flow['name']}.json"
    with open(pii_map_file, "w", encoding="utf-8") as f:
        json.dump(pii_mapping, f, indent=2)
    logging.info(f"Saved application map for flow '{flow['name']}' to {out_file}")
    logging.info(f"Saved PII mapping for flow '{flow['name']}' to {pii_map_file}")
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
    async def run_all_flows():
        for flow in scan_flows:
            await run_scan_flow(flow, base_url, scan_config, aut_id)
    asyncio.run(run_all_flows())
    logging.info("Agent run complete.")

if __name__ == "__main__":
    main() 