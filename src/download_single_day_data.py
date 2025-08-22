import os
import requests
from bs4 import BeautifulSoup
import datetime # Import the datetime module


# --- Configuration ---
url = 'https://opendata.cui.wroclaw.pl/dataset/wrmprzejazdy_data/resource_history/c737af89-bcf7-4f7d-8bbc-4a0946d7006e'
output_dir = '../data/raw/2025'

# --- Helper function for timestamped logging ---
def log_message(message):
    """Prepends a timestamp to a message and prints it."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} {message}")


# --- Setup Output Directory ---
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    log_message(f"Created directory: {output_dir}")
else:
    log_message(f"Output directory already exists: {output_dir}")

# --- Function to download a file from a URL ---
def download_file(url, output_dir):
    """Downloads a single file from a URL to the specified directory."""
    try:
        # Construct the full local path for the file
        filename = os.path.basename(url)
        if not filename: # Handle cases where URL might not end nicely
            log_message("Warning: Could not determine filename from URL, using default.")
            filename = "downloaded_file.csv" # Default filename
        local_filename = os.path.join(output_dir, filename)

        log_message(f'Attempting to download: {url}')
        # Send a GET request to the URL
        with requests.get(url, stream=True, timeout=30) as response: # Added timeout
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            # Write the content to a local file
            with open(local_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            log_message(f'Successfully downloaded and saved to: {local_filename}')
            return local_filename
    except requests.exceptions.RequestException as e:
        log_message(f'Error downloading {url}: {e}')
        return None
    except Exception as e:
        log_message(f'An unexpected error occurred during download: {e}')
        return None

# --- Main script logic ---
log_message(f"Script started. Fetching list of files from: {url}")
try:
    # Send a GET request to the webpage
    response = requests.get(url, timeout=15) # Added timeout
    response.raise_for_status()
    log_message(f"Successfully fetched page content from {url}")

    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    log_message("HTML content parsed successfully.")

    # Find the *first* 'a' element with class 'heading'
    first_link_element = soup.find('a', class_='heading')

    if first_link_element:
        # Extract the href attribute (the URL) from the first element
        target_url = first_link_element.get('href')

        if target_url:
            log_message(f"Most recent file URL found: {target_url}")
            # Download only this single file
            downloaded_path = download_file(target_url, output_dir)
            if downloaded_path:
                log_message("Download process complete for the most recent file.")
            else:
                log_message("Download failed for the most recent file.")
        else:
            log_message("Error: Found the link element but it has no 'href' attribute.")

    else:
        log_message("Error: Could not find any link element with class 'heading' on the page.")

except requests.exceptions.RequestException as e:
    log_message(f"Error fetching the page {url}: {e}")
except Exception as e:
    log_message(f"An unexpected error occurred: {e}")

log_message("Script finished.")