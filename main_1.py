import arcade
import fastf1

from core.session_manager import SessionManager
from core.telemetry_processor import TelemetryProcessor
from core.track_utils import transform_track, clean_track_data


SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800
SCREEN_TITLE = "F1 Track Visualizer"

YEAR = 2023
GP = "Monza"
SESSION_TYPE = "R"
# DRIVER = "VER"


class F1Visualizer(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)

        self.driver_data = {}
        self.sorted_drivers = []
        self.track_points = []   
        
        
        # self.current_lap = {}
        # self.current_index = {}
        # self.speed_array = {}
        # self.car_position = {}
        # self.track_points = [] 
        # self.results = None
        # self.current_speed_value = {}

        self.setup()

    def setup(self):
        self.manager = SessionManager(YEAR, GP, SESSION_TYPE)
        session = self.manager.session
        if session is None: return

        self.driver_data.clear()
        results = session.results.sort_values(by='GridPosition')

        for _, row in results.iterrows():
            abbr = row['Abbreviation']
            driver_laps = session.laps.pick_driver(abbr)
            if driver_laps.empty: continue

            lap_list = []
            for _, lap in driver_laps.iterrows():
                telemetry = lap.get_telemetry()
                if telemetry is None or telemetry.empty: continue

                lap_data = {
                    "x": telemetry["X"].to_numpy(),
                    "y": telemetry["Y"].to_numpy(),
                    "speed": telemetry["Speed"].to_numpy(),
                    "time": telemetry["Time"].dt.total_seconds().to_numpy() 
                }
                lap_list.append(lap_data)

            if lap_list:
                self.driver_data[abbr] = {
                    "laps": lap_list,
                    "current_lap": 0,
                    "current_index": 0,
                    "total_laps": len(lap_list),
                    "finished": False,
                    "total_time": 0.0,
                    "color": row['TeamColor']
                }

        # --- ALIGNMENT & ROTATION FIX ---
        first_lap = next(iter(self.driver_data.values()))["laps"][0]
        rotation = self.manager.get_circuit_rotation()

        padding_left = 320
        draw_width = SCREEN_WIDTH - padding_left - 100
        draw_height = SCREEN_HEIGHT - 150

        # Transform track and GET the scale used
        # (Assuming your transform_track returns x, y, AND scale)
        x_rot, y_rot = transform_track(
            first_lap["x"], 
            first_lap["y"], 
            draw_width, 
            draw_height, 
            rotation=rotation
        )

        # Calculate bounding box for the cars to use
        self.min_x, self.max_x = min(first_lap["x"]), max(first_lap["x"])
        self.min_y, self.max_y = min(first_lap["y"]), max(first_lap["y"])
        
        # Calculate the scale manually if your utility doesn't return it
        scale_x = draw_width / (self.max_x - self.min_x)
        scale_y = draw_height / (self.max_y - self.min_y)
        self.track_scale = min(scale_x, scale_y) # ✅ FIX: Now this exists!

        # Center the rotated track
        track_center_x = (min(x_rot) + max(x_rot)) / 2
        track_center_y = (min(y_rot) + max(y_rot)) / 2
        
        screen_center_x = padding_left + (draw_width / 2)
        screen_center_y = SCREEN_HEIGHT / 2

        self.offset_x = screen_center_x - track_center_x
        self.offset_y = screen_center_y - track_center_y
        self.rotation = rotation
        
        self.track_points = []
        for xi, yi in zip(x_rot, y_rot):
            self.track_points.append((xi + self.offset_x, yi + self.offset_y))
            
    def on_draw(self):
        self.clear()

        # 1️⃣ Leaderboard
        self.draw_leaderboard()

        # 2️⃣ Track
        if self.track_points:
            arcade.draw_line_strip(
                self.track_points,
                arcade.color.GREEN,
                5
            )
        
        # 3️⃣ All Cars
        for abbr, data in self.driver_data.items():
            if data["finished"]: continue

            lap_data = data["laps"][data["current_lap"]]
            raw_x = lap_data["x"][data["current_index"]]
            raw_y = lap_data["y"][data["current_index"]]

            # Use the SAME dimensions used in setup() to calculate track_points
            tx, ty = transform_track(
                [raw_x], [raw_y], 
                SCREEN_WIDTH - 420, SCREEN_HEIGHT - 150, 
                rotation=self.rotation
            )
            
            final_x = tx[0] + self.offset_x
            final_y = ty[0] + self.offset_y

            arcade.draw_circle_filled(final_x, final_y, 5, arcade.color.RED)
            arcade.draw_text(abbr, final_x + 8, final_y + 8, arcade.color.WHITE, 9)
                    
    def on_update(self, delta_time):
        race_positions = []

        for abbr, data in self.driver_data.items():
            if data["finished"]: continue

            lap_idx = data["current_lap"]
            pt_idx = data["current_index"]
            lap_data = data["laps"][lap_idx]

            # UPDATE TIME: Get the timestamp for the current point
            data["total_time"] = lap_data["time"][pt_idx]

            # Move forward
            data["current_index"] += 1
            if data["current_index"] >= len(lap_data["x"]):
                data["current_index"] = 0
                data["current_lap"] += 1
                if data["current_lap"] >= data["total_laps"]:
                    data["finished"] = True
                    continue

            # Sort helper: using (Lap * 100000 + Index) to track who is ahead
            progress = (data["current_lap"] * 100000) + data["current_index"]
            race_positions.append((abbr, progress))

        # Sort leaderboard by progress
        race_positions.sort(key=lambda x: x[1], reverse=True)
        self.sorted_drivers = [d[0] for d in race_positions]

    def draw_leaderboard(self):
        if not self.sorted_drivers: return

        start_x = 130
        start_y = SCREEN_HEIGHT - 30
        box_width = 220
        box_height = 24  # Thinner for 22 drivers
        spacing = 28     # Tighter spacing

        leader_time = self.driver_data[self.sorted_drivers[0]]["total_time"]

        for i, abbr in enumerate(self.sorted_drivers):
            curr_y = start_y - (i * spacing)
            data = self.driver_data[abbr]
            
            # ✅ FIX: Convert hex string to tuple if necessary
            raw_color = data.get("color", (54, 113, 198))
            if isinstance(raw_color, str):
                color = arcade.color_from_hex_string(f"#{raw_color}")
            else:
                color = raw_color
            
            # ✅ FIX: Use LRBT (Left, Right, Bottom, Top)
            arcade.draw_lrbt_rectangle_filled(
                start_x - box_width/2, 
                start_x + box_width/2, 
                curr_y - box_height/2, 
                curr_y + box_height/2, 
                color
            )

            gap = "LEADER" if i == 0 else f"+{data['total_time'] - leader_time:.3f}s"
            arcade.draw_text(f"{abbr} {gap}", start_x, curr_y, 
                             arcade.color.WHITE, 10, anchor_x="center", 
                             anchor_y="center", bold=True)    

    def draw_speedometer(self):
        center_x = SCREEN_WIDTH - 100
        center_y = SCREEN_HEIGHT - 100
        width = 150
        height = 75
        
        arcade.draw_lrbt_rectangle_filled(
            center_x - (width / 2),
            center_x + (width / 2),
            center_y - (height / 2),
            center_y + (height / 2),
            (30, 30, 30, 200)
        )
        
        # Draw the speed text
        arcade.draw_text(
            f"Speed: {int(self.current_speed_value)}",
            center_x,
            center_y,
            arcade.color.WHITE,
            font_size=14,
            anchor_x="center",
            anchor_y="center",
            bold=True   
        )               
        arcade.draw_text(   
            "KM/H",
            center_x,
            center_y - 20,
            arcade.color.GAINSBORO,
            font_size=10,
            anchor_x="center",
            anchor_y="center",
            bold=True
        )        
                    
def main():
    fastf1.Cache.enable_cache("cache")
    window = F1Visualizer()
    arcade.run()

if __name__ == "__main__":
    main()
    