import browser_cookie3, instaloader, os, shutil, glob

GALLERY = os.path.join(os.path.dirname(__file__), 'gallery')
os.makedirs(GALLERY, exist_ok=True)
USERNAME = 'lir.photographer'

print('Extracting Instagram cookies from Edge...')
try:
    cookies = browser_cookie3.edge(domain_name='.instagram.com')
    cookie_dict = {c.name: c.value for c in cookies}
    session_id = cookie_dict.get('sessionid')
    print(f'Found {len(cookie_dict)} cookies, sessionid: {"YES" if session_id else "NO"}')
except Exception as e:
    print(f'Edge cookies failed: {e}')
    session_id = None

if not session_id:
    print('Trying Chrome...')
    try:
        cookies = browser_cookie3.chrome(domain_name='.instagram.com')
        cookie_dict = {c.name: c.value for c in cookies}
        session_id = cookie_dict.get('sessionid')
        print(f'Chrome: {len(cookie_dict)} cookies, sessionid: {"YES" if session_id else "NO"}')
    except Exception as e:
        print(f'Chrome cookies failed: {e}')

if not session_id:
    print('ERROR: Could not get session ID. Make sure Instagram is open and logged in.')
    exit(1)

print(f'\nSession ID found! Starting download...')

L = instaloader.Instaloader(
    download_pictures=True,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    post_metadata_txt_pattern='',
    quiet=False,
)

# Inject the session
L.context._session.cookies.update(cookie_dict)

TMP = os.path.join(os.path.dirname(__file__), '_insta_tmp', USERNAME)
os.makedirs(TMP, exist_ok=True)

try:
    profile = instaloader.Profile.from_username(L.context, USERNAME)
    print(f'Profile: {profile.full_name}, {profile.mediacount} posts, {profile.followers} followers')

    existing_count = len([f for f in os.listdir(GALLERY) if f.endswith('.jpg')])
    print(f'Existing photos: {existing_count}. Will download up to 40 more posts.')

    num = existing_count + 1
    downloaded = 0

    for post in profile.get_posts():
        if post.typename == 'GraphSidecar':
            # Multi-image post — get first image
            pass
        try:
            # Download to tmp
            L.download_post(post, target=TMP)
            downloaded += 1
            print(f'  Post {downloaded} downloaded')
            if downloaded >= 40:
                break
        except Exception as e:
            print(f'  Skip: {e}')
            continue

    # Copy JPGs to gallery
    jpgs = sorted(glob.glob(os.path.join(TMP, '*.jpg')))
    print(f'\nCopying {len(jpgs)} images to gallery...')
    copied = 0
    num = existing_count + 1
    for jpg in jpgs:
        dest = os.path.join(GALLERY, f'lir_{num:02d}.jpg')
        if not os.path.exists(dest):
            shutil.copy2(jpg, dest)
            size = os.path.getsize(dest) // 1024
            print(f'  lir_{num:02d}.jpg ({size}KB)')
            num += 1
            copied += 1

    print(f'\n✅ Done! Copied {copied} new photos. Total: {len(os.listdir(GALLERY))} in gallery.')

except Exception as e:
    print(f'Download error: {e}')
    import traceback; traceback.print_exc()
