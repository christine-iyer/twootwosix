#!/usr/bin/env python3
"""
Merge Members of Congress (MOC) data with congressional district results.
Adds current representative name and reelection year to each district.
"""

import pandas as pd
import numpy as np

# State abbreviation to FIPS code mapping
STATE_TO_FIPS = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
    'CO': '08', 'CT': '09', 'DE': '10', 'FL': '12', 'GA': '13',
    'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18', 'IA': '19',
    'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23', 'MD': '24',
    'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28', 'MO': '29',
    'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33', 'NJ': '34',
    'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38', 'OH': '39',
    'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44', 'SC': '45',
    'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49', 'VT': '50',
    'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55', 'WY': '56',
    'AS': '60', 'GU': '66', 'MP': '69', 'PR': '72', 'VI': '78'
}

def create_district_geoid(row):
    """Create district GEOID from state abbreviation and district number."""
    state_ab = row['Ab']
    district = row['District']
    
    # Handle territories or missing data
    if pd.isna(state_ab) or state_ab not in STATE_TO_FIPS:
        return None
    
    fips = STATE_TO_FIPS[state_ab]
    
    # Handle at-large districts
    if pd.isna(district) or str(district).strip() in ['', 'At Large', ' At Large']:
        return f"{fips}00"
    
    # Handle numeric districts
    try:
        district_num = int(str(district).strip())
        return f"{fips}{district_num:02d}"
    except ValueError:
        print(f"Warning: Could not parse district '{district}' for {row['Name']} ({state_ab})")
        return None

def main():
    print("=" * 70)
    print("Merging MOC Data with Congressional District Results")
    print("=" * 70)
    
    # Load MOC data
    print("\nLoading MOC.csv...")
    moc = pd.read_csv('MOC.csv')
    print(f"  Total records: {len(moc)}")
    
    # Filter to House members only (Chamber = 'Congress')
    house = moc[moc['Chamber'] == 'Congress'].copy()
    print(f"  House members: {len(house)}")
    
    # Create district GEOID
    print("\nCreating district GEOIDs...")
    house['district_geoid'] = house.apply(create_district_geoid, axis=1)
    
    # Remove rows with no GEOID
    house_with_geoid = house[house['district_geoid'].notna()].copy()
    print(f"  Mapped to GEOIDs: {len(house_with_geoid)}")
    
    # Check for duplicates
    duplicates = house_with_geoid[house_with_geoid.duplicated('district_geoid', keep=False)]
    if len(duplicates) > 0:
        print(f"\n⚠ Warning: Found {len(duplicates)} duplicate district assignments:")
        print(duplicates[['Name', 'State', 'District', 'district_geoid']])
    
    # Load existing congressional district results
    print("\nLoading congressional_district_results.csv...")
    results = pd.read_csv('congressional_district_results.csv')
    print(f"  Districts: {len(results)}")
    
    # Ensure district_geoid is string in both dataframes
    results['district_geoid'] = results['district_geoid'].astype(str)
    house_with_geoid['district_geoid'] = house_with_geoid['district_geoid'].astype(str)
    
    # Merge MOC data with results
    print("\nMerging data...")
    merged = results.merge(
        house_with_geoid[['district_geoid', 'Name', 'Reelection', 'ServedSince']],
        on='district_geoid',
        how='left'
    )
    
    # Rename columns for clarity
    merged.rename(columns={
        'Name': 'representative',
        'Reelection': 'reelection_year',
        'ServedSince': 'served_since'
    }, inplace=True)
    
    # Check matching statistics
    matched = merged['representative'].notna().sum()
    print(f"  ✓ Matched {matched}/{len(results)} districts to representatives")
    
    # Show unmatched districts
    unmatched = merged[merged['representative'].isna()]
    if len(unmatched) > 0:
        print(f"\n⚠ Unmatched districts ({len(unmatched)}):")
        print(unmatched[['district_geoid', 'district_name', 'state']].head(10))
    
    # Save merged data
    output_file = 'congressional_district_results.csv'
    merged.to_csv(output_file, index=False)
    print(f"\n✓ Saved to: {output_file}")
    
    # Show sample
    print("\n" + "=" * 70)
    print("SAMPLE MERGED DATA")
    print("=" * 70)
    sample = merged[merged['representative'].notna()].head(10)
    print(sample[['district_geoid', 'state', 'representative', 'winner', 'reelection_year']].to_string(index=False))
    
    print("\n" + "=" * 70)
    print("✓ Merge complete!")
    print("=" * 70)

if __name__ == '__main__':
    main()
