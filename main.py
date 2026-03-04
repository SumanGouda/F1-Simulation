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

        self.current_index = {}
        self.speed_array = {}
        self.car_position = {}
        self.track_points = [] 
        self.results = None
        self.current_speed_value = {}

        self.setup()

    def setup(self):
        # 1️⃣ Load session
        manager = SessionManager(YEAR, GP, SESSION_TYPE)
        self.results = manager.get_session_results()

        first_driver = self.results.iloc[0]['Abbreviation']
        session = manager.session  
        driver_laps = session.laps.pick_driver(first_driver)

        # Sort laps in order
        driver_laps = driver_laps.sort_values("LapNumber")

        if driver_laps.empty:
            print("No laps found for first driver.")
            return

        # 2️⃣ Process telemetry-
        processor = TelemetryProcessor(driver_laps.iloc[0])
        x, y = processor.get_track_coordinates()
        x, y = clean_track_data(x, y)
        
        # self.speed_array = processor.get_speed_data()
        if x is None:
            print("No telemetry.")
            return

        # 3️⃣ Transform track
        rotation = manager.get_circuit_rotation()

        # Define the size of the drawing area (the 'card' inside the window)
        # Higher padding = smaller track
        padding = 300 
        draw_width = SCREEN_WIDTH - padding
        draw_height = SCREEN_HEIGHT - padding

        # Transform and scale the raw data
        x, y = transform_track(
            x,
            y,
            draw_width,
            draw_height,
            rotation=rotation
        )
        # --- CENTER THE TRACK ---
        # 1. Find the current center of the track points
        track_center_x = (min(x) + max(x)) / 2
        track_center_y = (min(y) + max(y)) / 2

        # 2. Find the center of screen
        screen_center_x = SCREEN_WIDTH / 2
        screen_center_y = SCREEN_HEIGHT / 2

        # 3. Apply the difference as an offset to every point
        x = x + (screen_center_x - track_center_x)
        y = y + (screen_center_y - track_center_y)

        # Convert to list of (x, y) tuples for Arcade
        self.track_points = list(zip(x, y))
        
        for _, row in self.results.iterrows():
            abbr = row['Abbreviation']
            driver_lap = manager.get_driver_laps(abbr, fastest_lap=True)
            
            if driver_lap is not None:
                d_processor = TelemetryProcessor(driver_lap)

                self.speed_array[abbr] = d_processor.get_speed_data()
                self.current_index[abbr] = 0.0
                self.car_position[abbr] = self.track_points[0]
                self.current_speed_value[abbr] = 0
        
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
        for abbr, position in self.car_position.items():

            x, y = position

            arcade.draw_circle_filled(
                x,
                y,
                6,
                arcade.color.RED
            )
            arcade.draw_text(
                abbr,
                x + 10,
                y + 10,
                arcade.color.WHITE,
                10,
                bold=True
            )

        # # 4️⃣ Speedometer
        # self.draw_speedometer()
    
    def on_update(self, delta_time):
        if not self.track_points or not self.speed_array:
            return

        max_points = len(self.track_points)

        # Loop through each driver
        for abbr in self.speed_array:

            speeds = self.speed_array[abbr]
            index = self.current_index[abbr]

            if len(speeds) == 0:
                continue

            # Get current speed
            current_speed = speeds[int(index) % len(speeds)]
            self.current_speed_value[abbr] = current_speed

            # Movement calculation
            movement = current_speed * delta_time * 0.05

            max_idx = min(max_points, len(speeds)) - 1

            # Update index with looping
            index = (index + movement) % max_idx
            self.current_index[abbr] = index

            # Interpolation
            base_index = int(index)
            next_index = (base_index + 1) % max_points

            t = index - base_index

            x1, y1 = self.track_points[base_index]
            x2, y2 = self.track_points[next_index]

            interp_x = x1 + (x2 - x1) * t
            interp_y = y1 + (y2 - y1) * t

            self.car_position[abbr] = (interp_x, interp_y)

    def draw_leaderboard(self):
        if not self.current_index:
            return

        box_color = (54, 113, 198)

        start_x = 120
        start_y = SCREEN_HEIGHT - 60
        box_width = 180
        box_height = 35
        spacing = 45

        # 🔥 SORT BY TRACK PROGRESS
        sorted_drivers = sorted(
            self.current_index.items(),
            key=lambda item: item[1],
            reverse=True
        )

        for i, (abbr, _) in enumerate(sorted_drivers):

            center_x = start_x
            center_y = start_y - i * spacing

            arcade.draw_lrbt_rectangle_filled(
                center_x - (box_width / 2),
                center_x + (box_width / 2),
                center_y - (box_height / 2),
                center_y + (box_height / 2),
                box_color
            )

            speed = int(self.current_speed_value.get(abbr, 0))

            arcade.draw_text(
                f"{i+1}. {abbr}  {speed} km/h",
                center_x,
                center_y,
                arcade.color.WHITE,
                font_size=12,
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
    
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
    