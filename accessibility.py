import os
from datetime import datetime
from playwright.async_api import async_playwright

async def capture_building_screenshot(building_name, output_dir="Captures"):
    """Capture full map + popup after zooming in, NOT just the popup box."""
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()

        print("Navigating to UofA map...")
        await page.goto("https://map.arizona.edu/")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(4000)

        print(f"Searching for: {building_name}")
        search_box = await page.wait_for_selector("input#searchInput", timeout=5000)
        await search_box.fill(building_name)
        await page.wait_for_timeout(1000)
        await search_box.press("Enter")

        # Wait for popup to appear
        try:
            await page.wait_for_selector(".esri-popup__header", timeout=7000)
            print("Popup appeared.")
        except Exception as e:
            print("Popup did not appear — capturing whatever is visible.")

        # Zoom in using CTRL + + (simulate zoom)
        for _ in range(2):
            await page.keyboard.down('Control')
            await page.keyboard.press('+')
            await page.keyboard.up('Control')
            await page.wait_for_timeout(1000)  # wait after zoom

        await page.wait_for_timeout(3000)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"map_{building_name.replace(' ', '_')}_{timestamp}.png"
        full_path = os.path.join(output_dir, filename)

        await page.screenshot(path=full_path, full_page=False)
        print(f"Screenshot saved to: {full_path}")

        await context.close()
        await browser.close()

        return full_path  # Single image path
