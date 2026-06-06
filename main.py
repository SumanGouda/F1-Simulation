import arcade
import sqlite3
import shutil 
import time
import os
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
from rendering.ui_renderer import draw_leaderboard, draw_lap_number, draw_corners, draw_weather_card, draw_track, draw_tel, draw_focused_driver_telemetry
from core.data_exporter import DataExporter
from core.session_manager import SessionManager
from core.telemetry_processor import TelemetryProcessor
from utils.helpers import prepare_track_layout, get_screen_coords, calculate_weather_frame_ratio, get_max_session_rows, hex_to_rgb

# Layout Constants
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 900
SCREEN_TITLE = "F1 Race Replay - Arcade Edition"

# Configuration
year = 2025
GP_NAME = "bahrain"  
DB_ROOT = f"database/race_{GP_NAME}"


class F1ReplayWindow(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)


        # Game State
        self.driver_metadata = {}   
        self.sorted_drivers = []  
        self.corner_data = []
        self.session_time = 0.0    
        self.is_paused = False
        self.current_race_time = pd.Timedelta(seconds=0) 
        self.current_weather = None
        self.selected_driver = None 
        self.raw_x = None
        self.raw_y = None
        self.fx = None
        self.fy = None

        self.control_hitboxes = {}
        self.setup()
        self.btn_icons = {
            "SLOW":  arcade.load_texture("assets/images/slow.png"),
            "PAUSE": arcade.load_texture("assets/images/pause.png"),
            "PLAY":  arcade.load_texture("assets/images/play.png"),
            "FAST":  arcade.load_texture("assets/images/fast.png"),
        }

    def _draw_playback_controls(self):
        btn_w, btn_h = 36, 36
        gap = 8
        border = 2
        center_y = 90
        left_edge = 20

        buttons = [
            ("SLOW",  left_edge + btn_w//2),
            ("PAUSE", left_edge + btn_w + gap + btn_w//2),
            ("FAST",  left_edge + btn_w*2 + gap*2 + btn_w//2),
        ]

        hitboxes = {}
        for name, cx in buttons:
            if name == "PAUSE":
                icon_key = "PLAY" if self.is_paused else "PAUSE"
            else:
                icon_key = name

            arcade.draw_texture_rect(
                self.btn_icons[icon_key],
                arcade.rect.XYWH(cx, center_y, btn_w, btn_h)
            )

            hitboxes[name] = {
                "left":   cx - btn_w / 2,
                "right":  cx + btn_w / 2,
                "bottom": center_y - btn_h / 2,
                "top":    center_y + btn_h / 2,
            }

        self.control_hitboxes = hitboxes

    def _on_slow(self, event):
        self.race_speed = max(0.5, round(self.race_speed - 0.5, 1))
        self._refresh_button_labels()

    def _on_pause(self, event):
        self.is_paused = not self.is_paused
        self._refresh_button_labels()

    def _on_fast(self, event):
        self.race_speed = min(5.0, round(self.race_speed + 0.5, 1))
        self._refresh_button_labels()

    def _refresh_button_labels(self):
        pass  # Labels are redrawn dynamically each frame

    def setup(self):
        # Load the F1 Session
        self.session_manager = SessionManager(year=year, gp=GP_NAME.title(), session_type="R")
        
        if self.session_manager.session is None:
            print("Failed to load F1 Session.")
            return

        # Create the .db files 
        self.exporter = DataExporter(self.session_manager)
        self.exporter.export_all_data()
        gp_clean = self.session_manager.gp.lower()
        self.db_path = f"database/race_{gp_clean}/{gp_clean}.db"
        
        # Prepare UI Metadata & Layout 
        self.results_df = self.session_manager.get_session_results()
        if self.results_df is not None:
            self.results_df = self.results_df.sort_values(by='GridPosition', na_position='last')
            self.driver_metadata = self.results_df.set_index('Abbreviation').to_dict('index')
            self.sorted_drivers = list(self.driver_metadata.keys())
        
        self.rotation = self.session_manager.get_circuit_rotation() or 0
        self.corner_data = self.session_manager.get_corner_data()
        
        fastest_lap = self.session_manager.get_session_fastest_lap()
        if fastest_lap is not None:
            tp_track = TelemetryProcessor(fastest_lap)
            raw_x, raw_y = tp_track.get_track_coordinates()
            
            if raw_x is not None and raw_y is not None: 
                self.raw_x = raw_x
                self.raw_y = raw_y
                
                (self.fx, self.fy, self.offset_x, self.offset_y, self.track_scale) = prepare_track_layout(
                        raw_x, raw_y, SCREEN_WIDTH, SCREEN_HEIGHT, 
                        padding_left=320, rotation=self.rotation
                    )            
                self.track_scale_focused = self.track_scale * 0.30
                self.foc_offset_x = self.offset_x + 300
                self.foc_offset_y = self.offset_y - 80
 
        self.car_colors = {abbr: hex_to_rgb(info.get('TeamColor', '#FFFFFF')) 
                           for abbr, info in self.driver_metadata.items()}
     
        self.current_car_positions = {abbr: (0, 0) for abbr in self.driver_metadata.keys()}
        self.driver_row_counters = {abbr: 0 for abbr in self.driver_metadata.keys()}
        
        # Frame & Weather Timing Logic 
        self.max_rows = get_max_session_rows(self.driver_metadata.keys(), self.db_path)
        self.weather_frame_ratio = calculate_weather_frame_ratio(self.driver_metadata.keys(), self.db_path)
 
        self.global_frame_counter = 0
        self.weather_index = 0
        self.race_speed = 1.5
        self.current_weather = None
        
        self.driver_float_counters = {abbr: 0.0 for abbr in self.driver_metadata.keys()}
        print(f"Setup complete. Weather ratio set to 1:{self.weather_frame_ratio}")
        
    def on_update(self, delta_time):
        if self.is_paused:
            return
 
        if self.global_frame_counter % self.weather_frame_ratio == 0:
            if os.path.exists(self.db_path):
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row 
                    cursor = conn.cursor() 
                    cursor.execute("SELECT * FROM weather LIMIT 1 OFFSET ?", (int(self.weather_index),))
                    result = cursor.fetchone()
                    conn.close()

                    if result:
                        self.current_weather = result
                        self.weather_index += self.race_speed
                except Exception as e:
                    print(f"Weather Update Error: {e}")
 
        self.global_frame_counter += 1
        race_positions = [] 
        
        if os.path.exists(self.db_path):
            for abbr in self.sorted_drivers:
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                     
                    self.driver_float_counters[abbr] += self.race_speed
                    current_row_index = int(self.driver_float_counters[abbr])
                    
                    table_name = f"telemetry_{abbr.lower()}"
                    
                    query = f"""
                        SELECT x, y, total_distance, gap_ahead, speed, rpm, ngear, 
                               throttle, brake, drs, lap_number 
                        FROM {table_name} LIMIT 1 OFFSET ?
                    """
                    cursor.execute(query, (current_row_index,))
                    result = cursor.fetchone()
                    conn.close()

                    if result:
                        (x, y, dist, gap, speed, rpm, gear, throttle, brake, drs, lap) = result
                        
                        if pd.notna(x) and pd.notna(y):
                            self.current_car_positions[abbr] = (x, y)
                        
                        self.driver_metadata[abbr].update({
                            'total_distance': dist,
                            'gap_ahead': gap if gap is not None else 0.0,
                            'speed': speed, 'rpm': rpm, 'gear': gear,
                            'throttle': throttle, 'brake': brake, 'drs': drs, 'lap_number': lap
                        })
                
                        if dist is not None and pd.notna(dist):
                            race_positions.append((abbr, dist))
                        
                        self.driver_row_counters[abbr] = current_row_index
                        
                except Exception as e:
                    print(f"Update error for table {table_name}: {e}")
                    
        if race_positions:
            race_positions.sort(key=lambda x: x[1], reverse=True)
            self.sorted_drivers = [d[0] for d in race_positions]

    def on_draw(self):
        self.clear()
        
        try:  
            leader_lap = self.driver_metadata.get(self.sorted_drivers[0], {}).get('lap_number', 0)
        except Exception as e:
            leader_lap = 0
            print(f"Skipping track draw due to error: {e}") 
                    
        if self.selected_driver is None:  
            
            if self.corner_data:
                try:
                    draw_corners(self.corner_data, self.rotation, self.track_scale, self.offset_x, self.offset_y)
                except Exception as e:
                    print(f"Skipping corner draw due to error: {e}")
             
            draw_track(self.fx, self.fy, self.sorted_drivers, leader_lap, self.db_path, scale=1.0)
                     
            for abbr in self.sorted_drivers:
                pos = self.current_car_positions.get(abbr)
                if pos is None or pos == (0, 0):
                    continue

                fx, fy = get_screen_coords(
                    pos[0], pos[1],
                    self.rotation, self.track_scale, self.offset_x, self.offset_y
                )
                color = self.car_colors.get(abbr, arcade.color.GRAY)
                arcade.draw_circle_filled(fx, fy, 8, color)
                arcade.draw_text(abbr, fx + 12, fy, arcade.color.WHITE, 10, bold=True, anchor_y="center")
                 
            self.leaderboard_hitboxes = draw_leaderboard(
                self.sorted_drivers, 
                self.driver_metadata, 
                self.car_colors, 
                self.height
            )
                 
        else:  
            draw_focused_driver_telemetry(
                self, leader_lap, get_screen_coords, draw_track, draw_tel
            )       
        
        # Draw Lap Number
        try:
            total_laps = int(self.results_df['Laps'].max()) if self.results_df is not None else 0
        except (ValueError, TypeError):
            total_laps = 0
        draw_lap_number(self.sorted_drivers, self.driver_metadata, self.width, self.height, int(total_laps))
        
        # Draw Weather Card 
        if self.current_weather is not None:
            draw_weather_card(self.current_weather, self.width, self.height)

        # Draw playback controls (always on top)
        self._draw_playback_controls()

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:

            # Check playback control buttons first
            for name, box in self.control_hitboxes.items():
                if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                    if name == "SLOW":
                        self._on_slow(None)
                    elif name == "PAUSE":
                        self._on_pause(None)
                    elif name == "FAST":
                        self._on_fast(None)
                    return

            # Check leaderboard hitboxes
            hitboxes = getattr(self, "leaderboard_hitboxes", []) or []
            for box in hitboxes:
                if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                    print(f"Selecting Driver: {box['driver']}")
                    self.selected_driver = box['driver']
                    return   
                
            print("Clicked empty area. Resetting to full track view.")
            self.selected_driver = None


def main(delete_on_exit=True):
    window = None
    try: 
        window = F1ReplayWindow()
        arcade.run()
    except Exception as e: 
        print(f"An unexpected error occurred: {e}")
    finally: 
        if delete_on_exit and window and hasattr(window, 'exporter'):
            print("Cleaning up database files before exit as requested...")  
        else:
            print("Persistence mode: Database files preserved for next run.")  

if __name__ == "__main__": 
    main(delete_on_exit=False)