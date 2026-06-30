import subprocess
import time

# Use playwright if available
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture console messages
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        
        # Capture page errors
        page_errors = []
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        
        # Navigate to the page
        response = page.goto("http://localhost:8004/frontend_demo.html", timeout=15000)
        print(f"Page status: {response.status}")
        print(f"Page title: {page.title()}")
        
        # Wait a moment for page to load
        time.sleep(2)
        
        # Click the analyze button
        page.click("#analyzeBtn")
        print("Clicked analyze button")
        
        # Wait for SSE to complete
        time.sleep(8)
        
        # Check status bar
        status_text = page.text_content("#statusBar")
        print(f"Status bar: {status_text}")
        
        # Check output content
        output_text = page.text_content("#outputContent")
        print(f"Output content length: {len(output_text)}")
        print(f"Output content preview: {output_text[:200]}")
        
        # Print console messages
        if console_messages:
            print(f"\nConsole messages ({len(console_messages)}):")
            for msg in console_messages:
                print(f"  {msg}")
        
        if page_errors:
            print(f"\nPage errors ({len(page_errors)}):")
            for err in page_errors:
                print(f"  {err}")
        
        browser.close()
        
except ImportError:
    print("playwright not available, trying selenium...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=options)
        driver.get("http://localhost:8004/frontend_demo.html")
        time.sleep(2)
        
        # Click
        button = driver.find_element("id", "analyzeBtn")
        button.click()
        time.sleep(8)
        
        status = driver.find_element("id", "statusBar").text
        print(f"Status bar: {status}")
        
        output = driver.find_element("id", "outputContent").text
        print(f"Output preview: {output[:200]}")
        
        driver.quit()
    except ImportError:
        print("Neither playwright nor selenium available")
