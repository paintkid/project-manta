# Project MANTA - Maritime Anomaly Notification & Tracking Application

Project MANTA is a full-stack web application currently in its prototype phase. It's designed to serve as an interactive intelligence dashboard for monitoring and analyzing maritime vessel traffic. It ingests Automatic Identification System (AIS) data, processes it to detect anomalous behaviors, and presents the findings on an interactive map interface.

---

## Key Features (Current Prototype)

- **Interactive Map Interface:** A dark-themed map allows users to explore vessel locations. It's constrained to prevent endless scrolling and zooming for a controlled user experience.
- **Contextual Anomaly Detection:** The backend runs an analysis pipeline on startup to flag suspicious vessels based on multiple criteria:
  - **Contextual Loitering:** Flags vessels that are moving at a very low speed (`SOG < 1 knot`) only if they are a significant distance away from any known port.
  - **"Going Dark" Events:** Detects vessels that may have turned off their AIS transponders by identifying unusually large gaps in their signal history.
- **Efficient Backend Processing:**
  - Uses a **KD-Tree spatial index** (`scipy.spatial.KDTree`) for highly efficient nearest-port calculations, avoiding slow brute-force comparisons.
  - Employs intelligent sampling to provide a representative dataset with complete vessel tracks for visualization.
- **Dynamic Visualization:**
  - Anomalous vessels are immediately highlighted with a distinct red marker.
  - Clicking any vessel marker centers the map and draws its historical track line.
  - Marker popups provide a detailed "analyst card" with key data like MMSI, speed, distance to port, and anomaly status.
- **Analyst Workflow Sidebar:**
  - A dedicated "Flagged Vessels" panel automatically populates with a unique list of all anomalous vessels.
  - The panel is fully interactive; clicking a vessel in the list centers the map and draws its track, creating a seamless analysis workflow.

---

## Tech Stack

- **Backend:** Python, Flask, Pandas
- **Frontend:** HTML, CSS, JavaScript
- **Geospatial Analysis:** `scipy` (for KDTree), `math`
- **Mapping Library:** Leaflet.js

---

## Setup and Installation

To run this project locally, you will need Python 3 installed.

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/paintkid/project-manta.git](https://github.com/paintkid/project-manta.git)
    cd project-manta
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # On Windows
    py -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Place Data Files:**

    - Ensure `AIS_2024_01_01 2.csv` (or your chosen AIS data file) is in the root `manta` directory.
    - Ensure `ports.csv` is in the root `manta` directory.

5.  **Run the application:**

    ```bash
    flask --app app run
    ```

6.  Open your web browser and navigate to `http://127.0.0.1:5000`.

---

## Future Enhancements

This project is under active development. Planned features include:

- **Search Functionality:** A robust search bar to find specific vessels by MMSI or name.
- **Weather Data Integration:** Overlaying real-time weather data to provide context for vessel speed and route deviations.
- **Performance Optimization:** Implementing frontend marker clustering to smoothly handle a much larger number of vessels.
- **Advanced Anomaly Types:** Adding new detection models for behaviors like route deviation from standard shipping lanes.
- **UI Reform:** Changing the overall look and interactions of the user interface to ensure a modern and more professional look to the project.
