#!/usr/bin/env python3
"""
Simple Congressional District Aggregation

This script downloads 2024 congressional district boundaries and provides
a framework to aggregate precinct data by district. Since precinct geometries
are complex, we'll use a state-by-state TopoJSON approach.
"""

import os
import json
import requests
import zipfile
from io import BytesIO
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, Point

def download_congressional_districts():
    """Download 2024 congressional district shapefiles."""
    # Try 2024 first, fall back to 2023 (118th Congress)
    urls = [
        ("https://www2.census.gov/geo/tiger/TIGER2024/CD/tl_2024_us_cd119.zip", "2024", "cd119"),
        ("https://www2.census.gov/geo/tiger/TIGER2023/CD/tl_2023_us_cd118.zip", "2023", "cd118"),
    ]
    
    for url, year, cd_name in urls:
        output_dir = f"congressional_districts_{year}"
        shapefile_name = f"tl_{year}_us_{cd_name}.shp"
        
        if os.path.exists(output_dir):
            print(f"✓ Using existing directory: {output_dir}")
            return f"{output_dir}/{shapefile_name}"
        
        print(f"Trying {year} Congressional District shapefiles...")
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            print("Extracting...")
            with zipfile.ZipFile(BytesIO(response.content)) as z:
                z.extractall(output_dir)
            
            print(f"✓ Downloaded to: {output_dir}/")
            return f"{output_dir}/{shapefile_name}"
        except requests.exceptions.HTTPError:
            print(f"  {year} not available, trying next...")
            continue
    
    raise Exception("Could not download congressional district shapefiles")

def load_state_precincts(state_code, precincts_dir='precincts-by-state'):
    """Load precinct geometries for a specific state from TopoJSON."""
    topojson_path = f"{precincts_dir}/{state_code}.topojson"
    
    if not os.path.exists(topojson_path):
        print(f"  ⚠ Warning: {topojson_path} not found")
        return None
    
    print(f"  Loading {state_code}...")
    
    with open(topojson_path, 'r') as f:
        topology = json.load(f)
    
    # Convert TopoJSON to GeoJSON using topojson library
    object_name = list(topology['objects'].keys())[0]
    
    # Extract features manually
    geometries = topology['objects'][object_name]['geometries']
    features = []
    
    for geom in geometries:
        props = geom.get('properties', {})
        if props.get('votes_total'):
            features.append({
                'type': 'Feature',
                'properties': props,
                'geometry': geom.get('geometry')  # Will need proper conversion
            })
    
    # For now, create a simplified GeoDataFrame
    # In practice, use ogr2ogr to convert TopoJSON -> GeoJSON first
    print(f"    Found {len(features)} precincts with data")
    
    return features

def aggregate_precincts_simple(csv_path='precincts-with-results.csv'):
    """
    Simple aggregation using CSV data.
    Groups by state and provides district-level summaries.
    """
    print("\n" + "="*70)
    print("SIMPLE APPROACH: Aggregate precinct data by state")
    print("="*70)
    
    print("\nLoading precinct CSV...")
    df = pd.read_csv(csv_path)
    
    # Clean data
    df = df[df['votes_total'].notna()].copy()
    df['votes_dem'] = pd.to_numeric(df['votes_dem'], errors='coerce').fillna(0)
    df['votes_rep'] = pd.to_numeric(df['votes_rep'], errors='coerce').fillna(0)
    df['votes_total'] = pd.to_numeric(df['votes_total'], errors='coerce').fillna(0)
    
    print(f"✓ Loaded {len(df)} precincts with vote data")
    
    # Aggregate by state
    state_results = df.groupby('state').agg({
        'votes_dem': 'sum',
        'votes_rep': 'sum',
        'votes_total': 'sum',
        'GEOID': 'count'
    }).reset_index()
    
    state_results.rename(columns={'GEOID': 'precinct_count'}, inplace=True)
    
    # Calculate percentages
    state_results['dem_pct'] = (
        state_results['votes_dem'] / state_results['votes_total'] * 100
    )
    state_results['rep_pct'] = (
        state_results['votes_rep'] / state_results['votes_total'] * 100
    )
    state_results['dem_lead'] = state_results['dem_pct'] - state_results['rep_pct']
    
    # Determine winner
    state_results['winner'] = state_results.apply(
        lambda row: 'DEM' if row['votes_dem'] > row['votes_rep'] else 'REP',
        axis=1
    )
    
    # Sort by total votes
    state_results = state_results.sort_values('votes_total', ascending=False)
    
    # Save results
    output_path = 'precinct_results_by_state.csv'
    state_results.to_csv(output_path, index=False)
    print(f"\n✓ Saved state-level results to: {output_path}")
    
    # Display summary
    print("\n" + "="*70)
    print("STATE-LEVEL SUMMARY (Top 10 by total votes)")
    print("="*70)
    print(state_results[['state', 'precinct_count', 'votes_dem', 'votes_rep', 
                         'votes_total', 'winner', 'dem_lead']].head(10).to_string(index=False))
    
    return state_results

def main():
    print("="*70)
    print("Congressional District Data Merger")
    print("="*70)
    
    # Download congressional districts
    shapefile_path = download_congressional_districts()
    
    # Load congressional districts
    print("\nLoading congressional districts...")
    districts = gpd.read_file(shapefile_path)
    print(f"✓ Loaded {len(districts)} congressional districts")
    print(f"  Columns: {', '.join(districts.columns)}")
    
    # Show sample
    print("\nSample districts:")
    print(districts[['STATEFP', 'CD119FP', 'GEOID', 'NAMELSAD']].head(10))
    
    # Save as GeoJSON for easier use
    geojson_path = 'congressional_districts_2024.geojson'
    districts.to_file(geojson_path, driver='GeoJSON')
    print(f"\n✓ Saved as GeoJSON: {geojson_path}")
    
    # Aggregate precinct data
    state_results = aggregate_precincts_simple()
    
    print("\n" + "="*70)
    print("NEXT STEPS FOR DISTRICT-LEVEL ANALYSIS:")
    print("="*70)
    print("""
Option 1: Use QGIS (GUI approach)
  1. Install QGIS (free, open-source)
  2. Load congressional_districts_2024.geojson
  3. Load precinct TopoJSON files (convert with ogr2ogr first)
  4. Use "Join attributes by location" to match precincts to districts
  5. Export joined data as CSV

Option 2: Use ogr2ogr (command-line approach)
  1. Convert TopoJSON to GeoJSON:
     ogr2ogr -f GeoJSON precincts.geojson data/precincts-with-results.topojson
  2. Spatial join in Python/GeoPandas
  3. Aggregate by district

Option 3: Manual mapping (if you have precinct-to-district crosswalk)
  1. Get a crosswalk file from Census or state election boards
  2. Join CSV data using GEOID
  3. Aggregate by district code

Would you like me to implement Option 2 (requires converting TopoJSON first)?
    """)

if __name__ == '__main__':
    main()
