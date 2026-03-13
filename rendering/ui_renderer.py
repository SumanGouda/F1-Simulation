# Starter file
import arcade
import math

def draw_leaderboard(sorted_drivers, driver_metadata, car_colors, screen_height):
    # Moved start_y down from -70 to -120 to 'drag' it down the screen
    start_x, start_y = 130, screen_height - 120 
    box_width = 240
    box_height = 28
    spacing = 32
    border_thickness = 3

    for i, abbr in enumerate(sorted_drivers):
        meta = driver_metadata.get(abbr, {})
        color = car_colors.get(abbr, arcade.color.GRAY)
        curr_y = start_y - (i * spacing)
        
        # Draw the Border (Team Color)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(start_x, curr_y, box_width, box_height), 
            color
        )
        # Draw the Inner Fill (Solid Black)
        arcade.draw_rect_filled(
            arcade.rect.XYWH(
                start_x, curr_y, 
                box_width - border_thickness, 
                box_height - border_thickness
            ), 
            arcade.color.BLACK
        )

        # --- GAP LOGIC ---
        if i == 0:
            gap_display = "INTERVAL"
        else:
            ahead_abbr = sorted_drivers[i-1]
            ahead_meta = driver_metadata.get(ahead_abbr, {})
            dist_now = meta.get('total_distance', 0.0)
            dist_ahead = ahead_meta.get('total_distance', 0.0)
            gap_meters = dist_ahead - dist_now
            speed_kmh = meta.get('speed', 0.1) 
            speed_ms = max(speed_kmh / 3.6, 0.5) 
            gap_seconds = gap_meters / speed_ms
            gap_display = f"+{max(0, gap_seconds):.1f}s"
        
        # Draw Text Elements
        arcade.draw_text(
            f"{i+1}  {abbr}", 
            start_x - 110, curr_y, 
            arcade.color.WHITE, 12, bold=True, anchor_y="center"
        )
        arcade.draw_text(
            gap_display, 
            start_x + 110, curr_y, 
            arcade.color.WHITE, 11, bold=True, anchor_x="right", anchor_y="center"
        )

def draw_lap_number(sorted_drivers, driver_metadata, screen_width, screen_height, total_laps): 
    start_x = screen_width - 150 
    start_y = screen_height - 70
    
    box_width = 240
    box_height = 40  
    border_thickness = 3
    
    # 2. Extract Data  
    if not sorted_drivers:
        return
        
    lead_abbr = sorted_drivers[0]
    meta = driver_metadata.get(lead_abbr, {}) 
    lap_number = int(meta.get('lap_number', 1))
    
    # 3. Draw the Card Style 
    arcade.draw_rect_filled(
        arcade.rect.XYWH(start_x, start_y, box_width, box_height), 
        arcade.color.WHITE
    )
    # Inner Fill (Solid Black)
    arcade.draw_rect_filled(
        arcade.rect.XYWH(
            start_x, start_y, 
            box_width - border_thickness, 
            box_height - border_thickness
        ), 
        arcade.color.BLACK
    )

    # 4. Draw Lap Text
    arcade.draw_text(
        f"LAP {lap_number} / {total_laps}", 
        start_x, start_y, 
        arcade.color.WHITE, 16, bold=True, 
        anchor_x="center", anchor_y="center"
    )
 
def draw_corners(corner_data, rotation, track_scale, offset_x, offset_y):
    """
    Renders corner markers and labels slightly offset from the track line.
    """
    if not corner_data:
        return

    # Pre-calculate rotation math once to save FPS [cite: 2026-03-07]
    rad = math.radians(rotation)
    cos_val = math.cos(rad)
    sin_val = math.sin(rad)
    
    # Distance to push the marker away from the track (in pixels)
    push_distance = 15 

    for corner in corner_data:
        raw_x = corner['x']
        raw_y = corner['y']
        
        # 1. Rotate the raw coordinates
        rx = raw_x * cos_val - raw_y * sin_val
        ry = raw_x * sin_val + raw_y * cos_val
        
        # 2. Basic Scale and Offset
        fx = (rx * track_scale) + offset_x
        fy = (ry * track_scale) + offset_y

        # 3. Apply "Side-of-Track" Offset [cite: 2026-03-07]
        # We use the 'angle' provided by FastF1 to determine the 'outside' direction
        # Angle is in degrees, convert to radians
        angle_rad = math.radians(corner.get('angle', 0) + rotation)
        
        # Adjust fx and fy to move them slightly off-center from the track line
        fx += math.cos(angle_rad) * push_distance
        fy += math.sin(angle_rad) * push_distance
        
        # 4. Draw Marker (Yellow Dot)
        arcade.draw_circle_filled(fx, fy, 3, arcade.color.YELLOW)
        
        # 5. Draw Text (Simplified for better performance)
        label = corner['number']
        arcade.draw_text(
            label, 
            fx, 
            fy + 8, # Positioned slightly above the dot
            arcade.color.WHITE, 
            9, 
            bold=True, 
            anchor_x="center",
            font_name="Kenney Future" # Optional: matches your card style
        )
                  
class UIRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def draw_driver_info(self, driver_name, team_name):
        arcade.draw_text(
            f"Driver: {driver_name}",
            20,
            self.height - 40,
            arcade.color.WHITE,
            16
        )

        arcade.draw_text(
            f"Team: {team_name}",
            20,
            self.height - 70,
            arcade.color.LIGHT_GRAY,
            14
        )

    def draw_speed(self, speed):
        arcade.draw_text(
            f"{int(speed)} km/h",
            self.width - 200,
            40,
            arcade.color.RED,
            28,
            bold=True
        )

    def draw_lap_time(self, lap_time):
        arcade.draw_text(
            f"Lap Time: {lap_time}",
            20,
            self.height - 100,
            arcade.color.YELLOW,
            14
        )