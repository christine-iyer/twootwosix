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
- Mississippi 2024 primary results 
House [NPR](https://apps.npr.org/primary-election-results-2024/states/MS.html#date=3%2F12%2F2024&office=H)

    - U.S. House District 1 
Democratic Primary: *Cliff Johnson*, a University of Mississippi law school professor, is running against former Marshall County state *Rep. Kelvin Buck*.

Republican Primary: Incumbent *Trent Kelly* is running unopposed in the Republican primary 

- U.S. House District 2 
Democratic Primary: Incumbent *Bennie Thompson* is running against *Evan Turnage*, a former aide to Senate Minority Leader Chuck Schumer of New York and Senate Conference Vice Chair Elizabeth Warren of Massachusetts. Thompson is also attempting to stave off a challenge from *Pertis Williams III*, who has focused on agricultural issues. 

Thompson has represented the 2nd Congressional District, which covers Jackson and the Delta, since 1993. Thompson, a civil rights leader and former chair of the House Select Committee investigating the Jan. 6th Capitol attack, is a towering figure in state and national politics. 

Republican Primary: Adams County Supervisor *Kevin Wilson* is squaring off against *Ron Eller*, a physician’s assistant and military veteran who is running again for the GOP nomination after losing to Thompson by nearly 25 points in 2024. 

U.S. House District 3 
Democratic Primary: *Michael Chiaradio*, a former baseball player turned regenerative farmer from New Jersey, is running unopposed for the Democratic nomination. Chiaradio told Mississippi Today he believes a localized message built around economic frustration can unite both disaffected conservatives and a fractured Democratic Party.

Republican Primary: Incumbent *Michael Guest* is running unopposed for the Republican nomination. Guest has sailed to general election victories three times since he was first elected in 2018. In 2024, he survived a primary challenge from the right that went to a runoff but ran unopposed in the general election.

U.S. House District 4 
Democratic Primary: Three candidates are competing for the Democratic nomination. They are *Jeffrey Hulum III*, a state representative from Gulfport, *D. Ryan Grover*, a business consultant who was the Democratic nominee for lieutenant governor in 2023 and *Paul Blackman*, a Navy veteran.

Republican Primary: Incumbent Republican *Mike Ezell*, first elected in 2022, is running against *Sawyer Walters*, who works for the Department of Marine Resources and serves as a lieutenant in the Mississippi Army National Guard.
### Senate
| Name                         | Party | Votes   | Percent |
| ---------------------------- | ----- | ------- | ------- |
| Scott Colom                  | Dem   | 105,716 | 73.1%   |
| Albert Littell               | Dem   | 12,266  | 8.5%    |
| Priscilla Till               | Dem   | 26,642  | 18.4%   |
| Cindy Hyde-Smith (incumbent) | Rep   | 125,557 | 80.8%   |
| Sarah Adlakha                | Rep   | 29,806  | 19.2%   |

### House

| Name                | Party | District | Votes  | Percent |
| ------------------- | ----- | -------- | ------ | ------- |
| Cliff Johnson       | Dem   | 1        | 17,879 | 63.6%   |
| Buck                | Dem   | 1        | 10,234 | 36.4%   |
| Kelly               | Rep   | 1        | -      | -       |
| Bennie Thompson     | Dem   | 2        | 61,013 | 86.2%   |
| Evan Turnage        | Dem   | 2        | 8,914  | 12.6%   |
| Pertis Williams III | Dem   | 2        | 893    | 1.3%    |
| Kevin Wilson        | Rep   | 2        | 12,120 | 49.1%   |
| Ron Eller           | Rep   | 2        | 12,554 | 50.9%   |
| Michael Guest       | Rep   | 3        | -      | -       |
| Michael Chiaradio   | Dem   | 3        | -      | -       |
| Jeffrey Hulum III   | Dem   | 4        | 10,928 | 57.6%   |
| D. Ryan Grover      | Dem   | 4        | 2,776  | 14.6%   |
| Paul Blackman       | Dem   | 4        | 5,234  | 27.2%   |
| Sawyer Walters      | Rep   | 4        | 7,443  | 15.9%   |
| Mike Ezell          | Rep   | 4        | 39,345 | 84.1%   |
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

## Mississippi 2024 House Primary Results

| Name            | Party | District | Votes  | Percent |
| --------------- | ----- | -------- | ------ | ------- |
| Dianne Black    | Dem   | 1        | 11,987 | 84.9%   |
| Bronco Williams | Dem   | 1        | 2,126  | 15.1%   |
| Trent Kelly     | Rep   | 1        | -      | -       |
| Bennie Thompson | Dem   | 2        | -      | -       |
| Ron Eller       | Rep   | 2        | 14,734 | 46.5%   |
| Andrew Smith    | Rep   | 2        | 11,374 | 35.9%   |
| Taylor Turcotte | REP   | 2        | 5,570  | 17.6&   |
| Craig Raybon    | Dem   | 4        | -      | -       |
| Mike Ezell      | Rep   | 4        | 51,237 | 73.3%   |
| Carl Boyanton   | Rep   | 4        | 13,273 | 19%     |
| Michael McGill  | R     | 4        | 5,362  | 7.7%    |
