import os
import time
import requests
from bs4 import BeautifulSoup

url = 'https://opendata.cui.wroclaw.pl/dataset/wrmprzejazdy_data/resource_history/c737af89-bcf7-4f7d-8bbc-4a0946d7006e'

# Directory to save the downloaded files
output_dir = '../data'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Send a GET request to the webpage
response = requests.get(url)

# Parse the HTML content of the page
soup = BeautifulSoup(response.content, 'html.parser')

# Find all a elements with class 'heading'
a_elements = soup.find_all('a', class_='heading')

# Extract the href attribute from each a element
urls = [a.get('href') for a in a_elements]

# Function to download a file from a URL
def download_file(url, output_dir):
    local_filename = os.path.join(output_dir, url.split('/')[-1])
    # Send a GET request to the URL
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        # Write the content to a local file
        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

total_files = len(urls)
for index, url in enumerate(urls):
    try:
        print(f'Downloading {url}... ({total_files - index} files left)')
        download_file(url, output_dir)
        print(f'Downloaded {url} successfully.')
        time.sleep(5)  # Time interval between downloads in seconds
    except Exception as e:
        print(f'Failed to download {url}: {e}')

print('All files downloaded.')