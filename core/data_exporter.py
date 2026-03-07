import sqlite3
import os
import pandas as pd
from core.telemetry_processor import TelemetryProcessor
from core.session_manager import SessionManager 

class DataExporter:
    # Pass the ALREADY LOADED session_manager here [cite: 2026-01-20]
    def __init__(self,session_manager):
        self.sm = session_manager  # Use the existing object 
        self.gp = self.sm.gp.lower()
        self.base_path = f"database/race_{self.gp}" # Fixed from self.race_place [cite: 2026-01-20]
        
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _export_driver_race(self, driver_abbr):
        driver_laps = self.sm.get_driver_laps(driver_abbr)
        if driver_laps is None:
            return 

        db_path = os.path.join(self.base_path, f"{driver_abbr}.db")
        conn = sqlite3.connect(db_path)
        
        # Schema for individual telemetry points
        conn.execute('''
            CREATE TABLE IF NOT EXISTS telemetry (
                session_time REAL PRIMARY KEY,
                x REAL, y REAL, speed INTEGER,
                rpm INTEGER, ngear INTEGER, 
                throttle INTEGER, brake BOOLEAN,
                drs INTEGER, gap_ahead REAL,
                total_distance REAL, lap_number INTEGER
            )
        ''')

        cumulative_distance = 0.0
        for _, lap in driver_laps.iterrows():
            tp = TelemetryProcessor(lap)
            if tp.telemetry is None or tp.telemetry.empty:
                continue

            tel = tp.telemetry.copy()
            
            # Map TelemetryProcessor attributes directly to avoid array length errors [cite: 2026-03-07]
            export_df = pd.DataFrame({
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

            # Remove overlaps between laps to keep session_time unique [cite: 2026-03-07]
            export_df = export_df.drop_duplicates(subset=['session_time'])
            export_df.to_sql('telemetry', conn, if_exists='append', index=False)
            
            cumulative_distance += tel['Distance'].iloc[-1]

        conn.commit()
        conn.close()
        
    def export_all_drivers(self):
        results = self.sm.get_session_results()
        if results is None or results.empty:
            print("No session results found.")
            return

        driver_list = results['Abbreviation'].tolist()
        print(f"Starting export for {len(driver_list)} drivers...")

        # Step A: Export raw data for everyone [cite: 2026-01-20]
        for abbr in driver_list:
            try:
                print(f"Processing: {abbr}...")
                self._export_driver_race(abbr)
            except Exception as e:
                print(f"Failed raw export for {abbr}: {e}")

        # Step B: Build the Master Timeline [cite: 2026-01-20]
        print("Synchronizing timelines...")
        all_timestamps = set()
        for abbr in driver_list:
            db_path = os.path.join(self.base_path, f"{abbr}.db")
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                # Just get the unique times from this driver
                times = pd.read_sql("SELECT session_time FROM telemetry", conn)
                all_timestamps.update(times['session_time'].tolist())
                conn.close()

        # Step C: Re-index every driver against the Master Timeline [cite: 2026-03-07]
        master_df = pd.DataFrame({'session_time': sorted(list(all_timestamps))})

        for abbr in driver_list:
            db_path = os.path.join(self.base_path, f"{abbr}.db")
            if not os.path.exists(db_path): continue
            
            conn = sqlite3.connect(db_path)
            driver_df = pd.read_sql("SELECT * FROM telemetry", conn)
            
            # Merge: If a driver is missing a timestamp, the row remains but becomes NaN [cite: 2026-03-07]
            sync_df = pd.merge(master_df, driver_df, on='session_time', how='left')
            
            # Overwrite the table with the fully aligned version
            sync_df.to_sql('telemetry', conn, if_exists='replace', index=False)
            
            # Add index back for fast game-loop querying [cite: 2026-01-20]
            conn.execute("CREATE INDEX idx_time ON telemetry(session_time)")
            conn.close()

        print("Export and Synchronization complete! All driver databases are ready.")
        
    # def export_results(self):
    #     """
    #     Saves the roster, team colors, and metadata to results.db.
    #     This is used for the game's UI and car coloring.
    #     """
    #     results = self.sm.get_session_results()
        
    #     if results is None:
    #         print("No results found to export.")
    #         return

    #     # Path to our master info file [cite: 2026-01-20]
    #     db_path = os.path.join(self.base_path, "results.db")
    #     conn = sqlite3.connect(db_path)
        
    #     # We store the results directly.
    #     results.to_sql('session_results', conn, if_exists='replace', index=False)
        
    #     conn.close()
    #     print(f"Race identity saved to {db_path}")
    
    def cleanup(self):
        """Removes the race folder, handling Windows file locks. [cite: 2026-01-20]"""
        import shutil
        import time
        
        # Give the OS a split second to release file handles after the window closes
        time.sleep(0.5) 
        
        if os.path.exists(self.base_path):
            try:
                shutil.rmtree(self.base_path)
                print(f"Successfully cleaned up: {self.base_path}")
            except PermissionError:
                 print("Warning: Files were still locked by the OS. Cleanup skipped.")