import arcade
import sqlite3
import os
import numpy as np
import pandas as pd
from core.data_exporter import DataExporter  
from core.session_manager import SessionManager
from core.telemetry_processor import TelemetryProcessor
from utils.helpers import prepare_track_layout, get_screen_coords

# Layout Constants
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 900
SCREEN_TITLE = "F1 Race Replay - Arcade Edition"

# Configuration
year = 2025
GP_NAME = "bahrain"  
DB_ROOT = f"database/race_{GP_NAME}"

def hex_to_rgb(hex_str):
    if not hex_str or not isinstance(hex_str, str): return (128, 128, 128)
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

class F1ReplayWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        # Game State
        self.driver_metadata = {}  # Loaded from results.db
        self.sorted_drivers = []   # For the leaderboard
        self.track_points = []
        self.session_time = 0.0    # The "Master Clock" for the replay
        self.speed_multiplier = 2.0 
        
        # Telemetry Cache (to avoid opening DB every frame)
        self.telemetry_cache = {} 
        
        self.setup()

    def setup(self):
        self.manager = SessionManager(year=year, gp=GP_NAME.title(), session_type="R")
        
        # 2. Initialize Exporter and RESET the database for this session [cite: 2026-01-20]
        self.exporter = DataExporter(self.manager)
        # We export fresh data every time the script runs
        self.exporter.export_all_drivers() 

        # 3. Load Static Metadata (Results, Colors, Rotation)
        results_df = self.manager.get_session_results()
        if results_df is not None:
            self.driver_metadata = results_df.set_index('Abbreviation').to_dict('index')
            self.sorted_drivers = list(self.driver_metadata.keys())
        
        self.rotation = self.manager.get_circuit_rotation() or 0

        # 4. Build the "Track Map" (The Green Line)
        # We use the fastest lap to get the most accurate racing line [cite: 2026-01-20]
        fastest_lap = self.manager.get_session_fastest_lap()
        if fastest_lap is not None:
            tp_track = TelemetryProcessor(fastest_lap)
            raw_x, raw_y = tp_track.get_track_coordinates()

            if raw_x is not None and raw_y is not None:
                layout = prepare_track_layout(
                    raw_x, raw_y, 
                    SCREEN_WIDTH, SCREEN_HEIGHT, 
                    padding_left=320, # Room for the leaderboard cards [cite: 2026-02-20]
                    rotation=self.rotation
                )
                (self.track_points, self.offset_x, self.offset_y, self.track_scale) = layout
        else:
            print("Error: Could not retrieve track coordinates for setup.")
            
        self.car_colors = {}
        for abbr, info in self.driver_metadata.items():
            self.car_colors[abbr] = hex_to_rgb(info.get('TeamColor', '#FFFFFF'))

        # 6. Initialize Game Timing & State
        self.session_time = 0.0      
        self.speed_multiplier = 1.0  # Controls replay speed (e.g., 2.0 for 2x speed)
        self.is_paused = False      
        
        self.current_car_positions = {abbr: (0, 0) for abbr in self.driver_metadata.keys()}

    def on_update(self, delta_time):
        if self.is_paused:
            return

        self.session_time += delta_time * self.speed_multiplier
        race_positions = []

        for abbr in self.driver_metadata.keys():
            db_path = os.path.join(DB_ROOT, f"{abbr}.db")
            if not os.path.exists(db_path): continue

            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # We pull x, y for the dots, and distance/gap for the leaderboard
                query = """
                    SELECT x, y, total_distance, gap_ahead 
                    FROM telemetry 
                    WHERE session_time <= ? 
                    ORDER BY session_time DESC 
                    LIMIT 1
                """
                cursor.execute(query, (self.session_time,))
                result = cursor.fetchone()
                conn.close()

                if result:
                    # Update live position for on_draw
                    self.current_car_positions[abbr] = (result[0], result[1])
                    
                    # Update metadata for the leaderboard cards
                    self.driver_metadata[abbr]['total_distance'] = result[2]
                    self.driver_metadata[abbr]['gap_ahead'] = result[3]
                    
                    # Track this for sorting
                    race_positions.append((abbr, result[2]))
                
            except Exception as e:
                print(f"Update error for {abbr}: {e}")

        # Re-sort the leaderboard based on actual distance covered [cite: 2026-01-20]
        if race_positions:
            race_positions.sort(key=lambda x: x[1], reverse=True)
            self.sorted_drivers = [d[0] for d in race_positions]
            
    def on_draw(self):
        self.clear()
        
        # 1. Draw Track Layout (The "Circuit Line")
        if self.track_points:
            arcade.draw_line_strip(self.track_points, arcade.color.DARK_GREEN, 3)
        
        # 2. Draw Leaderboard (Left Side Cards) [cite: 2026-02-20]
        self.draw_leaderboard()
        
        # 3. Draw Driver Circles (The "Cars")
        # We loop through sorted_drivers so the order is consistent [cite: 2026-01-20]
        for abbr in self.sorted_drivers:
            # Get the raw meters we stored during on_update
            pos = self.current_car_positions.get(abbr)
            if not pos or pos == (0, 0):
                continue

            # Map raw meters to screen pixels using our setup offsets
            fx, fy = get_screen_coords(
                pos[0], pos[1],
                self.rotation, self.track_scale, self.offset_x, self.offset_y
            )

            # Use our pre-built color dictionary for speed
            color = self.car_colors.get(abbr, arcade.color.GRAY)
            
            # Draw the circle and the Abbreviation label
            arcade.draw_circle_filled(fx, fy, 8, color)
            arcade.draw_text(
                abbr, fx + 12, fy, 
                arcade.color.WHITE, 10, bold=True, anchor_y="center"
            )
            
    def draw_leaderboard(self):
        # Card style UI settings [cite: 2025-12-16]
        start_x, start_y = 130, SCREEN_HEIGHT - 50
        box_width = 240
        box_height = 28
        spacing = 32

        for i, abbr in enumerate(self.sorted_drivers):
            meta = self.driver_metadata.get(abbr, {})
            color = self.car_colors.get(abbr, arcade.color.GRAY)
            curr_y = start_y - (i * spacing)
            
            # Draw the main Card (The Team Color background) [cite: 2026-02-20]
            arcade.draw_rect_filled(
                arcade.rect.XYWH(start_x, curr_y, box_width, box_height), 
                color
            )
            
            # Add a subtle dark overlay for the right-side text to improve readability
            arcade.draw_rect_filled(
                arcade.rect.XYWH(start_x + 60, curr_y, box_width / 2, box_height), 
                (0, 0, 0, 80) # Semi-transparent black
            )
            
            # Logic for the Gap Time (Gap is updated in on_update from DB)
            gap = meta.get('gap_ahead', 0)
            gap_text = "INTERVAL" if i == 0 else f"+{gap:.3f}s"
            
            # Draw Rank & Abbreviation
            arcade.draw_text(
                f"{i+1}  {abbr}", 
                start_x - 110, curr_y, 
                arcade.color.WHITE, 12, bold=True, anchor_y="center"
            )
            
            # Draw Gap Time
            arcade.draw_text(
                gap_text, 
                start_x + 110, curr_y, 
                arcade.color.WHITE, 11, anchor_x="right", anchor_y="center"
            )

def main():
    window = None
    try:
        window = F1ReplayWindow()
        arcade.run()
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        # This block runs when the window is closed [cite: 2026-01-20]
        if window is not None and hasattr(window, 'exporter'):
            try:
                print("Cleaning up database files before exit...")
                window.exporter.cleanup()
            except Exception as e:
                print(f"An error occurred while cleaning up database files: {e}")
        if window and hasattr(window, 'exporter'):
            print("Cleaning up database files before exit...")
            window.exporter.cleanup()


if __name__ == "__main__":
    main()