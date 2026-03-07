import arcade
import fastf1
import numpy as np

from core.session_manager import SessionManager
from core.telemetry_processor import TelemetryProcessor
from utils.helpers import prepare_track_layout, get_screen_coords

SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 900
SCREEN_TITLE = "F1 Track Visualizer"

YEAR = 2025
GP = "Bahrain"
SESSION_TYPE = "R"

def hex_to_rgb(hex_str):
    """Converts a hex string (with or without #) to an RGB tuple."""
    if not hex_str or not isinstance(hex_str, str): return (128, 128, 128)
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

class F1Visualizer(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        # Initialize all attributes to avoid "AttributeError" on first frame
        self.driver_data = {}
        self.sorted_drivers = []
        self.track_points = [] 
        self.current_speed_value = 0
        self.current_gear_value = 0
        self.current_rpm_value = 0
        self.rotation = 0
        self.offset_x = 0
        self.offset_y = 0
        self.draw_width = 0
        self.draw_height = 0
        
        self.setup()

    def setup(self):
        self.manager = SessionManager(YEAR, GP, SESSION_TYPE)
        session = self.manager.session
        if session is None: return

        self.driver_data.clear() 
        results = session.results

        # 1. Process Driver Telemetry
        for _, row in results.iterrows():
            abbr = row['Abbreviation']
            driver_laps = session.laps.pick_driver(abbr)
            if driver_laps.empty: continue

            laps_dict = {}
            for _, lap in driver_laps.iterrows():
                lap_num = int(lap['LapNumber'])
                tp = TelemetryProcessor(lap)
                tx, ty = tp.get_track_coordinates()
                
                if tx is None or tp.telemetry is None: continue 

                laps_dict[lap_num] = {
                    "x": tx, 
                    "y": ty,
                    "time": tp.telemetry["Time"].dt.total_seconds().to_numpy(),
                    "rpm": tp.get_RPM_data(),
                    "speed": tp.get_speed_data(),
                    "throttle": tp.get_throttle_data(),
                    "brake": tp.get_brake_data(),
                    "ngear": tp.telemetry["nGear"].to_numpy() if "nGear" in tp.telemetry else np.zeros(len(tx)),
                    "driver_ahead": tp.get_driver_ahead(),
                    "distance_ahead": tp.get_distance_ahead(),
                    "distance": tp.telemetry["Distance"].to_numpy() 
                }
            
            if not laps_dict: continue

            self.driver_data[abbr] = {
                "team_name": row['TeamName'],
                "color": row['TeamColor'],
                "name": row['FullName'],
                "driver_number": row['DriverNumber'],
                "laps": laps_dict,
                "current_lap": min(laps_dict.keys()),
                "current_index": 0,
                "finished": False,
                "lap_timer": 0.0
            }

        # 2. Track Setup 
        fastest_lap = session.laps.pick_fastest()
        tp_fastest = TelemetryProcessor(fastest_lap)
        raw_x, raw_y = tp_fastest.get_track_coordinates()

        if raw_x is not None:
            self.track_length = tp_fastest.telemetry["Distance"].max()
            self.rotation = self.manager.get_circuit_rotation()
            self.padding_left = 320 # Room for leaderboard 
            
            layout = prepare_track_layout(
                raw_x, raw_y, 
                SCREEN_WIDTH, SCREEN_HEIGHT, 
                self.padding_left, self.rotation
            )
            (self.track_points, self.offset_x, self.offset_y, self.track_scale) = layout
            
    def on_draw(self):
        self.clear()
        
        if self.track_points:
            arcade.draw_line_strip(self.track_points, arcade.color.DARK_GREEN, 3)
        
        self.draw_leaderboard()
        # self.draw_speedometer() # Added speedometer call
        
        # Layer 3: Driver Dots & On-Track Labels
        for abbr in self.sorted_drivers:
            data = self.driver_data[abbr]
            
            # 1. Get THIS driver's specific lap and index [cite: 2026-01-20]
            lap_num = data["current_lap"]
            max_idx = len(data["laps"][lap_num]["x"]) - 1
            idx = min(data["current_index"], max_idx)
            
            # 2. Extract coordinates from THIS driver's lap data [cite: 2026-01-20]
            # Do not use a global track_x/y variable here!
            raw_x = data["laps"][lap_num]["x"][idx]
            raw_y = data["laps"][lap_num]["y"][idx]
            
            # 3. Calculate screen position using the saved track_scale [cite: 2026-01-20]
            final_x, final_y = get_screen_coords(
                raw_x, raw_y,
                self.rotation,
                self.track_scale,
                self.offset_x,
                self.offset_y
            )

            # 4. Draw the driver's circle and abbreviation [cite: 2026-01-20]
            color = hex_to_rgb(data["color"])
            arcade.draw_circle_filled(final_x, final_y, 7, color)
            arcade.draw_text(
                f"{abbr}", 
                final_x + 15, final_y, 
                arcade.color.WHITE, 10, bold=True
            )
        
    def on_update(self, delta_time):
        """Updates driver positions and telemetry data independently."""
        speed_multiplier = 3.0  
        race_positions = []
        
        # Initialize the leaderboard timer if it doesn't exist [cite: 2026-01-20]
        if not hasattr(self, "leaderboard_timer"): 
            self.leaderboard_timer = 0.0
        self.leaderboard_timer += delta_time

        for abbr, data in self.driver_data.items():
            # 1. Handle finished drivers [cite: 2026-01-20]
            if data.get("finished", False):
                # Use infinity to keep them at the top or bottom of the sort logic [cite: 2026-01-20]
                race_positions.append((abbr, float('inf')))
                continue

            # 2. Advance the individual driver stopwatch [cite: 2026-01-20]
            data["lap_timer"] += delta_time * speed_multiplier
            
            lap_num = data["current_lap"]
            lap_data = data["laps"][lap_num]
            times = lap_data["time"]

            # 3. Find current position in telemetry using binary search [cite: 2026-01-20]
            current_index = np.searchsorted(times, data["lap_timer"], side="left")

            # 4. Instant Lap Transition: Check if the driver finished the current lap [cite: 2026-01-20]
            if current_index >= len(times):
                next_lap = lap_num + 1
                if next_lap in data["laps"]:
                    # Transition immediately to the start of the next lap [cite: 2026-01-20]
                    data["current_lap"] = next_lap
                    data["lap_timer"] = 0.0  # Reset only THIS driver's stopwatch [cite: 2026-01-20]
                    
                    # Update local variables to the new lap's data for immediate calculation [cite: 2026-01-20]
                    lap_num = next_lap
                    lap_data = data["laps"][lap_num]
                    current_index = 0 
                else:
                    # No more laps; flag as finished and cap at the last telemetry point [cite: 2026-01-20]
                    data["finished"] = True
                    data["current_index"] = len(times) - 1
                    race_positions.append((abbr, float('inf')))
                    continue

            # 5. Bound checking to prevent IndexError [cite: 2026-01-20]
            data["current_index"] = min(current_index, len(times) - 1)
            
            # 6. Calculate total race distance for the card-style leaderboard [cite: 2026-01-20, 2026-02-20]
            # (Current Lap * Track Length) + Meters into current lap [cite: 2026-01-20]
            track_length = lap_data["distance"][-1] 
            total_dist = (lap_num * track_length) + lap_data["distance"][data["current_index"]]
            race_positions.append((abbr, total_dist))

        # 7. Update sorted_drivers list for rendering [cite: 2026-01-20]
        # We ensure it runs on the first frame and then every 0.2s for performance [cite: 2026-01-20]
        if not self.sorted_drivers or self.leaderboard_timer > 0.2:
            race_positions.sort(key=lambda x: x[1], reverse=True)
            self.sorted_drivers = [d[0] for d in race_positions]
            self.leaderboard_timer = 0.0

        # 8. Update Dashboard values based on the current race leader [cite: 2026-01-20]
        if self.sorted_drivers:
            leader_abbr = self.sorted_drivers[0]
            leader = self.driver_data[leader_abbr]
            if not leader["finished"]:
                ld = leader["laps"][leader["current_lap"]]
                li = leader["current_index"]
                self.current_speed_value = ld["speed"][li]
                self.current_gear_value = ld["ngear"][li]
                self.current_rpm_value = ld["rpm"][li]
        
    def draw_leaderboard(self):
        # 1. Safety check: Don't draw if we haven't sorted any drivers yet [cite: 2026-01-20]
        if not self.sorted_drivers:
            return

        # 2. Layout Settings for Desktop Webpage [cite: 2025-12-16]
        start_x = 130  # X position for the center of the card
        start_y = SCREEN_HEIGHT - 50
        box_width = 240
        box_height = 28
        spacing = 32

        # 3. Loop through sorted drivers (P1 down to the last) [cite: 2026-01-20]
        for i, abbr in enumerate(self.sorted_drivers):
            curr_y = start_y - (i * spacing)
            data = self.driver_data[abbr]
            
            # Get the current lap data and index [cite: 2026-01-20]
            lap_num = data["current_lap"]
            lap_data = data["laps"][lap_num]
            idx = data["current_index"]

            # Define driver color [cite: 2026-01-20]
            color = hex_to_rgb(data["color"])
            
            # --- DRAW THE CARD --- [cite: 2026-02-20]
            # Draw the main colored card background
            arcade.draw_rect_filled(
                arcade.rect.XYWH(start_x, curr_y, box_width, box_height), 
                color
            )
            
            # Draw a dark overlay on the right half for the gap timing [cite: 2026-01-20]
            # (start_x + 60 shifts the overlay slightly to the right)
            arcade.draw_rect_filled(
                arcade.rect.XYWH(start_x + 60, curr_y, box_width / 2, box_height), 
                (0, 0, 0, 100) # Semi-transparent black [cite: 2026-01-20]
            )

            # --- PREPARE TEXT --- [cite: 2026-01-20]
            # "INTERVAL" shows for P1; actual time gap shows for everyone else
            gap_seconds = lap_data["distance_ahead"][idx]
            if i == 0:
                gap_text = "INTERVAL"
            elif not np.isnan(gap_seconds):
                gap_text = f"+{gap_seconds:.3f}s"
            else:
                gap_text = "---"

            # --- DRAW TEXT --- [cite: 2026-01-20]
            # Position/Abbr (Left side of card)
            arcade.draw_text(
                f"{i+1}  {abbr}", 
                start_x - 110, curr_y, 
                arcade.color.WHITE, 12, 
                anchor_x="left", anchor_y="center", bold=True
            )
            
            # Gap Time (Right side of card)
            arcade.draw_text(
                gap_text, 
                start_x + 110, curr_y, 
                arcade.color.WHITE, 11, 
                anchor_x="right", anchor_y="center"
            )            
            # --- END OF DRAWING ---
            
    
def main():
    fastf1.Cache.enable_cache("cache")
    window = F1Visualizer()
    arcade.run()

if __name__ == "__main__":
    main()