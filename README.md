# US Election Data Viewer

Interactive filterable tables for US election data, including County Presidential and US House election results.

## Live Demo

View the live app at: https://christine-iyer.github.io/twootwosix/

## Features

- **Two Interactive Tables:**
  - County Presidential Election Data (94,000+ records)
  - US House Election Data (33,000+ records)
  
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
- `data/house.tab` - US House election results

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript, jQuery
- **Tables:** DataTables library
- **CSV Parsing:** PapaParse (static version)
- **Backend:** Flask + Pandas (local version only)
