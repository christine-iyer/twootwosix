#!/usr/bin/env python3
"""
Script to scrape CNN election data from their 2026 primary pages.
CNN embeds election data in JSON format within the page or loads it via API.
"""

import requests
import json
import csv
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import sys

def extract_election_data_from_html(url):
    """
    Fetch the CNN election page and extract embedded JSON data.
    CNN often embeds data in <script> tags as __NEXT_DATA__ or similar.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"Fetching: {url}")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for __NEXT_DATA__ (Next.js pattern)
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
    if next_data_script:
        print("Found __NEXT_DATA__ script")
        data = json.loads(next_data_script.string)
        return data
    
    # Look for other script tags with JSON
    for script in soup.find_all('script'):
        if script.string and 'election' in script.string.lower():
            # Try to extract JSON from script content
            try:
                # Look for patterns like window.__data = {...}
                match = re.search(r'window\.__[\w]+\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                    return data
            except:
                pass
    
    return None

def try_api_endpoint(state_code, election_id):
    """
    Try to find CNN's API endpoint for election data.
    CNN sometimes uses patterns like:
    - /api/election/results/{year}/{election-type}/{state}
    """
    # Common CNN election API patterns
    api_patterns = [
        f"https://www.cnn.com/election/2026/api/results/{election_id}/admin1/{state_code}",
        f"https://www.cnn.com/api/election/2026/results/{election_id}/admin1/{state_code}",
        f"https://politics.api.cnn.io/election/2026/{election_id}/admin1/{state_code}",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    for api_url in api_patterns:
        try:
            print(f"Trying API: {api_url}")
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                print(f"Success! Found API endpoint: {api_url}")
                return response.json()
        except Exception as e:
            continue
    
    return None

def extract_county_results(data):
    """
    Extract county-level results from the JSON data structure.
    The exact path will depend on CNN's data structure.
    """
    results = []
    
    # Try different common paths in CNN's data structure
    paths_to_try = [
        ['props', 'pageProps', 'raceData', 'counties'],
        ['props', 'pageProps', 'counties'],
        ['counties'],
        ['admin2'],
        ['results', 'counties'],
        ['results', 'admin2'],
    ]
    
    county_data = None
    for path in paths_to_try:
        try:
            temp = data
            for key in path:
                temp = temp[key]
            county_data = temp
            print(f"Found data at path: {' -> '.join(path)}")
            break
        except (KeyError, TypeError):
            continue
    
    if not county_data:
        print("Could not find county data in expected locations")
        print("Data structure keys:", list(data.keys()) if isinstance(data, dict) else type(data))
        return None
    
    return county_data

def save_to_csv(data, output_file):
    """
    Save the extracted data to CSV format.
    """
    if not data:
        print("No data to save")
        return
    
    # Determine the structure and flatten it
    rows = []
    
    # Handle different data structures
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                rows.append(item)
    elif isinstance(data, dict):
        # Might be keyed by county ID or name
        for key, value in data.items():
            if isinstance(value, dict):
                value['id'] = key
                rows.append(value)
            else:
                rows.append({'id': key, 'data': value})
    
    if not rows:
        print("No rows to write")
        return
    
    # Get all unique keys
    all_keys = set()
    for row in rows:
        all_keys.update(flatten_dict(row).keys())
    
    fieldnames = sorted(all_keys)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(flatten_dict(row))
    
    print(f"Saved {len(rows)} rows to {output_file}")

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten nested dictionary structure.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            # Handle list of dicts (like candidates)
            for i, item in enumerate(v):
                items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_cnn_election.py <CNN_ELECTION_URL> [output.csv]")
        print("\nExample:")
        print("  python scrape_cnn_election.py 'https://www.cnn.com/election/2026/primaries/texas?admin1=48&election-data-id=2026-SD'")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'cnn_election_results.csv'
    
    # Parse URL to extract state and election ID
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    state_code = params.get('admin1', [None])[0]
    election_id = params.get('election-data-id', [None])[0]
    
    print(f"State Code: {state_code}")
    print(f"Election ID: {election_id}")
    print()
    
    # Try API endpoint first
    data = None
    if state_code and election_id:
        data = try_api_endpoint(state_code, election_id)
    
    # If API didn't work, try scraping HTML
    if not data:
        print("\nAPI approach didn't work, trying HTML extraction...")
        data = extract_election_data_from_html(url)
    
    if not data:
        print("Could not extract data from page")
        print("\nYou might need to:")
        print("1. Use browser dev tools to find the actual API endpoint")
        print("2. Use Selenium/Playwright to render JavaScript")
        print("3. Check if data is loaded dynamically after page load")
        sys.exit(1)
    
    # Save raw JSON for inspection
    with open('cnn_data_raw.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved raw data to cnn_data_raw.json for inspection")
    
    # Extract county results
    county_data = extract_county_results(data)
    
    if county_data:
        save_to_csv(county_data, output_file)
    else:
        print("\nCould not extract county data. Check cnn_data_raw.json to see the structure.")
        print("You may need to modify the extract_county_results() function.")

if __name__ == '__main__':
    main()
