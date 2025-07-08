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

def flag_loitering_vessels(vessels_df):
    """Flags vessels that may be loitering based on their speed.

    This function adds a boolean column 'is_anomalous' to the DataFrame.
    A vessel is flagged as anomalous if its Speed Over Ground (SOG) is
    less than 1 knot.

    Args:
        vessels_df (pd.DataFrame): The input DataFrame of vessel data.
            Must contain an 'SOG' column.

    Returns:
        pd.DataFrame: The DataFrame with the new 'is_anomalous' column.
    """
    vessels_df['is_anomalous'] = (vessels_df['SOG'] < 1)
    print("✅ Analyzed vessel data for loitering")
    return vessels_df

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
raw_vessel_data = load_vessel_data()

print("2. Analyzing data for anomalies...")
VESSEL_DATA = flag_loitering_vessels(raw_vessel_data)

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

