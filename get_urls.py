import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel='chrome',
            headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 900}
        )
        page = await ctx.new_page()

        print('Going to lir.photographer profile...')
        await page.goto('https://www.instagram.com/lir.photographer/', timeout=30000)
        await page.wait_for_timeout(5000)
        title = await page.title()
        print(f'Title: {title}')

        # Try to get post links
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[href*="/p/"]')).map(a => a.href);
        }''')
        print(f'Found {len(links)} post links:')
        for l in links[:30]:
            print(' ', l)

        # Also check what's visible
        content = await page.content()
        if 'login' in content.lower() or 'Log in' in content:
            print('\nLOGIN WALL DETECTED')

        await browser.close()

asyncio.run(main())
