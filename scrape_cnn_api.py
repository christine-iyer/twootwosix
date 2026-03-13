#!/usr/bin/env python3
"""
Direct CNN API scraper using discovered endpoints.
Based on the API pattern: https://politics.api.cnn.io/results/county-races/{ELECTION-ID}-{STATE}.json
"""

import requests
import json
import csv
import sys

def fetch_cnn_data(election_id, state_abbr):
    """
    Fetch election data from CNN's API.
    
    Args:
        election_id: Election identifier (e.g., '2026-SD' for 2026 Senate Democratic primary)
        state_abbr: Two-letter state code (e.g., 'TX', 'AR', 'NC')
    """
    # API endpoints discovered from network traffic
    county_url = f"https://politics.api.cnn.io/results/county-races/{election_id}-{state_abbr}.json"
    national_url = f"https://politics.api.cnn.io/results/national-races/{election_id}.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    print(f"Fetching county data: {county_url}")
    county_response = requests.get(county_url, headers=headers)
    
    if county_response.status_code != 200:
        print(f"Error fetching county data: {county_response.status_code}")
        return None, None
    
    county_data = county_response.json()
    
    print(f"Fetching national data: {national_url}")
    national_response = requests.get(national_url, headers=headers)
    national_data = None
    if national_response.status_code == 200:
        national_data = national_response.json()
    
    return county_data, national_data

def extract_county_results(data, state_abbr):
    """
    Extract county-level results from CNN API response.
    """
    results = []
    
    # Save raw data for inspection
    with open(f'raw-data/cnn_api_{state_abbr}_raw.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved raw API response to raw-data/cnn_api_{state_abbr}_raw.json")
    
    # CNN API returns an array of county objects at the top level
    if isinstance(data, list):
        print(f"Found {len(data)} counties")
        
        for county in data:
            if not isinstance(county, dict):
                continue
            
            # Extract county info
            county_name = county.get('countyName', 'Unknown')
            fips = county.get('countyFipsCode', '')
            state_name = county.get('stateName', '')
            race_type = county.get('raceType', '')
            contest_type = county.get('contestType', '')
            total_vote = county.get('totalVote', 0)
            pct_reporting = county.get('percentReporting', 0)
            timestamp = county.get('voteTimestamp', '')
            
            # Get candidates for this county
            candidates = county.get('candidates', [])
            
            # Create a record for each candidate
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                
                record = {
                    'state': state_name,
                    'county': county_name,
                    'fips': fips,
                    'race_type': race_type,
                    'contest_type': contest_type,
                    'candidate_id': candidate.get('candidateId', ''),
                    'candidate_name': candidate.get('fullName', ''),
                    'first_name': candidate.get('firstName', ''),
                    'last_name': candidate.get('lastName', ''),
                    'party': candidate.get('majorParty', ''),
                    'party_name': candidate.get('partyName', ''),
                    'votes': candidate.get('voteNum', 0),
                    'vote_pct': candidate.get('votePercentNum', 0),
                    'vote_pct_str': candidate.get('votePercentStr', ''),
                    'incumbent': candidate.get('isIncumbent', False),
                    'total_votes': total_vote,
                    'pct_reporting': pct_reporting,
                    'timestamp': timestamp,
                }
                
                results.append(record)
    
    elif isinstance(data, dict):
        # Fallback: might be a dict with race keys
        print("Data is a dictionary, trying alternate structure...")
        for race_key, race_data in data.items():
            if isinstance(race_data, list):
                # Recursive call
                results.extend(extract_county_results(race_data, state_abbr))
    
    return results

def save_to_csv(results, output_file):
    """
    Save results to CSV.
    """
    if not results:
        print("No results to save")
        return
    
    # Get all unique keys
    all_keys = set()
    for record in results:
        all_keys.update(record.keys())
    
    fieldnames = sorted(all_keys)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Saved {len(results)} records to {output_file}")

def main():
    if len(sys.argv) < 3:
        print("Usage: python scrape_cnn_api.py <ELECTION_ID> <STATE> [output.csv]")
        print("\nExamples:")
        print("  python scrape_cnn_api.py 2026-SD TX texas_primary_2026.csv")
        print("  python scrape_cnn_api.py 2026-SD AR arkansas_primary_2026.csv")
        print("  python scrape_cnn_api.py 2026-SD NC nc_primary_2026.csv")
        print("\nElection ID format:")
        print("  2026-SD = 2026 Senate Democratic primary")
        print("  2026-SR = 2026 Senate Republican primary")
        print("  2026-HD = 2026 House Democratic primary")
        print("  2026-HR = 2026 House Republican primary")
        sys.exit(1)
    
    election_id = sys.argv[1]
    state = sys.argv[2].upper()
    output_file = sys.argv[3] if len(sys.argv) > 3 else f'{state.lower()}_{election_id.lower()}_results.csv'
    
    print(f"Election ID: {election_id}")
    print(f"State: {state}")
    print(f"Output file: {output_file}\n")
    
    # Fetch data
    county_data, national_data = fetch_cnn_data(election_id, state)
    
    if not county_data:
        print("Failed to fetch data")
        sys.exit(1)
    
    # Extract results
    results = extract_county_results(county_data, state)
    
    if not results:
        print("\nNo results extracted. The data structure might be different than expected.")
        print(f"Please check raw-data/cnn_api_{state}_raw.json to see the actual structure.")
        sys.exit(1)
    
    # Save to CSV
    save_to_csv(results, output_file)
    
    print("\nDone!")

if __name__ == '__main__':
    main()
