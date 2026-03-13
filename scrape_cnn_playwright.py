#!/usr/bin/env python3
"""
Script to scrape CNN election data using Playwright to handle JavaScript rendering.
This approach will interact with the actual rendered page to extract tooltip data.
"""

import json
import csv
import sys
import re
import asyncio
from playwright.async_api import async_playwright

async def extract_county_data(url):
    """
    Use Playwright to render the page and extract county data from tooltips.
    """
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Intercept network requests to find API calls
        api_data = []
        
        async def handle_response(response):
            # Look for JSON responses that might contain election data
            if response.status == 200 and 'json' in response.headers.get('content-type', ''):
                url = response.url
                if 'election' in url or 'results' in url or 'admin' in url:
                    try:
                        data = await response.json()
                        api_data.append({'url': url, 'data': data})
                        print(f"Captured API call: {url}")
                    except:
                        pass
        
        page.on('response', handle_response)
        
        print(f"Loading page: {url}")
        await page.goto(url, wait_until='networkidle')
        
        # Wait for the map to load
        print("Waiting for map to load...")
        await page.wait_for_timeout(3000)
        
        # Try to find the actual data in the page context
        print("Extracting data from page...")
        
        # Method 1: Look for __NEXT_DATA__ or other embedded JSON
        next_data = await page.evaluate('''() => {
            const script = document.getElementById('__NEXT_DATA__');
            return script ? JSON.parse(script.textContent) : null;
        }''')
        
        if next_data:
            print("Found __NEXT_DATA__")
            api_data.append({'url': 'embedded', 'data': next_data})
        
        # Method 2: Try to extract data from window objects
        window_data = await page.evaluate('''() => {
            const keys = Object.keys(window);
            const dataKeys = keys.filter(k => k.includes('data') || k.includes('election') || k.includes('__'));
            const result = {};
            for (const key of dataKeys) {
                if (typeof window[key] === 'object' && window[key] !== null) {
                    result[key] = window[key];
                }
            }
            return result;
        }''')
        
        if window_data and len(window_data) > 0:
            print(f"Found window data: {list(window_data.keys())}")
            api_data.append({'url': 'window', 'data': window_data})
        
        # Method 3: Try to hover over map elements to get tooltips
        # This is more complex and would require finding all the county SVG elements
        county_elements = await page.query_selector_all('[data-county], [data-admin2], .county, .admin2')
        print(f"Found {len(county_elements)} potential county elements")
        
        await browser.close()
        
        return api_data

def find_county_data(all_data):
    """
    Search through all captured data to find county-level results.
    """
    for item in all_data:
        data = item['data']
        if not isinstance(data, dict):
            continue
        
        # Search through the data structure
        def search_dict(d, path=""):
            results = []
            if isinstance(d, dict):
                # Look for keys that suggest county data
                for key in ['counties', 'admin2', 'results', 'raceData', 'pageProps']:
                    if key in d:
                        new_path = f"{path}.{key}" if path else key
                        if isinstance(d[key], (list, dict)) and d[key]:
                            results.append((new_path, d[key]))
                        results.extend(search_dict(d[key], new_path))
                
                # Continue searching nested structures
                for key, value in d.items():
                    if key not in ['counties', 'admin2', 'results', 'raceData', 'pageProps']:
                        new_path = f"{path}.{key}" if path else key
                        results.extend(search_dict(value, new_path))
            elif isinstance(d, list) and d:
                for i, item in enumerate(d):
                    results.extend(search_dict(item, f"{path}[{i}]"))
            
            return results
        
        candidates = search_dict(data)
        if candidates:
            return candidates
    
    return []

def extract_to_csv(all_data, output_file):
    """
    Extract election results to CSV format.
    """
    # Save all captured data for manual inspection
    with open('raw-data/cnn_captured_data.json', 'w') as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved all captured data to raw-data/cnn_captured_data.json")
    
    # Try to find county data
    possible_county_data = find_county_data(all_data)
    
    if possible_county_data:
        print(f"\nFound {len(possible_county_data)} potential data locations:")
        for path, data in possible_county_data[:5]:  # Show first 5
            print(f"  - {path}")
            if isinstance(data, list):
                print(f"    (list with {len(data)} items)")
            elif isinstance(data, dict):
                print(f"    (dict with keys: {list(data.keys())[:5]}...)")
        
        # Take the most promising candidate (usually the first one with actual data)
        for path, data in possible_county_data:
            if isinstance(data, list) and len(data) > 10:  # Likely county data
                print(f"\nUsing data from: {path}")
                save_results_to_csv(data, output_file)
                return True
            elif isinstance(data, dict) and len(data) > 10:
                print(f"\nUsing data from: {path}")
                # Convert dict to list of records
                records = []
                for key, value in data.items():
                    if isinstance(value, dict):
                        value['county_id'] = key
                        records.append(value)
                if records:
                    save_results_to_csv(records, output_file)
                    return True
    
    print("\nCould not automatically extract county data.")
    print("Please inspect raw-data/cnn_captured_data.json to find the data structure.")
    return False

def save_results_to_csv(data, output_file):
    """
    Save data to CSV.
    """
    if not data:
        return
    
    # Flatten nested structures
    rows = []
    for item in data:
        rows.append(flatten_dict(item))
    
    # Get all fieldnames
    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())
    
    fieldnames = sorted(all_keys)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Saved {len(rows)} records to {output_file}")

def flatten_dict(d, parent_key='', sep='_'):
    """
    Flatten nested dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if v and isinstance(v[0], dict):
                # Flatten list of dicts (like candidates)
                for i, item in enumerate(v):
                    items.extend(flatten_dict(item, f"{new_key}_{i}", sep=sep).items())
            else:
                # Simple list, just join
                items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_cnn_playwright.py <CNN_ELECTION_URL> [output.csv]")
        print("\nExample:")
        print("  python scrape_cnn_playwright.py 'https://www.cnn.com/election/2026/primaries/texas?admin1=48&election-data-id=2026-SD'")
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'cnn_election_results.csv'
    
    try:
        all_data = await extract_county_data(url)
        
        if not all_data:
            print("\nNo data was captured. This could mean:")
            print("1. The page structure has changed")
            print("2. The data is loaded from a different source")
            print("3. Additional authentication or interaction is needed")
            sys.exit(1)
        
        success = extract_to_csv(all_data, output_file)
        
        if not success:
            print("\nNext steps:")
            print("1. Open raw-data/cnn_captured_data.json")
            print("2. Find the actual county data structure")
            print("3. Modify this script's find_county_data() function to extract it")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
