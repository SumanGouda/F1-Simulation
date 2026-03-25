# Starter file
import arcade
import math
import os
import sqlite3

def draw_leaderboard(sorted_drivers, driver_metadata, car_colors, screen_height):
    # Moved start_y down from -70 to -120 to 'drag' it down the screen
    start_x, start_y = 130, screen_height - 120 
    box_width = 240
    box_height = 28
    spacing = 32
    border_thickness = 3
    
    hitboxes = []

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
        hitboxes.append({
            "left": start_x - (box_width / 2),
            "right": start_x + (box_width / 2),
            "bottom": curr_y - (box_height / 2),
            "top": curr_y + (box_height / 2),
            "driver": abbr
        })
        
    return hitboxes

def draw_lap_number(sorted_drivers, driver_metadata, screen_width, screen_height, total_laps): 
    start_x = screen_width - 80
    start_y = screen_height - 75
    
    box_width = 80
    box_height = 50  
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
        f"{lap_number} / {total_laps}\nLAPS", 
        start_x, 
        start_y, 
        arcade.color.WHITE, 
        14, 
        bold=True, 
        anchor_x="center", 
        anchor_y="center",
        multiline=True,       
        width=box_width,     
        align="center"     
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

def draw_weather_card(weather_row, screen_width, screen_height):
    if weather_row is None:
        return

    # --- INITIALIZE STATIC CACHE (Runs once) ---
    if not hasattr(draw_weather_card, "icons"):
        icon_path = "assets/images"
        if not os.path.exists(icon_path):
            print(f"❌ ERROR: Icon folder not found at {os.path.abspath(icon_path)}")
            draw_weather_card.icons = None
        else:
            try:
                draw_weather_card.icons = {
                    'air_hot': arcade.load_texture(os.path.join(icon_path, "air_hot.png")),
                    'air_cold': arcade.load_texture(os.path.join(icon_path, "air_cold.png")),
                    'track': arcade.load_texture(os.path.join(icon_path, "track_temp.png")),
                    'humidity': arcade.load_texture(os.path.join(icon_path, "humidity.png")),
                    'wind': arcade.load_texture(os.path.join(icon_path, "wind.png"))
                }
                print("✅ Weather icons loaded successfully.")
            except Exception as e:
                print(f"❌ ERROR: Failed to load icons: {e}")
                draw_weather_card.icons = None

    # --- DEFINE CARD POSITION (Top Right) ---
    box_width, box_height = 260, 110
    padding = 20 
    center_x = screen_width - (box_width / 2) - padding
    center_y = screen_height - (box_height / 2) - padding - 100

    # --- DEFINE TEXT/ICON ANCHORS (Relative to center_x/y) ---
    left_align = center_x - (box_width / 2) + 15
    mid_point = center_x + (box_width / 2) - 85 
    
    top_y_text = center_y + (box_height / 2) - 20
    row1_y = center_y + 5    
    row2_y = center_y - 25   
    icon_size = 16      
    font_size = 13

    # --- DRAW HEADER ---
    arcade.draw_text("SESSION WEATHER", left_align, top_y_text, arcade.color.YELLOW, font_size, bold=True)
    
    #  Dry/Rain status indicator
    status_text = "DRY" if not weather_row['Rainfall'] else "RAIN"
    status_color = arcade.color.LIGHT_GREEN if not weather_row['Rainfall'] else arcade.color.SKY_BLUE
    arcade.draw_text(status_text, center_x + (box_width/2) - 45, top_y_text, status_color, font_size, bold=True)

    # --- DRAW CONTENT ---
    if draw_weather_card.icons:
         # Row 1: Air & Track
        temp = weather_row['AirTemp'] 
        icon_key = 'air_hot' if temp >= 25 else 'air_cold'
        arcade.draw_texture_rect(draw_weather_card.icons[icon_key],
            arcade.rect.XYWH(left_align + 7, row1_y, icon_size, icon_size))
        arcade.draw_text(f"{temp}°C", left_align + 28, row1_y, arcade.color.WHITE, font_size, anchor_y="center")
        arcade.draw_text(f"{temp}°C", left_align + 28, row1_y, arcade.color.WHITE, font_size, anchor_y="center")

        arcade.draw_texture_rect(draw_weather_card.icons['track'],
            arcade.rect.XYWH(mid_point + 7, row1_y, icon_size, icon_size))
        arcade.draw_text(f"{weather_row['TrackTemp']}°C", mid_point + 28, row1_y, arcade.color.WHITE, font_size, anchor_y="center")
        
        # Row 2: Humidity & Wind
        arcade.draw_texture_rect(draw_weather_card.icons['humidity'],
            arcade.rect.XYWH(left_align + 7, row2_y, icon_size, icon_size))
        arcade.draw_text(f"{weather_row['Humidity']}%", left_align + 28, row2_y, arcade.color.WHITE, font_size, anchor_y="center")
 
        arcade.draw_texture_rect(draw_weather_card.icons['wind'],
            arcade.rect.XYWH(mid_point + 7, row2_y, icon_size, icon_size))
        arcade.draw_text(f"{weather_row['WindSpeed']}m/s", mid_point + 28, row2_y, arcade.color.WHITE, font_size, anchor_y="center")
        
    else: 
        arcade.draw_text(f"Air: {weather_row['AirTemp']}°C", left_align, row1_y, arcade.color.WHITE, font_size)
        arcade.draw_text(f"Trk: {weather_row['TrackTemp']}°C", mid_point, row1_y, arcade.color.WHITE, font_size)
        arcade.draw_text(f"Hum: {weather_row['Humidity']}%", left_align, row2_y, arcade.color.WHITE, font_size)
        arcade.draw_text(f"Wnd: {weather_row['WindSpeed']}m/s", mid_point, row2_y, arcade.color.WHITE, font_size)
   
def draw_track(track_points, drv, current_lap, db_root):
    if track_points is None:
        return
    db_path =  f"{db_root}/race_data.db"
    
    if not hasattr(draw_track, "current_status"):
        draw_track.current_status = "1"
        draw_track.last_checked_lap = -1

    if current_lap != draw_track.last_checked_lap:
        try:
            leader = drv[0]
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            query = "SELECT TrackStatus FROM laps WHERE Driver = ? AND LapNumber = ?"
            cursor.execute(query, (leader, current_lap))
            result = cursor.fetchone()
            
            if result:
                draw_track.current_status = str(result[0])
                draw_track.last_checked_lap = current_lap
            
            conn.close()
        except Exception as e:
            print(f"Database injection error: {e}")
 
    status_colors = {
        '1': arcade.color.WHITE,
        '2': arcade.color.YELLOW,
        '4': arcade.color.ORANGE,
        '5': arcade.color.DARK_RED,
        '6': arcade.color.VIVID_VIOLET,
        '7': arcade.color.RED
    }
    priority_order = ['5', '4', '6', '7', '2', '1'] 
    
    color = arcade.color.ASH_GREY  # fallback
    for code in priority_order:
        if code in draw_track.current_status:
            color = status_colors[code]
            break

    arcade.draw_line_strip(track_points, color, 6)
    arcade.draw_line_strip(track_points, arcade.color.BLACK, 3)
  