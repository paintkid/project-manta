from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

def load_vessel_data():
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

VESSEL_DATA = load_vessel_data()

@app.route('/api/vessels')
def get_vessels():
    if VESSEL_DATA.empty:
        return jsonify([])
    
    vessels_json = VESSEL_DATA.to_dict(orient='records')
    return jsonify(vessels_json)

