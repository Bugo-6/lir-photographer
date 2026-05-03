import asyncio, os, base64
from playwright.async_api import async_playwright

GALLERY = os.path.join(os.path.dirname(__file__), 'gallery')
os.makedirs(GALLERY, exist_ok=True)

PROFILE_URL = 'https://www.instagram.com/lir.photographer/'

# Edge user data (already logged in to Instagram)
EDGE_USER_DATA = r'C:\Users\noamz\AppData\Local\Microsoft\Edge\User Data'

async def get_post_urls(page):
    print(f'Going to profile...')
    await page.goto(PROFILE_URL, wait_until='domcontentloaded', timeout=40000)
    await page.wait_for_timeout(5000)

    title = await page.title()
    print(f'Page title: {title}')

    # Scroll to load more posts
    for i in range(8):
        await page.evaluate('window.scrollBy(0, 1500)')
        await page.wait_for_timeout(1000)

    links = await page.evaluate('''() => {
        const anchors = Array.from(document.querySelectorAll('a[href*="/p/"]'));
        return [...new Set(anchors.map(a => a.href))];
    }''')
    print(f'Found {len(links)} post links')
    return links

async def download_post(page, filename, url):
    out = os.path.join(GALLERY, filename)
    if os.path.exists(out) and os.path.getsize(out) > 10000:
        print(f'  Skip {filename}')
        return True
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(3000)

        imgs = await page.evaluate('''() => {
            const all = Array.from(document.querySelectorAll('img'));
            const big = all.filter(i => i.naturalWidth > 300);
            return big.map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}));
        }''')

        if not imgs:
            print(f'  No image: {filename}')
            return False

        best = max(imgs, key=lambda i: i['w'] * i['h'])
        print(f'  {filename}: {best["w"]}x{best["h"]}')

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
        print(f'  ✓ {filename} ({len(data)//1024}KB)')
        return True
    except Exception as e:
        print(f'  ✗ {filename}: {e}')
        return False

async def main():
    existing = {f for f in os.listdir(GALLERY) if f.endswith('.jpg')}
    start_num = len(existing) + 1
    print(f'Existing: {len(existing)} photos. Starting from lir_{start_num:02d}.jpg')

    async with async_playwright() as p:
        # Use Edge with existing profile (already logged in to Instagram)
        browser = await p.chromium.launch(
            channel='msedge',
            headless=False,
            args=[
                '--no-sandbox',
                f'--user-data-dir={EDGE_USER_DATA}',
                '--profile-directory=Default',
                '--disable-blink-features=AutomationControlled',
            ]
        )
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await ctx.new_page()

        try:
            post_urls = await get_post_urls(page)
        except Exception as e:
            print(f'Profile scrape error: {e}')
            post_urls = []

        if not post_urls:
            print('No URLs found — using fallback list')
            post_urls = [
                'https://www.instagram.com/lir.photographer/p/DQzBr3RCPQE/',
                'https://www.instagram.com/lir.photographer/p/DQ1R2x7CkO3/',
                'https://www.instagram.com/lir.photographer/p/DPwJkA6C6Oh/',
                'https://www.instagram.com/lir.photographer/p/DPMj9WDCZ3l/',
                'https://www.instagram.com/lir.photographer/p/DOzG8j6iS0M/',
                'https://www.instagram.com/lir.photographer/p/DNw5c4fCwqT/',
                'https://www.instagram.com/lir.photographer/p/DNO6qZhCJ4d/',
                'https://www.instagram.com/lir.photographer/p/DMz3p8RiW9e/',
                'https://www.instagram.com/lir.photographer/p/DMPCxARiI8q/',
                'https://www.instagram.com/lir.photographer/p/DLwQEbRCe0U/',
                'https://www.instagram.com/lir.photographer/p/DLNmPIFicD9/',
                'https://www.instagram.com/lir.photographer/p/DKqwJsRC7zA/',
                'https://www.instagram.com/lir.photographer/p/DKI7vMXCxq8/',
                'https://www.instagram.com/lir.photographer/p/DJp4CpHC4vy/',
                'https://www.instagram.com/lir.photographer/p/DJHiQxACnzQ/',
                'https://www.instagram.com/lir.photographer/p/DIqTpzJC4bP/',
                'https://www.instagram.com/lir.photographer/p/DHzLdAGi8pX/',
                'https://www.instagram.com/lir.photographer/p/DHSOGcVitXQ/',
                'https://www.instagram.com/lir.photographer/p/DGxqVe-i5tN/',
                'https://www.instagram.com/lir.photographer/p/DGPpGqYiQM5/',
                'https://www.instagram.com/lir.photographer/p/DF1FGS1iRFv/',
                'https://www.instagram.com/lir.photographer/p/DFSomJNC4_w/',
                'https://www.instagram.com/lir.photographer/p/DE5s7Ndi0fG/',
                'https://www.instagram.com/lir.photographer/p/DEWcBoFiUAW/',
                'https://www.instagram.com/lir.photographer/p/DD_UVaGiuMY/',
            ]

        downloaded = 0
        num = start_num
        for url in post_urls:
            filename = f'lir_{num:02d}.jpg'
            if filename in existing:
                num += 1
                continue
            ok = await download_post(page, filename, url)
            if ok:
                downloaded += 1
            num += 1
            if downloaded >= 25:
                break

        await browser.close()
        total = len(os.listdir(GALLERY))
        print(f'\n✅ Done! Downloaded {downloaded} new. Total: {total} photos')

asyncio.run(main())
