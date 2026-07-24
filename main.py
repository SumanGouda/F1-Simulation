import os
import arcade
import sqlite3
import warnings
import pandas as pd
warnings.filterwarnings("ignore")
from core.data_exporter import DataExporter
from core.session_manager import SessionManager
from UI.pos_chart_tab import draw_position_chart
from UI.foc_tab import draw_focused_driver_telemetry
from UI.selection_tkinter_ui import get_race_selection
from core.telemetry_processor import TelemetryProcessor
from UI.h2h_tab import draw_h2h_selection_panel, draw_data_card
from UI.playback_controls import draw_playback_controls, on_slow, on_pause, on_fast
from UI.main_window import draw_tab_bar, draw_leaderboard, draw_lap_number, draw_corners, draw_weather_card, draw_track



from utils.helpers import (
    get_max_session_rows, hex_to_rgb, get_results_from_db,
    prepare_track_layout, get_screen_coords, calculate_weather_frame_ratio,
)

SCREEN_WIDTH        = 1500
SCREEN_HEIGHT       = 900

TRACK_PADDING_LEFT  = 500  # increase → smaller / more left-padded track

class F1ReplayWindow(arcade.Window):
    def __init__(self, year, gp_name):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT)
        arcade.set_background_color(arcade.color.BLACK)

        # --- Session Info & Window Metadata ---
        self.year           = year
        self.gp_name        = gp_name.lower()
        self.screen_title   = f"F1 Race Replay - {self.gp_name.title()} {self.year}"
        self.set_caption(self.screen_title)

        # --- Track Layout ---
        self.track_scale_focused    = 0.5
        self.foc_offset_x           = 1200
        self.foc_offset_y           = 0
        self.fx                     = None
        self.fy                     = None
        self.raw_x                  = None
        self.raw_y                  = None

        # --- App State ---
        self.sorted_drivers         = []
        self.corner_data            = []
        self.driver_metadata        = {}
        self.current_weather        = None
        self.selected_driver        = None
        self.leaderboard_gap_caches = {}

        # --- UI Components & Hitboxes ---
        self.control_hitboxes       = {}
        self.back_hitbox            = {}
        self.h2h_compare_btn        = {}

        # --- UI Navigation & Simulation State ---
        self.show_lap_chart         = False
        self.h2h_comparison         = False
        self.h2h_confirmed          = False
        self.is_paused              = False
        self.h2h_selected           = []

        # --- Asset Loading ---
        self.btn_icons = {
            "SLOW"  :   arcade.load_texture("assets/images/slow.png"),
            "PAUSE" :   arcade.load_texture("assets/images/pause.png"),
            "PLAY"  :   arcade.load_texture("assets/images/play.png"),
            "FAST"  :   arcade.load_texture("assets/images/fast.png"),
        }

        # --- Setup ---
        self.setup()

    # ─────────────────────────────────────────────
    #  SETUP
    # ─────────────────────────────────────────────

    def setup(self):
        # 1. Session
        self.session_manager = SessionManager(
            year=self.year, gp=self.gp_name.title(), session_type="R")
        if self.session_manager.session is None:
            print("Failed to load F1 Session.")
            return

        # 2. Database
        self.exporter = DataExporter(self.session_manager)
        self.exporter.export_all_data()
        gp_clean = self.session_manager.gp.lower()
        self.db_path = f"database/race_{gp_clean}_{self.year}/{gp_clean}_{self.year}.db"

        # 3. Driver metadata
        self.driver_metadata, self.sorted_drivers = get_results_from_db(
            self.db_path)
        self.initial_drivers = self.sorted_drivers.copy()

        # 4. Circuit layout
        self.rotation = self.session_manager.get_circuit_rotation() or 0
        self.corner_data = self.session_manager.get_corner_data()

        fastest_lap = self.session_manager.get_session_fastest_lap()
        if fastest_lap is not None:
            tp = TelemetryProcessor(fastest_lap)
            raw_x, raw_y = tp.get_track_coordinates()
            if raw_x is not None and raw_y is not None:
                self.raw_x = raw_x
                self.raw_y = raw_y
                (self.fx, self.fy, self.offset_x, self.offset_y, self.track_scale) = prepare_track_layout(
                    raw_x, raw_y, SCREEN_WIDTH, SCREEN_HEIGHT,
                    padding_left=TRACK_PADDING_LEFT, rotation=self.rotation
                )
                self.track_scale_focused = self.track_scale * 0.30
                self.fx = self.fx - 150        # shift track
                self.offset_x = self.offset_x - 150  # shift corners
                self.foc_offset_y = self.offset_y - 80   # Change to shift the track in y

        # 5. Colors & trackers
        self.car_colors = {abbr: hex_to_rgb(info.get('TeamColor', '#FFFFFF'))
                           for abbr, info in self.driver_metadata.items()}
        self.current_car_positions = {
            abbr: (0, 0) for abbr in self.driver_metadata}
        self.driver_row_counters = {abbr: 0 for abbr in self.driver_metadata}
        self.driver_float_counters = {
            abbr: 0.0 for abbr in self.driver_metadata}

        # 6. Timing & speed
        self.max_rows = get_max_session_rows(
            self.driver_metadata.keys(), self.db_path)
        self.weather_frame_ratio = calculate_weather_frame_ratio(
            self.driver_metadata.keys(), self.db_path)
        self.global_frame_counter = 0
        self.weather_index = 0
        self.race_speed = 1.5
        self.current_weather = None

    # ─────────────────────────────────────────────
    #  UPDATE
    # ─────────────────────────────────────────────

    def on_update(self, delta_time):
        if self.is_paused:
            return

        if self.global_frame_counter % self.weather_frame_ratio == 0:
            if os.path.exists(self.db_path):
                try:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT * FROM weather LIMIT 1 OFFSET ?", (int(self.weather_index),))
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
                    self.driver_float_counters[abbr] += self.race_speed
                    row_index = int(self.driver_float_counters[abbr])
                    table_name = f"telemetry_{abbr.lower()}"

                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(f"""
                        SELECT x, y, total_distance, gap_ahead, speed, rpm, ngear,
                               throttle, brake, drs, lap_number
                        FROM {table_name} LIMIT 1 OFFSET ?
                    """, (row_index,))
                    result = cursor.fetchone()
                    conn.close()

                    if result:
                        x, y, dist, gap, speed, rpm, gear, throttle, brake, drs, lap = result
                        if pd.notna(x) and pd.notna(y):
                            self.current_car_positions[abbr] = (x, y)
                        self.driver_metadata[abbr].update({
                            'total_distance': dist,
                            'gap_ahead':  gap if gap is not None else 0.0,
                            'speed': speed, 'rpm': rpm, 'gear': gear,
                            'throttle': throttle, 'brake': brake,
                            'drs': drs, 'lap_number': lap
                        })
                        if dist is not None and pd.notna(dist):
                            race_positions.append((abbr, dist))
                        self.driver_row_counters[abbr] = row_index

                except Exception as e:
                    print(f"Update error for {abbr}: {e}")

        if race_positions:
            race_positions.sort(key=lambda x: x[1], reverse=True)
            self.sorted_drivers = [d[0] for d in race_positions]

    # ─────────────────────────────────────────────
    #  DRAW
    # ─────────────────────────────────────────────

    def on_draw(self):
        self.clear()

        # Title
        arcade.draw_text(
            self.screen_title, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 20, arcade.color.RED,
            font_size=27, anchor_x="center", anchor_y="center"
        )
        # HUD
        try:
            total_laps = max(int(meta.get('Laps', 0) or 0)
                             for meta in self.driver_metadata.values())
        except (ValueError, TypeError):
            total_laps = 0

        # Leader Lap
        try:
            leader_lap = self.driver_metadata.get(
                self.sorted_drivers[0], {}).get('lap_number', 0)
        except Exception as e:
            leader_lap = 0
            print(f"Leader lap error: {e}")

        # Playback Controls
        draw_playback_controls(self)

        # Lap Chart Page
        if self.show_lap_chart:
            draw_position_chart(
                self.db_path, total_laps, len(
                    self.sorted_drivers), 120, 150, SCREEN_WIDTH - 280, SCREEN_HEIGHT - 320,
                self.car_colors, getattr(self, 'retired_icon',  None), getattr(
                    self, 'finished_icon', None)
            )

        # H2H Comparison Page
        elif self.h2h_comparison:
            draw_h2h_selection_panel(self)
            draw_track(self.fx, self.fy, self.sorted_drivers,
                       leader_lap, self.db_path)

            if self.h2h_confirmed:
                # Cars
                for abbr in self.h2h_selected:
                    pos = self.current_car_positions.get(abbr)
                    if not pos or pos == (0, 0):
                        continue
                    fx, fy = get_screen_coords(
                        pos[0], pos[1], self.rotation, self.track_scale, self.offset_x, self.offset_y)
                    color = self.car_colors.get(abbr, arcade.color.GRAY)

                    arcade.draw_circle_filled(fx, fy, 5, color)
                    arcade.draw_text(
                        abbr, fx + 12, fy, arcade.color.WHITE, 10, bold=True, anchor_y="center")
 
                draw_data_card(self, self.h2h_selected, self.db_path, SCREEN_WIDTH, SCREEN_HEIGHT)

            # Lap Number
            draw_lap_number(self.sorted_drivers, self.driver_metadata, int(total_laps))

        # Main Page
        else:
            if self.selected_driver is None:
                # Tab bar
                tabs = ["Lap Chart", "(H2H) Comparison",
                        "TELEMETRY", "WEATHER"]
                tab_w, tab_h = 160, 35
                pad = 12
                total_width = (len(tabs) * tab_w) + ((len(tabs) - 1) * pad)
                start_x = (SCREEN_WIDTH / 2) - (total_width / 2)
                self.tab_hitboxes = draw_tab_bar(
                    start_x, 120, pad, tabs, tab_w, tab_h)

                # Lap Number
                draw_lap_number(self.sorted_drivers, self.driver_metadata, int(total_laps))

                # Corners
                if self.corner_data:
                    try:
                        draw_corners(self.corner_data, self.rotation, self.track_scale, self.offset_x, self.offset_y)
                    except Exception as e:
                        print(f"Corner draw error: {e}")

                # Track
                draw_track(self.fx, self.fy, self.sorted_drivers, leader_lap, self.db_path)

                # Cars
                for abbr in self.sorted_drivers:
                    pos = self.current_car_positions.get(abbr)

                    if not pos or pos == (0, 0):
                        continue

                    fx, fy = get_screen_coords(
                        pos[0], pos[1], self.rotation, self.track_scale, self.offset_x, self.offset_y)
                    color = self.car_colors.get(abbr, arcade.color.GRAY)
                    arcade.draw_circle_filled(fx, fy, 5, color)
                    arcade.draw_text(
                        abbr, fx + 12, fy, arcade.color.WHITE, 10, bold=True, anchor_y="center")

                # Leaderboard
                self.leaderboard_hitboxes = draw_leaderboard(
                    self.sorted_drivers, self.driver_metadata, self.car_colors, self.height
                )
                # Weather Card
                if self.current_weather is not None:
                    draw_weather_card(self.current_weather, self.width, self.height)

            else:
                draw_focused_driver_telemetry(self, leader_lap, get_screen_coords, draw_track)
                draw_lap_number(self.sorted_drivers, self.driver_metadata, int(total_laps))

                if self.current_weather is not None:
                    draw_weather_card(self.current_weather, self.width, self.height)

    # ─────────────────────────────────────────────
    #  INPUT
    # ─────────────────────────────────────────────

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        for name, box in self.control_hitboxes.items():
            if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                {"SLOW": on_slow, "PAUSE": on_pause, "FAST": on_fast}[name](self)
                return

        # Lap chart view
        if self.show_lap_chart:
            if self.back_hitbox:
                box = self.back_hitbox
                if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                    self.show_lap_chart = False
                    return
            self.show_lap_chart = False
            return

        # H2H comparison view
        if self.h2h_comparison:
            # Compare button
            if self.h2h_compare_btn:
                box = self.h2h_compare_btn
                if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                    self.h2h_confirmed = True
                    return

            # Driver selection rows
            for abbr, box in self.h2h_panel_hitboxes.items():
                if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                    if abbr in self.h2h_selected:
                        self.h2h_selected.remove(abbr)   # deselect
                    elif len(self.h2h_selected) < 3:
                        self.h2h_selected.append(abbr)   # select
                    return

            if self.h2h_panel_hitboxes:
                sample_box = next(iter(self.h2h_panel_hitboxes.values()))
                panel_left = sample_box["left"]
                panel_right = sample_box["right"]

                if x < panel_left or x > panel_right:
                    self.h2h_comparison = False
                    self.h2h_confirmed = False
                    self.h2h_selected = []
                    return

            return

        # Tab bar
        if hasattr(self, 'tab_hitboxes'):
            for label, box in self.tab_hitboxes.items():
                if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                    if label == "Lap Chart":
                        self.show_lap_chart = True
                    elif label == "(H2H) Comparison":
                        self.h2h_comparison = True
                    return

        # Leaderboard
        for box in getattr(self, "leaderboard_hitboxes", []) or []:
            if box["left"] <= x <= box["right"] and box["bottom"] <= y <= box["top"]:
                self.selected_driver = box['driver']
                return

        self.selected_driver = None


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────

def main(delete_on_exit=True):
    year, gp = get_race_selection()
    if year is None or gp is None:
        print("No selection made. Exiting.")
        return

    window = None
    try:
        window = F1ReplayWindow(year=year, gp_name=gp)
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
