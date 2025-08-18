import os
import re
import time
import datetime as dt
from urllib.parse import urljoin
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup

URL = 'https://opendata.cui.wroclaw.pl/dataset/wrmprzejazdy_data/resource_history/c737af89-bcf7-4f7d-8bbc-4a0946d7006e'

# Directory to save the downloaded files (resolve relative to repo root)
# This makes it robust regardless of current working directory.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(REPO_ROOT, 'data', 'raw', '2025')

# Date range: from 2025-04-01 to today (inclusive)
START_DATE = dt.date(2025, 4, 1)
END_DATE = dt.date.today()


def ensure_output_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def extract_date_from_filename(filename):
    """
    Extract date in the form YYYY-M-D (month/day may be 1 or 2 digits) from file
    name.
    Example: "Historia_przejazdow_2025-4-2_16_19_13.csv" -> date(2025, 4, 2)
    Returns None if no date-like pattern is found or invalid.
    """
    m = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', filename)
    if not m:
        return None
    try:
        year, month, day = map(int, m.groups())
        return dt.date(year, month, day)
    except ValueError:
        return None


def in_range(d):
    return START_DATE <= d <= END_DATE


def make_session():
    s = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount('http://', adapter)
    s.mount('https://', adapter)
    s.headers.update({
        'User-Agent': 'wroclaw-bike-stats/1.0 (+https://github.com/)'
    })
    return s


def get_listing_urls(page_url, session=None):
    session = session or requests
    resp = session.get(page_url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    a_elements = soup.find_all('a', class_='heading')
    hrefs = [a.get('href') for a in a_elements if a.get('href')]
    # Ensure absolute URLs
    return [urljoin(page_url, h) for h in hrefs]


def filter_csvs_in_range(urls):
    filtered = []
    for u in urls:
        if not u.lower().endswith('.csv'):
            continue
        fname = os.path.basename(u)
        d = extract_date_from_filename(fname)
        if d and in_range(d):
            filtered.append(u)
    return filtered


def download_file(file_url, out_dir, session=None):
    local_path = os.path.join(out_dir, os.path.basename(file_url))
    # Skip if already downloaded
    if os.path.exists(local_path) and os.path.getsize(local_path) > 0:
        return local_path
    session = session or requests
    with session.get(file_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    return local_path


def main():
    ensure_output_dir(OUTPUT_DIR)
    session = make_session()
    all_urls = get_listing_urls(URL, session=session)
    target_urls = filter_csvs_in_range(all_urls)

    total = len(target_urls)
    print(f'Found {total} CSV files dated {START_DATE}..{END_DATE}.')
    for idx, u in enumerate(target_urls, start=1):
        remaining = total - idx + 1
        try:
            print(f'Downloading {u}... ({remaining} files left)')
            path = download_file(u, OUTPUT_DIR, session=session)
            if path and os.path.exists(path):
                print(f'Downloaded {os.path.basename(path)} successfully.')
            else:
                print(f'Skipped {u} (already exists).')
            time.sleep(2)  # polite interval between downloads
        except Exception as e:
            print(f'Failed to download {u}: {e}')


if __name__ == '__main__':
    main()
