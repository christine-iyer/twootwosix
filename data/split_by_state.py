#!/usr/bin/env python3
"""
Split TopoJSON by state into separate files.
This allows loading only one state at a time, dramatically reducing memory usage.
"""

import json
import sys
import os
from collections import defaultdict

def split_topojson_by_state(input_file, output_dir='precincts-by-state'):
    """
    Split a large TopoJSON file into separate files per state.
    Each state file will only contain the arcs needed for that state's precincts.
    """
    print(f"Loading {input_file}...")
    print("This may take a minute for a 610MB file...")
    
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except MemoryError:
        print("ERROR: Not enough memory to load the file.")
        print("Try running with: python3 -X memory_limit=4G split_by_state.py")
        sys.exit(1)
    
    print(f"File loaded successfully!")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the object name (should be 'tiles')
    object_name = list(data['objects'].keys())[0]
    geometries = data['objects'][object_name]['geometries']
    
    print(f"Total geometries: {len(geometries)}")
    
    # Group geometries by state
    states = defaultdict(list)
    for geom in geometries:
        state = geom.get('properties', {}).get('state')
        if state:
            states[state].append(geom)
    
    print(f"\nFound {len(states)} states")
    
    # For each state, create a new TopoJSON file
    for state_name, state_geometries in sorted(states.items()):
        print(f"Processing {state_name}: {len(state_geometries)} precincts...")
        
        # Collect all arc indices used by this state
        arc_indices = set()
        
        def collect_arcs(arcs_data):
            """Recursively collect all arc indices from arcs data"""
            if isinstance(arcs_data, int):
                arc_indices.add(abs(arcs_data))
            elif isinstance(arcs_data, list):
                for item in arcs_data:
                    collect_arcs(item)
        
        def process_geometry(geom):
            """Process a geometry to collect arcs"""
            if geom.get('type') == 'GeometryCollection':
                for g in geom.get('geometries', []):
                    process_geometry(g)
            elif 'arcs' in geom:
                collect_arcs(geom['arcs'])
        
        for geom in state_geometries:
            process_geometry(geom)
        
        # Create arc index mapping (old index -> new index)
        sorted_indices = sorted(arc_indices)
        arc_map = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted_indices)}
        
        # Remap arc references in geometries
        def remap_arcs_data(arcs_data):
            """Recursively remap arc indices"""
            if isinstance(arcs_data, int):
                abs_val = abs(arcs_data)
                new_idx = arc_map[abs_val]
                return new_idx if arcs_data >= 0 else -new_idx
            elif isinstance(arcs_data, list):
                return [remap_arcs_data(item) for item in arcs_data]
            return arcs_data
        
        def remap_geometry(geom):
            """Recursively remap arc indices in a geometry"""
            if geom.get('type') == 'GeometryCollection':
                for g in geom.get('geometries', []):
                    remap_geometry(g)
            elif 'arcs' in geom:
                geom['arcs'] = remap_arcs_data(geom['arcs'])
        
        # Deep copy geometries and remap
        import copy
        remapped_geometries = copy.deepcopy(state_geometries)
        for geom in remapped_geometries:
            remap_geometry(geom)
        
        # Create new TopoJSON with only this state's data
        try:
            state_arcs = [data['arcs'][i] for i in sorted_indices if i < len(data['arcs'])]
        except IndexError as e:
            print(f"  ⚠ Warning: Some arcs missing for {state_name}, skipping invalid indices")
            state_arcs = []
            for i in sorted_indices:
                if i < len(data['arcs']):
                    state_arcs.append(data['arcs'][i])
                else:
                    print(f"    Skipping arc index {i} (max: {len(data['arcs'])-1})")
        
        state_data = {
            'type': 'Topology',
            'transform': data['transform'],
            'objects': {
                object_name: {
                    'type': 'GeometryCollection',
                    'geometries': remapped_geometries
                }
            },
            'arcs': state_arcs
        }
        
        # Write to file
        output_file = os.path.join(output_dir, f'{state_name}.topojson')
        with open(output_file, 'w') as f:
            json.dump(state_data, f, separators=(',', ':'))
        
        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"  → {output_file} ({size_mb:.1f} MB, {len(sorted_indices)} arcs)")
    
    print(f"\n✓ Created {len(states)} state files in {output_dir}/")
    
    # Show total size
    total_size = sum(
        os.path.getsize(os.path.join(output_dir, f))
        for f in os.listdir(output_dir)
        if f.endswith('.topojson')
    ) / (1024 * 1024)
    
    print(f"Total size of all state files: {total_size:.1f} MB")

if __name__ == '__main__':
    input_file = 'precincts-with-results.topojson'
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found")
        print("Run this script from the data/ directory")
        sys.exit(1)
    
    split_topojson_by_state(input_file)
