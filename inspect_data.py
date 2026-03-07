import fastf1
import json
import numpy as np
import os
from core.session_manager import SessionManager

YEAR = 2023
GP = "Monza"
SESSION_TYPE = "R"

def inspect_f1_data():
    manager = SessionManager(YEAR, GP, SESSION_TYPE)
    session = manager.session
    if session is None: 
        return

    driver_data = {}
    # Just look at the top 3 drivers for the preview
    results = session.results.sort_values(by='GridPosition').head(3)

    for _, row in results.iterrows():
        abbr = row['Abbreviation']
        driver_laps = session.laps.pick_driver(abbr)
        
        if driver_laps.empty: continue

        lap_list = []
        # Look at the first 2 laps
        for i, (_, lap) in enumerate(driver_laps.iterrows()):
            if i >= 2: break 
            
            telemetry = lap.get_telemetry()
            if telemetry is None or telemetry.empty: continue

            # Convert numpy types to native Python types for JSON compatibility
            lap_data = {
                "lap_number": int(lap['LapNumber']),
                "x_sample": telemetry["X"].head(5).tolist(), 
                "y_sample": telemetry["Y"].head(5).tolist(),
                "speed_sample": telemetry["Speed"].head(5).tolist(),
                "data_points_total": len(telemetry)
            }
            lap_list.append(lap_data)

        driver_data[abbr] = {
            "team_color": str(row['TeamColor']),
            "total_laps_in_race": len(driver_laps),
            "laps_preview": lap_list
        }

    # ✅ FIX: Do NOT print to console (prevents OSError)
    # Write directly to a file instead
    output_file = "data_preview.json"
    with open(output_file, "w") as f:
        json.dump(driver_data, f, indent=4)
    
    print(f"--- Process Complete ---")
    print(f"Data has been saved to: {os.path.abspath(output_file)}")
    print("Open this file in VS Code to see your driver_data structure.")

if __name__ == "__main__":
    # Ensure cache is enabled to speed up the process
    fastf1.Cache.enable_cache("cache")
    inspect_f1_data()