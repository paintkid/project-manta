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
        df = pd.read_csv(vessel_data_file_path, usecols=required_cols, nrows=200000)
    except FileNotFoundError:
        print(f"ERROR: file {vessel_data_file_path} was not found.")
        return pd.DataFrame()
    
    df_clean = df.dropna()
    print(f"   - Initial data loaded with {len(df_clean)} rows.")

    print("   - Identifying moving vessels...")
    variance = df_clean.groupby('MMSI')[['LAT', 'LON']].std().sum(axis=1)
    moving_mmsis = variance[variance > 0.001].index.tolist()

    if not moving_mmsis:
        print("⚠️ No moving vessels found in the data sample. Try increasing nrows.")
        # Fallback to the old method if no moving vessels are found
        unique_mmsis = df_clean['MMSI'].unique()
        sample_size = min(50, len(unique_mmsis))
        sampled_mmsis = pd.Series(unique_mmsis).sample(n=sample_size, random_state=1).tolist()
    else:
        # 2. Randomly select from the list of ONLY the moving vessels.
        sample_size = min(50, len(moving_mmsis))
        sampled_mmsis = pd.Series(moving_mmsis).sample(n=sample_size, random_state=1).tolist()

    # 3. Filter the original DataFrame to get all rows for the selected MMSIs.
    df_final_sample = df_clean[df_clean['MMSI'].isin(sampled_mmsis)]

    print("✅ Vessel data loaded and ready.")
    return df_final_sample  

# --- Analysis Functions ---
def analyze_vessel_anomalies(vessels_df, ports_df):
    """
    Main analysis pipeline. Flags vessels for various anomalous behaviors.
    """
    # --- Loitering Analysis ---
    if not ports_df.empty:
        DISTANCE_THRESHOLD_NM = 5 # Using sensitive threshold for testing
        port_coords = ports_df[['LATITUDE', 'LONGITUDE']].values
        port_tree = KDTree(port_coords)
        vessel_coords = vessels_df[['LAT', 'LON']].values
        distances, _ = port_tree.query(vessel_coords, k=1)
        vessels_df['dist_to_nearest_port'] = distances * 60
        vessels_df['is_loitering'] = (vessels_df['SOG'] < 1) & (vessels_df['dist_to_nearest_port'] > DISTANCE_THRESHOLD_NM)
        loitering_count = vessels_df['is_loitering'].sum()
        print(f"   - Found {loitering_count} potential loitering events.")
    else:
        vessels_df['is_loitering'] = False

    # --- Going Dark Analysis ---
    TIME_THRESHOLD_HOURS = 0.1 # Using sensitive threshold for testing
    TIME_THRESHOLD_SECONDS = TIME_THRESHOLD_HOURS * 3600
    vessels_df['BaseDateTime'] = pd.to_datetime(vessels_df['BaseDateTime'], errors='coerce')
    vessels_df.sort_values(by=['MMSI', 'BaseDateTime'], inplace=True)
    time_gaps = vessels_df.groupby('MMSI')['BaseDateTime'].diff().dt.total_seconds()
    vessels_df['time_gap_seconds'] = time_gaps.fillna(0)
    vessels_df['is_dark'] = vessels_df['time_gap_seconds'] > TIME_THRESHOLD_SECONDS
    dark_count = vessels_df['is_dark'].sum()
    print(f"   - Found {dark_count} potential 'going dark' events.")

    # --- Final Anomaly Flag ---
    # Combine all individual flags into the final 'is_anomalous' column.
    vessels_df['is_anomalous'] = vessels_df['is_loitering'] | vessels_df['is_dark']
    
    print("✅ Analysis complete.")
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
VESSEL_DATA = analyze_vessel_anomalies(raw_vessel_data, PORT_DATA)

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

@app.route('/api/anomalies')
def get_anomalies():
    """Provides only the anomalous vessel data as a JSON API endpoint."""
    if VESSEL_DATA.empty:
        return jsonify([])

    # Find all unique MMSIs that have at least one anomalous point. 
    anomalous_mmsis = VESSEL_DATA[VESSEL_DATA['is_anomalous'] == True]['MMSI'].unique()
    
    # Filter DataFrame to get all rows for these anomalous vessels.
    anomalous_vessels_df = VESSEL_DATA[VESSEL_DATA['MMSI'].isin(anomalous_mmsis)]
    
    # Get most recent data point for each unique anomalous vessel.
    latest_anomalies = anomalous_vessels_df.loc[anomalous_vessels_df.groupby('MMSI')['BaseDateTime'].idxmax()]
    
    vessels_json = latest_anomalies.to_dict(orient='records')
    return jsonify(vessels_json)