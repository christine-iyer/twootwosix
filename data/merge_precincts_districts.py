#!/usr/bin/env python3
"""
Merge precinct election data with 2024 congressional districts.

This script:
1. Loads congressional district shapefiles (by state)
2. Loads precinct geometries from state-specific TopoJSON files
3. Performs spatial join to assign each precinct to its congressional district
4. Aggregates vote totals by congressional district
5. Exports results as GeoJSON and CSV
"""

import os
import json
import glob
import zipfile
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from pathlib import Path

# FIPS code to state abbreviation mapping
FIPS_TO_STATE = {
    '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA',
    '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL',
    '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN',
    '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME',
    '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS',
    '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH',
    '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
    '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI',
    '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT',
    '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI',
    '56': 'WY', '60': 'AS', '66': 'GU', '69': 'MP', '72': 'PR', '78': 'VI'
}

def extract_all_district_shapefiles(districts_dir='cdistricts-by-state'):
    """Extract all congressional district zip files."""
    print("Extracting congressional district shapefiles...")
    
    zip_files = glob.glob(f"{districts_dir}/*.zip")
    print(f"Found {len(zip_files)} state district files")
    
    for zip_path in zip_files:
        # Check if already extracted
        shp_name = Path(zip_path).stem + '.shp'
        if os.path.exists(f"{districts_dir}/{shp_name}"):
            continue
        
        print(f"  Extracting {Path(zip_path).name}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(districts_dir)
    
    print("✓ All shapefiles extracted")

def load_all_congressional_districts(districts_dir='cdistricts-by-state'):
    """Load and combine all state congressional district shapefiles."""
    print("\nLoading congressional districts...")
    
    shp_files = glob.glob(f"{districts_dir}/*.shp")
    print(f"Found {len(shp_files)} shapefiles")
    
    all_districts = []
    for shp_path in shp_files:
        gdf = gpd.read_file(shp_path)
        all_districts.append(gdf)
    
    # Combine all districts
    combined = pd.concat(all_districts, ignore_index=True)
    
    print(f"✓ Loaded {len(combined)} congressional districts")
    print(f"  CRS: {combined.crs}")
    print(f"  States: {combined['STATEFP'].nunique()}")
    
    return combined

def convert_topojson_to_geodataframe(topojson_path):
    """
    Convert TopoJSON file to GeoDataFrame.
    Uses ogr2ogr for robust conversion.
    """
    geojson_path = topojson_path.replace('.topojson', '_temp.geojson')
    
    # Use ogr2ogr to convert
    import subprocess
    try:
        subprocess.run([
            'ogr2ogr', '-f', 'GeoJSON',
            geojson_path, topojson_path
        ], check=True, capture_output=True)
        
        gdf = gpd.read_file(geojson_path)
        
        # Clean up temp file
        os.remove(geojson_path)
        
        return gdf
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"    ⚠ ogr2ogr failed or not installed: {e}")
        return None

def manual_topojson_to_geodataframe(topojson_path):
    """
    Manually convert TopoJSON to GeoDataFrame (simplified approach).
    This creates point geometries from the first coordinate of each precinct.
    """
    print(f"    Loading {Path(topojson_path).name}...")
    
    with open(topojson_path, 'r') as f:
        topology = json.load(f)
    
    object_name = list(topology['objects'].keys())[0]
    geometries_data = topology['objects'][object_name]['geometries']
    transform = topology.get('transform', {})
    arcs = topology['arcs']
    
    features = []
    for geom_data in geometries_data:
        props = geom_data.get('properties', {})
        
        # Skip if no vote data
        if not props.get('votes_total'):
            continue
        
        # Try to get a point geometry from the first arc
        geom = geom_data.get('geometries', [geom_data])[0] if geom_data.get('type') == 'GeometryCollection' else geom_data
        
        if 'arcs' in geom and len(geom['arcs']) > 0:
            # Get first arc - handle nested lists
            arc_ref = geom['arcs'][0]
            
            # Unwrap nested lists to get the actual arc index
            while isinstance(arc_ref, list) and len(arc_ref) > 0:
                arc_ref = arc_ref[0]
            
            if isinstance(arc_ref, int):
                arc_idx = abs(arc_ref)
                
                if arc_idx < len(arcs):
                    # Get first coordinate from arc
                    coords = arcs[arc_idx][0]
                    
                    # Apply transform
                    scale = transform.get('scale', [1, 1])
                    translate = transform.get('translate', [0, 0])
                    lon = coords[0] * scale[0] + translate[0]
                    lat = coords[1] * scale[1] + translate[1]
                    
                    features.append({
                        'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                        'properties': props
                    })
    
    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame.from_features(features, crs='EPSG:4269')
    
    return gdf

def spatial_join_state(state_code, districts_gdf, precincts_dir='precincts-by-state'):
    """Spatially join precincts to districts for a single state."""
    topojson_path = f"{precincts_dir}/{state_code}.topojson"
    
    if not os.path.exists(topojson_path):
        print(f"  ⚠ Skipping {state_code}: TopoJSON not found")
        return None
    
    # Try ogr2ogr first, fall back to manual
    precinct_gdf = convert_topojson_to_geodataframe(topojson_path)
    
    if precinct_gdf is None:
        precinct_gdf = manual_topojson_to_geodataframe(topojson_path)
    
    if precinct_gdf is None or len(precinct_gdf) == 0:
        print(f"  ⚠ Skipping {state_code}: No precincts loaded")
        return None
    
    print(f"    Loaded {len(precinct_gdf)} precincts")
    
    # Filter districts to this state
    state_fp = {
        'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
        # Add more as needed...
    }.get(state_code)
    
    if state_fp:
        state_districts = districts_gdf[districts_gdf['STATEFP'] == state_fp].copy()
    else:
        # Try to match by state name in precinct data
        state_districts = districts_gdf.copy()
    
    # Ensure same CRS
    if precinct_gdf.crs != state_districts.crs:
        precinct_gdf = precinct_gdf.to_crs(state_districts.crs)
    
    # Spatial join
    print(f"    Performing spatial join...")
    joined = gpd.sjoin(precinct_gdf, state_districts[['GEOID', 'NAMELSAD', 'geometry']], 
                       how='left', predicate='within')
    
    print(f"    Columns after join: {list(joined.columns)}")
    
    # Find the district GEOID column (could be GEOID_right if there's a conflict)
    if 'GEOID_right' in joined.columns:
        district_geoid_col = 'GEOID_right'
    elif 'GEOID' in joined.columns and 'index_right' in joined.columns:
        # GEOID from districts, precinct had different or no GEOID
        district_geoid_col = 'GEOID'
    else:
        district_geoid_col = 'GEOID'
    
    matched = len(joined[joined[district_geoid_col].notna()])
    print(f"    ✓ Matched {matched}/{len(joined)} precincts to districts")
    
    # Rename for clarity
    if district_geoid_col != 'district_geoid':
        joined.rename(columns={district_geoid_col: 'district_geoid'}, inplace=True)
    if 'NAMELSAD' in joined.columns:
        joined.rename(columns={'NAMELSAD': 'district_name'}, inplace=True)
    elif 'NAMELSAD_right' in joined.columns:
        joined.rename(columns={'NAMELSAD_right': 'district_name'}, inplace=True)
    
    return joined

def aggregate_by_district(joined_gdf):
    """Aggregate precinct votes by congressional district."""
    print("\nAggregating votes by congressional district...")
    
    # Ensure numeric columns
    for col in ['votes_dem', 'votes_rep', 'votes_total']:
        joined_gdf[col] = pd.to_numeric(joined_gdf[col], errors='coerce').fillna(0)
    
    # Group by district (use district_geoid from the renamed column)
    district_results = joined_gdf.groupby('district_geoid').agg({
        'district_name': 'first',
        'votes_dem': 'sum',
        'votes_rep': 'sum',
        'votes_total': 'sum'
    }).reset_index()
    
    # Derive state from district GEOID (first 2 digits = FIPS code)
    district_results['state'] = district_results['district_geoid'].str[:2].map(FIPS_TO_STATE)
    
    # Calculate percentages
    district_results['dem_pct'] = (
        district_results['votes_dem'] / district_results['votes_total'] * 100
    ).round(2)
    district_results['rep_pct'] = (
        district_results['votes_rep'] / district_results['votes_total'] * 100
    ).round(2)
    district_results['dem_lead_pct'] = (
        district_results['dem_pct'] - district_results['rep_pct']
    ).round(2)
    
    # Determine winner
    district_results['winner'] = district_results.apply(
        lambda row: 'DEM' if row['votes_dem'] > row['votes_rep'] else 'REP',
        axis=1
    )
    
    print(f"✓ Aggregated results for {len(district_results)} districts")
    
    return district_results

def main():
    print("=" * 70)
    print("Precinct to Congressional District Merger")
    print("=" * 70)
    
    # Get script directory to make paths relative
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}\n")
    
    # Step 1: Extract shapefiles
    extract_all_district_shapefiles()
    
    # Step 2: Load all congressional districts
    districts = load_all_congressional_districts()
    
    # Step 3: Check if ogr2ogr is available
    import subprocess
    try:
        subprocess.run(['ogr2ogr', '--version'], capture_output=True, check=True)
        print("\n✓ ogr2ogr available for TopoJSON conversion")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n⚠ ogr2ogr not found - will use simplified point-based approach")
        print("  Install GDAL for full polygon support:")
        print("    brew install gdal  (macOS)")
        print("    apt-get install gdal-bin  (Linux)")
    
    # Step 4: Process states one by one
    print("\n" + "=" * 70)
    print("Processing states...")
    print("=" * 70)
    
    all_joined = []
    
    # Get list of states that have BOTH precinct data AND district shapefiles
    state_files = glob.glob('precincts-by-state/*.topojson')
    precinct_states = set([Path(f).stem for f in state_files])
    
    district_files = glob.glob('cdistricts-by-state/tl_2024_*_cd119.shp')
    district_fips_codes = set([Path(f).stem.split('_')[2] for f in district_files])
    
    # Convert FIPS codes to state abbreviations
    district_states = set([FIPS_TO_STATE.get(fips) for fips in district_fips_codes if FIPS_TO_STATE.get(fips)])
    
    # Only process states with both datasets
    states_to_process = sorted(precinct_states.intersection(district_states))
    
    print(f"\nFound {len(precinct_states)} state precinct files")
    print(f"Found {len(district_states)} state district files")
    print(f"Processing {len(states_to_process)} states with both datasets: {', '.join(states_to_process)}")
    
    for i, state_code in enumerate(states_to_process, 1):
        print(f"\n[{i}/{len(states_to_process)}] Processing {state_code}...")
        joined = spatial_join_state(state_code, districts)
        if joined is not None:
            all_joined.append(joined)
    
    if not all_joined:
        print("\n❌ No data successfully joined")
        return
    
    # Combine all states
    print("\n" + "=" * 70)
    combined = pd.concat(all_joined, ignore_index=True)
    print(f"✓ Combined data from {len(all_joined)} states")
    print(f"  Total precincts: {len(combined)}")
    print(f"  Matched to districts: {len(combined[combined['district_geoid'].notna()])}")
    
    # Step 5: Aggregate by district
    district_results = aggregate_by_district(combined)
    
    # Step 6: Save results
    output_csv = 'congressional_district_results.csv'
    district_results.to_csv(output_csv, index=False)
    print(f"\n✓ Saved to: {output_csv}")
    
    # Display summary
    print("\n" + "=" * 70)
    print("CONGRESSIONAL DISTRICT RESULTS (Sample)")
    print("=" * 70)
    print(district_results.head(10).to_string(index=False))
    
    print("\n" + "=" * 70)
    print("WINNER SUMMARY")
    print("=" * 70)
    winner_counts = district_results['winner'].value_counts()
    print(winner_counts)

if __name__ == '__main__':
    main()
