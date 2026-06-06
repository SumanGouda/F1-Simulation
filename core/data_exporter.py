import sqlite3
import os
import shutil  
import time    
import gc
import pandas as pd

class DataExporter:
    def __init__(self, session_manager):
        self.sm = session_manager  
        self.gp = self.sm.gp.lower()
        self.base_path = f"database/race_{self.gp}" 
        
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def __export_driver_tel(self, driver_abbr):
        # Path to the unified grand prix database file
        db_path = os.path.join(self.base_path, f"{self.gp}.db")
        table_name = f"telemetry_{driver_abbr.lower()}"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if this specific driver's table already exists to save time
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone():
            print(f"Skipping {driver_abbr}: Table '{table_name}' already exists in {self.gp}.db.")
            conn.close()
            return 
        
        driver_laps = self.sm.get_driver_laps(driver_abbr)
        if driver_laps is None:
            conn.close()
            return  
        
        cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
        cursor.execute(f'''
            CREATE TABLE {table_name} (
                session_time REAL PRIMARY KEY,
                x REAL, y REAL, speed INTEGER,
                rpm INTEGER, ngear INTEGER, 
                throttle INTEGER, brake BOOLEAN,
                drs INTEGER, gap_ahead REAL,
                total_distance REAL, lap_number INTEGER
            )
        ''')

        all_laps_data = []
        cumulative_distance = 0.0

        for _, lap in driver_laps.iterrows():
            try:
                tel = lap.get_telemetry() 
                if tel.empty:
                    continue
                
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
                
                cumulative_distance += tel['Distance'].iloc[-1]
            except Exception as e:
                print(f"Skipping lap {lap['LapNumber']} for {driver_abbr}: {e}")

        if all_laps_data:
            final_df = pd.concat(all_laps_data).drop_duplicates(subset=['session_time'])
            final_df.to_sql(table_name, conn, if_exists='append', index=False)

        cursor.execute(f"CREATE INDEX idx_time_{driver_abbr.lower()} ON {table_name}(session_time)")
        conn.commit()
        conn.close()
           
    def __export_weather(self):
        """Exports session weather data to a dedicated table inside the main database."""
        db_path = os.path.join(self.base_path, f"{self.gp}.db")
        table_name = "weather"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table already exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone():
            print(f"Skipping Weather: Table '{table_name}' already exists in {self.gp}.db.")
            conn.close()
            return

        weather_data = self.sm.get_weather_data()
        if weather_data is None or weather_data.empty:
            print("No weather data found to export.")
            conn.close()
            return
         
        conn.execute(f'DROP TABLE IF EXISTS {table_name}')
        
        weather_df = weather_data.copy()
        weather_df['Time'] = weather_df['Time'].dt.total_seconds()
 
        weather_df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.execute(f"CREATE INDEX idx_weather_time ON {table_name}(Time)")
        
        conn.commit()
        conn.close()
        print(f"Weather export complete inside: {db_path}")

    def __export_race_data(self): 
        """Exports consolidated race laps data to a dedicated table inside the main database."""
        db_path = os.path.join(self.base_path, f"{self.gp}.db")
        table_name = "laps"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the table already exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone():
            print(f"Skipping Race Data: Table '{table_name}' already exists in {self.gp}.db.")
            conn.close()
            return

        race_data = self.sm.get_race_laps_data()
        if race_data is None or race_data.empty:
            print("No race data found to export.")
            conn.close()
            return
    
        conn.execute(f'DROP TABLE IF EXISTS {table_name}')
        
        race_df = race_data.copy()
        
        time_cols = ['Sector1Time', 'Sector2Time', 'Sector3Time', 'LapTime', 'PitOutTime', 'PitInTime']
        for col in time_cols:
            if col in race_df.columns:
                race_df[col] = race_df[col].dt.total_seconds() 
              
        race_df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.execute(f"CREATE INDEX idx_race_time ON {table_name}(Time)")
        
        conn.commit()
        conn.close()
        print(f"Race export complete inside: {db_path}")
        
    def cleanup(self):
        gc.collect() 
        time.sleep(0.7) 
        if os.path.exists(self.base_path):
            try:
                shutil.rmtree(self.base_path)
                print(f"Successfully cleaned up: {self.base_path}")
            except PermissionError:
                 print(f"Warning: {self.base_path} is still locked. Cleanup skipped.")
    
    def export_all_data(self):
        results = self.sm.get_session_results()
        if results is None or results.empty:
            print("No session results found. Cannot export data.")
            return

        driver_list = results['Abbreviation'].tolist()
        print(f"Starting sequential export for {len(driver_list)} drivers...")

        try:
            print("Processing: Consolidated Race Laps...")
            self.__export_race_data()
        except Exception as e:
            print(f"Failed to export consolidated race data: {e}")
            
        for abbr in driver_list:
            try:
                print(f"Processing Driver: {abbr}...")
                self.__export_driver_tel(abbr)
            except Exception as e:
                print(f"Failed export for {abbr}: {e}")

        try:
            print("Processing: Weather...")
            self.__export_weather()
        except Exception as e:
            print(f"Failed to export weather data: {e}")

        print("Export complete! All databases (Drivers & Weather) are ready.")       

