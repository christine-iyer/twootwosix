#!/usr/bin/env python3
"""
Scraper for 2024 Texas primary election data from 270toWin.
Uses the Decision Desk HQ (DDHQ) API that 270toWin embeds.
"""

import requests
import json
import csv
import sys
from collections import defaultdict

# Known race IDs from the 270toWin page
TEXAS_2024_SENATE_RACES = {
    'Democratic': 25671,
    'Republican': 25672
}

def fetch_race_data(race_id):
    """
    Fetch race data from DDHQ API.
    
    Args:
        race_id: The race ID from DDHQ
    
    Returns:
        dict: Race data including candidates, votes, and county results
    """
    url = f"https://embed-api.ddhq.io/v1/races/{race_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"Fetching race {race_id}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching race {race_id}: {response.status_code}")
        return None
    
    return response.json()

def extract_county_results(race_data):
    """
    Extract county-level results from race data.
    
    Returns:
        list: List of dicts with county results
    """
    results = []
    
    # Get candidate mapping
    candidates = {c['cand_id']: f"{c['first_name']} {c['last_name']}" 
                  for c in race_data.get('candidates', [])}
    
    # Get statewide topline
    topline = race_data.get('topline_results', {})
    total_votes = topline.get('total_votes', 0)
    
    print(f"\nRace: {race_data['year']} {race_data['state']} {race_data['party']} {race_data['office']} {race_data['name']}")
    print(f"Total votes: {total_votes:,}")
    print(f"\nStatewide results:")
    
    statewide_results = {}
    for cand_id, votes in topline.get('votes', {}).items():
        cand_name = candidates.get(int(cand_id), f"Candidate_{cand_id}")
        pct = (votes / total_votes * 100) if total_votes > 0 else 0
        print(f"  {cand_name}: {votes:,} ({pct:.2f}%)")
        statewide_results[cand_name] = {'votes': votes, 'pct': pct}
    
    # Extract county-level data (VCUs = Voting Count Units, which are counties in this case)
    print(f"\nExtracting county data...")
    for vcu in race_data.get('vcus', []):
        county_name = vcu['vcu']
        county_fips = vcu['fips']
        county_total = sum(vcu.get('votes', {}).values())
        
        county_results = {
            'county': county_name,
            'fips': county_fips,
            'total_votes': county_total,
            'precincts_reporting': vcu.get('precincts', {}).get('reporting', 0),
            'precincts_total': vcu.get('precincts', {}).get('total', 0),
        }
        
        # Add candidate votes
        for cand_id, votes in vcu.get('votes', {}).items():
            cand_name = candidates.get(int(cand_id), f"Candidate_{cand_id}")
            pct = (votes / county_total * 100) if county_total > 0 else 0
            county_results[f'{cand_name}_votes'] = votes
            county_results[f'{cand_name}_pct'] = round(pct, 2)
        
        results.append(county_results)
    
    print(f"Extracted {len(results)} counties")
    
    return results, candidates, statewide_results

def save_to_csv(results, candidates, party, filename):
    """
    Save results to CSV file in format similar to 2026 data.
    """
    if not results:
        print("No results to save")
        return
    
    # Determine columns
    candidate_names = sorted(candidates.values())
    
    fieldnames = ['county', 'fips', 'total_votes', 'precincts_reporting', 'precincts_total']
    
    # Add columns for each candidate (votes and percentage)
    for cand_name in candidate_names:
        fieldnames.append(f'{cand_name}_votes')
        fieldnames.append(f'{cand_name}_pct')
    
    print(f"\nSaving to {filename}...")
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Saved {len(results)} rows to {filename}")

def main():
    for party, race_id in TEXAS_2024_SENATE_RACES.items():
        print(f"\n{'='*70}")
        print(f"Processing {party} race (ID: {race_id})")
        print(f"{'='*70}")
        
        # Fetch race data
        race_data = fetch_race_data(race_id)
        if not race_data:
            continue
        
        # Extract results
        results, candidates, statewide = extract_county_results(race_data)
        
        # Save to CSV
        party_lower = party.lower()
        filename = f"election-results/senate/texas_{party_lower[:3]}_senate_2024.csv"
        save_to_csv(results, candidates, party, filename)
        
        # Also save raw JSON for reference
        json_filename = f"raw-data/texas_{party_lower[:3]}_senate_2024_raw.json"
        with open(json_filename, 'w') as f:
            json.dump(race_data, f, indent=2)
        print(f"Saved raw data to {json_filename}")

if __name__ == "__main__":
    main()
