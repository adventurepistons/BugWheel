"""
Playwright Utilities for Local Agent
- Browser/context setup
- Navigation helpers
"""
from playwright.async_api import async_playwright
from locator_utils import generate_basic_locators, is_unique, select_best_locator, score_locator, generate_description

async def launch_browser(headless=True):
    """Launch a Playwright browser instance."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
    return playwright, browser

async def new_context(browser):
    """Create a new browser context."""
    return await browser.new_context()

async def goto_page(context, url):
    """Open a new page and navigate to the given URL."""
    page = await context.new_page()
    await page.goto(url)
    return page

async def close_browser(playwright, browser):
    """Close the browser and stop Playwright."""
    await browser.close()
    await playwright.stop()

async def perform_login(page, login_details):
    """Perform login using provided selectors and credentials. Returns True if login appears successful, else False."""
    try:
        await page.goto(login_details["login_url"])
        await page.fill(login_details["username_selector"], login_details["username"])
        await page.fill(login_details["password_selector"], login_details["password"])
        await page.click(login_details["login_button_selector"])
        # TODO: Add logic to verify login success (e.g., check for dashboard element or URL change)
        await page.wait_for_load_state("networkidle")
        return True
    except Exception as e:
        print(f"[ERROR] Login failed: {e}")
        return False

async def get_css_selector(handle):
    """Generate a CSS selector for the element using id, class, attributes, nth-child, etc."""
    selector = await handle.evaluate('''el => {
        if (el.id) return `#${el.id}`;
        if (el.className && typeof el.className === "string") {
            const classes = el.className.split(/\s+/).filter(Boolean);
            if (classes.length) return `${el.tagName.toLowerCase()}.${classes.join('.')}`;
        }
        // Fallback to nth-child
        let path = el.tagName.toLowerCase();
        let parent = el.parentElement;
        while (parent) {
            let siblings = Array.from(parent.children).filter(e => e.tagName === el.tagName);
            if (siblings.length > 1) {
                let idx = siblings.indexOf(el) + 1;
                path = `${parent.tagName.toLowerCase()} > ${el.tagName.toLowerCase()}:nth-of-type(${idx})`;
            } else {
                path = `${parent.tagName.toLowerCase()} > ${path}`;
            }
            el = parent;
            parent = el.parentElement;
        }
        return path;
    }''')
    return selector

async def get_xpath(handle):
    """Generate an XPath for the element using id, attributes, or position."""
    xpath = await handle.evaluate('''el => {
        if (el.id) return `//*[@id='${el.id}']`;
        // By attributes
        const attrs = ["name", "type", "role", "aria-label", "placeholder", "title", "value"];
        for (const attr of attrs) {
            if (el.getAttribute(attr)) {
                return `//${el.tagName.toLowerCase()}[@${attr}='${el.getAttribute(attr)}']`;
            }
        }
        // By text
        if (el.textContent && el.textContent.trim().length > 0) {
            return `//${el.tagName.toLowerCase()}[normalize-space(text())='${el.textContent.trim()}']`;
        }
        // Fallback to nth-child
        let path = '';
        let node = el;
        while (node && node.nodeType === 1) {
            let idx = 1;
            let sibling = node.previousSibling;
            while (sibling) {
                if (sibling.nodeType === 1 && sibling.tagName === node.tagName) idx++;
                sibling = sibling.previousSibling;
            }
            path = `/${node.tagName.toLowerCase()}[${idx}]` + path;
            node = node.parentElement;
        }
        return path;
    }''')
    return xpath

async def is_selector_unique(page, selector):
    """Check if a CSS selector is unique on the page."""
    try:
        count = await page.eval_on_selector_all(selector, 'els => els.length')
        return count == 1
    except Exception:
        return False

async def is_xpath_unique(page, xpath):
    """Check if an XPath is unique on the page."""
    try:
        count = await page.evaluate("(xpath) => { return document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null).snapshotLength }", xpath)
        return count == 1
    except Exception:
        return False

async def extract_elements(page):
    """Extract all relevant elements and their locators from the page, including CSS/XPath and uniqueness. Only score visible, interactive elements."""
    elements = []
    selector = "input, button, a, select, textarea, h1, h2, h3, h4, h5, h6, p, img, li, div[role], span[role], [aria-label], [data-test-id], [type='submit'], [type='reset'], [type='button']"
    handles = await page.query_selector_all(selector)
    raw_elements = []
    for handle in handles:
        try:
            tag_name = (await handle.evaluate("el => el.tagName")).lower()
            attributes = await handle.evaluate("el => Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value]))")
            # Remove 'value' from attributes for all elements
            attributes.pop("value", None)
            text_content = await handle.inner_text() if tag_name not in ["img"] else ""
            is_visible = await handle.is_visible()
            # Consider interactive if enabled and not disabled
            is_interactive = await handle.is_enabled() if tag_name in ["input", "button", "select", "textarea", "a"] else True
            el = {
                "tag": tag_name,
                "attributes": attributes,
                "text_content": text_content,
                "id": attributes.get("id"),
                "class": attributes.get("class"),
                "name": attributes.get("name"),
                "type": attributes.get("type"),
                "aria_label": attributes.get("aria-label"),
                "role": attributes.get("role"),
                # Always skip 'value' for all elements
                "value": None,
                "text": text_content,
                "is_visible": is_visible,
                "is_interactive": is_interactive,
                "_handle": handle,  # Keep for selector generation
            }
            el["description"] = generate_description(el)
            raw_elements.append(el)
        except Exception as e:
            print(f"[ERROR] Failed to extract element: {e}")
    # Second pass: generate locators, check uniqueness, select best, add CSS/XPath
    for el in raw_elements:
        if not el["is_visible"] or not el["is_interactive"]:
            continue  # Skip scoring for non-visible or non-interactive elements
        locators = generate_basic_locators(el)
        for locator in locators:
            locator["unique"] = is_unique(locator["type"], locator["value"], raw_elements)
            locator["element_tag"] = el["tag"]  # Pass tag for dynamic scoring
            locator["score"] = score_locator(locator)
        handle = el.pop("_handle")
        css_selector = await get_css_selector(handle)
        xpath = await get_xpath(handle)
        css_unique = await is_selector_unique(page, css_selector)
        xpath_unique = await is_xpath_unique(page, xpath)
        # Use new best locator selection logic
        best_locator = select_best_locator(
            locators,
            best_unique_xpath=xpath if xpath_unique else None,
            best_unique_css=css_selector if css_unique else None,
            threshold=70
        )
        element_info = {
            **el,
            "locators": locators,
            "best_locator": best_locator,
            "css_selector": css_selector,
            "css_unique": css_unique,
            "xpath": xpath,
            "xpath_unique": xpath_unique,
            "best_unique_css": css_selector if css_unique else None,
            "best_unique_xpath": xpath if xpath_unique else None,
        }
        elements.append(element_info)
    return elements

async def crawl_application(context, base_url, scan_config):
    """Basic BFS crawl: visits pages, extracts elements, captures screenshots, returns application map."""
    from pathlib import Path
    import hashlib
    visited = set()
    queue = [base_url]
    pages_crawled = 0
    app_map = []
    while queue and pages_crawled < scan_config["max_pages"]:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        page = await context.new_page()
        try:
            await page.goto(url)
            # Extract elements
            elements = await extract_elements(page)
            # Capture screenshot
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            screenshot_filename = f"screenshot_{url_hash}.png"
            screenshot_path = Path("screenshots") / screenshot_filename
            await page.screenshot(path=str(screenshot_path), full_page=True)
            # Extract links for further crawling
            links = await page.eval_on_selector_all('a[href]', 'els => els.map(e => e.href)')
            # Respect include/exclude patterns
            for link in links:
                if any(pat in link for pat in scan_config.get("exclude_patterns", [])):
                    continue
                if scan_config.get("include_patterns") and not any(pat in link for pat in scan_config["include_patterns"]):
                    continue
                if link not in visited and link not in queue:
                    queue.append(link)
            # Add page data to app_map
            app_map.append({
                "url": url,
                "elements": elements,
                "screenshot": str(screenshot_path)
            })
            pages_crawled += 1
        except Exception as e:
            print(f"[ERROR] Failed to crawl {url}: {e}")
        finally:
            await page.close()
    return app_map 