#!/usr/bin/env python3
"""
Script to scrape 270toWin 2024 Texas primary election data.
Uses Playwright to handle JavaScript rendering and extract election results.
"""

import json
import csv
import sys
import re
import asyncio
from playwright.async_api import async_playwright

async def scrape_270towin_data(url, output_file):
    """
    Scrape election data from 270toWin using Playwright.
    """
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Intercept network requests to find API calls
        api_data = []
        
        async def handle_response(response):
            # Look for JSON responses that might contain election data
            if response.status == 200:
                url = response.url
                content_type = response.headers.get('content-type', '')
                
                # Check for JSON API calls or data files
                if 'json' in content_type or url.endswith('.json'):
                    try:
                        data = await response.json()
                        api_data.append({'url': url, 'data': data})
                        print(f"Captured API call: {url}")
                    except Exception as e:
                        print(f"Failed to parse JSON from {url}: {e}")
        
        page.on('response', handle_response)
        
        print(f"Loading page: {url}")
        try:
            await page.goto(url, wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f"Page load issue: {e}")
        
        # Wait for content to load
        print("Waiting for content to load...")
        await page.wait_for_timeout(5000)
        
        # Extract data from the page
        print("Extracting data from page...")
        
        # Method 1: Look for embedded JSON data in script tags
        scripts = await page.query_selector_all('script')
        embedded_data = []
        
        for script in scripts:
            try:
                script_content = await script.inner_text()
                # Look for common patterns of embedded data
                if 'results' in script_content.lower() or 'candidates' in script_content.lower():
                    # Try to extract JSON objects
                    json_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', script_content)
                    for match in json_matches[:10]:  # Limit to first 10 to avoid noise
                        try:
                            data = json.loads(match)
                            if isinstance(data, dict) and len(str(data)) > 100:
                                embedded_data.append(data)
                        except:
                            pass
            except:
                pass
        
        # Method 2: Extract visible race data from the page
        print("Extracting visible race data...")
        
        # Look for race containers
        races = []
        race_elements = await page.query_selector_all('.primary-race')
        
        for race_element in race_elements:
            try:
                race_html = await race_element.inner_html()
                race_text = await race_element.inner_text()
                
                # Extract race ID and party from class names
                class_attr = await race_element.get_attribute('class')
                id_attr = await race_element.get_attribute('id')
                
                race_info = {
                    'id': id_attr,
                    'classes': class_attr,
                    'html': race_html[:500],  # Limit HTML length
                    'text': race_text[:500]
                }
                races.append(race_info)
                print(f"Found race: {id_attr}")
            except Exception as e:
                print(f"Error extracting race: {e}")
        
        # Method 3: Try to access window variables
        print("Checking for window variables...")
        try:
            window_data = await page.evaluate('''() => {
                const data = {};
                
                // Common variable names that might contain election data
                const varNames = ['raceData', 'electionResults', 'resultsData', 'primaryResults'];
                
                for (const varName of varNames) {
                    if (typeof window[varName] !== 'undefined') {
                        data[varName] = window[varName];
                    }
                }
                
                // Also check for data attributes
                const elements = document.querySelectorAll('[data-race], [data-results], [data-candidates]');
                data.dataElements = Array.from(elements).map(el => ({
                    id: el.id,
                    dataset: Object.assign({}, el.dataset)
                }));
                
                return data;
            }''')
            
            if window_data:
                print("Found window data:", list(window_data.keys()))
        except Exception as e:
            print(f"Error accessing window variables: {e}")
            window_data = {}
        
        await browser.close()
        
        # Save all collected data
        output_data = {
            'url': url,
            'api_calls': api_data,
            'embedded_data': embedded_data[:5],  # Limit to first 5
            'races': races,
            'window_data': window_data
        }
        
        print(f"\nSaving data to {output_file}")
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Data saved! Found:")
        print(f"  - {len(api_data)} API calls")
        print(f"  - {len(embedded_data)} embedded data objects")
        print(f"  - {len(races)} race elements")
        print(f"  - Window data: {list(window_data.keys())}")
        
        return output_data

async def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # Default to Texas 2024 primary
        url = "https://www.270towin.com/2024-election-results-live/state/texas/primary"
    
    output_file = "270towin_2024_texas_primary_raw.json"
    
    print(f"Scraping: {url}")
    print(f"Output: {output_file}\n")
    
    data = await scrape_270towin_data(url, output_file)
    
    # Try to extract specific candidate data
    print("\n" + "="*60)
    print("Analyzing data for senate races...")
    print("="*60)
    
    # Look for Cruz, Allred, etc. in the collected data
    all_text = json.dumps(data).lower()
    candidates = ['cruz', 'allred', 'gutierrez']
    
    for candidate in candidates:
        if candidate in all_text:
            print(f"✓ Found '{candidate}' in data")
        else:
            print(f"✗ '{candidate}' not found in data")

if __name__ == "__main__":
    asyncio.run(main())
