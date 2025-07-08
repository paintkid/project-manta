# ==============================================================================
# Imports
# ==============================================================================
from flask import Flask, jsonify, render_template
import pandas as pd

# ==============================================================================
# Flask Application Initialization
# ==============================================================================
app = Flask(__name__)

# ==============================================================================
# Data Processing and Analysis Functions
# ==============================================================================

def load_vessel_data():
    """Loads and prepares the initial vessel data from a CSV file.

    This function reads a large AIS data file, selects only the required
    columns, drops any rows with missing data, and returns a smaller,
    manageable sample for the application to use.

    Returns:
        pd.DataFrame: A cleaned and sampled DataFrame of vessel data,
                      or an empty DataFrame if the source file is not found.
    """
    csv_file_path = 'AIS_2024_01_01 2.csv'

    required_cols = ['MMSI', 'BaseDateTime', 'LAT', 'LON', 'SOG', 'COG']
    try:
        df = pd.read_csv(csv_file_path, usecols=required_cols)
    except FileNotFoundError:
        print(f"ERROR: file {csv_file_path} was not found.")
        return pd.DataFrame()
    
    df_clean = df.dropna()
    if len(df_clean) > 1000:
        df_sample = df_clean.sample(n=1000, random_state=1)
    else:
        df_sample = df_clean

    print("✅ Vessel data loaded and ready.")
    return df_sample

# ==============================================================================
# Application Startup Sequence
# ==============================================================================
print("--- MANTA Application Starting ---")

print("1. Loading vessel data from source file...")
VESSEL_DATA = load_vessel_data()

print("3. Application ready. Starting web server...")
print("------------------------------------")

# ==============================================================================
# API and Page Routes
# ==============================================================================

@app.route('/')
def index():
    """Serves the main HTML page with the map."""
    return render_template('index.html')

@app.route('/api/vessels')
def get_vessels():
    """Provides the vessel data as a JSON API endpoint."""
    if VESSEL_DATA.empty:
        return jsonify([])
    
    vessels_json = VESSEL_DATA.to_dict(orient='records')
    return jsonify(vessels_json)

