#!/usr/bin/env python3
"""
Merge precinct election data with congressional district boundaries.

This script:
1. Downloads 2024 congressional district shapefiles from Census Bureau
2. Loads precinct geometries from TopoJSON
3. Performs spatial join to assign each precinct to a district
4. Aggregates vote totals by congressional district
5. Exports results as GeoJSON and CSV

Requirements: pip install geopandas requests shapely
"""

import os
import json
import requests
import zipfile
from io import BytesIO
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape

def download_congressional_districts():
    """
    Download 2024 (119th Congress) district boundaries from Census Bureau.
    """
    print("Downloading 2024 Congressional District shapefiles...")
    
    # Census Bureau: 119th Congress (2025-2026) district boundaries
    url = "https://www2.census.gov/geo/tiger/TIGER2024/CD/tl_2024_us_cd119.zip"
    
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    print("Extracting shapefiles...")
    with zipfile.ZipFile(BytesIO(response.content)) as z:
        z.extractall("congressional_districts_2024")
    
    print("✓ Downloaded to: congressional_districts_2024/")
    return "congressional_districts_2024/tl_2024_us_cd119.shp"

def load_precinct_geometries(topojson_path):
    """
    Load precinct geometries and vote data from TopoJSON.
    """
    print(f"\nLoading {topojson_path}...")
    print("This may take a few minutes for the 610MB file...")
    
    with open(topojson_path, 'r') as f:
        topology = json.load(f)
    
    print("Converting TopoJSON to GeoDataFrame...")
    
    # Get the object name
    object_name = list(topology['objects'].keys())[0]
    geometries_data = topology['objects'][object_name]['geometries']
    arcs = topology['arcs']
    transform = topology.get('transform', {})
    
    # Simple TopoJSON to GeoJSON conversion
    # For production use, consider using topojson library or GDAL
    features = []
    
    for i, geom_data in enumerate(geometries_data):
        if i % 10000 == 0:
            print(f"  Processing precinct {i}/{len(geometries_data)}...")
        
        props = geom_data.get('properties', {})
        
        # Skip if no vote data
        if not props.get('votes_total'):
            continue
        
        # For now, create point geometries at precinct centroids
        # Full polygon conversion would require implementing TopoJSON arc stitching
        # Consider using ogr2ogr for full conversion: 
        # ogr2ogr -f GeoJSON output.geojson input.topojson
        
        features.append({
            'type': 'Feature',
            'properties': props,
            'geometry': None  # Placeholder - will use centroid or point
        })
    
    print(f"Loaded {len(features)} precincts with vote data")
    
    # Create GeoDataFrame from features
    # Note: Without full TopoJSON decoding, we'll use a simpler approach
    return features

def spatial_join_precincts_to_districts(precinct_gdf, district_gdf):
    """
    Perform spatial join to assign precincts to congressional districts.
    """
    print("\nPerforming spatial join...")
    
    # Ensure same CRS
    if precinct_gdf.crs != district_gdf.crs:
        print(f"Reprojecting precincts from {precinct_gdf.crs} to {district_gdf.crs}")
        precinct_gdf = precinct_gdf.to_crs(district_gdf.crs)
    
    # Spatial join
    joined = gpd.sjoin(precinct_gdf, district_gdf[['GEOID', 'NAMELSAD', 'geometry']], 
                       how='left', predicate='within')
    
    print(f"✓ Matched {len(joined[joined['GEOID'].notna()])} precincts to districts")
    print(f"  Unmatched: {len(joined[joined['GEOID'].isna()])} precincts")
    
    return joined

def aggregate_by_district(joined_gdf):
    """
    Aggregate precinct vote totals by congressional district.
    """
    print("\nAggregating votes by congressional district...")
    
    # Group by district and sum votes
    district_results = joined_gdf.groupby('GEOID').agg({
        'NAMELSAD': 'first',
        'votes_dem': 'sum',
        'votes_rep': 'sum',
        'votes_total': 'sum',
        'state': 'first'
    }).reset_index()
    
    # Calculate percentages
    district_results['dem_pct'] = (
        district_results['votes_dem'] / district_results['votes_total'] * 100
    )
    district_results['rep_pct'] = (
        district_results['votes_rep'] / district_results['votes_total'] * 100
    )
    district_results['dem_lead_pct'] = district_results['dem_pct'] - district_results['rep_pct']
    
    # Determine winner
    district_results['winner'] = district_results.apply(
        lambda row: 'DEM' if row['votes_dem'] > row['votes_rep'] else 'REP',
        axis=1
    )
    
    print(f"✓ Created results for {len(district_results)} congressional districts")
    
    return district_results

def main():
    """
    Main workflow: Download districts, load precincts, join, aggregate.
    """
    print("=" * 70)
    print("Congressional District Election Results Merger")
    print("=" * 70)
    
    # Check if geopandas is installed
    try:
        import geopandas as gpd
    except ImportError:
        print("\n❌ GeoPandas not installed!")
        print("\nInstall with:")
        print("  pip install geopandas")
        print("\nOr using conda:")
        print("  conda install geopandas")
        return
    
    # Step 1: Download congressional district boundaries
    if not os.path.exists("congressional_districts_2024"):
        district_shapefile = download_congressional_districts()
    else:
        district_shapefile = "congressional_districts_2024/tl_2024_us_cd119.shp"
        print(f"Using existing shapefile: {district_shapefile}")
    
    # Load districts
    print("\nLoading congressional districts...")
    districts = gpd.read_file(district_shapefile)
    print(f"✓ Loaded {len(districts)} congressional districts")
    print(f"  CRS: {districts.crs}")
    
    # Step 2: Alternative approach - use CSV with state/county/precinct mapping
    print("\n" + "=" * 70)
    print("ALTERNATIVE APPROACH: Aggregate by State First")
    print("=" * 70)
    print("\nSince TopoJSON conversion is complex, let's use a simpler approach:")
    print("1. Load precinct CSV data")
    print("2. Use Census GEOCORR to map precincts to congressional districts")
    print("3. Aggregate votes by district")
    
    # Load precinct CSV
    print("\nLoading precinct CSV data...")
    df = pd.read_csv('precincts-with-results.csv')
    print(f"✓ Loaded {len(df)} precincts")
    
    # For now, export the data in a format ready for geocoding
    print("\nExporting precinct data for geocoding...")
    
    # Create output with GEOID for matching
    output = df[['GEOID', 'state', 'votes_dem', 'votes_rep', 'votes_total']].copy()
    output.to_csv('precincts_for_geocoding.csv', index=False)
    print("✓ Exported to: precincts_for_geocoding.csv")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("\n1. Use Census GEOCORR (https://mcdc.missouri.edu/applications/geocorr.html)")
    print("   to map precinct GEOIDs to congressional districts")
    print("\n2. Or use ogr2ogr to convert TopoJSON to GeoJSON:")
    print("   ogr2ogr -f GeoJSON precincts.geojson precincts-with-results.topojson")
    print("\n3. Then run this script again with the converted GeoJSON")

if __name__ == '__main__':
    main()
