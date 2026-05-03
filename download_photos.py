import asyncio, os, base64
from playwright.async_api import async_playwright

GALLERY = os.path.join(os.path.dirname(__file__), 'gallery')
os.makedirs(GALLERY, exist_ok=True)

POSTS = [
    ('lir_01.jpg', 'https://www.instagram.com/lir.photographer/p/DSygPEHCBW7/'),
    ('lir_02.jpg', 'https://www.instagram.com/lir.photographer/p/DGY69Q_iham/'),
    ('lir_03.jpg', 'https://www.instagram.com/lir.photographer/p/DOYWlS7iIqC/'),
    ('lir_04.jpg', 'https://www.instagram.com/lir.photographer/p/DXSPIQ1iIjw/'),
    ('lir_05.jpg', 'https://www.instagram.com/lir.photographer/p/DXPhuXiCKwT/'),
    ('lir_06.jpg', 'https://www.instagram.com/lir.photographer/p/DW9R-b5CFeI/'),
    ('lir_07.jpg', 'https://www.instagram.com/lir.photographer/p/DW62uDyCLxg/'),
    ('lir_08.jpg', 'https://www.instagram.com/lir.photographer/p/DWt8fu9CApV/'),
    ('lir_09.jpg', 'https://www.instagram.com/lir.photographer/p/DVQfrg_CGrW/'),
    ('lir_10.jpg', 'https://www.instagram.com/lir.photographer/p/DU2kgkwCHac/'),
    ('lir_11.jpg', 'https://www.instagram.com/lir.photographer/p/DTXmbJjiHHD/'),
    ('lir_12.jpg', 'https://www.instagram.com/lir.photographer/p/DR2GUB7CP8S/'),
]

async def download_post(page, filename, url):
    out = os.path.join(GALLERY, filename)
    if os.path.exists(out) and os.path.getsize(out) > 10000:
        print(f'Skip {filename} (exists)')
        return True
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(3000)
        imgs = await page.evaluate('''() => {
            const all = Array.from(document.querySelectorAll('img'));
            const big = all.filter(i => i.naturalWidth > 400);
            return big.map(i => ({src: i.src, w: i.naturalWidth, h: i.naturalHeight}));
        }''')
        if not imgs:
            print(f'No image for {filename}')
            return False
        best = max(imgs, key=lambda i: i['w'])
        print(f'{filename}: found {best["w"]}x{best["h"]} image, downloading...')
        # Download via fetch
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
        print(f'Saved {filename} ({len(data)//1024}KB)')
        return True
    except Exception as e:
        print(f'Error {filename}: {e}')
        return False

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel='chrome',
            headless=True,
            args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
        )
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = await ctx.new_page()
        for filename, url in POSTS:
            await download_post(page, filename, url)
        await browser.close()
    print('Done!')

asyncio.run(main())
