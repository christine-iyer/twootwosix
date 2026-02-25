import pandas as pd
from flask import Flask, render_template, jsonify
import os

app = Flask(__name__)

# Load the data
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'house.tab')
COUNTY_PRES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'countypres.csv')

# Load House data
try:
    df_house = pd.read_csv(DATA_PATH, low_memory=False)
    print(f"Successfully loaded House data with {len(df_house)} rows and {len(df_house.columns)} columns")
except Exception as e:
    print(f"Error loading House data: {e}")
    df_house = pd.DataFrame()

# Load County Presidential data
try:
    df_county_pres = pd.read_csv(COUNTY_PRES_PATH, low_memory=False)
    print(f"Successfully loaded County Presidential data with {len(df_county_pres)} rows and {len(df_county_pres.columns)} columns")
except Exception as e:
    print(f"Error loading County Presidential data: {e}")
    df_county_pres = pd.DataFrame()

@app.route('/')
def index():
    """Render the main page with the filterable table"""
    house_columns = df_house.columns.tolist()
    county_pres_columns = df_county_pres.columns.tolist()
    return render_template('index.html', 
                         house_columns=house_columns, 
                         county_pres_columns=county_pres_columns)

@app.route('/api/house')
def get_house_data():
    """API endpoint to get the House data as JSON"""
    try:
        if df_house.empty:
            return jsonify({'error': 'No House data loaded'}), 500
        data = df_house.fillna('').to_dict('records')
        return jsonify({
            'data': data,
            'recordsTotal': len(data),
            'recordsFiltered': len(data)
        })
    except Exception as e:
        print(f"Error in /api/house: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/countypres')
def get_county_pres_data():
    """API endpoint to get the County Presidential data as JSON"""
    try:
        if df_county_pres.empty:
            return jsonify({'error': 'No County Presidential data loaded'}), 500
        data = df_county_pres.fillna('').to_dict('records')
        return jsonify({
            'data': data,
            'recordsTotal': len(data),
            'recordsFiltered': len(data)
        })
    except Exception as e:
        print(f"Error in /api/countypres: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/columns')
def get_columns():
    """API endpoint to get column information"""
    columns = [{"title": col, "data": col} for col in df_house.columns]
    return jsonify(columns)

@app.route('/favicon.ico')
def favicon():
    """Return empty response for favicon"""
    return '', 204

if __name__ == '__main__':
    print(f"Loaded {len(df_house)} House records")
    print(f"Loaded {len(df_county_pres)} County Presidential records")
    print("\nStarting server at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
