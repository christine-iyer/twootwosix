#!/usr/bin/env python3
"""
Simplify TopoJSON by reducing coordinate precision and optionally filtering states.
This can reduce file size by 50-80% while maintaining visual quality.
"""

import json
import sys

def round_coordinates(coords, precision=2):
    """Round coordinates to reduce precision (fewer decimal places = smaller file)"""
    if isinstance(coords, list):
        if len(coords) > 0 and isinstance(coords[0], (int, float)):
            # This is a coordinate pair [x, y]
            return [round(c, precision) for c in coords]
        else:
            # This is a nested list
            return [round_coordinates(c, precision) for c in coords]
    return coords

def simplify_topojson(input_file, output_file, precision=2, states=None):
    """
    Simplify TopoJSON by:
    1. Reducing coordinate precision
    2. Optionally filtering to specific states
    
    Args:
        input_file: Path to input TopoJSON
        output_file: Path to output TopoJSON
        precision: Number of decimal places for coordinates (default 2)
        states: List of state names to include (default None = all states)
    """
    print(f"Loading {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    print(f"Original file loaded. Processing...")
    
    # Round transform scale and translate
    if 'transform' in data:
        data['transform']['scale'] = [round(s, precision + 2) for s in data['transform']['scale']]
        data['transform']['translate'] = [round(t, precision + 2) for t in data['transform']['translate']]
    
    # Round arc coordinates
    if 'arcs' in data:
        original_arcs = len(data['arcs'])
        print(f"Rounding {original_arcs} arcs to {precision} decimal places...")
        data['arcs'] = [round_coordinates(arc, precision) for arc in data['arcs']]
    
    # Filter geometries by state if requested
    if states:
        print(f"Filtering to states: {', '.join(states)}")
        for obj_name, obj_data in data['objects'].items():
            if 'geometries' in obj_data:
                original_count = len(obj_data['geometries'])
                obj_data['geometries'] = [
                    geom for geom in obj_data['geometries']
                    if geom.get('properties', {}).get('state') in states
                ]
                filtered_count = len(obj_data['geometries'])
                print(f"Filtered {obj_name}: {original_count} -> {filtered_count} geometries")
    
    print(f"Writing to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(data, f, separators=(',', ':'))  # Compact JSON
    
    print("Done!")

if __name__ == '__main__':
    import os
    
    input_file = 'precincts-with-results.topojson'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        print("Run this script from the data/ directory")
        sys.exit(1)
    
    # Create simplified version with reduced precision
    print("\n=== Creating simplified version (precision=1) ===")
    simplify_topojson(
        input_file,
        'precincts-with-results-simplified.topojson',
        precision=1
    )
    
    # Show file sizes
    original_size = os.path.getsize(input_file) / (1024 * 1024)
    simplified_size = os.path.getsize('precincts-with-results-simplified.topojson') / (1024 * 1024)
    
    print(f"\nFile sizes:")
    print(f"  Original:   {original_size:.1f} MB")
    print(f"  Simplified: {simplified_size:.1f} MB ({simplified_size/original_size*100:.1f}%)")
    print(f"  Saved:      {original_size - simplified_size:.1f} MB")
