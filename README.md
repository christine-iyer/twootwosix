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
  - Color-coded precincts by partisan lean
  - Blue for Democratic-leaning precincts
  - Red for Republican-leaning precincts
  - Hover for detailed results
  
- **Functionality:**
  - Search and filter across all columns
  - Sort by any column
  - Export to CSV, Excel, or copy to clipboard
  - Pagination with customizable page sizes
  - Responsive design with horizontal scrolling

## Local Development

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
- `data/house.tab` - US House election results

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript, jQuery
- **Tables:** DataTables library
- **CSV Parsing:** PapaParse (static version)
- **Backend:** Flask + Pandas (local version only)
