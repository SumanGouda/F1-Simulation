import sqlite3
import os
import shutil  
import time    
import gc
import pandas as pd
from core.telemetry_processor import TelemetryProcessor
from core.session_manager import SessionManager 

class DataExporter:
    def __init__(self, session_manager):
        self.sm = session_manager  
        self.gp = self.sm.gp.lower()
        self.base_path = f"database/race_{self.gp}" 
        
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _export_driver_race(self, driver_abbr):
        db_path = os.path.join(self.base_path, f"{driver_abbr}.db")
        
        # Check if the file exists before doing ANY heavy lifting 
        if os.path.exists(db_path):
            print(f"Skipping {driver_abbr}: Database already exists.")
            return # Exit immediately to save time 
        
        driver_laps = self.sm.get_driver_laps(driver_abbr)
        if driver_laps is None:
            return 

        conn = sqlite3.connect(db_path)
        
        # Clear old data to start fresh [cite: 2026-01-20]
        conn.execute('DROP TABLE IF EXISTS telemetry')
        conn.execute('''
            CREATE TABLE telemetry (
                session_time REAL PRIMARY KEY,
                x REAL, y REAL, speed INTEGER,
                rpm INTEGER, ngear INTEGER, 
                throttle INTEGER, brake BOOLEAN,
                drs INTEGER, gap_ahead REAL,
                total_distance REAL, lap_number INTEGER
            )
        ''')

        # This list will hold dataframes for every lap 
        all_laps_data = []
        cumulative_distance = 0.0

        for _, lap in driver_laps.iterrows():
            # IMPORTANT: Explicitly get telemetry for this specific lap 
            try:
                tel = lap.get_telemetry() 
                if tel.empty:
                    continue
                
                # Create the dataframe for this specific lap  
                lap_df = pd.DataFrame({
                    'session_time': tel['Time'].dt.total_seconds(),
                    'x': tel['X'],
                    'y': tel['Y'],
                    'speed': tel['Speed'],
                    'rpm': tel['RPM'],
                    'ngear': tel['nGear'],       
                    'throttle': tel['Throttle'],
                    'brake': tel['Brake'],
                    'drs': tel['DRS'],          
                    'gap_ahead': tel.get('DistanceToDriverAhead', 0), 
                    'total_distance': tel['Distance'] + cumulative_distance,
                    'lap_number': int(lap['LapNumber'])
                })
                all_laps_data.append(lap_df)
                
                # Update distance for the start of the next lap  
                cumulative_distance += tel['Distance'].iloc[-1]
            except Exception as e:
                print(f"Skipping lap {lap['LapNumber']} for {driver_abbr}: {e}")

        # Combine all laps and save once for better performance  
        if all_laps_data:
            final_df = pd.concat(all_laps_data).drop_duplicates(subset=['session_time'])
            final_df.to_sql('telemetry', conn, if_exists='append', index=False)

        conn.execute("CREATE INDEX idx_time ON telemetry(session_time)")
        conn.commit()
        conn.close()
           
    def export_all_drivers(self):
        """Exports each driver into their own independent database file. [cite: 2026-01-20]"""
        results = self.sm.get_session_results()
        if results is None or results.empty:
            print("No session results found.")
            return

        driver_list = results['Abbreviation'].tolist()
        print(f"Starting sequential export for {len(driver_list)} drivers...")

        for abbr in driver_list:
            try:
                print(f"Processing: {abbr}...")
                self._export_driver_race(abbr)
            except Exception as e:
                print(f"Failed export for {abbr}: {e}")

        print("Export complete! Sequential databases are ready.")
    
    def cleanup(self):
        gc.collect() 
        time.sleep(0.7) 
        if os.path.exists(self.base_path):
            try:
                shutil.rmtree(self.base_path)
                print(f"Successfully cleaned up: {self.base_path}")
            except PermissionError:
                 print(f"Warning: {self.base_path} is still locked. Cleanup skipped.")