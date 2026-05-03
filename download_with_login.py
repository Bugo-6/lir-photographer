import asyncio, os, base64
from playwright.async_api import async_playwright

GALLERY = os.path.join(os.path.dirname(__file__), 'gallery')
os.makedirs(GALLERY, exist_ok=True)
SESSION_FILE = os.path.join(os.path.dirname(__file__), 'ig_session.json')

async def main():
    existing = sorted([f for f in os.listdir(GALLERY) if f.endswith('.jpg')])
    start_num = len(existing) + 1
    print(f'Existing: {len(existing)} photos. Starting from lir_{start_num:02d}.jpg')

    async with async_playwright() as p:
        ctx_opts = {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'viewport': {'width': 1280, 'height': 900},
        }
        # Try saved session
        if os.path.exists(SESSION_FILE):
            import json
            with open(SESSION_FILE) as f:
                ctx_opts['storage_state'] = json.load(f)
            print('Loaded saved session.')

        browser = await p.chromium.launch(
            channel='chrome', headless=False,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        ctx = await browser.new_context(**ctx_opts)
        page = await ctx.new_page()

        await page.goto('https://www.instagram.com/', timeout=30000)
        await page.wait_for_timeout(3000)

        # Wait for login — poll until sessionid cookie exists
        print('Waiting for Instagram login...')
        print('(Please log in to the browser window if needed)')
        for _ in range(120):  # wait up to 2 minutes
            cookies = await ctx.cookies()
            session = next((c for c in cookies if c['name'] == 'sessionid'), None)
            if session:
                print('✓ Logged in!')
                break
            await asyncio.sleep(1)
        else:
            print('Timeout waiting for login.')
            await browser.close()
            return

        # Save session
        import json
        state = await ctx.storage_state()
        with open(SESSION_FILE, 'w') as f:
            json.dump(state, f)
        print('Session saved.')

        # Go to lir.photographer profile
        print('\nNavigating to @lir.photographer...')
        await page.goto('https://www.instagram.com/lir.photographer/', timeout=30000)
        await page.wait_for_timeout(4000)

        title = await page.title()
        print(f'Page: {title}')

        # Scroll to load all posts
        print('Scrolling to load posts...')
        for i in range(12):
            await page.evaluate('window.scrollBy(0, 1200)')
            await page.wait_for_timeout(700)

        links = await page.evaluate('''() => {
            const anchors = Array.from(document.querySelectorAll('a[href*="/p/"]'));
            return [...new Set(anchors.map(a => a.href))];
        }''')
        print(f'\nFound {len(links)} posts to download!')

        # Download each
        num = start_num
        downloaded = 0
        for url in links:
            filename = f'lir_{num:02d}.jpg'
            out = os.path.join(GALLERY, filename)
            if os.path.exists(out) and os.path.getsize(out) > 5000:
                print(f'  Skip {filename} (exists)')
                num += 1
                continue
            try:
                await page.goto(url, wait_until='domcontentloaded', timeout=25000)
                await page.wait_for_timeout(2000)

                imgs = await page.evaluate('''() => {
                    const all = Array.from(document.querySelectorAll('img'));
                    const big = all.filter(i => i.naturalWidth > 400);
                    return big.map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}));
                }''')

                if not imgs:
                    print(f'  {filename}: no image')
                    num += 1
                    continue

                best = max(imgs, key=lambda i: i['w'] * i['h'])

                b64 = await page.evaluate(f'''async () => {{
                    const r = await fetch("{best['src']}");
                    const buf = await r.arrayBuffer();
                    const bytes = new Uint8Array(buf);
                    let bin = "";
                    for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
                    return btoa(bin);
                }}''')

                data = base64.b64decode(b64)
                with open(out, 'wb') as f:
                    f.write(data)
                print(f'  ✓ {filename} — {best["w"]}x{best["h"]} ({len(data)//1024}KB)')
                downloaded += 1
                num += 1

            except Exception as e:
                print(f'  ✗ {filename}: {e}')
                num += 1

        await browser.close()
        print(f'\n✅ Done! Downloaded {downloaded} new photos. Total: {len(os.listdir(GALLERY))}')

asyncio.run(main())
