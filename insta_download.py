import instaloader, os, shutil, glob

GALLERY = os.path.join(os.path.dirname(__file__), 'gallery')
os.makedirs(GALLERY, exist_ok=True)

USERNAME = 'lir.photographer'
TMP = os.path.join(os.path.dirname(__file__), '_insta_tmp')

L = instaloader.Instaloader(
    download_pictures=True,
    download_videos=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False,
    post_metadata_txt_pattern='',
    filename_pattern='{profile}_{mediaid}',
    quiet=False,
)

try:
    print(f'Downloading posts from @{USERNAME}...')
    profile = instaloader.Profile.from_username(L.context, USERNAME)
    print(f'Profile: {profile.full_name}, {profile.mediacount} posts, {profile.followers} followers')

    # Download to tmp folder
    os.makedirs(TMP, exist_ok=True)
    os.chdir(TMP)

    count = 0
    for post in profile.get_posts():
        try:
            L.download_post(post, target=USERNAME)
            count += 1
            print(f'Downloaded post {count}')
            if count >= 40:
                break
        except Exception as e:
            print(f'Skip post: {e}')
            continue

    # Move JPGs to gallery folder, rename sequentially
    existing_count = len([f for f in os.listdir(GALLERY) if f.endswith('.jpg')])
    jpgs = sorted(glob.glob(os.path.join(TMP, USERNAME, '*.jpg')))
    print(f'\nFound {len(jpgs)} JPG files to copy...')

    num = existing_count + 1
    for jpg in jpgs:
        dest = os.path.join(GALLERY, f'lir_{num:02d}.jpg')
        if not os.path.exists(dest):
            shutil.copy2(jpg, dest)
            print(f'  Copied -> lir_{num:02d}.jpg')
            num += 1

    print(f'\nTotal gallery photos: {len(os.listdir(GALLERY))}')

except Exception as e:
    print(f'Error: {e}')
    print('Note: Public profiles may require a logged-in session.')
    print('Try: L.load_session_from_file("your_username") after login.')
