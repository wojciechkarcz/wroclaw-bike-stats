from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import contextlib

def scrape_bike_stations(url, output_file='wroclaw_bike_stations.csv'):
    """Scrape bike station data and save to CSV."""
    # Set up Chrome options
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')

    # Use context manager for the driver to ensure proper cleanup
    with webdriver.Chrome(options=options) as driver:
        # Open the website
        driver.get(url)

        # Wait for table to load instead of using fixed sleep
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table tbody'))
        )

        # Extract rows
        rows = table.find_elements(By.TAG_NAME, 'tr')

        # Parse data
        stations = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) >= 5:
                try:
                    coords = cells[3].text.strip().split(', ')
                    stations.append({
                        'station_id': cells[0].text.strip(),
                        'station_name': cells[1].text.strip(),
                        'lat': coords[0],
                        'lon': coords[1],
                        'capacity': cells[4].text.strip()
                    })
                except IndexError:
                    # Skip rows with incorrect format
                    continue

    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['station_id', 'station_name', 'lat', 'lon', 'capacity']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(stations)

    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    scrape_bike_stations('https://wroclawskirower.pl/mapa-stacji/')