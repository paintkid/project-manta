# ==============================================================================
# Imports
# ==============================================================================
from flask import Flask, jsonify, render_template
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
from scipy.spatial import KDTree

# ==============================================================================
# Flask Application Initialization
# ==============================================================================
app = Flask(__name__)

# ==============================================================================
# Data Processing and Analysis Functions
# ==============================================================================

# --- Helper Functions ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points on Earth in nautical miles.

    Args:
        lat1 (float): Latitude of the first point.
        lon1 (float): Longitude of the first point.
        lat2 (float): Latitude of the second point.
        lon2 (float): Longitude of the second point.

    Returns:
        float: The distance in nautical miles.
    """
    R = 3440  # Radius of Earth in nautical miles

    # Convert latitude and longitude from degrees to radians.
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)

    # Haversine formula
    a = sin(dLat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance

# --- Data Loading Functions --
def load_port_data():
    """Loads and prepares the world port location data.

    This function reads port data from a CSV file, selects only the
    necessary columns, and cleans the data for use in distance calculations.

    Returns:
        pd.DataFrame: A DataFrame containing port names, latitudes, and
                      longitudes, or an empty DataFrame if the file is not found.
    """
    port_file_path = 'ports.csv'
    required_cols = ['Main Port Name', 'Latitude', 'Longitude']
    try:
        df = pd.read_csv(port_file_path, usecols=required_cols)
    except FileNotFoundError:
        print(f"ERROR: file {port_file_path} was not found.")
        return pd.DataFrame()
    except ValueError as e:
        print(f"ERROR: Could not find required columns in {port_file_path}. Please check the column names.")
        print(f"Details: {e}")
        return pd.DataFrame()
    
    # Rename columns for consistency and ease of use
    df.rename(columns={
        'Main Port Name': 'PORT_NAME',
        'Latitude': 'LATITUDE',
        'Longitude': 'LONGITUDE'
    }, inplace=True)


    df_clean = df.dropna()
    print("✅ Port data loaded and ready.")
    return df_clean

def load_vessel_data():
    """Loads and prepares the initial vessel data from a CSV file.

    This function reads a large AIS data file, selects only the required
    columns, drops any rows with missing data, and returns a smaller,
    manageable sample for the application to use.

    Returns:
        pd.DataFrame: A cleaned and sampled DataFrame of vessel data,
                      or an empty DataFrame if the source file is not found.
    """
    vessel_data_file_path = 'AIS_2024_01_01 2.csv'

    required_cols = ['MMSI', 'BaseDateTime', 'LAT', 'LON', 'SOG', 'COG']
    try:
        df = pd.read_csv(vessel_data_file_path, usecols=required_cols, nrows=2000)
    except FileNotFoundError:
        print(f"ERROR: file {vessel_data_file_path} was not found.")
        return pd.DataFrame()
    
    df_clean = df.dropna()
    print("✅ Vessel data loaded and ready.")
    return df_clean

# --- Main Analysis Function ---
def flag_loitering_vessels(vessels_df, ports_df):
    """Flags vessels that are loitering far from any known port using spatial index.

    Args:
        vessels_df (pd.DataFrame): DataFrame of vessel data.
        ports_df (pd.DataFrame): DataFrame of port location data.

    Returns:
        pd.DataFrame: The vessel DataFrame with a new 'is_anomalous' column.
    """
    if ports_df.empty:
        print("⚠️ Port data is empty. Skipping distance analysis.")
        vessels_df['is_anomalous'] = (vessels_df['SOG'] < 1)
        return vessels_df
    
    DISTANCE_THRESHOLD_NM = 50 # In nautial miles

    port_coords = ports_df[['LATITUDE', 'LONGITUDE']].values
    port_tree = KDTree(port_coords)

    vessel_coords = vessels_df[['LAT', 'LON']].values

    distances, _ = port_tree.query(vessel_coords, k=1)
    vessels_df['dist_to_nearest_port'] = distances * 60
    
    print("   - Calculating distance to nearest port for each vessel...")

    vessels_df['is_anomalous'] = (vessels_df['SOG'] < 1) & (vessels_df['dist_to_nearest_port'] > DISTANCE_THRESHOLD_NM)

    print("✅ Analyzed vessel data for contextual loitering")
    return vessels_df

# ==============================================================================
# Application Startup Sequence
# ==============================================================================
print("--- MANTA Application Starting ---")

print("1. Loading port data from source file...")
PORT_DATA = load_port_data()

print("2. Loading vessel data from source file...")
raw_vessel_data = load_vessel_data()

print("3. Analyzing data for anomalies...")
VESSEL_DATA = flag_loitering_vessels(raw_vessel_data, PORT_DATA)

print("4. Application ready. Starting web server...")
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

