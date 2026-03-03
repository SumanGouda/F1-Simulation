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
DRIVER = "VER"


class F1Visualizer(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        arcade.set_background_color(arcade.color.BLACK)

        self.current_index = 0
        self.speed_array = None
        self.car_position = None
        self.track_points = None

        self.setup()

    def setup(self):
        # 1️⃣ Load session
        manager = SessionManager(YEAR, GP, SESSION_TYPE)

        lap = manager.get_driver_laps(DRIVER, fastest_lap=True)
        if lap is None:
            print("No lap found.")
            return

        # 2️⃣ Process telemetry-
        processor = TelemetryProcessor(lap)

        x, y = processor.get_track_coordinates()
        x, y = clean_track_data(x, y)
        
        self.speed_array = processor.get_speed_data()
        
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
        # ------------------------

        # Convert to list of (x, y) tuples for Arcade
        self.track_points = list(zip(x, y))
        
    def on_draw(self):
        self.clear()
        
        if self.track_points:
            arcade.draw_line_strip(
                self.track_points,
                arcade.color.GREEN,
                5
            )
        if self.car_position:
            arcade.draw_circle_filled(
                self.car_position[0],
                self.car_position[1],
                6,
                arcade.color.RED
            )
            
    def on_update(self, delta_time):
        if not self.track_points or self.speed_array is None:
            return

        # Use the smaller length to avoid 'Out of Index' errors
        # track_points has +1 point now because of the loop closure
        max_idx = min(len(self.track_points), len(self.speed_array)) - 1

        if self.current_index >= max_idx:
            self.current_index = 0  # Reset to start of lap
            return

        # Get speed at current point
        speed = self.speed_array[int(self.current_index)]
        
        # Adjust movement factor if the car feels too slow/fast
        movement = speed * delta_time * 0.05 
        self.current_index += movement

        # Interpolation logic
        base_index = int(self.current_index)
        next_index = (base_index + 1) % len(self.track_points) # Loop back to 0 if at end

        t = self.current_index - base_index

        x1, y1 = self.track_points[base_index]
        x2, y2 = self.track_points[next_index]

        interp_x = x1 + (x2 - x1) * t
        interp_y = y1 + (y2 - y1) * t

        self.car_position = (interp_x, interp_y)
            
def main():
    fastf1.Cache.enable_cache("cache")
    window = F1Visualizer()
    arcade.run()

if __name__ == "__main__":
    main()