# US Election Data Viewer

Interactive filterable tables for US election data, including County Presidential and US House election results.

## Live Demo

View the live app at: https://christine-iyer.github.io/twootwosix/

## Features

- **Three Interactive Tables:**
  - County Presidential Election Data (94,000+ records)
  - 2024 Precinct-Level Results (163,000+ records)
  - US House Election Data (33,000+ records)

- **Interactive Map Visualization:**
  - State-by-state precinct-level presidential results
  - Color-coded precincts by partisan lean (blue=Dem, red=Rep)
  - Hover for detailed vote counts and percentages
  - Select any state to load its precincts
  - Fast loading with state-specific data files (0.4-50 MB per state)

  
- **Functionality:**
  - Search and filter across all columns
  - Sort by any column
  - Export to CSV, Excel, or copy to clipboard
  - Pagination with customizable page sizes
  - Responsive design with horizontal scrolling

## Local Development

### Viewing the Map

The precinct map requires a local web server:

```bash
python3 -m http.server 8080
```

Then open http://localhost:8080/map.html

The map loads state-specific TopoJSON files from `data/precincts-by-state/` directory. These files were created by splitting the original 610MB TopoJSON file to enable fast browser loading.

### Static Version (GitHub Pages)

Simply open `index.html` in a web browser. The data files are loaded directly from the `data/` folder.

### Flask Version (Local Server)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python3 tables/script.py
   ```

3. Open http://127.0.0.1:5000 in your browser

## Data Sources

- `data/countypres.csv` - County-level presidential election results
- `data/precincts-with-results.csv` - 2024 precinct-level presidential results (from NY Times)
- `data/precincts-by-state/` - State-specific TopoJSON boundary files (generated from original 610MB file)
- `data/house.tab` - US House election results

### Preprocessing Large Files

The original `precincts-with-results.topojson` (610MB) was split into 50 state-specific files using:

```bash
cd data
python3 split_by_state.py
```

This creates individual state files ranging from 0.4 MB (Rhode Island) to 50 MB (California), enabling fast loading in browsers.

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript, jQuery
- **Tables:** DataTables library
- **Mapping:** Leaflet.js with TopoJSON
- **CSV Parsing:** PapaParse (static version)
- **Backend:** Flask + Pandas (local version only)
- **Data Processing:** Python for TopoJSON splitting
